[![Static Badge](https://img.shields.io/badge/Project_Name-Pyrolysate-blue)](https://github.com/lignum-vitae/pyrolysate)
[![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Flignum-vitae%2Fpyrolysate%2Fmain%2Fpyproject.toml)](https://github.com/lignum-vitae/pyrolysate)
[![PyPI version](https://img.shields.io/pypi/v/pyrolysate.svg)](https://pypi.org/project/pyrolysate/)
[![GitHub License](https://img.shields.io/github/license/lignum-vitae/pyrolysate)](https://github.com/lignum-vitae/pyrolysate/blob/main/LICENSE)
[![GitHub branch check runs](https://img.shields.io/github/check-runs/lignum-vitae/pyrolysate/main)](https://github.com/lignum-vitae/pyrolysate)

# Pyrolysate

Pyrolysate is a Python library and CLI tool for parsing and validating URLs and email addresses.
It breaks down URLs and emails into their component parts, validates against IANA's official TLD list,
and outputs structured data in JSON, CSV, or text format.

The library offers both a programmer-friendly API and a command-line interface,
making it suitable for both development integration and quick data processing tasks.
It handles single entries or large datasets efficiently using Python's generator functionality,
and provides flexible input/output options including file processing with custom delimiters.

## Features

### URL Parsing
  - Extract scheme, subdomain, domain, TLD, port, path, query, and fragment components
  - Support for complex URL patterns including ports, queries, and fragments
  - Support for IP addresses in URLs
  - Support for both direct input and file processing via CLI or API
  - Output as JSON, CSV, or text format through CLI or API

### Email Parsing
  - Extract username, mail server, and domain components
  - Support for plus addressing (e.g., user+tag@domain.com)
  - Support for both direct input and file processing via CLI or API
  - Output as JSON, CSV, or text format through CLI or API

### Top Level Domain Validation
  - Automatic updates from IANA's official TLD list
  - Local TLD file caching for offline use
  - Fallback to common TLDs if both online and local sources fail

### Flexible Input/Output
  - Process single or multiple entries
  - Support for government domain emails (.gov.tld)
  - Custom delimiters for file input
  - Multiple output formats with .txt format as default (JSON, CSV, text)
  - Pretty-printed or minified JSON output
  - Console output or file saving options
  - Memory-efficient processing of large datasets using Python generators
  - Support for compressed input files:
    - ZIP archives (processes all text files within .zip)
    - GZIP (.gz)
    - BZIP2 (.bz2)
    - LZMA (.xz, .lzma)

### Developer Friendly
  - Type hints for better IDE support
  - Comprehensive docstrings
  - Modular design for easy integration
  - Command-line interface for quick testing

## API Reference

### Email Class

| Method                                           | Parameters                                              | Description                    |
|---------------------                             |---------------------                                    |-----------------               |
| `parse_email(email_str)`                         | `email_str: str`                                        | Parses single email address    |
| `parse_email_array(emails)`                      | `emails: list[str]`                                     | Parses list of email addresses |
| `to_json(emails, prettify=True)`                 | `emails: str\|list[str]`, `prettify: bool`              | Converts to JSON format        |
| `to_json_file(file_name, emails, prettify=True)` | `file_name: str`, `emails: list[str]`, `prettify: bool` | Converts and saves JSON to file|
| `to_csv(emails)`                                 | `emails: str\|list[str]`                                | Converts to CSV format         |
| `to_csv_file(file_name, emails)`                 | `file_name: str`, `emails: list[str]`                   | Converts and saves CSV to file |

### URL Class

| Method                                         | Parameters                                            | Description                                               |
|------------------                              |----------------------                                 |-------------------                                        |
| `parse_url(url_str, tlds=[])`                  | `url_str: str`, `tlds: list[str]`                     | Parses single URL                                         |
| `parse_url_array(urls, tlds=[])`               | `urls: list[str]`, `tlds: list[str]`                  | Parses list of URLs                                       |
| `to_json(urls, prettify=True)`                 | `urls: str\|list[str]`, `prettify: bool`              | Converts to JSON format                                   |
| `to_json_file(file_name, urls, prettify=True)` | `file_name: str`, `urls: list[str]`, `prettify: bool` | Converts and saves JSON to file                           |
| `to_csv(urls)`                                 | `urls: str\|list[str]`                                | Converts to CSV format                                    |
| `to_csv_file(file_name, urls)`                 | `file_name: str`, `urls: list[str]`                   | Converts and saves CSV to file                            |
| `get_tld(path_to_tlds_file='tld.txt')`         | `path_to_tlds_file: str = 'tld.txt'`                  | Fetches current TLD list from IANA                        |
| `local_tld_file(file_name)`                    | `file_name: str`                                      | Fetches and stores `get_tld()` output as a local txt file |

### Miscellaneous

| Method                                          | Parameters                               | Description                                     |
|------------------                               |----------------------                    |-------------------------                        |
| `file_to_list(input_file_name, delimiter='\n')` | `input_file_name: str`, `delimiter: str` | Parses input file into python list by delimiter |

## CLI Reference

| Argument               | Type   | Value when argument is omitted| Description                        |
|------------------------|--------|--------------------           |------------------------------------|
| `target`               | `str`  | `None`                        | Email or URL string(s) to process  |
| `-u`, `--url`          | `flag` | `False`                       | Specify URL input                  |
| `-e`, `--email`        | `flag` | `False`                       | Specify Email input                |
| `-i`, `--input_file`   | `str`  | `None`                        | Input file name with extension     |
| `-o`, `--output_file`  | `str`  | `None`                        | Output file name without extension |
| `-c`, `--csv`          | `flag` | `False`                       | Save output as CSV format          |
| `-j`, `--json`         | `flag` | `False`                       | Save output as JSON format         |
| `-np`, `--no_prettify` | `flag` | `False`                       | Turn off prettified JSON output    |
| `-d`, `--delimiter`    | `str`  | `'\n'`                        | Delimiter for input file parsing   |

### Input File Support
| Format | Extension  | Description                    |
|--------|------------|--------------------------------|
| Text   | .txt       | Plain text files               |
| Log    | .log       | Plain text log files           |
| CSV    | .csv       | Comma-separated values         |
| ZIP    | .zip       | Archives containing text files |
| GZIP   | .gz        | GZIP compressed files          |
| BZIP2  | .bz2       | BZIP2 compressed files         |
| LZMA   | .xz, .lzma | LZMA compressed files          |

## Output Types

### Email Parse Output

| Field        | Description                   | Example            |
|--------------|-------------------------------|--------------------|
| input        | Full email                    | user+tag@gmail.com |
| username     | Part before + or @ symbol     | user               |
| plus_address | Optional part between + and @ | tag                |
| mail_server  | Domain before TLD             | gmail              |
| domain       | Top-level domain              | com                |

Example output:
```json
{"user+tag@gmail.com": 
    {
    "username": "user",
    "plus_address": "tag",
    "mail_server": "gmail",
    "domain": "com"
    }
}
```

```csv
email,username,plus_address,mail_server,domain
user+tag@gmail.com,user,tag,gmail,com
```

### URL Parse Output

| Field               | Description      | Example   |
|--------------       |---------------   |---------  |
| scheme              | Protocol         | https     |
| subdomain           | Domain prefix    | www       |
| second_level_domain | Main domain      | example   |
| top_level_domain    | Domain suffix    | com       |
| port                | Port number      | 443       |
| path                | URL path         | blog/post |
| query               | Query parameters | q=test    |
| fragment            | URL fragment     | section1  |

Example output:
```json
{"https://www.example.com:443/blog/post?q=test#section1": 
    {
    "scheme": "https",
    "subdomain": "www",
    "second_level_domain": "example",
    "top_level_domain": "com",
    "port": "443",
    "path": "blog/post",
    "query": "q=test",
    "fragment": "section1"
    }
}
```

```csv
url,scheme,subdomain,second_level_domain,top_level_domain,port,path,query,fragment
https://www.example.com:443/blog/post?q=test#section1,https,www,example,com,443,blog/post,q=test,section1
```

## 🚀 Installation
### From PyPI
```bash
pip install pyrolysate
```
### For Development
1. **Clone the repository**
```bash
git clone https://github.com/dawnandrew100/pyrolysate.git
cd pyrolysate
```
2. **Create and activate a virtual environment**
```bash
# Using hatch (recommended)
hatch env create

# Or using venv
python -m venv .venv
# Windows
.venv\Scripts\activate
# Unix/MacOS
source .venv/bin/activate
```
3. **Install in development mode**
```bash
# Using hatch
hatch run dev

# Or using pip
pip install -e .
```
### Verify Installation
```bash
# Using hatch (recommended)
hatch run pyro -u example.com

# Or using the CLI directly
pyro -u example.com
```
The CLI command `pyro` will be available after installation. If the command isn't found, ensure Python's Scripts directory is in your PATH.

## Usage

### Input File Parsing
```python
from pyrolysate import file_to_list
```
#### Parse file with default newline delimiter
```python
urls = file_to_list("urls.txt")
```
#### Parse file with custom delimiter
```python
emails = file_to_list("emails.csv", delimiter=",")
```
### Supported Outputs
- JSON (prettified or minified)
- CSV
- Text (default)
- File output with custom naming
- Console output
### Email Parsing
```python
from pyrolysate import email
```
#### Parse single email
```python
result = email.parse_email("user@example.com")
```
#### Parse plus addressed email
```python
result = email.parse_email("user+tag@example.com")
```
#### Parse multiple emails
```python
emails = ["user1@example.com", "user2@agency.gov.uk"]
result = email.parse_email_array(emails)
```
#### Convert to JSON
```python
json_output = email.to_json("user@example.com")
json_output = email.to_json(["user1@example.com", "user2@example.com"])
```
#### Save to JSON file
```python
email.to_json_file("output", "user@example.com")
email.to_json_file("output", ["user1@example.com", "user2@test.org"])
```
#### Convert to CSV
```python
csv_output = email.to_csv("user@example.com")
csv_output = email.to_csv(["user1@example.com", "user2@test.org"])

```
#### Save to CSV file
```python
email.to_csv_file("output", "user@example.com")
email.to_csv_file("output", ["user1@example.com", "user2@test.org"])
```

### URL Parsing
```python
from pyrolysate import url
```
#### Parse single URL
```python
result = url.parse_url("https://www.example.com/path?q=test#fragment")
```
#### Parse multiple URLs
```python
urls = ["example.com", "https://www.test.org"]
result = url.parse_url_array(urls)
```
#### Convert to JSON
```python
json_output = url.to_json("example.com")
json_output = url.to_json(["example.com", "test.org"])
```
#### Save to JSON file
```python
url.to_json_file("output", "example.com")
url.to_json_file("output", ["example.com", "test.org"])
```
#### Convert to CSV
```python
csv_output = url.to_csv("example.com")
csv_output = url.to_csv(["example.com", "test.org"])

```
#### Save to CSV file
```python
url.to_csv_file("output", "example.com")
url.to_csv_file("output", ["example.com", "test.org"])
```
### Command Line Interface
#### CLI help
```bash
pyro -h
```
#### Parse single URL
```bash
pyro -u example.com
```
#### Parse multiple URLs
```bash
pyro -u example1.com example2.com
```
#### Parse URLs from file (one per line by default)
```bash
pyro -u -i urls.txt
```
#### Parse URLs from CSV file with comma delimiter
```bash
pyro -u -i urls.csv -d ","
```
#### Parse email with plus addressing
```bash
pyro -e user+newsletter@example.com
```
#### Parse multiple emails and save as JSON
```bash
pyro -e user1@example.com user2@example.com -j -o output
```
#### Parse URLs from file and save as CSV
```bash
pyro -u -i urls.txt -c -o parsed_urls
```
#### Parse emails from file with comma delimiter
```bash
pyro -e -i emails.txt -d "," -o output
```
#### Parse emails with non-prettified JSON output
```bash
pyro -e user@example.com -j -np
```
#### Parse different file types
```bash
# Parse log file
pyro -u -i server.log

# Parse compressed log file
pyro -u -i server.log.gz

# Parse BZIP2 compressed file
pyro -e -i emails.txt.bz2

# Parse ZIP archive containing logs and text files
pyro -u -i archive.zip
```

## Supported Formats

### Email Formats
- Standard: `example@mail.com`
- Plus Addresses: `example+tag@mail.com`
- Government: `example@agency.gov.uk`

### URL Formats
- Basic: `example.com`
- With subdomain: `www.example.com`
- With scheme: `https://example.org`
- With path: `example.com/path/to/file.txt`
- With port: `example.com:8080`
- With query: `example.com/search?q=test`
- With fragment: `example.com#section1`
- IP addresses: `192.168.1.1:8080`
- Government domains: `agency.gov.uk`
- Full complex URLs: `https://www.example.gov.uk:8080/path?q=test#section1`

### Input File Support
- Plain text files (.txt)
- Plain text log files (.log)
- Comma-separated values (.csv)
- ZIP archives containing text files (.zip)
- GZIP compressed files (.gz)
- BZIP2 compressed files (.bz2)
- LZMA compressed files (.xz, .lzma)

#### ZIP Archive Support
- Processes all text files within the archive (.txt, .csv, .log)
- Handles nested directories
- Continues processing if some files are corrupted
- UTF-8 encoding expected for text files

### Outputs
- Text file (default)
- JSON file (prettified or minified)
- CSV file
- Console output
