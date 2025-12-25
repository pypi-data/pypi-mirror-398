import argparse

from iker.setup import setup, version_string

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="setup script integrating dynamic version printer")
    parser.add_argument("--print-version-string", action="store_true", help="print version string and exit")

    args, _ = parser.parse_known_args()
    if args.print_version_string:
        print(version_string())
    else:
        setup()
