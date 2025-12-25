import argparse
from . import kate_kelly, nathan_lies

def main():
    parser = argparse.ArgumentParser(prog="aimpf", description="AIMPF CLI for researcher tools.")
    subparsers = parser.add_subparsers(title="Users", dest="user")

    # Add subcommands for each user
    kate_kelly.add_subcommands(subparsers)
    nathan_lies.add_subcommands(subparsers)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

