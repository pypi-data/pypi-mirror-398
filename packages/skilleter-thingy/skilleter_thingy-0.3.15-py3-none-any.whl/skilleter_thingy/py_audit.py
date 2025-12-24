#!/usr/bin/env python3

""" Query api.osv.dev to determine whether a specified version of a particular
    Python package is subject to known security vulnerabilities """

################################################################################

import sys
import requests
import subprocess
import tempfile
import re
import glob
import argparse

################################################################################

PIP_PACKAGES = ('pip', 'pkg_resources', 'setuptools')
PIP_OPTIONS = '--no-cache-dir'

QUERY_URL = "https://api.osv.dev/v1/query"
QUERY_HEADERS = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}

ANSI_NORMAL = '\x1b[0m'
ANSI_BOLD = '\x1b[1m'

################################################################################

def audit(package, version):
    """ Main function """

    # Query api.osv.dev for known vulnerabilties in this version of the package

    payload = '{"version": "'+version+'", "package": {"name": "'+package+'", "ecosystem": "PyPI"}}'
    result = requests.post(QUERY_URL, data=payload, headers=QUERY_HEADERS)

    # Parse and report the results

    details = result.json()

    print('-' * 80)
    if package in PIP_PACKAGES:
        print(f'Package: {package} {version} (part of Pip)')
    else:
        print(f'Package: {package} {version}')

    print()

    if 'vulns' in details:
        print(f'{len(details["vulns"])} known vulnerabilities')

        for v in details['vulns']:
            print()
            print(f'{ANSI_BOLD}Vulnerability: {v["id"]}{ANSI_NORMAL}')

            if 'summary' in v:
                print(f'Summary:       {v["summary"]}')

            if 'aliases' in v:
                print('Aliases:       %s' % (', '.join(v['aliases'])))

            if 'details' in v:
                print()
                print(v['details'])
    else:
        print('No known vulnerabilities')

################################################################################

def main():
    """ Entry point """

    parser = argparse.ArgumentParser(
        description='Query api.osv.dev to determine whether Python packagers in a requirments.txt file are subject to known security vulnerabilities')
    parser.add_argument('requirements', nargs='*', type=str, action='store',
                        help='The requirements file (if not specified, then the script searches for a requirements.txt file)')
    args = parser.parse_args()

    requirements = args.requirements or glob.glob('**/requirements.txt', recursive=True)

    if not requirements:
        print('No requirements.txt file(s) found')
        sys.exit(0)

    # Create a venv for each requirements file, install pip and the packages
    # and prerequisites, get the list of installed package versions
    # and check each one.

    for requirement in requirements:
        print('=' * 80)
        print(f'{ANSI_BOLD}File: {requirement}{ANSI_NORMAL}')
        print()

        with tempfile.TemporaryDirectory() as env_dir:
            with tempfile.NamedTemporaryFile() as package_list:
                script = f'python3 -m venv {env_dir}' \
                         f' && . {env_dir}/bin/activate' \
                         f' && python3 -m pip {PIP_OPTIONS} install --upgrade pip setuptools' \
                         f' && python3 -m pip {PIP_OPTIONS} install -r {requirement}' \
                         f' && python3 -m pip {PIP_OPTIONS} list | tail -n+3 | tee {package_list.name}' \
                          ' && deactivate'

                try:
                    subprocess.run(script, check=True, shell=True)

                except subprocess.CalledProcessError as exc:
                    print(f'ERROR #{exc.returncode}: {exc.stdout}')
                    sys.exit(exc.returncode)

                with open(package_list.name) as infile:
                    for package in infile.readlines():
                        package_info = re.split(' +', package.strip())

                        audit(package_info[0], package_info[1])

################################################################################

def py_audit():
    """Entry point"""

    try:
        main()

    except KeyboardInterrupt:
        sys.exit(1)

    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    py_audit()
