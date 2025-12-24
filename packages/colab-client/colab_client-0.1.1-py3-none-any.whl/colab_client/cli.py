from __future__ import annotations

import argparse
import logging
import sys

from .client import ColabClient
from .config import Config
from .models import RuntimeVariant

EXAMPLES = {
    "1": ("Hello World", "print('Hello World!')"),
    "2": (
        "System Info",
        """import platform, sys
print('Python:', platform.python_version())
print('OS:', platform.system(), platform.release())
print('Machine:', platform.machine())
print('CPU cores:', __import__('os').cpu_count())""",
    ),
    "3": ("Check GPU", "!nvidia-smi"),
    "4": (
        "Memory Info",
        """import psutil
mem = psutil.virtual_memory()
print(f'Total: {mem.total / 1024**3:.1f} GB')
print(f'Available: {mem.available / 1024**3:.1f} GB')
print(f'Used: {mem.percent}%')""",
    ),
    "5": ("Disk Space", "!df -h"),
    "6": ("Installed Packages", "!pip list | head -20"),
    "7": ("Custom Code", None),
}


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def interactive_mode(client: ColabClient) -> None:
    print("\n[1] Logging in...")
    client.login()

    print("\n[2] Requesting server...")
    client.get_or_create_server(variant=RuntimeVariant.DEFAULT)

    print("\n[3] Getting or creating session...")
    client.get_or_create_session()

    client.start_keep_alive()

    while True:
        print("\n=== Examples ===")
        for key, (name, _) in EXAMPLES.items():
            print(f"  {key}. {name}")
        print("  q. Quit")

        choice = input("\nSelect example (1-7, q): ").strip().lower()

        if choice == "q":
            break

        if choice not in EXAMPLES:
            print("Invalid choice!")
            continue

        name, code = EXAMPLES[choice]

        if code is None:
            print("Enter code (end with empty line):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            code = "\n".join(lines)

        print(f"\n[Executing: {name}]")
        result = client.execute(code)

        print("\n=== Output ===")
        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print("STDERR:", result.stderr)

        if result.result:
            print("RESULT:", result.result)

        if result.error:
            print(f"ERROR: {result.error}")

    print("\nStopping keep-alive...")
    client.stop_keep_alive()
    print("Done! Server is still running.")


def execute_code(client: ColabClient, code: str) -> int:
    client.login()
    client.get_or_create_server()
    client.get_or_create_session()

    result = client.execute(code)

    if result.stdout:
        print(result.stdout, end="")

    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.error:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="colab-client",
        description="Python client for Google Colab",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "-c",
        "--code",
        type=str,
        help="Execute code and exit",
    )
    parser.add_argument(
        "--variant",
        type=str,
        choices=[v.value for v in RuntimeVariant],
        default="DEFAULT",
        help="Runtime variant (default: DEFAULT)",
    )
    parser.add_argument(
        "--unassign",
        action="store_true",
        help="Unassign current server and exit",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List current assignments and exit",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    config = Config()

    with ColabClient(config) as client:
        if args.list:
            client.login()
            assignments = client.list_assignments()
            if not assignments:
                print("No active assignments")
            else:
                for a in assignments:
                    print(f"Endpoint: {a['endpoint']}")
                    print(f"  Accelerator: {a.get('accelerator', 'N/A')}")
                    print(f"  Variant: {a.get('variant', 'N/A')}")
            return 0

        if args.unassign:
            client.login()
            client.get_or_create_server()
            if client.unassign_server():
                print("Server unassigned successfully")
                return 0
            print("Failed to unassign server")
            return 1

        if args.code:
            return execute_code(client, args.code)

        print("=== Colab Python Client ===")
        interactive_mode(client)

    return 0


if __name__ == "__main__":
    sys.exit(main())
