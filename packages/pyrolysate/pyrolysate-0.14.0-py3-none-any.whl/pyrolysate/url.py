# Typing, type hints, and errors
from typing import Generator

# internal dependencies
from pyrolysate.common import Shared
from pyrolysate.update_tlds import get_tld
from pyrolysate.converter_async import async_support


class Url:
    def __init__(self):
        self.shared = Shared()
        self.schemes_and_ports = {"https": "443", "http": "80"}
        self.two_part_tlds_lhs = [
            "gov",
            "co",
            "com",
            "org",
            "net",
            "ac",
            "edu",
            "net",
            "or",
            "ne",
            "go",
        ]
        self.header = [
            "url",
            "scheme",
            "subdomain",
            "second_level_domain",
            "top_level_domain",
            "port",
            "path",
            "query",
            "fragment",
        ]
        self.empty_dict = {field: "" for field in self.header[1:]}
        self.field_generator = lambda entry, details: [entry] + [
            details[field] for field in self.header[1:]
        ]

    @async_support
    def parse_url(
        self, url_string: str, tlds: list[str] | None = None
    ) -> dict[str, dict[str, str]] | None:
        """Parses url addresses into component parts
        :param url_string: A string containing a url
        :type url_string: str
        :param tlds: custom or up-to-date list of all current top level domains
        :type tlds: list[str]
        :return: dictionary containing url parsed into sub-parts
        :rtype: dict[str, dict[str, str]] | None
        """
        if not isinstance(url_string, str) or len(url_string) == 0:
            return None
        ip_present = False
        url_string = url_string.lower()
        temp_url_string = url_string

        url_dict = {url_string: self.empty_dict.copy()}
        if tlds is None:
            _, tlds = get_tld()
        scheme = url_string.split("://")[0]
        if "://" in url_string and scheme not in self.schemes_and_ports.keys():
            return None
        if scheme in self.schemes_and_ports.keys():
            url_dict[url_string]["scheme"], temp_url_string = url_string.split("://")
            url_dict[url_string]["port"] = self.schemes_and_ports[
                url_dict[url_string]["scheme"]
            ]

        if ":" in temp_url_string:
            domain_port_etc = temp_url_string.split(":")
            port_etc = domain_port_etc[1].split("/")
            url_dict[url_string]["port"] = port_etc[0]
            port_etc.append("")
            temp_url_string = domain_port_etc[0] + "/" + "/".join(port_etc[1:])

        parts = temp_url_string.split("/")
        parts = parts[0].split(".")
        if all(part.isdigit() and 0 <= int(part) <= 255 for part in parts[:4]):
            ip_present = True
            url_dict[url_string]["top_level_domain"] = ".".join(parts[:4])

        if ip_present is False and not any(tld in url_string for tld in tlds):
            url_dict[url_string]["scheme"] = ""
            url_dict[url_string]["port"] = ""
            return url_dict

        temp = temp_url_string.split(".")
        match len(temp):
            case 2:
                # example.org or example.org/directory
                tld_and_dir = temp[1].split("/")
                if tld_and_dir[0] in tlds:
                    url_dict[url_string]["second_level_domain"] = temp[0]
                    url_dict[url_string]["top_level_domain"] = tld_and_dir[0]
            case 3:
                tld_and_dir = temp[2].split("/")
                if tld_and_dir[0] in tlds:
                    if temp[1] in self.two_part_tlds_lhs:
                        # example.gov.bs or example.gov.bs/directory
                        url_dict[url_string]["second_level_domain"] = temp[0]
                        url_dict[url_string]["top_level_domain"] = ".".join(
                            [temp[1], tld_and_dir[0]]
                        )
                    else:
                        # www.example.com or www.example.com/directory
                        url_dict[url_string]["subdomain"] = temp[0]
                        url_dict[url_string]["second_level_domain"] = temp[1]
                        url_dict[url_string]["top_level_domain"] = tld_and_dir[0]
                else:
                    # example.org/directory.txt
                    if temp[1].split("/")[0] in tlds:
                        url_dict[url_string]["second_level_domain"] = temp[0]
                        temp = ".".join(temp[1:]).split("/")
                        url_dict[url_string]["top_level_domain"] = temp[0]
                        tld_and_dir = temp[:]
            case 4:
                tld_and_dir = ".".join(temp[2:]).split("/")
                if tld_and_dir[0] in tlds and temp[1] in self.two_part_tlds_lhs:
                    # example.gov.bs/directory.xhtml
                    url_dict[url_string]["second_level_domain"] = temp[0]
                    url_dict[url_string][
                        "top_level_domain"
                    ] = f"{temp[1]}.{tld_and_dir[0]}"
                elif tld_and_dir[0] in tlds:
                    # www.example.org/directory.xhtml
                    url_dict[url_string]["subdomain"] = temp[0]
                    url_dict[url_string]["second_level_domain"] = temp[1]
                    url_dict[url_string]["top_level_domain"] = tld_and_dir[0]
                else:
                    # www.bahamas.gov.bs/directory
                    temp_tld = tld_and_dir[0].split(".")
                    if temp_tld[0] in self.two_part_tlds_lhs and temp_tld[1] in tlds:
                        url_dict[url_string]["subdomain"] = temp[0]
                        url_dict[url_string]["second_level_domain"] = temp[1]
                        url_dict[url_string]["top_level_domain"] = tld_and_dir[0]
            case 5:
                tld_and_dir = ".".join(temp[3:]).split("/")
                if all(tld in tlds for tld in [temp[2], tld_and_dir[0]]):
                    # www.example.gov.bs/directory.xhtml
                    url_dict[url_string]["subdomain"] = temp[0]
                    url_dict[url_string]["second_level_domain"] = temp[1]
                    url_dict[url_string]["top_level_domain"] = ".".join(
                        [temp[2], tld_and_dir[0]]
                    )
            case _:
                url_dict[url_string]["scheme"] = ""
                url_dict[url_string]["port"] = ""
                return url_dict

        if url_dict[url_string]["top_level_domain"] == "":
            url_dict[url_string]["scheme"] = ""
            url_dict[url_string]["port"] = ""
            return url_dict

        path_query_fragment = "/".join(tld_and_dir[1:])
        if "?" not in path_query_fragment and "#" not in path_query_fragment:
            path = path_query_fragment.strip("/")
            url_dict[url_string]["path"] = path

        elif "?" in path_query_fragment:
            path_query = [value.strip("/") for value in path_query_fragment.split("?")]
            url_dict[url_string]["path"] = path_query[0]
            if "#" in path_query[1]:
                fragment = path_query[1].split("#")
                url_dict[url_string]["query"] = fragment[0]
                if len(fragment) >= 2:
                    url_dict[url_string]["fragment"] = "".join(fragment[1:])
            elif len(path_query) >= 2:
                url_dict[url_string]["query"] = "".join(path_query[1:])
        elif "#" in path_query_fragment:
            fragment = [value.strip("/") for value in path_query_fragment.split("#")]
            url_dict[url_string]["path"] = fragment[0]
            if len(fragment) >= 2:
                url_dict[url_string]["fragment"] = "".join(fragment[1:])
        return url_dict

    def parse_url_array(
        self, urls: list[str], tlds: list[str] | None = None
    ) -> dict[str, dict[str, str]] | None:
        """Parses each url in an array
        :param urls: list of urls
        :type urls: list[str]
        :return: parsed list of urls in a dictionary
        :rtype: dict[str, dict[str, str]] | None
        """
        if not urls or all(item == "" for item in urls) or not isinstance(urls, list):
            return None
        results = self._parse_url_array(urls, tlds)
        if results is None:
            return None

        url_array = {}
        for result in results:
            if result is None:
                continue
            url_array.update(result)

        if url_array == {}:
            return None
        return url_array

    def _parse_url_array(
        self, urls: list[str], tlds: list[str] | None = None
    ) -> Generator[dict[str, dict[str, str]], None, None] | None:
        """Parses each url in an array
        :param urls: list of urls
        :type urls: list[str]
        :return: parsed list of urls in a dictionary
        :rtype: dict[str, dict[str, str]] | None
        """
        if not urls or all(item == "" for item in urls) or not isinstance(urls, list):
            return None
        if tlds is None:
            _, tlds = get_tld()
        for url in urls:
            yield self.parse_url(url, tlds)

    def to_json(self, urls: list[str] | str, prettify=True) -> str | None:
        """Creates a JSON string representation of URLs.
        :param urls: A list of URLs or a single URL string.
        :type urls: list[str] | str
        :param prettify: Whether to format the JSON output with indentation for readability.
        :type prettify: bool, optional (default is True)
        :return: A JSON string of the parsed URLs or None if the input is invalid or empty.
        :rtype: str | None
        """
        return self.shared._to_json(
            self.parse_url, self._parse_url_array, urls, prettify
        )

    def to_json_file(
        self, file_name: str, urls: list[str], prettify: bool = True
    ) -> tuple[str, int]:
        """Writes parsed URLs to a JSON file.
        :param file_name: The name of the file (without extension) to write the JSON data.
        :type file_name: str
        :param urls: A list of URLs to parse and write to the file.
        :type urls: list[str]
        :param prettify: Whether to format the JSON output with indentation for readability.
        :type prettify: bool, optional (default is True)
        :return: A tuple containing the file name with extension and an int. 0 for a pass, 1 for a fail.
        :rtype: tuple[str, int]
        """
        return self.shared._to_json_file(
            self.parse_url, self._parse_url_array, file_name, urls, prettify
        )

    def to_csv(self, urls: list[str] | str) -> str | None:
        """Creates a CSV string representation of URLs.
        :param urls: A list of URLs or a single URL string.
        :type urls: list[str] | str
        :return: A CSV string of the parsed URLs or None if the input is invalid or empty.
        :rtype: str | None
        """
        return self.shared._to_csv(
            self.header,
            self.field_generator,
            self.parse_url,
            self._parse_url_array,
            urls,
        )

    def to_csv_file(self, file_name, urls: list[str] | str) -> tuple[str, int]:
        """Writes parsed URLs to a CSV file.
        :param file_name: The name of the file (without extension) to write the CSV data.
        :type file_name: str
        :param urls: A list of URLs or a single URL string to parse and write to the file.
        :type urls: list[str] | str
        :return: A tuple containing the file name with extension and an int. 0 for a pass, 1 for a fail.
        :rtype: tuple[str, int]
        """
        return self.shared._to_csv_file(
            self.header,
            self.field_generator,
            self.parse_url,
            self._parse_url_array,
            file_name,
            urls,
        )


url = Url()
