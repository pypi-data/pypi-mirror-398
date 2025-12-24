#! /usr/bin/env python3

################################################################################
""" Basic YML validator

    Copyright (C) 2017, 2018 John Skilleter
    """
################################################################################

import sys
import argparse

import yaml

################################################################################

def yaml_process(name, data):
    """ Recursive yaml nosher """

    if isinstance(data, dict):
        for item in data:
            yaml_process('%s::%s' % (name, item), data[item])
    else:
        print('%s: %s' % (name, data))

################################################################################

def main():
    """ Parse the command line - just takes one option (to dump the file after
        successfully parsing it) and a list of 1 or more files to parse """

    parser = argparse.ArgumentParser(description='Validate one or more YAML source files')
    parser.add_argument('--dump', action='store_true', help='Dump the YAML data after parsing it')
    parser.add_argument('--block', action='store_true', help='Force block style when dumping the YAML data')
    parser.add_argument('--flow', action='store_true', help='Force flow style when dumping the YAML data')
    parser.add_argument('--hiera', action='store_true', help='Process the file as Puppet Hiera data')
    parser.add_argument('files', nargs='+', help='YAML source file')
    args = parser.parse_args()

    if args.block and args.flow:
        sys.stderr.write('You cannot specify both block and flow style output')

    if args.block:
        flow_style = False
    elif args.flow:
        flow_style = True
    else:
        flow_style = None

    # Try to parse each file, optionally dumping the result back to stdout
    # and catching and reporting exceptions

    for filename in args.files:
        try:
            for yaml_data in yaml.safe_load_all(open(filename)):

                if args.dump:
                    if len(args.files) > 1:
                        print('File: %s' % filename)

                    print(yaml.dump(yaml_data, default_flow_style=flow_style))

                if args.hiera:
                    for data in yaml_data:
                        yaml_process(data, yaml_data[data])

        except yaml.YAMLError as exc:
            sys.stderr.write('Error: %s\n' % exc)

        except IOError:
            sys.stderr.write('Error reading %s\n' % filename)
            sys.exit(2)

################################################################################

def yamlcheck():
    """Entry point"""

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(2)

################################################################################

if __name__ == '__main__':
    yamlcheck()
