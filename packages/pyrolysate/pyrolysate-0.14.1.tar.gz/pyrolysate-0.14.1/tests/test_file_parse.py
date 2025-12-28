import unittest
import os
import bz2
import gzip
import lzma
import zipfile
import tempfile
import shutil
from pathlib import Path

from pyrolysate import file_to_list


class TestInputFile(unittest.TestCase):
    def setUp(self):
        """Create temporary directory and register cleanup"""
        self.temp_dir = tempfile.mkdtemp()
        # Register cleanup to ensure temp directory is always removed
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

        self.test_content = "test1@example.com\ntest2@example.com\ntest3@example.com"
        self.expected_result = [
            "test1@example.com",
            "test2@example.com",
            "test3@example.com",
        ]

    def create_test_file(self, filename, content=None, compression=None):
        """Helper to create test files with cleanup"""
        path = Path(self.temp_dir) / filename
        content = content if content is not None else self.test_content

        if compression == "bz2":
            with bz2.open(path, "wt") as f:
                f.write(content)
        elif compression == "gz":
            with gzip.open(path, "wt") as f:
                f.write(content)
        elif compression in ("xz", "lzma"):
            with lzma.open(path, "wt") as f:
                f.write(content)
        else:
            with open(path, "w") as f:
                f.write(content)

        # Register cleanup for this specific file
        self.addCleanup(os.remove, path)
        return path

    def test_parse_text_file(self):
        """Test parsing regular text file"""
        path = self.create_test_file("test.txt")
        result = file_to_list(str(path))
        self.assertEqual(result, self.expected_result)

    def test_parse_bz2_file(self):
        """Test parsing bz2 compressed file"""
        path = self.create_test_file("test.bz2", compression="bz2")
        result = file_to_list(str(path))
        self.assertEqual(result, self.expected_result)

    def test_parse_gzip_file(self):
        """Test parsing gzip compressed file"""
        path = self.create_test_file("test.gz", compression="gz")
        result = file_to_list(str(path))
        self.assertEqual(result, self.expected_result)

    def test_parse_lzma_file(self):
        """Test parsing lzma compressed file"""
        path = self.create_test_file("test.lzma", compression="lzma")
        result = file_to_list(str(path))
        self.assertEqual(result, self.expected_result)

    def test_parse_xz_file(self):
        """Test parsing xz compressed file"""
        path = self.create_test_file("test.xz", compression="xz")
        result = file_to_list(str(path))
        self.assertEqual(result, self.expected_result)

    def test_custom_delimiter(self):
        """Test parsing with custom delimiter"""
        content = "test1@example.com,test2@example.com,test3@example.com"
        path = self.create_test_file("test_delimiter.txt", content=content)
        result = file_to_list(str(path), delimiter=",")
        self.assertEqual(result, self.expected_result)

    def test_nonexistent_file(self):
        """Test handling of nonexistent file"""
        path = Path(self.temp_dir) / "nonexistent.txt"
        result = file_to_list(str(path))
        self.assertIsNone(result)

    def test_empty_file(self):
        """Test handling of empty file"""
        path = self.create_test_file("empty.txt", content="")
        result = file_to_list(str(path))
        self.assertEqual(result, [])

    def test_invalid_input_type(self):
        """Test handling of invalid input type"""
        result = file_to_list(123)  # Not a string
        self.assertIsNone(result)

    def test_unsupported_compression(self):
        """Test handling of unsupported compression type"""
        path = self.create_test_file("test.rar")
        result = file_to_list(str(path))
        self.assertEqual(
            result, self.expected_result
        )  # Should handle as regular text file

    def test_corrupted_bz2_file(self):
        """Test handling of corrupted bz2 file"""
        path = self.create_test_file(
            "corrupt.bz2", content="This is not a valid bz2 file"
        )
        result = file_to_list(str(path))
        self.assertIsNone(result)

    def test_corrupted_gzip_file(self):
        """Test handling of corrupted gzip file"""
        path = self.create_test_file(
            "corrupt.gz", content="This is not a valid gzip file"
        )
        result = file_to_list(str(path))
        self.assertIsNone(result)

    def test_corrupted_lzma_file(self):
        """Test handling of corrupted lzma/xz file"""
        path = self.create_test_file(
            "corrupt.xz", content="This is not a valid lzma file"
        )
        result = file_to_list(str(path))
        self.assertIsNone(result)

    def test_parse_zip_single_text_file(self):
        """Test parsing zip file containing a single text file"""
        zip_path = Path(self.temp_dir) / "single.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("emails.txt", self.test_content)
        self.addCleanup(os.remove, zip_path)

        result = file_to_list(str(zip_path))
        self.assertEqual(result, self.expected_result)

    def test_parse_zip_multiple_text_files(self):
        """Test parsing zip file containing multiple text files"""
        content1 = "test1@example.com\ntest2@example.com"
        content2 = "test3@example.com\ntest4@example.com"
        content3 = "test5@example.com"
        expected = [
            "test1@example.com",
            "test2@example.com",
            "test3@example.com",
            "test4@example.com",
            "test5@example.com",
        ]

        zip_path = Path(self.temp_dir) / "multiple.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("first.txt", content1)
            zip_file.writestr("second.txt", content2)
            zip_file.writestr("third.csv", content3)
        self.addCleanup(os.remove, zip_path)

        result = file_to_list(str(zip_path))
        self.assertEqual(result, expected)

    def test_parse_zip_with_nested_directories(self):
        """Test parsing zip file with text files in nested directories"""
        content1 = "test1@example.com\ntest2@example.com"
        content2 = "test3@example.com"
        expected = ["test1@example.com", "test2@example.com", "test3@example.com"]

        zip_path = Path(self.temp_dir) / "nested.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("dir1/nested/emails.txt", content1)
            zip_file.writestr("dir2/other.txt", content2)
        self.addCleanup(os.remove, zip_path)

        result = file_to_list(str(zip_path))
        self.assertEqual(result, expected)

    def test_parse_zip_with_non_text_files(self):
        """Test parsing zip file containing both text and non-text files"""
        content1 = "test1@example.com"
        content2 = "test2@example.com"
        expected = ["test1@example.com", "test2@example.com"]

        zip_path = Path(self.temp_dir) / "mixed.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("data1.txt", content1)
            zip_file.writestr("data2.txt", content2)
            zip_file.writestr("image.jpg", b"binary data")
            zip_file.writestr("document.pdf", b"pdf data")
        self.addCleanup(os.remove, zip_path)

        result = file_to_list(str(zip_path))
        self.assertEqual(result, expected)

    def test_parse_zip_different_text_extensions(self):
        """Test parsing zip file with different text file extensions"""
        content1 = "test1@example.com"
        content2 = "test2@example.com"
        content3 = "test3@example.com"
        expected = ["test1@example.com", "test2@example.com", "test3@example.com"]

        zip_path = Path(self.temp_dir) / "extensions.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("data.log", content1)
            zip_file.writestr("data.csv", content2)
            zip_file.writestr("data.txt", content3)
        self.addCleanup(os.remove, zip_path)

        result = file_to_list(str(zip_path))
        self.assertEqual(set(result), set(expected))

    def test_parse_zip_empty_text_files(self):
        """Test parsing zip file with empty text files"""
        content = "test1@example.com"
        expected = ["test1@example.com"]

        zip_path = Path(self.temp_dir) / "empty_files.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("empty1.txt", "")
            zip_file.writestr("data.txt", content)
            zip_file.writestr("empty2.txt", "")
        self.addCleanup(os.remove, zip_path)

        result = file_to_list(str(zip_path))
        self.assertEqual(result, expected)

    def test_corrupted_zip_file_invalid_content(self):
        """Test handling of corrupted zip file with invalid content"""
        path = self.create_test_file(
            "corrupt.zip", content="This is not a valid zip file"
        )
        result = file_to_list(str(path))
        self.assertIsNone(result)

    def test_corrupted_zip_file_truncated(self):
        """Test handling of truncated zip file"""
        # Create a valid zip file first
        zip_path = Path(self.temp_dir) / "truncated.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("test.txt", self.test_content)

        # Truncate the file to corrupt it
        with open(zip_path, "rb") as f:
            data = f.read()[:-20]  # Remove last 20 bytes
        with open(zip_path, "wb") as f:
            f.write(data)

        self.addCleanup(os.remove, zip_path)
        result = file_to_list(str(zip_path))
        self.assertIsNone(result)

    def test_corrupted_zip_file_with_corrupted_member(self):
        """Test handling of zip file with corrupted member file"""
        zip_path = Path(self.temp_dir) / "corrupt_member.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            # Add a valid file
            zip_file.writestr("valid.txt", "valid@example.com")
            # Add a corrupted file by directly writing to the ZIP
            zip_file.writestr("corrupt.txt", b"\x80\x81\x82\x83")  # Invalid UTF-8

        self.addCleanup(os.remove, zip_path)
        result = file_to_list(str(zip_path))
        # Should still get content from valid file
        self.assertEqual(result, ["valid@example.com"])

    def test_corrupted_zip_file_empty(self):
        """Test handling of empty (0 byte) zip file"""
        zip_path = Path(self.temp_dir) / "empty.zip"
        with open(zip_path, "wb") as f:
            f.write(b"")  # Create empty file

        self.addCleanup(os.remove, zip_path)
        result = file_to_list(str(zip_path))
        self.assertIsNone(result)

    def test_corrupted_zip_file_partial_header(self):
        """Test handling of zip file with partial header"""
        zip_path = Path(self.temp_dir) / "partial_header.zip"
        with open(zip_path, "wb") as f:
            f.write(b"PK\x03\x04")  # Just the ZIP magic number

        self.addCleanup(os.remove, zip_path)
        result = file_to_list(str(zip_path))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
