"""Command-line interface for HashIndex."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from hashindex.core import index_pdf, query_index


def main():
    """Main CLI entry point."""
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in environment variables or .env file.")
        print("Please set OPENROUTER_API_KEY in your environment or create a .env file:")
        print("  OPENROUTER_API_KEY=your_api_key_here")
        sys.exit(1)

    print("HashIndex - Document Indexing and Query System")
    print("=" * 50)

    while True:
        print("\nWhat would you like to do?")
        print("1. Index a PDF document")
        print("2. Query an existing index")
        print("3. Exit")

        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == "1":
            pdf_path = input("Enter path to PDF file: ").strip()
            if not pdf_path:
                print("Error: PDF path cannot be empty.")
                continue

            if not Path(pdf_path).exists():
                print(f"Error: File not found: {pdf_path}")
                continue

            try:
                print(f"\nIndexing {pdf_path}...")
                index = index_pdf(pdf_path)

                default_index_path = Path(pdf_path).with_suffix(".index.json")
                save_path = input(
                    f"\nEnter path to save index (default: {default_index_path}): "
                ).strip()
                if not save_path:
                    save_path = str(default_index_path)

                index.save(save_path)
                print(f"\nIndex saved to: {save_path}")
            except Exception as e:
                print(f"\nError during indexing: {e}")

        elif choice == "2":
            index_path = input("Enter path to index file (.json): ").strip()
            if not index_path:
                print("Error: Index path cannot be empty.")
                continue

            if not Path(index_path).exists():
                print(f"Error: File not found: {index_path}")
                continue

            question = input("\nEnter your question: ").strip()
            if not question:
                print("Error: Question cannot be empty.")
                continue

            try:
                print(f"\nQuerying index...")
                answer = query_index(index_path, question)
                print(f"\nAnswer:\n{answer}")
            except Exception as e:
                print(f"\nError during query: {e}")

        elif choice == "3":
            print("\nGoodbye!")
            break

        else:
            print("\nInvalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
