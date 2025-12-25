import itertools
import json
import os
import pathlib
from typing import List, Tuple

from bibtexparser import Library, parse_file
from bibtexparser.middlewares import LatexDecodingMiddleware

from .. import logger

class FileManager:
    """
    Handles reading of JSON configration and BibTeX files.
    """

    @staticmethod
    def read_config(filename: str) -> Tuple[List[str], int, str, str, str, str]:
        """
        Load the configuration from a JSON file.

        :param filename: Path to the JSON configuration file.
        :return: A tuple containing:
                 - reviewers (List[str]),
                 - reviewers_per (int),
                 - cache_directory (str),
                 - division_directory (str),
                 - review_directory (str),
                 - report_directory (str)
        :raises ValueError: If the configuration file is invalid or improperly formatted.
        """

        if not os.path.exists(filename):
            logger.error(f"Config JSON file not found: {filename}")
            raise ValueError("Config file is not a valid file path.")

        if pathlib.Path(filename).suffix.lower() != '.json':
            raise ValueError("Config file is not a JSON file.")

        logger.info("Loading configuration JSON file...")

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON file {filename}: {e}")
            raise ValueError("Failed to parse JSON file.")

        # Extract reviewers (optional)
        reviewers_config = config.get('reviewers')
        reviewers = []
        if reviewers_config:
            # Handle both int and list of strings for reviewers
            if isinstance(reviewers_config, int):
                if reviewers_config <= 0:
                    raise ValueError("'reviewers' must be a positive integer when specified as int.")
                reviewers = [f"reviewer_{i+1:02d}" for i in range(reviewers_config)]
            elif isinstance(reviewers_config, list):
                if not all(isinstance(name, str) for name in reviewers_config):
                    raise ValueError("'reviewers' list must contain only strings.")
                if len(reviewers_config) == 0:
                    raise ValueError("'reviewers' list cannot be empty.")
                reviewers = reviewers_config
            else:
                raise ValueError("'reviewers' must be either an integer or a list of strings.")

        # Extract reviewers_per (optional)
        reviewers_per = config.get('reviewers_per')
        if reviewers_per is not None:
            if not isinstance(reviewers_per, int) or reviewers_per <= 0:
                raise ValueError("'reviewers_per' must be a positive integer.")
            if reviewers and reviewers_per > len(reviewers):
                raise ValueError("'reviewers_per' cannot be greater than the number of reviewers.")

        # Extract directories (optional)
        cache_directory = config.get('cache_directory', '')
        division_directory = config.get('division_directory', '')
        review_directory = config.get('review_directory', '')
        report_directory = config.get('report_directory', '')

        logger.info("Configuration loaded successfully")

        return reviewers, reviewers_per, cache_directory, division_directory, review_directory, report_directory


    @staticmethod
    def read_bibtex_directory(bibtex_directory: str) -> Library:
        """
        Load and merge articles from possibly multiple BibTeX files in the specified directory.

        :param bibtex_directory: Path to the directory containing BibTeX files.
        :return: bibtexparser.library.Library object.
        """
        logger.debug(f"Reading bibtex directory {bibtex_directory}")
        library = Library()
        bib_patterns = ['*.bib', '*.bibtex']
        bib_file_paths = itertools.chain.from_iterable(
            pathlib.Path(bibtex_directory).glob(pattern) for pattern in bib_patterns
        )
        for bib_file_path in bib_file_paths:
            logger.debug(f"Adding bibfile with path {bib_file_path}")
            library.add(parse_file(path=bib_file_path,
                                   parse_stack=None,
                                   append_middleware=[LatexDecodingMiddleware()]).entries)
        if not library.entries:
            raise RuntimeError("No articles found.")
        logger.debug(f"Finished reading bibtex directory {bibtex_directory}")
        return library