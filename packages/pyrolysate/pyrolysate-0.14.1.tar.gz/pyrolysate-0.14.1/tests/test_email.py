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
                    "local": "example",
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
                    "local": "user",
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
                    "local": "user",
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
                    "local": "test1",
                    "plus_address": "spam",
                    "mail_server": "example",
                    "domain": "com",
                },
                "test2+shopping@domain.org": {
                    "local": "test2",
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
                    "local": "regular",
                    "plus_address": "",
                    "mail_server": "example",
                    "domain": "com",
                },
                "user+tag@domain.org": {
                    "local": "user",
                    "plus_address": "tag",
                    "mail_server": "domain",
                    "domain": "org",
                },
            },
        )

    def test_parse_no_domain(self):
        """Email without domain is invalid"""
        result = email.parse_email("easy@")
        self.assertIsNone(result)

    def test_parse_no_local(self):
        """Email without local is invalid"""
        result = email.parse_email("@example.com")
        self.assertIsNone(result)

    def test_comment(self):
        """Comments are removed"""
        result = email.parse_email("john.doe(work)(urgent)@example.com")
        self.assertEqual(
            result,
            {
                "john.doe@example.com": {
                    "local": "john.doe",
                    "plus_address": "",
                    "mail_server": "example",
                    "domain": "com",
                }
            },
        )

    def test_no_trailing_or_leading_dot(self):
        """Negative Control"""
        result = email.parse_email("trailing-dot@example.com")
        self.assertEqual(
            result,
            {
                "trailing-dot@example.com": {
                    "local": "trailing-dot",
                    "plus_address": "",
                    "mail_server": "example",
                    "domain": "com",
                }
            },
        )

    def test_double_dot(self):
        """Two or more consecutive periods are invalid"""
        result = email.parse_email("invalid..email@gmail.com")
        self.assertIsNone(result)

    def test_trailing_dot(self):
        """Trailing dot and leading dot are invalid"""
        result = email.parse_email("trailing-dot.@example")
        self.assertIsNone(result)

    def test_leading_dot(self):
        """Trailing dot and leading dot are invalid"""
        result = email.parse_email(".trailing-dot@example")
        self.assertIsNone(result)

    def test_trailing_space(self):
        """Trailing and leading space are valid"""
        result = email.parse_email("trailing-space @example.com")
        self.assertEqual(
            result,
            {
                "trailing-space @example.com": {
                    "local": "trailing-space ",
                    "plus_address": "",
                    "mail_server": "example",
                    "domain": "com",
                }
            },
        )

    def test_leading_space(self):
        """Trailing and leading space are valid"""
        result = email.parse_email(" leading-space@example.com")
        self.assertEqual(
            result,
            {
                " leading-space@example.com": {
                    "local": " leading-space",
                    "plus_address": "",
                    "mail_server": "example",
                    "domain": "com",
                }
            },
        )

    def test_between_spaces(self):
        """Spaces between words not allowed"""
        result = email.parse_email("what about spaces@example.com")
        self.assertIsNone(result)

    def test_parse_email_invalid_no_at(self):
        """Test parsing of invalid email without @ symbol"""
        result = email.parse_email("invalid.email.com")
        self.assertIsNone(result)

    def test_parse_email_invalid_too_many_dots(self):
        """Test parsing of invalid email with too many dots"""
        result = email.parse_email("user@too.many.dots.com")
        self.assertIsNone(result)

    def test_comments(self):
        """Test that comments are removed in final output"""
        result = email.parse_email("john.doe(this should be removed)@example.com")
        self.assertEqual(
            result,
            {
                "john.doe@example.com": {
                    "local": "john.doe",
                    "plus_address": "",
                    "mail_server": "example",
                    "domain": "com",
                }
            },
        )

    def test_only_comment(self):
        """Local that is only a comment is invalid"""
        result = email.parse_email("(This should return None)@example.com")
        self.assertIsNone(result)

    def test_only_comment_mail_server(self):
        """Local that is only a comment is invalid"""
        result = email.parse_email("This_should_return_None@(example).com")
        self.assertIsNone(result)

    def test_comment_domain(self):
        """Local that is only a comment is invalid"""
        result = email.parse_email("This_should_return_something@example(comment).com")
        self.assertEqual(
            result,
            {
                "This_should_return_something@example.com": {
                    "local": "This_should_return_something",
                    "plus_address": "",
                    "mail_server": "example",
                    "domain": "com",
                }
            },
        )

    def test_email_array_valid(self):
        """Test parsing array of valid emails"""
        emails = ["test1@example.com", "test2@domain.org"]
        result = email.parse_email_array(emails)
        self.assertEqual(
            result,
            {
                "test1@example.com": {
                    "local": "test1",
                    "plus_address": "",
                    "mail_server": "example",
                    "domain": "com",
                },
                "test2@domain.org": {
                    "local": "test2",
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
        self.assertIn("local", result)
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
        self.assertIn("local", result)
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
