import os
import subprocess
from setuptools.command.build_py import build_py
from setuptools.command.egg_info import egg_info
from setuptools.command.install import install
import logging
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

proto_src_dir = "src/protos"
proto_dest_dir = "strique_proto_schema"
prefix = "strique_proto_schema."


# Function to get all valid proto modules
def get_valid_proto_modules(proto_src_dir):
    """Get all valid proto modules that should be prefixed with strique_proto_schema."""
    logging.info(f"Getting valid proto modules from {proto_src_dir}")
    valid_modules = set()

    try:
        for root, _, files in os.walk(proto_src_dir):
            for file in files:
                if file.endswith(".proto"):
                    # Convert file path to module path
                    relative_path = os.path.relpath(
                        os.path.join(root, file), proto_src_dir
                    )
                    module_path = os.path.splitext(relative_path)[0].replace(
                        os.path.sep, "."
                    )
                    valid_modules.add(module_path)

        logging.info(f"Found {len(valid_modules)} valid proto modules")
        return valid_modules
    except Exception as e:
        logging.error(f"Error getting valid proto modules: {e}")
        raise


# Function to fix imports in a single .py file
def fix_imports_in_file(file_path, prefix):
    logging.debug(f"Fixing imports in file: {file_path}")
    try:
        with open(file_path, "r") as file:
            contents = file.read()

        # Find the section between _sym_db and DESCRIPTOR
        pattern = re.compile(
            r"(_sym_db = _symbol_database.Default\(\)\n)(.*?)(\nDESCRIPTOR = _descriptor_pool.Default\(\).AddSerializedFile)",
            re.DOTALL,
        )
        match = pattern.search(contents)
        if match:
            imports_section = match.group(2)

            # Use regular expressions to replace the import statements in the matched section
            # Ignore imports that start with 'google'
            def replace_import(match):
                module = match.group(1)
                if module.startswith("google"):
                    return match.group(0)
                return f"from {prefix}{module} import {match.group(2)}"

            modified_imports_section = re.sub(
                r"from (\S+) import (\S+)", replace_import, imports_section
            )
            # Replace the original imports section with the modified one
            contents = contents.replace(imports_section, modified_imports_section)
            logging.debug(f"Updated imports in {file_path}")
        else:
            logging.warning(f"No import section found in {file_path}")

        with open(file_path, "w") as file:
            file.write(contents)
    except Exception as e:
        logging.error(f"Error fixing imports in {file_path}: {e}")
        raise


# Function to fix imports in a single .pyi file
def fix_imports_in_pyi_file(file_path, prefix, valid_modules):
    """Fix imports in .pyi files by prefixing all valid proto modules."""
    logging.debug(f"Fixing imports in .pyi file: {file_path}")
    try:
        with open(file_path, "r") as file:
            contents = file.read()

        # Process each valid module
        for module in valid_modules:
            # Escape dots in module name for regex
            escaped_module = re.escape(module)

            # Single comprehensive pattern that handles all cases
            # Matches module names that are not already prefixed
            contents = re.sub(
                rf"(?<!{re.escape(prefix)})\b{escaped_module}(_pb2)?\b",
                f"{prefix}{module}\\1",
                contents,
            )

        with open(file_path, "w") as file:
            file.write(contents)
        logging.debug(f"Updated .pyi imports in {file_path}")
    except Exception as e:
        logging.error(f"Error fixing imports in .pyi file {file_path}: {e}")
        raise


def compile_protos():
    print("Compiling proto files...")
    logging.info("Starting compile_protos()")

    try:
        proto_files = []
        for root, _, files in os.walk(proto_src_dir):
            for file in files:
                if file.endswith(".proto"):
                    proto_files.append(os.path.join(root, file))

        logging.info(f"Found {len(proto_files)} proto files to compile")

        # Compile all the proto files in one shot
        try:
            print(f"Compiling {len(proto_files)} proto files...")
            subprocess.check_call(
                [
                    "python3",
                    "-m",
                    "grpc_tools.protoc",
                    f"--proto_path={proto_src_dir}",
                    f"--python_out={proto_dest_dir}",
                    # Generate .pyi stubs for IDE/mypy type hints
                    f"--mypy_out={proto_dest_dir}",
                    *proto_files,
                ]
            )
            print("Successfully compiled all proto files")
            logging.info("Proto compilation completed successfully")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to compile proto files: {e}")
            raise

        # Verify and log stub generation
        stub_count = 0
        for root, _, files in os.walk(proto_dest_dir):
            for file in files:
                if file.endswith(".pyi"):
                    stub_count += 1
                    logging.debug(f"Generated stub: {os.path.join(root, file)}")
        logging.info(f"Generated {stub_count} .pyi stub files")

        # Update __init__.py
        logging.info("Updating __init__.py file")
        init_file = os.path.join(proto_dest_dir, "__init__.py")
        with open(init_file, "w") as f:
            for root, _, files in os.walk(proto_dest_dir):
                for file in files:
                    if file.endswith(("_pb2.py")):
                        module_name = os.path.splitext(file)[0]
                        relative_path = os.path.relpath(root, proto_dest_dir).replace(
                            os.path.sep, "."
                        )
                        if relative_path == ".":
                            f.write(f"from .{module_name} import *\n")
                        else:
                            f.write(f"from .{relative_path}.{module_name} import *\n")
        logging.info("__init__.py file updated successfully")

        # Get valid proto modules for .pyi file processing
        valid_modules = get_valid_proto_modules(proto_src_dir)

        # Iterate over the files in the proto directory and fix imports
        logging.info("Fixing imports in generated files")
        py_files_processed = 0
        pyi_files_processed = 0
        for root, _, files in os.walk(proto_dest_dir):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    file_path = os.path.join(root, file)
                    fix_imports_in_file(file_path, prefix)
                    py_files_processed += 1
                elif file.endswith(".pyi"):
                    file_path = os.path.join(root, file)
                    fix_imports_in_pyi_file(file_path, prefix, valid_modules)
                    pyi_files_processed += 1

        logging.info(
            f"Processed {py_files_processed} .py files and {pyi_files_processed} .pyi files"
        )
        logging.info("Finished compile_protos()")

    except Exception as e:
        logging.error(f"Error in compile_protos(): {e}")
        raise


def compile_textproto():
    """
    Process textproto files to binary_pb files.
    """
    logging.info("Starting compile_textproto()")
    print("Processing textproto files...")

    try:
        textproto_files = []
        for root, _, files in os.walk(proto_src_dir):
            for file in files:
                if file.endswith(".textproto"):
                    textproto_files.append(os.path.join(root, file))

        logging.info(f"Found {len(textproto_files)} textproto files to process")

        processed_count = 0
        skipped_count = 0
        error_count = 0

        for textproto_file_path in textproto_files:
            try:
                with open(textproto_file_path, "r") as f:
                    first_line = f.readline().strip()
                    second_line = f.readline().strip()

                if not first_line.startswith("#") or not second_line.startswith("#"):
                    logging.warning(
                        f"SKIPPING: Invalid format in {textproto_file_path}"
                    )
                    skipped_count += 1
                    continue

                logging.info(
                    f"Generating binary file from textproto file for {textproto_file_path}"
                )

                proto_file_path = first_line.replace("# proto-file: ", "")
                message_name = second_line.replace("# proto-message: ", "")

                proto_file_path = f"./{proto_file_path}"

                with open(proto_file_path, "r") as f:
                    content = f.read()
                    package = re.search(r"^package\s+([^;]+);", content, re.MULTILINE)
                    if package:
                        package = package.group(1)
                    else:
                        logging.error(
                            f"ERROR: Could not find package in {proto_file_path}"
                        )
                        error_count += 1
                        continue

                proto_message_name = f"{package}.{message_name}"

                binary_file_path = textproto_file_path.replace(
                    ".textproto", ".binary_pb"
                )
                binary_file_path = binary_file_path.replace(
                    proto_src_dir, proto_dest_dir
                )

                os.makedirs(os.path.dirname(binary_file_path), exist_ok=True)

                try:
                    logging.info(f"Generating binary file for {textproto_file_path}...")
                    with open(textproto_file_path, "rb") as input_file, open(
                        binary_file_path, "wb"
                    ) as output_file:
                        subprocess.run(
                            [
                                "python3",
                                "-m",
                                "grpc_tools.protoc",
                                f"--proto_path={proto_src_dir}",
                                f"--encode={proto_message_name}",
                                proto_file_path,
                            ],
                            input=input_file.read(),
                            stdout=output_file,
                            check=True,
                        )
                    logging.info(f"SUCCESS: Binary file at path {binary_file_path}")
                    processed_count += 1
                except subprocess.CalledProcessError as e:
                    logging.error(
                        f"ERROR: Failed to generate binary file for {textproto_file_path}: {e}"
                    )
                    error_count += 1
            except Exception as e:
                logging.error(f"Error processing {textproto_file_path}: {e}")
                error_count += 1

        logging.info(
            f"Textproto processing completed: {processed_count} processed, {skipped_count} skipped, {error_count} errors"
        )
        logging.info("Finished compile_textproto()")

    except Exception as e:
        logging.error(f"Error in compile_textproto(): {e}")
        raise


class StriqueBuildCommand(build_py):
    def run(self):
        logging.info("Starting StriqueBuildCommand.run()")
        try:
            compile_protos()
            compile_textproto()
            super().run()
            logging.info("StriqueBuildCommand completed successfully")
        except Exception as e:
            logging.error(f"Error in StriqueBuildCommand.run(): {e}")
            raise
        finally:
            logging.info("Finished StriqueBuildCommand.run()")


class StriqueEggInfoCommand(egg_info):
    def run(self):
        logging.info("Starting StriqueEggInfoCommand.run()")
        try:
            if not os.path.exists(proto_dest_dir):
                logging.info(f"Creating {proto_dest_dir} directory")
                os.makedirs(proto_dest_dir)
            else:
                logging.info(f"{proto_dest_dir} directory already exists")
            super().run()
            logging.info("StriqueEggInfoCommand completed successfully")
        except Exception as e:
            logging.error(f"Error in StriqueEggInfoCommand.run(): {e}")
            raise
        finally:
            logging.info("Finished StriqueEggInfoCommand.run()")


class StriqueInstallCommand(install):
    def run(self):
        logging.info("Starting StriqueInstallCommand.run()")
        try:
            compile_protos()
            compile_textproto()
            super().run()
            logging.info("StriqueInstallCommand completed successfully")
        except Exception as e:
            logging.error(f"Error in StriqueInstallCommand.run(): {e}")
            raise
        finally:
            logging.info("Finished StriqueInstallCommand.run()")
