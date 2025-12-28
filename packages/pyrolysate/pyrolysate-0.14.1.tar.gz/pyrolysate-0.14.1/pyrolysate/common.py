# Data formats and compression
import bz2
import gzip
import lzma
import zipfile
import csv
import json

# Typing, type hints, and errors
from typing import Generator
import collections.abc
import zlib

# Standard library utilities
from io import StringIO


def main():
    pass


class _ZIP:
    @staticmethod
    def _read_zip_member(
        zip_file: zipfile.ZipFile, member_name: str, delimiter: str
    ) -> list[str]:
        """Read and parse a single member of a ZIP file.

        Args:
            zip_file: Open ZIP file object
            member_name: Name of the member file to read
            delimiter: String delimiter for splitting content

        Returns:
            List of non-empty strings from the file
        """
        try:
            with zip_file.open(member_name) as file:
                content = file.read().decode("utf-8")
                return [x.strip() for x in content.split(delimiter) if x.strip()]
        except UnicodeDecodeError as err:
            print(f"Warning: Could not decode file {member_name}: {err}")
            return []
        except zipfile.BadZipFile as err:
            print(f"Warning: Corrupted file in archive {member_name}: {err}")
            return []
        except Exception as err:
            print(f"Warning: Error reading file {member_name}: {err}")
            return []

    @staticmethod
    def _process_zip_file(file_path: str, delimiter: str) -> list[str] | None:
        """Process a ZIP file and extract content from all text files.

        Args:
            file_path: Path to the ZIP file
            delimiter: String delimiter for splitting content

        Returns:
            Combined list of strings from all text files, or None if processing fails
        """
        try:
            with zipfile.ZipFile(file_path, "r") as zip_file:
                # Get all text files from the ZIP
                text_files = [
                    f
                    for f in zip_file.namelist()
                    if f.endswith((".txt", ".csv", ".log"))
                ]

                if not text_files:
                    print("No supported text files found in ZIP archive")
                    return None

                # Process all text files
                temp = []
                for text_file in text_files:
                    lines = _ZIP._read_zip_member(zip_file, text_file, delimiter)
                    temp.extend(lines)

                return temp if temp != [] else None

        except zipfile.BadZipFile as err:
            print(f"Invalid ZIP file: {err}")
            return None
        except Exception as err:
            print(f"Error processing ZIP file: {err}")
            return None


def file_to_list(input_file_name: str, delimiter: str = "\n") -> list[str] | None:
    if not isinstance(input_file_name, str):
        return None

    supp_compression = {
        "bz2": (bz2, OSError),
        "gz": (gzip, OSError),
        "lzma": (lzma, lzma.LZMAError),
        "xz": (lzma, lzma.LZMAError),
        "zip": (zipfile, zipfile.BadZipFile),
    }

    extension = input_file_name.split(".")[-1]

    if input_file_name.endswith(".zip"):
        return _ZIP._process_zip_file(input_file_name, delimiter)

    if extension in supp_compression:
        comp_module, comp_error = supp_compression[extension]
        try:
            with comp_module.open(input_file_name, "rt") as file:
                result = file.read()
                temp = [x.strip() for x in result.split(delimiter) if x != ""]
                return temp
        except comp_error as err:
            print(f"Compression error: {err}")
            return None
        except zlib.error as err:
            print(f"Decompression failed: {err}")
            return None
        except FileNotFoundError:
            print("The file does not exist.")
            return None
        except OSError as err:
            print(f"OS error with compressed file: {err}")
            return None
        except EOFError:
            print("Reached unexpected end of file. The file might be truncated.")
            return None
    try:
        with open(input_file_name, "r") as file:
            result = file.read()
    except OSError as err:
        print("OS error:", err)
        return None
    except IOError:
        print("An error occured while attempting to read the file.")
        return None
    except PermissionError:
        print("You do not have permission to open file.")
        return None
    except FileNotFoundError:
        print("Unable to locate file.")
        return None

    temp = [x.strip() for x in result.split(delimiter) if x != ""]
    return temp


class Shared:
    def _validate_data(
        self, string_parse, array_parse, data
    ) -> (
        Generator[dict[str, dict[str, str]], None, None]
        | dict[str, dict[str, str]]
        | None
    ):
        if not isinstance(data, str) and not isinstance(data, list):
            return None
        if isinstance(data, str) or (isinstance(data, list) and len(data) == 1):
            data = [data] if isinstance(data, str) else data
            results = string_parse(data[0])
            return results
        return None

    def _to_json(self, string_parse, array_parse, data, pretty) -> str | None:
        result = self._validate_data(string_parse, array_parse, data)
        if isinstance(data, list) and len(data) >= 2:
            result = array_parse(data)
        if isinstance(result, collections.abc.Generator):
            solution = "{\n    " if pretty is True else "{"
            first = True
            for item in result:
                key = list(item)[0]
                if first is not True:
                    solution += ",\n    " if pretty is True else ", "
                if pretty is True:
                    solution += json.dumps(key, indent=8)
                    solution += ": "
                    solution += json.dumps(item[key], indent=8)
                if pretty is False:
                    solution += json.dumps(key)
                    solution += ": "
                    solution += json.dumps(item[key])
                first = False
            solution += "\n}" if pretty is True else "}"
            return solution

        if result is None:
            return None
        if not pretty:
            return json.dumps(result)
        return json.dumps(result, indent=4)

    def _to_json_file(
        self, string_parse, array_parse, file_name, data, pretty
    ) -> tuple[str, int]:
        result = self._validate_data(string_parse, array_parse, data)
        if isinstance(data, list) and len(data) >= 2:
            result = array_parse(data)
        if isinstance(result, collections.abc.Generator):
            with open(f"{file_name}.json", "w") as file:
                file.write("{\n    " if pretty is True else "{")
                first = True
                for item in result:
                    key = list(item)[0]
                    if first is not True:
                        file.write(",\n    " if pretty is True else ", ")
                    if pretty is True:
                        json.dump(key, file, indent=8)
                        file.write(": ")
                        json.dump(item[key], file, indent=8)
                    if pretty is False:
                        json.dump(key, file)
                        file.write(": ")
                        json.dump(item[key], file)
                    first = False
                file.write("\n}" if pretty is True else "}")
                return "File successfully written", 0

        if result is None:
            return "Failed to write file", 1
        if not pretty:
            with open(f"{file_name}.json", "w") as file:
                json.dump(result, file)
        if pretty:
            with open(f"{file_name}.json", "w") as file:
                json.dump(result, file, indent=4)
        return "File successfully written", 0

    def _to_csv(
        self, headers, data_fields, string_parse, array_parse, data
    ) -> str | None:
        buffer = StringIO()  # Open StringIO object
        csv_writer = csv.writer(buffer)
        csv_writer.writerow(headers)
        result = self._validate_data(string_parse, array_parse, data)
        if isinstance(data, list) and len(data) >= 2:
            result = array_parse(data)
        if isinstance(result, collections.abc.Generator):
            for full_dict in result:
                raw_input = list(full_dict)[0]
                parsed_fields = full_dict[raw_input]
                csv_writer.writerow(data_fields(raw_input, parsed_fields))
        else:
            if result is None:
                return None
            for raw_input, parsed_fields in result.items():
                csv_writer.writerow(data_fields(raw_input, parsed_fields))
        csv_data = buffer.getvalue()
        buffer.close()  # Close the StringIO object
        return csv_data

    def _to_csv_file(
        self, headers, data_fields, string_parse, array_parse, file_name, data
    ) -> tuple[str, int]:
        with open(f"{file_name}.csv", "w") as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(headers)
            result = self._validate_data(string_parse, array_parse, data)
            if isinstance(data, list) and len(data) >= 2:
                result = array_parse(data)
            if isinstance(result, collections.abc.Generator):
                for full_dict in result:
                    raw_input = list(full_dict)[0]
                    parsed_fields = full_dict[raw_input]
                    csv_writer.writerow(data_fields(raw_input, parsed_fields))
            else:
                if result is None:
                    return "Failed to write file", 1
                for raw_input, parsed_fields in result.items():
                    csv_writer.writerow(data_fields(raw_input, parsed_fields))
        return "File successfully written", 0


if __name__ == "__main__":
    main()
