"""SmartGit CLI interface"""

import sys
import json
import argparse
from .smartgit import SmartGit


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="smartgit",
        description="SmartGit - Intelligent Git automation with minimal commands",
    )

    # Global options
    parser.add_argument(
        "--path", default=".", help="Working directory (default: current directory)"
    )
    parser.add_argument(
        "--github-user", default="abucodingai", help="GitHub username (default: abucodingai)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # all command
    all_parser = subparsers.add_parser("all", help="Complete workflow")
    all_parser.add_argument(
        "-no-version", action="store_true", help="Skip versioning"
    )
    all_parser.add_argument(
        "-no-deploy", action="store_true", help="Skip deployment"
    )

    # repo command
    repo_parser = subparsers.add_parser("repo", help="Create repository")
    repo_parser.add_argument("name", help="Repository name")

    # ignore command
    ignore_parser = subparsers.add_parser("ignore", help="Ignore files")
    ignore_parser.add_argument("files", nargs="+", help="Files to ignore")

    # include command
    include_parser = subparsers.add_parser("include", help="Include files")
    include_parser.add_argument("files", nargs="+", help="Files to include")

    # version command
    version_parser = subparsers.add_parser("version", help="Create version")
    version_parser.add_argument("project", help="Project name")
    version_parser.add_argument("version", help="Version name")
    version_parser.add_argument("files", nargs="*", help="Files (optional)")

    # addfile command
    addfile_parser = subparsers.add_parser("addfile", help="Add files to version")
    addfile_parser.add_argument("project", help="Project name")
    addfile_parser.add_argument("version", help="Version name")
    addfile_parser.add_argument("files", nargs="+", help="Files to add")

    # lab command
    lab_parser = subparsers.add_parser("lab", help="Activate GitLab mode")
    lab_parser.add_argument("project", nargs="?", help="Project name (optional)")

    # shortcut command
    shortcut_parser = subparsers.add_parser("shortcut", help="Create shortcut")
    shortcut_parser.add_argument("name", help="Shortcut name")
    shortcut_parser.add_argument("command", nargs="+", help="Command")

    # auth command
    auth_parser = subparsers.add_parser("auth", help="GitHub authentication")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command", help="Auth commands")
    
    # auth set
    auth_set_parser = auth_subparsers.add_parser("set", help="Set credentials")
    auth_set_parser.add_argument("username", help="GitHub username or email")
    auth_set_parser.add_argument("password", help="GitHub password or token")
    auth_set_parser.add_argument("--2fa", help="2FA code (optional)")
    auth_set_parser.add_argument("--extra", help="Extra data as JSON (optional)")
    
    # auth status
    auth_subparsers.add_parser("status", help="Show auth status")
    
    # auth clear
    auth_subparsers.add_parser("clear", help="Clear credentials")

    # help command
    subparsers.add_parser("help", help="Show help")

    args = parser.parse_args()

    if not args.command or args.command == "help":
        parser.print_help()
        return

    try:
        smartgit = SmartGit(path=args.path, github_user=args.github_user)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.command == "all":
            smartgit.all(
                no_version=args.no_version, no_deploy=args.no_deploy
            )
        elif args.command == "repo":
            smartgit.repo(args.name)
        elif args.command == "ignore":
            smartgit.ignore(args.files)
        elif args.command == "include":
            smartgit.include(args.files)
        elif args.command == "version":
            smartgit.version(args.project, args.version, args.files or None)
        elif args.command == "addfile":
            smartgit.addfile(args.project, args.version, args.files)
        elif args.command == "lab":
            smartgit.lab(args.project)
        elif args.command == "shortcut":
            smartgit.shortcut(args.name, " ".join(args.command))
        elif args.command == "auth":
            if args.auth_command == "set":
                extra = None
                if args.extra:
                    try:
                        extra = json.loads(args.extra)
                    except:
                        print("Error: Invalid JSON for --extra", file=sys.stderr)
                        sys.exit(1)
                smartgit.auth(args.username, args.password, args.__dict__.get("2fa"), extra)
            elif args.auth_command == "status":
                smartgit.auth_status()
            elif args.auth_command == "clear":
                smartgit.auth_clear()
            else:
                print("Error: auth command required (set, status, clear)", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
