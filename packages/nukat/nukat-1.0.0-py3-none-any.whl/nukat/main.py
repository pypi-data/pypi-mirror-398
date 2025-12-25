"""Main module for nukat - demonstration of NUKAT client usage."""

import argparse
import sys

from nukat.client import Nukat, NukatError


def main():
    """Main entry point for the application - NUKAT client demonstration."""
    parser = argparse.ArgumentParser(
        description="Client for searching NUKAT catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  nukat "Python programming"                # First 10 results
  nukat "Ireneusz Kania" --all              # All results
  nukat "Artificial intelligence" --limit 5 # First 5 results
  nukat 48685 --id                          # Record details with ID 48685
        """,
    )

    parser.add_argument("query", nargs="+", help="Search query or record ID (with --id)")
    parser.add_argument("--all", action="store_true", help="Fetch all results")
    parser.add_argument(
        "--limit", type=int, default=10, help="Number of results to display (default: 10)"
    )
    parser.add_argument(
        "--id", action="store_true", help="Fetch record details by ID (biblionumber)"
    )

    args = parser.parse_args()
    query = " ".join(args.query)

    try:
        client = Nukat()

        # Record details fetch mode
        if args.id:
            print(f"Fetching details for record {query}...\n")
            details = client.get_record_details(query)

            if not details:
                print("Record not found.")
                return

            print("Record details:\n")
            for key, value in details.items():
                # Format key (replace _ with spaces and capitalize)
                formatted_key = key.replace("_", " ").capitalize()
                print(f"{formatted_key}: {value}")
            return

        # Search mode
        if args.all:
            print(f"Searching: {query} (all results)")
            print("This may take a moment...\n")
            results = client.search_all(query)
        else:
            print(f"Searching: {query} (first {args.limit} results)\n")
            results = client.search(query, limit=args.limit)

        if not results:
            print("No results found.")
            return

        total_msg = f"Showing {len(results)} results"
        print(f"{total_msg}:\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. {result.get('title', 'No title')}")
            if "id" in result:
                print(f"   ID: {result['id']}")
            if "author" in result:
                print(f"   Author: {result['author']}")
            if "year" in result:
                print(f"   Year: {result['year']}")
            if "url" in result:
                print(f"   URL: {result['url']}")
            print()

    except NukatError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
