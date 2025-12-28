import unittest
from pyrolysate import url
from pyrolysate.update_tlds import get_tld


class TestUrl(unittest.TestCase):
    def test_parse_url_basic(self):
        """Test parsing of basic URL"""
        result = url.parse_url("example.com")
        self.assertEqual(
            result,
            {
                "example.com": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "",
                    "path": "",
                    "query": "",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_with_www(self):
        """Test parsing URL with www subdomain"""
        result = url.parse_url("www.example.org")
        self.assertEqual(
            result,
            {
                "www.example.org": {
                    "scheme": "",
                    "subdomain": "www",
                    "second_level_domain": "example",
                    "top_level_domain": "org",
                    "port": "",
                    "path": "",
                    "query": "",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_with_scheme(self):
        """Test parsing URL with http/https scheme"""
        result = url.parse_url("https://example.com")
        self.assertEqual(
            result,
            {
                "https://example.com": {
                    "scheme": "https",
                    "subdomain": "",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "443",
                    "path": "",
                    "query": "",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_with_directory(self):
        """Test parsing URL with path"""
        result = url.parse_url("example.com/path/to/resource")
        self.assertEqual(
            result,
            {
                "example.com/path/to/resource": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "",
                    "path": "path/to/resource",
                    "query": "",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_complex(self):
        """Test parsing complex URL with all components"""
        result = url.parse_url("https://www.example.com/path/to/resource.html")
        self.assertEqual(
            result,
            {
                "https://www.example.com/path/to/resource.html": {
                    "scheme": "https",
                    "subdomain": "www",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "443",
                    "path": "path/to/resource.html",
                    "query": "",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_government_domain(self):
        """Test parsing government domain URLs"""
        result = url.parse_url("https://data.gov.uk/dataset")
        self.assertEqual(
            result,
            {
                "https://data.gov.uk/dataset": {
                    "scheme": "https",
                    "subdomain": "",
                    "second_level_domain": "data",
                    "top_level_domain": "gov.uk",
                    "port": "443",
                    "path": "dataset",
                    "query": "",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_invalid_scheme(self):
        """Test parsing URL with invalid scheme"""
        schemes = ["ftp", "htp", "nes", "message"]
        for scheme in schemes:
            result = url.parse_url(f"{scheme}://example.com")
            self.assertIsNone(result)

    def test_parse_empty_url_string(self):
        """Test parsing URL with invalid scheme"""
        urls = [[""], [], ""]
        for x in urls:
            result = url.parse_url(x)
            self.assertIsNone(result)

    def test_parse_empty_url_array(self):
        """Test parsing URL with invalid scheme"""
        result = url.parse_url_array([])
        self.assertIsNone(result)

        urls = [[""], [], ""]
        result = url.parse_url_array(urls)
        self.assertIsNone(result)

    def test_parse_url_invalid_tld(self):
        """Test parsing URL with invalid top-level domain"""
        result = url.parse_url("example.invalidtld")
        self.assertEqual(
            result,
            {
                "example.invalidtld": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "",
                    "top_level_domain": "",
                    "port": "",
                    "path": "",
                    "query": "",
                    "fragment": "",
                }
            },
        )

    def test_url_array_valid(self):
        """Test parsing array of valid URLs"""
        urls = ["example.com", "www.test.org"]
        result = url.parse_url_array(urls)
        self.assertEqual(
            result,
            {
                "example.com": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "",
                    "path": "",
                    "query": "",
                    "fragment": "",
                },
                "www.test.org": {
                    "scheme": "",
                    "subdomain": "www",
                    "second_level_domain": "test",
                    "top_level_domain": "org",
                    "port": "",
                    "path": "",
                    "query": "",
                    "fragment": "",
                },
            },
        )

    def test_to_json_single_url(self):
        """Test JSON conversion of single URL"""
        result = url.to_json("example.com")
        self.assertIsInstance(result, str)
        self.assertIn("second_level_domain", result)
        self.assertIn("top_level_domain", result)

    def test_to_json_multiple_urls(self):
        """Test JSON conversion of multiple URLs"""
        urls = ["example.com", "test.org"]
        result = url.to_json(urls)
        self.assertIsInstance(result, str)
        self.assertIn('"second_level_domain": "example"', result)
        self.assertIn('"top_level_domain": "com"', result)
        self.assertIn('"second_level_domain": "test"', result)
        self.assertIn('"top_level_domain": "org"', result)

    def test_to_json_invalid_url(self):
        """Test JSON conversion of invalid URL"""
        result = url.to_json("invalid.invalidtld", prettify=False)
        self.assertEqual(
            result,
            (
                '{"invalid.invalidtld": '
                "{"
                '"scheme": "", '
                '"subdomain": "", '
                '"second_level_domain": "", '
                '"top_level_domain": "", '
                '"port": "", '
                '"path": "", '
                '"query": "", '
                '"fragment": ""'
                "}"
                "}"
            ),
        )

    def test_to_json_empty(self):
        """Test JSON conversion of empty list"""
        result = url.to_json([])
        self.assertIsNone(result)

        result = url.to_json("")
        self.assertIsNone(result)

    def test_parse_url_with_custom_tlds(self):
        """Test parsing URL with custom TLD list"""
        custom_tlds = ["com", "net", "custom"]
        result = url.parse_url("example.custom", tlds=custom_tlds)
        self.assertEqual(
            result,
            {
                "example.custom": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "example",
                    "top_level_domain": "custom",
                    "port": "",
                    "path": "",
                    "query": "",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_with_port(self):
        """Test parsing URL with explicit port"""
        result = url.parse_url("example.com:8080")
        self.assertEqual(
            result,
            {
                "example.com:8080": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "8080",
                    "path": "",
                    "query": "",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_default_ports(self):
        """Test parsing URLs with default ports for http/https"""
        cases = [("http://example.com", "80"), ("https://example.com", "443")]
        for test_url, expected_port in cases:
            result = url.parse_url(test_url)
            self.assertEqual(result[test_url]["port"], expected_port)

    def test_parse_url_with_query(self):
        """Test parsing URL with query parameters"""
        result = url.parse_url("example.com/search?q=test&page=1")
        self.assertEqual(
            result,
            {
                "example.com/search?q=test&page=1": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "",
                    "path": "search",
                    "query": "q=test&page=1",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_with_fragment(self):
        """Test parsing URL with fragment"""
        result = url.parse_url("example.com/page#section1")
        self.assertEqual(
            result,
            {
                "example.com/page#section1": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "",
                    "path": "page",
                    "query": "",
                    "fragment": "section1",
                }
            },
        )

    def test_parse_url_complex_path(self):
        """Test parsing URL with complex path including file extension"""
        result = url.parse_url("example.com/blog/2023/post.html")
        self.assertEqual(
            result,
            {
                "example.com/blog/2023/post.html": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "",
                    "path": "blog/2023/post.html",
                    "query": "",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_all_components(self):
        """Test parsing URL with all possible components"""
        test_url = (
            "https://www.example.com:8443/path/to/page.html?q=search&lang=en#section2"
        )
        result = url.parse_url(test_url)
        self.assertEqual(
            result,
            {
                "https://www.example.com:8443/path/to/page.html?q=search&lang=en#section2": {
                    "scheme": "https",
                    "subdomain": "www",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "8443",
                    "path": "path/to/page.html",
                    "query": "q=search&lang=en",
                    "fragment": "section2",
                }
            },
        )

    def test_parse_url_query_and_fragment(self):
        """Test parsing URL with both query parameters and fragment"""
        result = url.parse_url("example.com/search?q=test#results")
        self.assertEqual(
            result,
            {
                "example.com/search?q=test#results": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "",
                    "path": "search",
                    "query": "q=test",
                    "fragment": "results",
                }
            },
        )

    def test_parse_url_multiple_query_params(self):
        """Test parsing URL with multiple query parameters"""
        result = url.parse_url("example.com/search?q=test&page=1&sort=desc")
        self.assertEqual(
            result,
            {
                "example.com/search?q=test&page=1&sort=desc": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "",
                    "path": "search",
                    "query": "q=test&page=1&sort=desc",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_special_chars_in_path(self):
        """Test parsing URL with special characters in path"""
        result = url.parse_url("example.com/path-with_special.chars")
        self.assertEqual(
            result,
            {
                "example.com/path-with_special.chars": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "example",
                    "top_level_domain": "com",
                    "port": "",
                    "path": "path-with_special.chars",
                    "query": "",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_ip_address(self):
        """Test parsing URL with IP address"""
        result = url.parse_url("https://192.168.1.1:8080/admin")
        self.assertEqual(
            result,
            {
                "https://192.168.1.1:8080/admin": {
                    "scheme": "https",
                    "subdomain": "",
                    "second_level_domain": "",
                    "top_level_domain": "192.168.1.1",
                    "port": "8080",
                    "path": "admin",
                    "query": "",
                    "fragment": "",
                }
            },
        )
        result = url.parse_url("https://192.168.1.1/admin")
        self.assertEqual(
            result,
            {
                "https://192.168.1.1/admin": {
                    "scheme": "https",
                    "subdomain": "",
                    "second_level_domain": "",
                    "top_level_domain": "192.168.1.1",
                    "port": "443",
                    "path": "admin",
                    "query": "",
                    "fragment": "",
                }
            },
        )
        result = url.parse_url("192.168.1.1/admin")
        self.assertEqual(
            result,
            {
                "192.168.1.1/admin": {
                    "scheme": "",
                    "subdomain": "",
                    "second_level_domain": "",
                    "top_level_domain": "192.168.1.1",
                    "port": "",
                    "path": "admin",
                    "query": "",
                    "fragment": "",
                }
            },
        )

    def test_parse_url_empty_components(self):
        """Test parsing URL with empty components between delimiters"""
        urls = ["example.com/path/?#", "example.com/path/#", "example.com/path/?"]
        for url_item in urls:
            result = url.parse_url(url_item)
            self.assertEqual(
                result,
                {
                    url_item: {
                        "scheme": "",
                        "subdomain": "",
                        "second_level_domain": "example",
                        "top_level_domain": "com",
                        "port": "",
                        "path": "path",
                        "query": "",
                        "fragment": "",
                    }
                },
            )

    def test_get_tld(self):
        """Test fetching TLDs from IANA"""
        last_updated, tlds = get_tld()
        self.assertIsInstance(last_updated, str)
        self.assertIsInstance(tlds, list)
        self.assertGreater(len(tlds), 0)
        # Check for some common TLDs
        self.assertIn("com", tlds)
        self.assertIn("org", tlds)
        self.assertIn("net", tlds)
        self.assertIn("io", tlds)

    def test_to_csv_single_url(self):
        """Test CSV conversion of single URL"""
        result = url.to_csv("example.com")
        self.assertIsInstance(result, str)
        self.assertIn("second_level_domain", result)
        self.assertIn("top_level_domain", result)

    def test_to_csv_multiple_urls(self):
        """Test CSV conversion of multiple URLs"""
        urls = ["example.com", "test.org"]
        result = url.to_csv(urls)
        self.assertIsInstance(result, str)
        self.assertIn("example.com", result)
        self.assertIn("example", result)
        self.assertIn("com", result)
        self.assertIn("test.org", result)
        self.assertIn("test", result)
        self.assertIn("org", result)

    def test_to_csv_invalid_url(self):
        """Test CSV conversion of invalid URL"""
        result = url.to_csv("invalid.invalidtld")
        self.assertEqual(
            result,
            "url,scheme,subdomain,second_level_domain,top_level_domain,port,path,query,fragment\r\ninvalid.invalidtld,,,,,,,,\r\n",
        )

    def test_to_csv_empty(self):
        """Test CSV conversion of empty list"""
        result = url.to_csv([])
        self.assertIsNone(result)

        result = url.to_csv("")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
