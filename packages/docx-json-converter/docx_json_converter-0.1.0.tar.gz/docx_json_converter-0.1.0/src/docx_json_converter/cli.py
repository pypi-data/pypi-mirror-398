import os
import argparse
from .prompts import PROMPT_TEMPLATE

def generate_prompt_file():
    """
    CLI entry point to generate 'llm.txt' in the current directory.
    """
    parser = argparse.ArgumentParser(description="Generate an LLM prompt file for docx-json-converter.")
    parser.add_argument(
        "--filename", 
        default="llm.txt", 
        help="Name of the file to generate (default: llm.txt)"
    )
    
    args = parser.parse_args()
    
    output_path = os.path.join(os.getcwd(), args.filename)
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(PROMPT_TEMPLATE)
        print(f"[OK] Generated prompt file at: {output_path}")
        print("You can now paste this file's content into your LLM context window.")
    except Exception as e:
        print(f"[ERROR] Error generating file: {e}")

if __name__ == "__main__":
    generate_prompt_file()

