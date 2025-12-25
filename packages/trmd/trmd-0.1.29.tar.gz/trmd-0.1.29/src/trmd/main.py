#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import logging
import os
from pathlib import Path
import sys

from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

LANG_LIST = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
}


def chunk_text(text: str, fragment_size: int) -> list[str]:
    """
    Splits the input text into chunks that are at most fragment_size characters.
    The algorithm tries to split on line breaks (preserving blank lines and indentations)
    so that Markdown structures are less likely to be broken.

    Args:
        text: Input text to be chunked.
        fragment_size: Maximum size of each chunk.

    Returns:
        List of chunks.
    """
    lines = text.splitlines(keepends=True)
    chunks = []
    current_chunk = ""

    for line in lines:
        # If adding the next line would exceed the fragment size, push the current chunk.
        if len(current_chunk) + len(line) > fragment_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                # If a single line exceeds the fragment size, break it into smaller parts.
                while len(line) > fragment_size:
                    chunks.append(line[:fragment_size])
                    line = line[fragment_size:]
                current_chunk = line
        else:
            current_chunk += line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


async def translate(
    client: AsyncOpenAI,
    model: str,
    temperature: float,
    additional_prompt: str,
    text: str,
    fragment_size: int,
    source_language: str,
    target_language: str,
) -> str:
    """
    Translate a Markdown document using OpenAI API.

    Args:
        client: AsyncOpenAI client.
        model: OpenAI model name.
        temperature: Temperature for the model.
        additional_prompt: Additional prompt for the model.
        text: Text to translate.
        fragment_size: Size of each chunk.
        source_language: Source language.
        target_language: Target language.

    Returns:
        Translated Markdown document.
    """
    instructions = (
        "You are a professional translator."
        "You need to translate a Markdown document under the following conditions:"
        "- Never change the Markdown structure. Never add or remove links. Never change any URL."
        "- Never change the contents of code blocks even if they appear to have a bug."
        "- Always preserve the original line breaks and indentations. Never add or remove blank lines."
        "- Never touch the permalink such as '{/*examples*/}' at the end of each heading."
        "- Never touch HTML-like tags such as `<Notes>`."
        f"{additional_prompt}"
    )

    chunks = chunk_text(text, fragment_size)

    translated_chunks = []
    for index, chunk in enumerate(chunks):
        log.info(f"Translating chunk {index + 1}/{len(chunks)}...")
        response = await client.responses.create(
            model=model,
            temperature=temperature,
            instructions=instructions,
            input=f"Translate the following text from {source_language} to {target_language}.\n{chunk}",
        )
        translated_chunks.append(response.output_text)

    return "".join(translated_chunks)


async def write_file(file_path: str, content: str) -> None:
    """
    Write the content to the specified file path.

    Args:
        file_path (str): The path to the file.
        content (str): The content to be written.
    """
    log.info(f"Writing file {file_path}...")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)


def is_valid_markdown(text: str) -> bool:
    """
    Check if the text is valid Markdown.

    Args:
        text (str): The text to be checked.

    Returns:
        bool: True if the text is valid Markdown, False otherwise.
    """
    return text.startswith("#") or text.startswith("*") or text.startswith("-")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    DEFAULT_MODEL = "gpt-4"
    parser = argparse.ArgumentParser(description="Trmd")
    parser.add_argument(
        "input_file", type=str, help="Path to Markdown file to be translated"
    )
    parser.add_argument(
        "-o", "--output_file", type=str, help="Path to the translated file"
    )
    parser.add_argument(
        "-k",
        "--key",
        type=str,
        default=os.environ.get("OPENAI_API_KEY", ""),
        help="OpenAI API key",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"OpenAI Model to use, default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Temperature for API requests, default: 0.1",
    )
    parser.add_argument(
        "--fragment-size",
        type=int,
        default=4096,
        help="Fragment size for API requests, default: 4096",
    )
    parser.add_argument(
        "-s",
        "--source-language",
        choices=LANG_LIST.keys(),
        default="en",
        help="Language of source Markdown, default: en",
    )
    parser.add_argument(
        "-t",
        "--target-language",
        choices=LANG_LIST.keys(),
        default="ja",
        help="Language to translate to, default: ja",
    )
    parser.add_argument(
        "-a",
        "--additional-prompt-file",
        type=str,
        default="additional_prompt.txt",
        help="Additional prompt for translation",
    )

    return parser.parse_args()


async def async_main() -> None:
    """
    Async entry point: Initialize the application and run the main loop.
    """
    args = parse_arguments()

    if not os.path.exists(args.input_file):
        log.error("Input file does not exist: %s", args.input_file)
        sys.exit(1)

    if not args.key:
        log.error(
            "OpenAI API key is required, env var OPENAI_API_KEY is also acceptable."
        )
        sys.exit(1)

    if not args.source_language:
        log.error("Source language is required")
        sys.exit(1)

    if not args.target_language:
        log.error("Target language is required")
        sys.exit(1)

    if args.source_language == args.target_language:
        log.error("Source and target languages must be different")
        sys.exit(1)

    if args.additional_prompt_file:
        if not os.path.exists(args.additional_prompt_file):
            log.error(
                "Additional prompt file does not exist: %s", args.additional_prompt_file
            )
            sys.exit(1)

    with open(args.input_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    if not is_valid_markdown(text=md_content):
        log.warning("Input file does not seem to be a valid Markdown file")

    additional_prompt = ""
    if args.additional_prompt_file:
        with open(args.additional_prompt_file, "r", encoding="utf-8") as f:
            additional_prompt = f.read()

    try:
        async with AsyncOpenAI(api_key=args.key) as client:
            log.info(f"Translating file {args.input_file}...")
            translated = await translate(
                client=client,
                model=args.model,
                temperature=args.temperature,
                additional_prompt=additional_prompt,
                text=md_content,
                fragment_size=args.fragment_size,
                source_language=LANG_LIST[args.source_language],
                target_language=LANG_LIST[args.target_language],
            )
    except Exception as e:
        log.error("Failed to initialize OpenAI client: %s", e)
        sys.exit(1)

    if translated:
        if args.output_file:
            output_file_path = args.output_file
        else:
            p = Path(args.input_file)
            output_file_path = (
                f"{str(p.parent)}/{str(p.stem)}_{args.target_language}{str(p.suffix)}"
            )

        await write_file(output_file_path, translated)
        log.info(f"Translation saved to {output_file_path}")

    else:
        log.error("Translation failed")


def main():
    """
    Main entry point: Initialize the application and run the main loop.
    """
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
