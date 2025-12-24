#! /usr/bin/env python3

"""
Read JSON Terraform output and convert back to human-readable text
This allows multiple errors and warnings to be reported as there's
no way of doing this directly from Terraform
"""

import os
import sys
import json
import argparse
from collections import defaultdict

from skilleter_modules import colour

################################################################################

def error(msg, status=1):
    """Report an error and quit"""

    colour.write(f'[RED:ERROR]: {msg}')
    sys.exit(status)

################################################################################

def main():
    """Everything"""

    # Command line is either empty or contains the input file

    parser = argparse.ArgumentParser(description='Convert Terraform JSON output back into human-readable text')
    parser.add_argument('--abspath', '-a', action='store_true', help='Output absolute file paths')
    parser.add_argument('infile', nargs='*', help='The error file (defaults to standard input if not specified)')

    args = parser.parse_args()

    # Open the input file or use stdin and read the JSON

    jsonfile = open(args.infile[0], 'rt') if args.infile else sys.stdin

    terraform = json.loads(jsonfile.read())

    # Collect each of the error/warnings

    report = defaultdict(list)

    if 'diagnostics' in terraform:
        for diagnostics in terraform['diagnostics']:
            severity = diagnostics['severity'].title()

            if 'range' in diagnostics:
                file_path = os.path.abspath(diagnostics['range']['filename']) if args.abspath else diagnostics['range']['filename']

            category = f'{severity}: {diagnostics["summary"]} - {diagnostics["detail"]}'

            message = ''
            if 'range' in diagnostics:
                message += f'In [BLUE:{file_path}:{diagnostics["range"]["start"]["line"]}]'

            if 'address' in diagnostics:
                message += f' in [BLUE:{diagnostics["address"]}]'

            report[category].append(message)

    for category in report:
        colour.write()

        # Fudge emboldening multi-line warnings

        formatted_category = '[BOLD:' + category.replace('\n', ']\n[BOLD:') + ']'
        colour.write(formatted_category)

        for entry in sorted(report[category]):
            colour.write(f'    {entry}')

    # Summarise the results

    error_count = terraform.get('error_count', 0)
    warning_count = terraform.get('warning_count', 0)

    colour.write()
    colour.write(f'[BOLD:Summary:] [BLUE:{error_count}] [BOLD:errors and] [BLUE:{warning_count}] [BOLD:warnings]')

################################################################################

def tfparse():
    """Entry point"""

    try:
        main()

    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    tfparse()
