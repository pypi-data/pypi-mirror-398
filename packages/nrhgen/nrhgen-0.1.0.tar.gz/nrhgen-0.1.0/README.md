# nrhgen

**nrhgen** - Generate cryptographic hashes (MD5, SHA1, SHA256) for text or files.

## Features

- Hash **text** or **files** using MD5, SHA1, or SHA256
- Verify files against expected hashes
- Verbose mode

## Installation

```bash
git clone https://github.com/noraraven/nrhgen.git
cd nrhgen
pip install -e .
```

## Usage

```bash
 # Show help page
nrhgen -h

 # Hash a text string
nrhgen -t "text" -a sha256

 # Hash file(s)
nrhgen -f file1 [file2 ...] -a md5

 # Verify files
nrhgen -c file:hash [file:hash ...] -a sha256

 # Verbose mode
nrhgen -v -f file1 [file2 ...] -a md5
```

## License

This project is licensed under the [MIT License](LICENSE).

## Author

Made by [noraraven](https://github.com/noraraven)
