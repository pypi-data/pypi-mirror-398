import argparse
import sys
from .api import fetch_by_pincode, fetch_by_postoffice_name
from .exceptions import PincodePackageError


def main():
    parser = argparse.ArgumentParser(description="Indian Pincode Lookup Tool")
    parser.add_argument(
        "query",
        help="Pincode (e.g. 682001) or Post Office Name (e.g. Ernakulam)"
    )
    args = parser.parse_args()

    try:
        if args.query.isdigit():
            data = fetch_by_pincode(args.query)
        else:
            data = fetch_by_postoffice_name(args.query)

        if not data:
            print("No data found.")
            return

        for r in data:
            print(
                f"{r.get('Name', 'N/A')} | "
                f"{r.get('Region', 'N/A')} | "
                f"{r.get('District', 'N/A')} | "
                f"{r.get('State', 'N/A')} | "
                f"{r.get('Division', 'N/A')} | "
                f"{r.get('Pincode', 'N/A')}"
            )

    except PincodePackageError as e:
        print(f"Error: {e}")
        sys.exit(1)
