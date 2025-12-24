# Function decorators and caching
from functools import cache

# Standard library
from datetime import datetime

# HTTP requests (third-party)
import requests


@cache
def get_tld(path_to_tlds_file: str = "tld.txt") -> tuple[str, list[str]]:
    """Grabs top level domains from internet assigned numbers authority
    :param path_to_tlds_file: Path to local TLD file for fallback
    :type path_to_tlds_file: str
    :return: A tuple containing the last updated date and a list of top-level domains.
    :rtype: tuple[str, list[str]]
    """
    # Try IANA first
    iana_result = get_from_iana()
    if iana_result is not None:
        return iana_result
    # Try local file next
    local_result = get_from_local(path_to_tlds_file)
    if local_result is not None:
        return local_result
    # Return None if other methods fail
    print("Failed to get both iana tlds and locally stored tlds.")
    return None


def get_from_iana() -> tuple[str, list[str]] | None:
    try:
        response = requests.get(
            "https://data.iana.org/TLD/tlds-alpha-by-domain.txt", timeout=10
        )
        response.raise_for_status()
        lines = response.text.split("\n")
        return lines[0], list(map(lambda x: x.lower(), filter(None, lines[1:])))
    except requests.RequestException as e:
        print(f"Error fetching TLD list: {e}")
        return None


def get_from_local(path_to_tlds_file: str) -> tuple[str, list[str]] | None:
    try:
        with open(path_to_tlds_file, "r") as file:
            lines = file.readlines()
            version = lines[1].strip()
            dated = lines[2].strip()
            last_updated = f"{version}, {dated}"
            tlds = [line.strip().lower() for line in lines[4:] if line.strip()]
            return last_updated, tlds
    except (IOError, IndexError) as e:
        print(f"Error reading local TLD file: {e}")
        return None


def update_local_tld_file(file_name: str = "tld") -> tuple[str, int]:
    if not isinstance(file_name, str):
        return "Failed to write file. File name must be a string.", 1
    tlds = get_tld()
    if tlds is None:
        return "Failed to fetch tlds", 1
    ver_dated, tldss = tlds
    version, dated = ver_dated.split(",")

    if not file_name.endswith(".txt"):
        file_name = f"{file_name}.txt"
    with open(file_name, "w") as file:
        file.write(f"File Created: {datetime.now().strftime('%d %B %Y %H:%M')}\n")
        file.write(f"{version}\n")
        file.write(f"{dated}\n\n")
        for tld in tldss:
            file.write(f"{tld}\n")
    return "File created successfully", 0


def update(file_name: str = "tld"):
    return update_local_tld_file(file_name)


if __name__ == "__main__":
    update()
