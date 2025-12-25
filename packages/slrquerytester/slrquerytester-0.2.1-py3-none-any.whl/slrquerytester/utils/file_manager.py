import itertools
import json
import os
import pathlib
from typing import List, Tuple, Dict

from langcodes import Language
from bibtexparser import Library, parse_file
from bibtexparser.middlewares import LatexDecodingMiddleware

from .. import logger

class FileManager:
    """
    Handles reading of Excel and BibTeX files.
    """

    @staticmethod
    def read_config(filename: str) -> Tuple[Dict, str, str, str, int, str, str, str, Language]:
        """
        Load the configuration from a JSON file.

        If the 'repository' field is specified in the JSON, other paths are set
        to default subdirectories or files within the repository path. Otherwise,
        the user can specify each path manually or rely on default values.

        :param filename: Path to the JSON configuration file.
        :return: A tuple containing:
                 - api_keys (dict)
                 - cache_directory (str)
                 - golden_solution_directory (str)
                 - report_directory (str)
                 - threshold_days (int)
                 - queries_file (str)
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

        # Extract API keys (optional)
        api_keys = config.get('api_keys', {})

        # Extract language (optional)
        language = Language.get(config.get('language', 'en'))

        # Extract threshold_days (optional with default)
        threshold_days = config.get('threshold_days', 30)

        # Check if 'repository' is specified
        repository = config.get('repository', None)

        if repository:
            # Ensure repository is a valid path
            repository_path = pathlib.Path(repository)
            if not repository_path.is_dir():
                logger.info(f"Repository directory does not exist. Attempting to create: {repository}")
                try:
                    repository_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Repository directory created: {repository}")
                except Exception as e:
                    logger.error(f"Failed to create repository directory {repository}: {e}")
                    raise ValueError(f"Cannot create repository directory: {repository}")

            # Ensure no individual paths are specified to avoid conflicts
            individual_paths = ['cache_directory', 'golden_solution_directory', 'report_directory', 'queries_file']
            specified_individual = [path for path in individual_paths if path in config]
            if specified_individual:
                logger.error(f"Cannot specify {specified_individual} when 'repository' is provided.")
                raise ValueError(
                    f"Specify either 'repository' or individual paths ({', '.join(individual_paths)}), not both.")

            # Set default subdirectories/files within the repository
            cache_directory = str(repository_path / 'slrquerytester.cache')
            golden_solution_directory = str(repository_path / 'golden_solution')
            report_directory = str(repository_path / 'reports')
            queries_file = str(repository_path / 'queries.json')
            manual_articles_directory = str(repository_path / 'manual_articles')

            logger.info("Configuration paths set based on 'repository' field.")
        else:
            # Set paths based on individual specifications or default values
            cache_directory = config.get('cache_directory', 'slrquerytester.cache')
            golden_solution_directory = config.get('golden_solution_directory', 'golden_solution')
            report_directory = config.get('report_directory', 'reports')
            queries_file = config.get('queries_file', 'queries.json')
            manual_articles_directory = config.get('manual_articles_directory', 'manual_articles')

            logger.info("Configuration paths set based on individual fields or default values.")

        return api_keys, cache_directory, golden_solution_directory, report_directory, threshold_days, queries_file, repository, manual_articles_directory, language

    @staticmethod
    def read_queries_json(filename: str) -> List[dict]:
        """
        Read queries and their decomposition levels from the specified JSON file.

        :param filename: Path to the JSON file containing queries and decomposition levels.
        :return: List of dictionaries with 'query' and 'decomposition_level'.
        """
        if not os.path.exists(filename):
            logger.error(f"Queries file not found: {filename}")
            raise ValueError("Queries file is not a valid file path.")
        elif not pathlib.Path(filename).suffix in ['.json']:
            raise ValueError("File is not a JSON file.")
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                queries = json.load(f)
                for query in queries:
                    if 'query' not in query:
                        logger.error(f"Invalid query entry in {filename}: {query}")
                        raise ValueError("File is not a JSON file.")
                return queries
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON file {filename}: {e}")
            raise ValueError("Failed to parse JSON file.")

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