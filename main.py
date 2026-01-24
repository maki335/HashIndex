

from pathlib import Path
from markitdown import MarkItDown
from typing import Dict
import json
import os
import sys

from dotenv import load_dotenv

from model import Model, Message
from tools import GenerateHashKey, ListKeys, GetSummary, GetContent

MAX_TOKEN_PER_PAGE = 10000
CHARS_PER_TOKEN = 4
MAX_CHARS_PER_PAGE = MAX_TOKEN_PER_PAGE * CHARS_PER_TOKEN
MAX_CONTEXT_TOKENS = 60000
MAX_CONTEXT_CHARS = MAX_CONTEXT_TOKENS * CHARS_PER_TOKEN

class HashIndex:
    def __init__(self):
        self.PageTable: Dict[str, 'HashObject'] = {}

    def to_json(self) -> str:
        """
        Convert the index to a JSON string.

        Returns:
            JSON string representation of the index.
        """
        data = {
            "pages": [
                {
                    "hash_key": key,
                    "content": obj.content,
                    "page_number": obj.page_number,
                    "summary": obj.summary,
                }
                for key, obj in self.PageTable.items()
            ]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'HashIndex':
        """
        Create an index from a JSON string.

        Args:
            json_str: JSON string representation of the index.

        Returns:
            HashIndex object.
        """
        data = json.loads(json_str)

        index = cls()
        for page_data in data["pages"]:
            index.PageTable[page_data["hash_key"]] = HashObject(
                content=page_data["content"],
                page_number=page_data["page_number"],
                summary=page_data["summary"],
            )
        return index

    def save(self, file_path: str) -> None:
        """Save the index to a file."""
        data = {
            "pages": [
                {
                    "hash_key": key,
                    "content": obj.content,
                    "page_number": obj.page_number,
                    "summary": obj.summary,
                }
                for key, obj in self.PageTable.items()
            ]
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, file_path: str) -> 'HashIndex':
        """Load an index from a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        index = cls()
        for page_data in data["pages"]:
            index.PageTable[page_data["hash_key"]] = HashObject(
                content=page_data["content"],
                page_number=page_data["page_number"],
                summary=page_data["summary"],
            )
        return index

class HashObject:
    def __init__(self, content: str, page_number: int, summary: str):
        self.content = content
        self.page_number = page_number
        self.summary = summary


def convert_pdf_to_md(file_path: str) -> str:
    """Convert a PDF file to Markdown and return the path to the generated MD file."""
    # Convert to Path object for easier manipulation
    pdf_path = Path(file_path)

    # Validate input file exists and is a PDF
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    if pdf_path.suffix.lower() != '.pdf':
        raise ValueError(f"Input file must be a PDF: {file_path}")

    # Generate output markdown path (same location, different extension)
    md_path = pdf_path.with_suffix('.md')

    # Convert PDF to Markdown using markitdown
    md = MarkItDown()
    result = md.convert(str(pdf_path))

    # Write the markdown content to the output file
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(result.text_content)

    return str(md_path) 


def _split_into_pages(content: str) -> list[str]:
    """
    Split content into pages of max MAX_CHARS_PER_PAGE characters.
    Be lenient with word boundaries - include the complete last word.
    """
    pages = []
    start = 0

    while start < len(content):
        # Calculate end position (max chars per page)
        end = start + MAX_CHARS_PER_PAGE

        # If we're not at the end, find a good breaking point
        if end < len(content):
            # Look for a sentence end (period, exclamation, question mark followed by space or newline)
            search_area = content[start:end]
            for i in range(len(search_area) - 1, max(0, len(search_area) - 500), -1):
                if search_area[i] in '.!?' and i + 1 < len(search_area) and search_area[i + 1] in ' \n':
                    end = start + i + 1
                    break
            else:
                # No sentence end found, look for word boundary
                for i in range(len(search_area) - 1, max(0, len(search_area) - 200), -1):
                    if search_area[i].isspace():
                        end = start + i + 1
                        break
                else:
                    # No word boundary found, just use the max chars
                    pass

        # Extract the page content
        page_content = content[start:end].strip()
        if page_content:
            pages.append(page_content)

        start = end

    return pages


def _build_system_prompt(
    previous_hash_key: str | None,
    last_summaries: list[str],
) -> str:
    """Build the system prompt with context from previous pages."""
    prompt = "You are analyzing document pages to create a searchable hash-based index.\n\n"
    prompt += "Your task:\n"
    prompt += "1. Generate a DESCRIPTIVE hash key that will be used to RETRIEVE this section later.\n"
    prompt += "   - The key must clearly describe WHAT content is in this section\n"
    prompt += "   - Users will query the index using natural language, so keys should be intuitive and searchable\n"
    prompt += "   - Format: lowercase_with_underscores, 3-8 specific words (e.g., 'neural_network_backpropagation')\n"
    prompt += "2. Generate a concise summary (2-4 sentences) of the content\n\n"

    if previous_hash_key or last_summaries:
        prompt += "Context from previous pages:\n"

    if previous_hash_key:
        prompt += f"- Previous hash key: {previous_hash_key}\n"

    if last_summaries:
        prompt += "- Recent page summaries:\n"
        for i, summary in enumerate(last_summaries, 1):
            prompt += f"  {i}. {summary}\n"

    prompt += "\nUse this context to ensure consistency and avoid duplicate hash keys.\n"
    prompt += "Think: 'If someone searches for this topic later, what key would help them find this section?'\n"

    return prompt


def index_md(file_path: str) -> HashIndex:
    """
    Index a markdown file using hash-based indexing.

    Args:
        file_path: Path to the PDF file to index.

    Returns:
        HashIndex object with indexed pages.
    """
    # Convert PDF to markdown
    md_path = convert_pdf_to_md(file_path)

    # Read the markdown content
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Split into pages
    pages = _split_into_pages(md_content)
    print(f"Split into {len(pages)} pages")

    # Initialize index and model
    index = HashIndex()
    model = Model()
    existing_keys: set[str] = set()

    # Track context for LLM
    previous_hash_key: str | None = None
    last_summaries: list[str] = []

    # Process each page
    for page_num, page_content in enumerate(pages, start=1):
        print(f"Processing page {page_num}/{len(pages)}...")

        # Build messages
        system_prompt = _build_system_prompt(previous_hash_key, last_summaries)
        messages: list[Message] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Page {page_num} content:\n\n{page_content}\n\n"
                f"Please generate a unique hash key and summary for this page.",
            },
        ]

        # Create tool with current existing keys
        hash_key_tool = GenerateHashKey(existing_keys)

        # Call LLM with retry logic - each page is a fresh conversation
        response = model.complete_with_retry(
            messages=messages,
            tools=[hash_key_tool.to_dict()],
            max_retries=3,
        )

        # Process tool call
        hash_key = None
        summary = None

        if response["tool_calls"]:
            for tool_call in response["tool_calls"]:
                function_name = tool_call["function"]["name"]
                arguments_str = tool_call["function"]["arguments"]

                # Handle empty arguments for tools with no parameters
                if not arguments_str or not arguments_str.strip():
                    arguments_str = "{}"

                try:
                    args = json.loads(arguments_str)
                except json.JSONDecodeError as e:
                    print(f"  Error parsing arguments: {e}")
                    continue

                if function_name == "generate_hash_key_and_summary":
                    hash_key = args.get("hash_key")
                    summary = args.get("summary")
                    # Register the key and summary
                    try:
                        hash_key_tool(**args)
                    except ValueError as e:
                        print(f"  Validation error: {e}")
                    break

        # Fallback if no tool calls
        if not hash_key:
            hash_key = f"page_{page_num}"
            while hash_key in existing_keys:
                hash_key = f"page_{page_num}_{len(existing_keys)}"
            existing_keys.add(hash_key)

        if not summary:
            summary = f"Page {page_num} content (auto-generated summary)"

        # Create hash object and add to index
        hash_obj = HashObject(
            content=page_content,
            page_number=page_num,
            summary=summary,
        )
        index.PageTable[hash_key] = hash_obj

        # Update context for next page
        previous_hash_key = hash_key
        last_summaries.append(summary)
        if len(last_summaries) > 3:
            last_summaries.pop(0)

        print(f"  Hash key: {hash_key}")
        print(f"  Summary: {summary[:80]}...")

    print(f"Indexing complete! Total pages indexed: {len(index.PageTable)}")
    return index


def _count_tokens(messages: list[Message]) -> int:
    """
    Estimate the token count for a list of messages.
    Uses 4 characters = 1 token approximation.
    """
    total_chars = 0
    for msg in messages:
        total_chars += len(msg.get("content", ""))
        # Add some overhead for role and metadata
        total_chars += 20
    return total_chars // CHARS_PER_TOKEN


def _compress_conversation(
    messages: list[Message],
    max_tokens: int = MAX_CONTEXT_TOKENS,
) -> list[Message]:
    """
    Compress conversation by summarizing older messages if needed.

    Keeps recent messages as-is and creates a summary of older messages.

    Args:
        messages: List of messages in the conversation.
        max_tokens: Maximum tokens to keep in the conversation.

    Returns:
        Compressed list of messages.
    """
    current_tokens = _count_tokens(messages)

    if current_tokens <= max_tokens:
        return messages

    # Keep system message and recent messages
    system_messages = [m for m in messages if m.get("role") == "system"]
    recent_messages = []

    # Build from most recent, keeping system messages
    tokens_count = 0
    for msg in reversed(messages):
        if msg.get("role") == "system":
            continue

        msg_tokens = (len(msg.get("content", "")) + 20) // CHARS_PER_TOKEN
        if tokens_count + msg_tokens > max_tokens * 0.8:  # Leave room for system
            break

        recent_messages.insert(0, msg)
        tokens_count += msg_tokens

    # Create a summary of what was removed
    removed_count = len(messages) - len(system_messages) - len(recent_messages)
    if removed_count > 0:
        summary_msg: Message = {
            "role": "system",
            "content": f"[Note: {removed_count} earlier messages have been compressed to manage context length. "
            f"The conversation has covered previous questions and answers about the document. "
            f"Continue based on the recent context provided.]",
        }
        system_messages.append(summary_msg)

    return system_messages + recent_messages


def query_index(index_or_file: str | HashIndex, question: str, max_iterations: int = 10) -> str:
    """
    Query a hash index with a question.

    The agent can access summaries first, then full content as needed.
    Conversation is compressed if it exceeds 60000 tokens.

    Args:
        index_or_file: Either a HashIndex object or path to an index JSON file.
        question: The question to answer.
        max_iterations: Maximum number of tool-using iterations.

    Returns:
        The final answer to the question.
    """
    # Load index if file path provided
    if isinstance(index_or_file, str):
        index = HashIndex.load(index_or_file)
    else:
        index = index_or_file

    # Initialize model and tools
    model = Model()
    tools = [ListKeys(index), GetSummary(index), GetContent(index)]

    # Build initial messages
    messages: list[Message] = [
        {
            "role": "system",
            "content": "You are a helpful assistant that answers questions about a document using a hash index. "
            "You have access to tools that let you:\n"
            "1. list_keys - See all available pages with their summaries\n"
            "2. get_summary - Get the summary for a specific page\n"
            "3. get_content - Get the full content for a specific page\n\n"
            "Start by listing keys to understand what's available, then get summaries of relevant pages, "
            "and finally get full content when needed to answer the question in detail.",
        },
        {
            "role": "user",
            "content": f"Question: {question}\n\nPlease use the available tools to find the information and answer the question.",
        },
    ]

    # Conversation loop with tool use
    for iteration in range(max_iterations):
        # Check and compress if needed
        current_tokens = _count_tokens(messages)
        if current_tokens > MAX_CONTEXT_TOKENS:
            print(f"Context too large ({current_tokens} tokens), compressing...")
            messages = _compress_conversation(messages)

        print(f"\n=== Iteration {iteration + 1} ===")
        print(f"Number of messages: {len(messages)}")
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content_preview = msg.get("content", "")[:100]
            print(f"  Message {i}: role={role}, content_preview={content_preview}...")
            if "tool_call_id" in msg:
                print(f"    (tool_call_id: {msg['tool_call_id']})")

        # Get completion with tools
        try:
            response = model.complete_with_retry(
                messages=messages,
                tools=[tool.to_dict() for tool in tools],
                max_retries=1,  # Reduce retries for debugging
            )
        except Exception as e:
            print(f"Error getting completion: {e}")
            print("Messages that caused error:")
            for i, msg in enumerate(messages):
                print(f"  {i}: {json.dumps(msg, indent=2)}")
            raise

        # Add assistant response with both content and tool_calls
        assistant_msg: Message = {"role": "assistant"}
        if response["content"]:
            assistant_msg["content"] = response["content"]
        if response["tool_calls"]:
            assistant_msg["tool_calls"] = response["tool_calls"]
        messages.append(assistant_msg)

        # If no tool calls, LLM is done - return the answer
        if not response["tool_calls"] or not response["tool_calls"]:
            break

        # Process tool calls
        for tool_call in response["tool_calls"]:
            tool_call_id = tool_call["id"]
            function_name = tool_call["function"]["name"]
            arguments_str = tool_call["function"]["arguments"]

            # Handle empty arguments for tools with no parameters
            if not arguments_str or not arguments_str.strip():
                arguments_str = "{}"
                print(f"Note: Tool {function_name} called with no arguments, using empty dict")

            try:
                args = json.loads(arguments_str)
            except json.JSONDecodeError as e:
                print(f"Error parsing arguments for {function_name}: {e}")
                print(f"Arguments string: {arguments_str[:200]}")
                # Create a tool response with the error
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps({"error": f"Invalid JSON in arguments: {str(e)}"}, ensure_ascii=False),
                })
                continue

            # Execute the appropriate tool
            for tool in tools:
                if tool.name == function_name:
                    try:
                        result = tool(**args)
                        # Add tool response message with tool_call_id
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": json.dumps(result, ensure_ascii=False),
                        })
                        print(f"Tool call: {function_name}")
                        if function_name == "get_content":
                            print(f"  Retrieved content for: {args.get('hash_key')}")
                        elif function_name == "get_summary":
                            print(f"  Retrieved summary for: {args.get('hash_key')}")
                    except Exception as e:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": json.dumps({"error": str(e)}, ensure_ascii=False),
                        })
                    break

    # Return the final assistant message
    final_msg = messages[-1]
    if final_msg.get("role") == "assistant":
        return final_msg.get("content", "No response generated.")

    return "Unable to generate a response."

def main():
    """Main CLI entry point."""
    # Load environment variables from .env file
    load_dotenv()

    # Check for API key
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
            # Index a PDF
            pdf_path = input("Enter path to PDF file: ").strip()
            if not pdf_path:
                print("Error: PDF path cannot be empty.")
                continue

            if not Path(pdf_path).exists():
                print(f"Error: File not found: {pdf_path}")
                continue

            try:
                print(f"\nIndexing {pdf_path}...")
                index = index_md(pdf_path)

                # Save the index
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
            # Query an index
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
            # Exit
            print("\nGoodbye!")
            break

        else:
            print("\nInvalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
