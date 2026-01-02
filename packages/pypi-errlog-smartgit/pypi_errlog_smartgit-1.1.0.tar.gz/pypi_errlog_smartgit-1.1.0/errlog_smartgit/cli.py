"""errlog-smartgit CLI interface"""

import sys
import argparse
from .errlog_smartgit import SmartGitErr


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="smartgit-err",
        description="SmartGit Error Handler - Detailed error feedback and step-by-step process view",
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
        smartgit_err = SmartGitErr(path=args.path, github_user=args.github_user)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.command == "all":
            smartgit_err.all(
                no_version=args.no_version, no_deploy=args.no_deploy
            )
        elif args.command == "repo":
            smartgit_err.repo(args.name)
        elif args.command == "ignore":
            smartgit_err.ignore(args.files)
        elif args.command == "include":
            smartgit_err.include(args.files)
        elif args.command == "version":
            smartgit_err.version(args.project, args.version, args.files or None)
        elif args.command == "addfile":
            smartgit_err.addfile(args.project, args.version, args.files)
        elif args.command == "lab":
            smartgit_err.lab(args.project)
        elif args.command == "shortcut":
            smartgit_err.shortcut(args.name, " ".join(args.command))
        elif args.command == "auth":
            if args.auth_command == "set":
                smartgit_err.auth(args.username, args.password, args.__dict__.get("2fa"))
            elif args.auth_command == "status":
                smartgit_err.auth_status()
            elif args.auth_command == "clear":
                smartgit_err.auth_clear()
            else:
                print("Error: auth command required (set, status, clear)", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
