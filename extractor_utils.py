import json
from pathlib import Path
from typing import List, Dict, Union
from extractor.base import DocstringExtractor
from logger import logger 


def collect_all_docstrings_in_project(
    root_dir: Union[str, Path],
    extractors: List[DocstringExtractor]
) -> List[Dict]:
    """
    Walks through a project directory and extracts docstrings using all supported language extractors.

    Args:
        root_dir (str | Path): Root directory of the codebase.
        extractors (List[DocstringExtractor]): A list of extractors for different languages.

    Returns:
        list of dicts with keys: 'file', 'parent', 'name', 'type', 'docstring'
    """
    root_dir = Path(root_dir)
    all_docs = []

    # Build a mapping from file extension to its extractor
    suffix_to_extractor = {}
    for extractor in extractors:
        for suffix in extractor.suffix:
            suffix_to_extractor[suffix] = extractor

    for file_path in root_dir.rglob("*"):
        extractor = suffix_to_extractor.get(file_path.suffix)
        if extractor:
            try:
                code = file_path.read_text(encoding="utf8")
                docs = extractor.extract_docstrings(code)
                for entry in docs:
                    all_docs.append({
                        "file": str(file_path),
                        "parent": entry.get("parent"),
                        "name": entry.get("name", "<anonymous>"),
                        "type": entry.get("type", "unknown"),
                        "docstring": entry.get("docstring", "")
                    })
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")

    logger.info(f"Collected {len(all_docs)} docstrings from {root_dir}")
    return all_docs


def collect_docstrings_in_project(
    root_dir: Union[str, Path],
    extractor: DocstringExtractor
) -> List[Dict]:
    """
    Walks through a project directory and extracts docstrings using the provided extractor.

    Args:
        root_dir (str | Path): Root directory of the codebase.
        extractor (DocstringExtractor): An instance of a concrete extractor (e.g., PythonDocstringExtractor).
        suffix (str): File extension to match (default: ".py").

    Returns:
        list of dicts with keys: 'file', 'name', 'type', 'docstring'
    """
    root_dir = Path(root_dir)
    all_docs = []

    for file_path in root_dir.rglob(f"*"):
        if file_path.suffix in extractor.suffix:
            try:
                code = file_path.read_text(encoding="utf8")
                docs = extractor.extract_docstrings(code)
                for entry in docs:
                    all_docs.append({
                        "file": str(file_path),
                        "parent": entry.get("parent"),
                        "name": entry.get("name", "<anonymous>"),
                        "type": entry.get("type", "unknown"),
                        "docstring": entry.get("docstring", "")
                    })
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")

    logger.info(f"Collected {len(all_docs)} docstrings from {root_dir}")
    return all_docs


def save_docstrings_to_json(
    docstrings: List[Dict],
    output_path: Union[str, Path]
):
    """
    Saves extracted docstrings to a JSON file.

    Args:
        docstrings (list of dicts): Output from `collect_docstrings_in_project`
        output_path (str | Path): Where to write the JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)  # Create parent directories if needed

    output_path.write_text(json.dumps(docstrings, indent=2), encoding="utf8")
    logger.info(f"Saved {len(docstrings)} docstrings to {output_path}")