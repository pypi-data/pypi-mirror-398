#!/usr/bin/env python3
import argparse
import sys
import os
from crew_utils import create_initial_crew_file, load_crew_file, install_package, install_all, run_script, generate_flags, create_project

def handle_init(args):
    # Interactive wizard for creating crew.json.
    # Mimics npm init behavior.
    print("This utility will walk you through creating a crew.json file.")
    print("See `crew help init` for definitive documentation on these fields and exactly what they do.")
    print("Use `npm install <pkg>` afterwards to install a package and save it as a dependency in the crew.json file.")
    print("Press ^C at any time to quit.")
    
    name = input(f"package name: ({os.path.basename(os.getcwd())}) ") or os.path.basename(os.getcwd())
    version = input("version: (1.0.0) ") or "1.0.0"
    description = input("description: ")
    main = input("entry point: (main.c) ") or "main.c"
    author = input("author: ")
    license = input("license: (GPL-3.0) ") or "GPL-3.0"
    
    # Attempt creation. Fail gracefully if it exists.
    if create_initial_crew_file(name, version, description, main, author, license):
        print("created crew.json")
    else:
        print("Aborted.")

def handle_install(args):
    # If a specific package arg is present, install it.
    # Otherwise, install all deps from crew.json (standard npm install behavior).
    if args.package:
        install_package(args.package)
    else:
        install_all()

def handle_run(args):
    run_script(args.script)

def handle_flags(args):
    print(generate_flags())

def handle_create(args):
    create_project(args.name, args.template)

def main():
    parser = argparse.ArgumentParser(description="Crew - The C/C++ Package Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize a new crew project")

    # install command
    install_parser = subparsers.add_parser("install", help="Install dependencies")
    install_parser.add_argument("package", nargs="?", help="Git URL of the package to install")

    # run command
    run_parser = subparsers.add_parser("run", help="Run a script defined in crew.json")
    run_parser.add_argument("script", help="Name of the script to run")

    # flags command
    flags_parser = subparsers.add_parser("flags", help="Output compiler flags for installed packages")

    # create command
    create_parser = subparsers.add_parser("create", help="Create a new C/C++ project")
    create_parser.add_argument("name", help="Name of the project")
    create_parser.add_argument("--template", choices=["c", "cpp"], default="c", help="Template to use (c/cpp)")

    args = parser.parse_args()

    if args.command == "init":
        handle_init(args)
    elif args.command == "install":
        handle_install(args)
    elif args.command == "run":
        handle_run(args)
    elif args.command == "flags":
        handle_flags(args)
    elif args.command == "create":
        handle_create(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
