#!/usr/bin/env python -B
# vi: set syntax=python ts=4 sw=4 sts=4 et ff=unix ai si :
#
# (c) Steven Scholnick <scholnicks@gmail.com>
# The chname source code is published under a MIT license.

"""
Usage:
    chname append [--dry-run --quiet --verbose] <suffix> <files>...
    chname lower [--dry-run --quiet --verbose] <files>...
    chname merge [--dry-run --quiet --verbose] <directory> <files>...
    chname order [--dry-run --quiet --verbose] <files>...
    chname remove [--dry-run --quiet --verbose] <pattern> <files>...
    chname prepend [--dry-run --quiet --verbose] <prefix> <files>...
    chname substitute [--dry-run --quiet --verbose] <old> <new> <files>...
    chname titles [--dry-run --quiet --verbose] <input> <files>...
    chname usage
    chname (-h | --help)
    chname --version

Options:
    --dry-run                  Show what would be done, but don't actually do it
    -h, --help                 Show this help screen
    -q, --quiet                Quiet mode
    -v, --verbose              Verbose mode
    --version                  Prints the version
"""

import os
import random
import re
import sys
from pathlib import Path

from docopt import DocoptExit, docopt

arguments = {}

OPERATIONS = {
    "append": lambda: append(),
    "lower": lambda: lower(),
    "merge": lambda: merge(),
    "order": lambda: order(),
    "remove": lambda: remove(),
    "prepend": lambda: prepend(),
    "substitute": lambda: substitute(),
    "titles": lambda: titles(),
    "usage": lambda: usage(),
}


def main() -> None:
    """Main entry point for chname utility"""
    try:
        global arguments
        arguments = docopt(__doc__, version="chname 3.0.2")
        for operation, func in OPERATIONS.items():
            if arguments[operation]:
                func()

        sys.exit(0)
    except (DocoptExit, KeyError):
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(1)


def substitute() -> None:
    """Substitutes a pattern in the specified files"""
    for filePath in arguments["<files>"]:
        rename_file(filePath, filePath.replace(arguments["<old>"], arguments["<new>"]))


def append() -> None:
    """Appends a suffix to the specified files"""
    for filePath in arguments["<files>"]:
        rename_file(filePath, f"{filePath}{arguments["<suffix>"]}")


def lower() -> None:
    """Translates filenames to lowercase"""
    for filePath in arguments["<files>"]:
        rename_file(filePath, filePath.lower())


def prepend() -> None:
    """To prepends a prefix to the specified files"""
    for filePath in arguments["<files>"]:
        p = Path(filePath)
        rename_file(filePath, str(p.parent / f"{arguments['<prefix>']}{p.name}"))


def remove() -> None:
    """Removes a pattern from the specified files"""
    for filePath in arguments["<files>"]:
        rename_file(filePath, re.sub(arguments["<pattern>"], r"", filePath))


def order() -> None:
    """Orders the files"""
    filenameTemplate = r"{num:02d} - {filename}" if len(arguments["<files>"]) < 100 else r"{num:04d} - {filename}"

    for index, currentFilePath in enumerate(sorted(arguments), 1):
        newFilePath = os.path.join(
            os.path.dirname(currentFilePath),
            filenameTemplate.format(num=index, filename=os.path.basename(currentFilePath)),
        )
        rename_file(currentFilePath, newFilePath)


def merge() -> None:
    """Merges files into a single directory with standardized names"""
    # determine the extension
    extension = calculateExtension(arguments["<files>"])

    # rename the files in argument specified order
    for index, filename in enumerate(arguments["<files>"], 1):
        new_file_name = os.path.join(arguments["<directory>"], f"file_{index:04d}" + extension)
        rename_file(filename, new_file_name)


def calculateExtension(files) -> str:
    """determines a single extension"""
    extensions = set((os.path.splitext(f)[1].lower() for f in files))
    if len(extensions) > 1:
        raise SystemExit(f"Only one extension allowed. Found: {", ".join(extensions)}")

    return extensions.pop()


def titles() -> None:
    """Names files by using an input text file"""
    extension = calculateExtension(arguments["<files>"])

    titlesFilePath = arguments["<input>"]
    if not titlesFilePath.exists(titlesFilePath):
        raise SystemExit(f"Titles file {titlesFilePath} does not exist")

    with titlesFilePath.open("r") as fp:
        exportFileNames = [line.strip() for line in fp if line.strip()]

    if len(arguments["<files>"]) != len(exportFileNames):
        raise SystemExit(
            f"{arguments["<input>"]} filenames ({len(exportFileNames)}) and files length ({len(arguments["<files>"])}) do not match"
        )

    filenameTemplate = (
        r"{num:02d} - {filename}{extension}"
        if len(arguments["<files>"]) < 100
        else r"{num:04d} - {filename}{extension}"
    )

    index: int = 1
    for currentFilePath, newFileName in zip(arguments["<files>"], exportFileNames):
        newFilePath = os.path.join(
            os.path.dirname(currentFilePath),
            filenameTemplate.format(num=index, filename=newFileName, extension=extension),
        )
        rename_file(currentFilePath, newFilePath)
        index += 1


def rename_file(oldName, newName) -> None:
    """Performs the actual file rename"""
    if arguments["--verbose"] or arguments["--dry-run"]:
        print(f"Renaming {oldName} to {newName}")

    if not Path(oldName).exists():
        if not arguments["--quiet"]:
            print(f"File {oldName} does not exist", file=sys.stderr)
        return

    if not arguments["--dry-run"]:
        os.rename(oldName, newName)


def usage() -> None:
    print(
        __doc__
        + """
Merge
-----
To merge files from two different directories into the current directory:

chname --merge d1/* d2/*

Input Files: d1/file1.txt d1/file2.txt d2/file1.txt
Results: ./file_0001.txt ./file_0002.txt ./file_0003.txt

where file_0003.txt is d2/file3.txt

All of the files must have the same extension. The filename format is file_NUMBER.extension.


Order
-----

Adds a numerical prefix to sorted input files. Example:

chname --order filea.mp3 fileb.mp3

becomes:

01 - filea.mp3 02 - fileb.mp3

"""
    )


if __name__ == "__main__":
    main()
