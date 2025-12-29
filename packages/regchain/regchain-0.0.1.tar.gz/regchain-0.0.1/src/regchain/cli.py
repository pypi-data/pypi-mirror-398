import argparse
from regchain import __version__


def main():
    parser = argparse.ArgumentParser(description="RegChain CLI")
    parser.add_argument("--version", action="version", version=f"RegChain {__version__}")
    args = parser.parse_args()

    if args.version:
        print(f"RegChain version: {__version__}")
        return

    print("Welcome to RegChain CLI")
