import json
from pathlib import Path
from typing import List, Dict, Union
from extractor.base import DocstringExtractor
from logger import logger 
from datamodels import Docstring, Symbol


def collect_all_docstrings_in_project(
    root_dir: Union[str, Path],
    extractors: List[DocstringExtractor]
) -> List[Docstring]:
    """
    Walks through a project directory and extracts docstrings using all supported language extractors.

    Args:
        root_dir (str | Path): Root directory of the codebase.
        extractors (List[DocstringExtractor]): A list of extractors for different languages.

    Returns:
        List[Docstring]: Extracted docstrings with optional file information.
    """
    root_dir = Path(root_dir)
    all_docs: List[Docstring] = []

    suffix_to_extractor = {
        suffix: extractor
        for extractor in extractors
        for suffix in extractor.suffix
    }

    for file_path in root_dir.rglob("*"):
        extractor = suffix_to_extractor.get(file_path.suffix)
        if extractor:
            try:
                code = file_path.read_text(encoding="utf8")
                docstring_objs = extractor.extract_docstrings(code)

                for doc in docstring_objs:
                    doc.file = str(file_path)  # Inject file path here
                    all_docs.append(doc)
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")

    logger.info(f"Collected {len(all_docs)} docstrings from {root_dir}")
    return all_docs


def collect_docstrings_in_project(
    root_dir: Union[str, Path],
    extractor: "DocstringExtractor"
) -> List[Docstring]:
    """
    Walks through a project directory and extracts docstrings using the provided extractor.

    Args:
        root_dir (str | Path): Root directory of the codebase.
        extractor (DocstringExtractor): An instance of a concrete extractor.

    Returns:
        List[Docstring]: Extracted docstrings with optional file information.
    """
    root_dir = Path(root_dir)
    all_docs: List[Docstring] = []

    for file_path in root_dir.rglob("*"):
        if file_path.suffix in extractor.suffix:
            try:
                code = file_path.read_text(encoding="utf8")
                docstring_objs = extractor.extract_docstrings(code)

                for doc in docstring_objs:
                    doc.file = str(file_path)
                    all_docs.append(doc)
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")

    logger.info(f"Collected {len(all_docs)} docstrings from {root_dir}")
    return all_docs


def save_docstrings_to_json(
    docstrings: List[Docstring],
    output_path: Union[str, Path]
):
    """
    Saves extracted docstrings to a JSON file.

    Args:
        docstrings (List[Docstring]): Output from `collect_docstrings_in_project`
        output_path (str | Path): Where to write the JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    json_data = [doc.model_dump() for doc in docstrings]
    output_path.write_text(json.dumps(json_data, indent=2), encoding="utf8")

    logger.info(f"Saved {len(docstrings)} docstrings to {output_path}")


def save_symbols_to_json(
    symbols: List[Symbol],
    output_path: Union[str, Path]
):
    """
    Saves extracted symbols to a JSON file.

    Args:
        symbols (list of dicts): Output from `collect_docstrings_in_project`
        output_path (str | Path): Where to write the JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)  # Create parent directories if needed

    json_data = [symbol.model_dump() for symbol in symbols]
    output_path.write_text(json.dumps(json_data, indent=2), encoding="utf8")
    
    logger.info(f"Saved {len(symbols)} symbols to {output_path}")