# Typing, type hints, and errors
from typing import Generator

# internal dependencies
from pyrolysate.common import Shared
from pyrolysate.converter_async import async_support


class Email:
    def __init__(self):
        self.shared = Shared()
        self.header = ["email", "local", "plus_address", "mail_server", "domain"]
        self.empty_dict = {field: "" for field in self.header[1:]}
        self.field_generator = lambda entry, details: [entry] + [
            details[field] for field in self.header[1:]
        ]

    @async_support
    def parse_email(self, e_mail_string: str) -> dict[str, dict[str, str]] | None:
        """Parses email addresses into component parts
        :param e_mail_string: A string containing an email address
        :type e_mail_string: str
        :return: Dictionary containing email parsed into sub-parts
        :rtype: dict[str, dict[str, str]] | None
        """
        if (
            not isinstance(e_mail_string, str)
            or len(e_mail_string) == 0
            or len(e_mail_string) >= 998
        ):
            return None

        new_email_string = e_mail_string
        temp = new_email_string.split("@")
        comments = get_comments_check_dots(new_email_string)
        if comments == None:
            return None

        if comments:
            for comment in comments:
                new_email_string = new_email_string.replace(comment, "")
                temp[0] = temp[0].replace(comment, "")
                temp[1] = temp[1].replace(comment, "")

        if len(temp) != 2 or any(
            [
                part == ""
                or part.startswith(".")
                or part.endswith(".")
                or " " in part.strip()
                for part in temp
            ]
        ):
            # None returned for invalid emails
            # trailing or leading periods
            # spaces between words
            # consecutive periods anywhere
            # multiple @ symbols or lack of @ symbol
            # parentheses present in domain or mail server
            return None

        email_dict = {new_email_string: self.empty_dict.copy()}

        local_temp = temp[0]
        plus_address = local_temp.split("+")
        if len(plus_address) == 2:
            email_dict[new_email_string]["local"] = plus_address[0]
            email_dict[new_email_string]["plus_address"] = plus_address[1]
        else:
            email_dict[new_email_string]["local"] = local_temp
        server_and_domain = temp[1].split(".")
        if len(server_and_domain) > 3:
            return None  # invalid email with too many periods
        email_dict[new_email_string]["mail_server"] = server_and_domain[0]
        # handles emails ending in standard tld or government emails (.gov.bs)
        email_dict[new_email_string]["domain"] = ".".join(server_and_domain[1:])
        return email_dict

    def parse_email_array(self, emails: list[str]) -> dict[str, dict[str, str]] | None:
        """Parses each email in an array
        :param emails: list of emails
        :type emails: list[str]
        :return: parsed list of emails in a dictionary
        :rtype: dict[str, dict[str, str]] | None
        """
        results = self._parse_email_array(emails)
        if results is None:
            return None

        email_array = {}
        for result in results:
            if result is None:
                continue
            email_array.update(result)

        if email_array == {}:
            return None
        return email_array

    def _parse_email_array(
        self, emails: list[str]
    ) -> Generator[dict[str, dict[str, str]], None, None] | None:
        """Parses each email in an array
        :param emails: list of emails
        :type emails: list[str]
        :return: parsed list of emails in a dictionary
        :rtype: dict[str, dict[str, str]] | None
        """
        if not isinstance(emails, list) or len(emails) < 1:
            return None
        for email in emails:
            yield self.parse_email(email)

    def to_json(self, emails: list[str] | str, prettify=True) -> str | None:
        """Creates a JSON string representation of emails.
        :param emails: A list of emails or a single email string.
        :type emails: list[str] | str
        :param prettify: Whether to format the JSON output with indentation for readability.
        :type prettify: bool, optional (default is True)
        :return: A JSON string of the parsed emails or None if the input is invalid or empty.
        :rtype: str | None
        """
        return self.shared._to_json(
            self.parse_email, self._parse_email_array, emails, prettify
        )

    def to_json_file(
        self, file_name: str, emails: list[str], prettify: bool = True
    ) -> tuple[str, int]:
        """Writes parsed emails to a JSON file.
        :param file_name: The name of the file (without extension) to write the JSON data.
        :type file_name: str
        :param emails: A list of emails to parse and write to the file.
        :type emails: list[str]
        :param prettify: Whether to format the JSON output with indentation for readability.
        :type prettify: bool, optional (default is True)
        :return: A tuple containing the file name with extension and an int. 0 for a pass, 1 for a fail.
        :rtype: tuple[str, int]
        """
        return self.shared._to_json_file(
            self.parse_email, self._parse_email_array, file_name, emails, prettify
        )

    def to_csv(self, emails: list[str] | str) -> str | None:
        """Creates a CSV string representation of URLs.
        :param urls: A list of URLs or a single URL string.
        :type urls: list[str] | str
        :return: A CSV string of the parsed URLs or None if the input is invalid or empty.
        :rtype: str | None
        """
        return self.shared._to_csv(
            self.header,
            self.field_generator,
            self.parse_email,
            self._parse_email_array,
            emails,
        )

    def to_csv_file(self, file_name, urls: list[str] | str) -> tuple[str, int]:
        """Writes parsed emails to a CSV file.
        :param file_name: The name of the file (without extension) to write the CSV data.
        :type file_name: str
        :param emails: A list of emails or a single email string to parse and write to the file.
        :type emails: list[str] | str
        :return: A tuple containing the file name with extension and an int. 0 for a pass, 1 for a fail.
        :rtype: tuple[str, int]
        """
        return self.shared._to_csv_file(
            self.header,
            self.field_generator,
            self.parse_email,
            self._parse_email_array,
            file_name,
            urls,
        )


def get_comments_check_dots(text: str) -> list[str] | None:
    results = []
    stack = 0
    start_index = None
    prev_dot = False

    for i, char in enumerate(text):
        if char == ".":
            if prev_dot is True:
                return None
            prev_dot = True
        else:
            prev_dot = False

        if char == "(":
            if stack == 0:
                start_index = i
            stack += 1
        elif char == ")":
            stack -= 1
            if stack == 0:
                content = text[start_index : i + 1]
                results.append(content)
        # Return None if seen '(' != ')' ie. a string like ))()
        if stack < 0:
            return None
    # Return None if there are unclosed parentheses
    if stack != 0:
        return None

    return results


email = Email()
