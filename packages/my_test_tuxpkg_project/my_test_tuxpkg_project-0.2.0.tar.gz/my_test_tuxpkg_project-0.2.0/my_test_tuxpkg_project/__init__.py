"""
my-test-tuxpkg-project is ...
"""

__version__ = "0.2.0"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="my-test-tuxpkg-project")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.parse_args()

    print(f"my-test-tuxpkg-project version {__version__}")
