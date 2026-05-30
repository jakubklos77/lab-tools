#!/bin/python

# Usage: ./apt_tool.py "local_fix" / "diff" / "bookmark" / "restore" / "mark_auto"> <args>

import os
import subprocess
import argparse

def run_bash_command_output(command):
    try:
        print(f"Executing:\n{command}")

        # Execute the command in a shell, capture output
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        output = []
        # Read and print each line of output in real-time
        for line in iter(process.stdout.readline, b''):
            data = line.decode('utf-8')
            print(data, end='')
            output.append(data)

        # Return the output
        return output
    except subprocess.CalledProcessError as e:
        # Handle errors if the command fails
        print(f"Error executing command: {e}")
        return None

def run_bash_command_output_quiet(command):
    """Like run_bash_command_output but without any console printing — used for per-package loops."""
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = []
        for line in iter(process.stdout.readline, b''):
            output.append(line.decode('utf-8'))
        return output
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return []

def execute_command(command):
    try:
        print(f"Executing:\n{command}")

        # Execute the command in the shell directly
        return subprocess.run(command, shell=True)
    except subprocess.CalledProcessError as e:
        # Handle errors if the command fails
        print(f"Error executing command: {e}")

def load_package_list_dict(filename, condition=""):
    result = {}
    with open(filename) as file:
        for line in file:

            # Parse
            line = line.strip()
            split = line.split('/')

            # Check line
            if len(split) > 1:

                # Get state and package
                package = split[0]
                state = line.split('[')[1].split(']')[0]

                # Set states
                if state == 'installed,automatic':
                    state = 'auto'
                elif state == 'installed':
                    state = 'manual'
            else:
                package = split[0]
                state = package

            # Condition
            if condition != "":
                if condition != state:
                    continue

            # Result
            result[package] = state

    print('Got %s %s records' % (filename, len(result)))
    return result

def compare_package_list(masters, slaves):
    result = {}

    for slave in slaves:
        if slave not in masters:
            result[slave] = 'remove'
        elif masters[slave] != slaves[slave]:
            result[slave] = 'mark_' + masters[slave]  # 'mark_auto' or 'mark_manual'

    for master in masters:
        if master not in slaves:
            result[master] = 'install'

    return result

def load_and_compare_package_lists(master_file, slave_file):

    # Load masters
    masters = load_package_list_dict(master_file, "")

    # Load slaves
    slaves = load_package_list_dict(slave_file, "")

    # Compare
    result = compare_package_list(masters, slaves)

    return result

def detect_codename():
    try:
        result = subprocess.run(['lsb_release', '-cs'], capture_output=True, text=True)
        name = result.stdout.strip()
        if name:
            return name
    except FileNotFoundError:
        pass
    try:
        with open('/etc/os-release') as f:
            for line in f:
                if line.startswith('VERSION_CODENAME='):
                    return line.split('=', 1)[1].strip().strip('"')
    except OSError:
        pass
    return None

def bookmark_to_file(bookmark_file):

    apt_command = 'apt list --installed > ' + bookmark_file

    # Get local files
    run_bash_command_output(apt_command)

if __name__ == "__main__":

    # Parse arguments
    parser = argparse.ArgumentParser(description='APT tool')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    # Subparser for local_fix
    parser_local_fix = subparsers.add_parser('local_fix', help='Reinstall locally installed packages from the repository')
    parser_local_fix.add_argument('--code-name', type=str, default=None, help='Code name for the repository (default: auto-detected)')

    # Subparser for local_delete
    parser_local_fix = subparsers.add_parser('local_delete', help='Delete locally installed packages from the repository')

    # Subparser for diff
    parser_list_diff = subparsers.add_parser('diff', help='Compare master and slave package lists. Create lists with: ./apt_tool.py bookmark <file>')
    parser_list_diff.add_argument('master_file', type=str, help='Master file')
    parser_list_diff.add_argument('slave_file', type=str, help='Slave file')

    # Subparser for bookmark
    parser_list_diff = subparsers.add_parser('bookmark', help='Create a list of installed packages')
    parser_list_diff.add_argument('bookmark_file', type=str, help='Write to this bookmark file')

    # Subparser for restore
    parser_list_diff = subparsers.add_parser('restore', help='Restore a list of installed packages. Compares the current list with the bookmark file and removes extra packages or the ones marked from automatic to manual')
    parser_list_diff.add_argument('bookmark_file', type=str, help='Read from the bookmark file')

    # Subparser for mark_auto
    subparsers.add_parser('mark_auto', help='Mark manually-installed packages as auto if any auto-installed package depends on them')

    args = parser.parse_args()

    if args.action == "local_fix":

        code_name = args.code_name or detect_codename()
        if not code_name:
            print("Error: could not detect OS codename. Pass --code-name explicitly.")
            exit(1)
        print(f"Using codename: {code_name}")

        # Command
        apt_command = 'apt list --installed | grep "local]"'

        # Get local files
        lines = run_bash_command_output(apt_command)
        for line in lines:

            # Process each line
            package, _ = line.split('/')

            # Reinstall
            execute_command("apt install --reinstall " + package + "/" + code_name)

    if args.action == "local_delete":

        # Command
        apt_command = 'apt list --installed | grep "local]"'

        # Get local files
        lines = run_bash_command_output(apt_command)
        for line in lines:

            # Process each line
            package, _ = line.split('/')

            # Reinstall
            execute_command("apt remove " + package)

    elif args.action == "mark_auto":

        # Fetch all manually installed packages
        print("Fetching manually installed packages...")
        manual_lines = run_bash_command_output("apt-mark showmanual")
        manual_packages = [l.strip() for l in manual_lines if l.strip()]
        print(f"Found {len(manual_packages)} manually installed package(s)\n")

        # Fetch all auto installed packages into a set for fast lookup (quiet — list is huge)
        auto_lines = run_bash_command_output_quiet("apt-mark showauto")
        auto_packages_set = set(l.strip() for l in auto_lines if l.strip())

        # Check each manual package for reverse-dependencies from auto-installed packages
        print("Checking reverse dependencies (this may take a moment)...")
        candidates = []
        for package in manual_packages:
            rdep_lines = run_bash_command_output_quiet(
                f"apt-cache rdepends --installed {package} | awk 'NR>2'"
            )
            # Clean up each rdepend entry (lines may be prefixed with '|' for alternatives)
            rdeps = [l.strip().lstrip('|').strip() for l in rdep_lines if l.strip()]

            # Also fetch ALL outgoing relationships of this package (Depends, Recommends,
            # Suggests, Pre-Depends, ...).  If an auto-installed rdepend was pulled in
            # by *any* of those relationships it forms a cycle
            # (e.g. vlc Recommends vlc-plugin-notify; vlc-plugin-notify Depends vlc)
            # and must be excluded — otherwise top-level manually installed packages
            # like vlc would be incorrectly flagged.
            own_dep_lines = run_bash_command_output_quiet(
                f"apt-cache depends --installed {package} | awk '{{print $NF}}' | tr -d '<>'"
            )
            own_deps = set(l.strip() for l in own_dep_lines if l.strip())

            # A valid auto rdepend is one that is auto-installed but is NOT a forward
            # dependency of this package (ruling out the circular-reference false positives)
            has_valid_auto_rdep = any(
                rdep in auto_packages_set and rdep not in own_deps
                for rdep in rdeps
            )

            if has_valid_auto_rdep:
                candidates.append(package)
                print(f"  Auto-dependency found: {package}")

        if not candidates:
            print("\nNo manually installed packages with auto-installed dependents found.")
        else:
            print(f"\nPackages to mark as auto ({len(candidates)}):")
            for pkg in candidates:
                print(f"  {pkg}")

            confirm = input(f"\nMark these {len(candidates)} package(s) as auto? [y/N] ")
            if confirm.strip().lower() == 'y':
                execute_command("apt-mark auto " + " ".join(candidates))
            else:
                print("Aborted.")

    elif args.action == "diff":

        master_file = args.master_file
        slave_file = args.slave_file

        # Compare
        result = load_and_compare_package_lists(master_file, slave_file)

        # Print result
        print('Compare diff %s ' % len(result))
        for key, value in result.items():
            print(f"{key}: {value}")

    elif args.action == "bookmark":

        bookmark_file = args.bookmark_file

        # Bookmark
        bookmark_to_file(bookmark_file)

    elif args.action == "restore":

        master_file = args.bookmark_file
        slave_file = master_file + ".slave.tmp"

        # Bookmark to slave file
        bookmark_to_file(slave_file)

        # Compare
        result = load_and_compare_package_lists(master_file, slave_file)

        remove_packages = []
        install_packages = []
        auto_packages = []
        manual_packages = []
        for key, value in result.items():
            if value == 'remove':
                remove_packages.append(key)
            elif value == 'install':
                install_packages.append(key)
            elif value == 'mark_auto':
                auto_packages.append(key)
            elif value == 'mark_manual':
                manual_packages.append(key)

        if remove_packages:
            execute_command("apt remove " + " ".join(remove_packages))
        if install_packages:
            execute_command("apt install " + " ".join(install_packages))
        if auto_packages:
            execute_command("apt-mark auto " + " ".join(auto_packages))
        if manual_packages:
            execute_command("apt-mark manual " + " ".join(manual_packages))

        # Remove slave_file
        os.remove(slave_file)

    else:
        print(f"Unknown action: {args.action}")
        parser.print_help()