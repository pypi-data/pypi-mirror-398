# TRMD

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.13%2B-blue)

Translate Markdown using OpenAI.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Install](#install)
- [Usage](#usage)
- [Release Notes](#release-notes)
- [License](#license)

## Prerequisites

- Python 3.13 and above

## Install

- with brew

```bash
brew tap rioriost/trmd
brew install trmd
```

- with uv

```bash
uv init your_project
cd your_project
uv venv
source .venv/bin/activate
uv add trmd
```

- with python venv on macOS / Linux

```bash
mkdir your_project
cd your_project
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install trmd
```

- with python venv on Windows

```bash
mkdir your_project
cd your_project
python -m venv venv
.\venv\Scripts\activate
python -m pip install trmd
```

## Usage

```bash
trmd --help
usage: trmd [-h] [-o OUTPUT_FILE] [-k KEY] [-m MODEL] [--temperature TEMPERATURE] [--fragment-size FRAGMENT_SIZE] [-s {en,fr,es,de,it,pt,ru,ja,zh,ko}]
            [-t {en,fr,es,de,it,pt,ru,ja,zh,ko}] [-a ADDITIONAL_PROMPT_FILE]
            input_file

Trmd

positional arguments:
  input_file            Path to Markdown file to be translated

options:
  -h, --help            show this help message and exit
  -o, --output_file OUTPUT_FILE
                        Path to the translated file
  -k, --key KEY         OpenAI API key
  -m, --model MODEL     OpenAI Model to use
  --temperature TEMPERATURE
                        Temperature for API requests
  --fragment-size FRAGMENT_SIZE
                        Fragment size for API requests
  -s, --source-language {en,fr,es,de,it,pt,ru,ja,zh,ko}
                        Language of source Markdown
  -t, --target-language {en,fr,es,de,it,pt,ru,ja,zh,ko}
                        Language to translate to
  -a, --additional-prompt-file ADDITIONAL_PROMPT_FILE
                        Additional prompt for translation
```

## Release Notes

### 0.1.29 Release
- Dependency Update

### 0.1.28 Release
- Dependency Update

### 0.1.27 Release
- Security Update

### 0.1.26 Release
- Dependency Update

### 0.1.25 Release
- Dependency Update

### 0.1.24 Release
- Dependency Update

### 0.1.23 Release
- Dependency Update

### 0.1.22 Release
- Dependency Update

### 0.1.21 Release
- Dependency Update

### 0.1.20 Release
- Dependency Update

### 0.1.19 Release
- Dependency Update

### 0.1.18 Release
- Dependency Update

### 0.1.17 Release
- Dependency Update

### 0.1.16 Release
- Dependency Update

### 0.1.15 Release
- Dependency Update

### 0.1.14 Release
- Dependency Update

### 0.1.13 Release
- Dependency Update

### 0.1.12 Release
- Dependency Update

### 0.1.11 Release
- Dependency Update

### 0.1.10 Release
- Dependency Update

### 0.1.9 Release
- Dependency Update

### 0.1.8 Release
- Dependency Update

### 0.1.7 Release
- Dependency Update

### 0.1.6 Release
- Dependency Update

### 0.1.5 Release
- Dependency Update

### 0.1.4 Release
- Dependency Update

### 0.1.3 Release
- Dependency Update

### 0.1.2 Release
- Dependency Update

### 0.1.1 Release
- Dependency Update

### 0.1.0 Release
- Initial release

## License

MIT License
