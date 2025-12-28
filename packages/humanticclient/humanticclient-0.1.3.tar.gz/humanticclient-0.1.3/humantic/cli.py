#!/usr/bin/env python3
"""Humantic AI CLI - Analyze LinkedIn profiles for sales insights."""

import argparse
import json
import sys
from humantic import HumanticClient


def main():
    parser = argparse.ArgumentParser(
        description="Analyze LinkedIn profiles using Humantic AI API"
    )
    parser.add_argument(
        "profile",
        help="LinkedIn profile URL (e.g., https://www.linkedin.com/in/username/)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Save output to JSON file (default: prints to stdout)",
        type=str
    )
    parser.add_argument(
        "-p", "--persona",
        default="sales",
        choices=["sales", "hiring"],
        help="Persona for analysis (default: sales)"
    )
    parser.add_argument(
        "--api-key",
        help="Humantic AI API key (default: from HUMANTIC_API_KEY env var or .env file)",
        type=str
    )

    args = parser.parse_args()

    with HumanticClient(api_key=args.api_key) as client:
        result = client.get_or_create_profile(args.profile, persona=args.persona)

        if args.output:
            # Save to file
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Saved to {args.output}", file=sys.stderr)
        else:
            # Print to stdout
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
