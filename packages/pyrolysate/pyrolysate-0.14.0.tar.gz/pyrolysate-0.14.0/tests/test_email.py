import unittest
from pyrolysate import email


class TestEmail(unittest.TestCase):
    def test_parse_email_valid(self):
        """Test parsing of valid email addresses"""
        result = email.parse_email("example@gmail.com")
        self.assertEqual(
            result,
            {
                "example@gmail.com": {
                    "username": "example",
                    "plus_address": "",
                    "mail_server": "gmail",
                    "domain": "com",
                }
            },
        )

    def test_parse_email_government(self):
        """Test parsing of government email addresses"""
        result = email.parse_email("user@agency.gov.bs")
        self.assertEqual(
            result,
            {
                "user@agency.gov.bs": {
                    "username": "user",
                    "plus_address": "",
                    "mail_server": "agency",
                    "domain": "gov.bs",
                }
            },
        )

    def test_parse_email_with_plus(self):
        """Test parsing of email addresses with plus addressing"""
        result = email.parse_email("user+tag@hotmail.com")
        self.assertEqual(
            result,
            {
                "user+tag@hotmail.com": {
                    "username": "user",
                    "plus_address": "tag",
                    "mail_server": "hotmail",
                    "domain": "com",
                }
            },
        )

    def test_parse_email_array_with_plus(self):
        """Test parsing array of emails including plus addresses"""
        emails = ["test1+spam@example.com", "test2+shopping@domain.org"]
        result = email.parse_email_array(emails)
        self.assertEqual(
            result,
            {
                "test1+spam@example.com": {
                    "username": "test1",
                    "plus_address": "spam",
                    "mail_server": "example",
                    "domain": "com",
                },
                "test2+shopping@domain.org": {
                    "username": "test2",
                    "plus_address": "shopping",
                    "mail_server": "domain",
                    "domain": "org",
                },
            },
        )

    def test_parse_email_mixed_plus(self):
        """Test parsing array with mixed plus and regular addresses"""
        emails = ["regular@example.com", "user+tag@domain.org"]
        result = email.parse_email_array(emails)
        self.assertEqual(
            result,
            {
                "regular@example.com": {
                    "username": "regular",
                    "plus_address": "",
                    "mail_server": "example",
                    "domain": "com",
                },
                "user+tag@domain.org": {
                    "username": "user",
                    "plus_address": "tag",
                    "mail_server": "domain",
                    "domain": "org",
                },
            },
        )

    def test_parse_email_invalid_no_at(self):
        """Test parsing of invalid email without @ symbol"""
        result = email.parse_email("invalid.email.com")
        self.assertIsNone(result)

    def test_parse_email_invalid_too_many_dots(self):
        """Test parsing of invalid email with too many dots"""
        result = email.parse_email("user@too.many.dots.com")
        self.assertIsNone(result)

    def test_email_array_valid(self):
        """Test parsing array of valid emails"""
        emails = ["test1@example.com", "test2@domain.org"]
        result = email.parse_email_array(emails)
        self.assertEqual(
            result,
            {
                "test1@example.com": {
                    "username": "test1",
                    "plus_address": "",
                    "mail_server": "example",
                    "domain": "com",
                },
                "test2@domain.org": {
                    "username": "test2",
                    "plus_address": "",
                    "mail_server": "domain",
                    "domain": "org",
                },
            },
        )

    def test_email_array_empty(self):
        """Test parsing empty email array"""
        result = email.parse_email_array([])
        self.assertIsNone(result)

        emails = [[""], [], ""]
        result = email.parse_email_array(emails)
        self.assertIsNone(result)

    def test_email_empty(self):
        """Test parsing empty email array"""
        result = email.parse_email("")
        self.assertIsNone(result)

    def test_email_array_invalid_input(self):
        """Test parsing with invalid input type"""
        result = email.parse_email_array("not a list")
        self.assertIsNone(result)

    def test_to_json_single_email(self):
        """Test JSON conversion of single email"""
        result = email.to_json("test@example.com")
        self.assertIsInstance(result, str)
        self.assertIn("test@example.com", result)
        self.assertIn("username", result)
        self.assertIn("mail_server", result)
        self.assertIn("domain", result)

    def test_to_json_multiple_emails(self):
        """Test JSON conversion of multiple emails"""
        emails = ["test1@example.com", "test2@domain.org"]
        result = email.to_json(emails)
        self.assertIsInstance(result, str)
        self.assertIn("test1@example.com", result)
        self.assertIn("test2@domain.org", result)

    def test_to_json_invalid_email(self):
        """Test JSON conversion of invalid email"""
        result = email.to_json("invalid.email")
        self.assertIsNone(result)

    def test_to_json_empty(self):
        """Test JSON conversion of empty list"""
        result = email.to_json([])
        self.assertIsNone(result)

        result = email.to_json("")
        self.assertIsNone(result)

    def test_to_csv_single_email(self):
        """Test CSV conversion of single email"""
        result = email.to_csv("test@example.com")
        self.assertIsInstance(result, str)
        self.assertIn("test@example.com", result)
        self.assertIn("username", result)
        self.assertIn("mail_server", result)
        self.assertIn("domain", result)

    def test_to_csv_multiple_emails(self):
        """Test CSV conversion of multiple emails"""
        emails = ["test1@example.com", "test2@domain.org"]
        result = email.to_csv(emails)
        self.assertIsInstance(result, str)
        self.assertIn("test1@example.com", result)
        self.assertIn("test2@domain.org", result)

    def test_to_csv_invalid_email(self):
        """Test CSV conversion of invalid email"""
        result = email.to_csv("invalid.email")
        self.assertIsNone(result)

    def test_to_csv_empty(self):
        """Test CSV conversion of empty list"""
        result = email.to_csv([])
        self.assertIsNone(result)

        result = email.to_csv("")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
