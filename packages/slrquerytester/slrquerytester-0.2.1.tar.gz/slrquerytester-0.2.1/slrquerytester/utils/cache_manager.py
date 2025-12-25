"""
.. include:: ../../docs/caching.md
"""

import datetime
import json
import os
import hashlib
import re
import shutil
import threading
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from typing import List, Dict, Any, Union
from datetime import datetime, timedelta, timezone

import requests
from bibtexparser.middlewares import AddEnclosingMiddleware, MonthAbbreviationMiddleware, SortFieldsAlphabeticallyMiddleware
from bibtexparser import Library, parse_file, write_file
from bibtexparser.model import Entry, Field
from fuzzywuzzy import fuzz
from lark import Tree

from .file_manager import FileManager
from ..translators.base_transformer import BaseTransformer
from ..translators.query_translator import translate_query
from .. import logger


class CacheManager:
    """
    Manages caching of API responses to avoid redundant API calls and maintain metadata about cached results.
    """

    METADATA_FILENAME = 'metadata.json'
    UNION_DIRECTORY_NAME = 'slrquerytester-union'
    ARTICLE_LIMIT = 500
    METADATA_NUM_ARTICLES_RETRIEVED = 'num_articles_retrieved'
    METADATA_EXPECTED_NUM_ARTICLES = 'expected_num_articles'
    METADATA_LAST_API_CALL_TIME = 'last_api_call_time'
    METADATA_TRANSLATED_QUERY_STRING = 'translated_query_string'
    METADATA_GENERAL_QUERY_STRING = 'general_query_string'
    METADATA_MANUALLY_OBTAINED = 'manually_obtained'
    DEFAULT_METADATA = {METADATA_EXPECTED_NUM_ARTICLES: 0,
                        METADATA_NUM_ARTICLES_RETRIEVED: 0,
                        METADATA_LAST_API_CALL_TIME: None,
                        METADATA_TRANSLATED_QUERY_STRING: '',
                        METADATA_GENERAL_QUERY_STRING: ''}
    _JABREF_URL: str = (
        "https://raw.githubusercontent.com/"
        "JabRef/abbrv.jabref.org/main/journals/journal_abbreviations_general.csv"
    )
    _MIN_FUZZ_COMPARISON_SCORE: int = 75

    def __init__(self,
                 cache_dir: str,
                 repository_path: str | None,
                 stale_after_days: int,
                 autogit: bool = False):
        """
        Initialize the CacheManager.

        :param cache_dir: Directory for caching articles and metadata.
        :param repository_path: Path to the repository for Git integration.
        :param stale_after_days: Number of days after which cache is considered stale.
        :param autogit: Whether to enable automatic Git commit management.
        """
        self.cache_dir = cache_dir
        self.repository_path = repository_path
        self._STALE_AFTER_DAYS = stale_after_days
        self.autogit = autogit
        self._ABBREVIATION_MAP = self._fetch_abbreviations()
        os.makedirs(cache_dir, exist_ok=True)
        if repository_path and autogit:
            self.repository_path = repository_path
            self.commit_message_file = os.path.join(self.repository_path, 'git_commit_message.txt')
            self.commit_message_lock = threading.Lock()

    def _fetch_abbreviations(self) -> dict:
        """
        Fetch journal abbreviations from JabRef's repository or the cache.

        :return: A mapping of abbreviations to full journal names.
        """
        json_files = [
            f for f in os.listdir(self.cache_dir) if f.endswith(".json")
        ]

        if json_files:
            # Since we assume there's only one cache file, use the first one found.
            cache_file = os.path.join(self.cache_dir, json_files[0])
            file_mod_time = os.path.getmtime(cache_file)
            if (
                    datetime.now(timezone.utc)
                    - datetime.fromtimestamp(file_mod_time, tz=timezone.utc)
            ) < timedelta(days=self._STALE_AFTER_DAYS):
                with open(cache_file, "r", encoding="utf-8") as f:
                    logger.info("Fetching JabRef from cache.")
                    return json.load(f)

        logger.info("Fetching JabRef annotated abbreviations from URL.")
        response = requests.get(self._JABREF_URL)
        abbreviation_map = {}

        if response.status_code == requests.codes.ok:
            # Split into lines safely (handles different newline conventions)
            for line in response.text.splitlines():
                parts = line.split(";")
                if len(parts) >= 2:
                    full_name = parts[0].strip().lower()
                    abbrev = parts[1].strip().lower()
                    abbreviation_map[abbrev] = full_name  # Map abbrev to full form

            # Save the new abbreviations using the current timestamp as the filename.
            timestamp = int(datetime.now(timezone.utc).timestamp())
            new_cache_file = os.path.join(self.cache_dir, f"{timestamp}.json")
            with open(new_cache_file, "w", encoding="utf-8") as f:
                json.dump(abbreviation_map, f, indent=2)

        return abbreviation_map

    ## METADATA

    @staticmethod
    def _get_query_hash(query_string: str) -> str:
        """
        Generate an MD5 hash for the given query string.

        :param query_string: The query string to hash.
        :return: MD5 hash of the query string.
        """
        return hashlib.md5(query_string.encode('utf-8')).hexdigest()

    def _get_sub_dir(self,
                     query_hash: str,
                     database_name: str) -> str:
        """
        Construct the subdirectory path for a given query and database.

        :param query_hash: Hash of the query string.
        :param database_name: The database name.
        :return: Subdirectory path.
        """
        return os.path.join(self.cache_dir, query_hash, database_name)

    def _get_metadata_path(self,
                           sub_dir: str) -> str:
        """
        Return the path to the metadata.json file within the subdirectory.

        :param sub_dir: Subdirectory path.
        :return: Path to the metadata.json file.
        """
        return os.path.join(sub_dir, self.METADATA_FILENAME)

    def _load_metadata(self,
                       sub_dir: str) -> Dict[str, Any]:
        """
        Load metadata from the metadata.json file or return default values.

        :param sub_dir: Subdirectory path.
        :return: Metadata dictionary.
        """
        metadata_path = self._get_metadata_path(sub_dir)
        if not os.path.exists(metadata_path):
            logger.info(f"No metadata file found in {sub_dir}. Returning default values. Metadata file not created..")
            return self.DEFAULT_METADATA
        with open(metadata_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # Handle corrupted metadata file by resetting it
                logger.warning(f"Metadata file in {sub_dir} is corrupt. Returning default values.")
                return self.DEFAULT_METADATA

    def _save_metadata(self,
                       sub_dir: str,
                       metadata: Dict[str, Any]):
        """
        Save metadata to the metadata.json file.

        :param sub_dir: Subdirectory path.
        :param metadata: Metadata dictionary to save.
        """
        metadata_path = self._get_metadata_path(sub_dir)
        if os.path.exists(metadata_path):
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4)
            logger.info(self._append_commit_message(f"Metadata file updated in {sub_dir}."))
        else:
            os.makedirs(sub_dir, exist_ok=True)
            with open(metadata_path, 'x', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4)
            logger.info(self._append_commit_message(f"Metadata file created in {sub_dir}."))

    def get_expected_num_articles(self,
                                  query_string: str,
                                  database_name: str) -> int:
        """
        Retrieve the expected number of articles for a given query and database.

        :param query_string: The query string.
        :param database_name: The name of the database.
        :return: Expected number of articles.
        """
        query_hash = self._get_query_hash(query_string)
        sub_dir = self._get_sub_dir(query_hash, database_name)
        metadata = self._load_metadata(sub_dir)
        expected = metadata.get(self.METADATA_EXPECTED_NUM_ARTICLES, 0)
        logger.debug(f"Expected number of articles for query '{query_string}' in database '{database_name}': {expected}")
        return expected

    def set_expected_num_articles(self,
                                  query_string: str,
                                  database_name: str,
                                  expected_num: int):
        """
        Set the expected number of articles for a given query and database.

        :param query_string: The query string.
        :param database_name: The name of the database.
        :param expected_num: The expected number of articles.
        """
        query_hash = self._get_query_hash(query_string)
        sub_dir = self._get_sub_dir(query_hash, database_name)
        metadata = self._load_metadata(sub_dir)
        previous_expected = metadata.get(self.METADATA_EXPECTED_NUM_ARTICLES, 0)
        metadata[self.METADATA_EXPECTED_NUM_ARTICLES] = max(previous_expected, expected_num)
        self._save_metadata(sub_dir, metadata)
        logger.info(self._append_commit_message(f"Sett-ed expected number of articles for query '{query_string}' in database '{database_name}' to {metadata[self.METADATA_EXPECTED_NUM_ARTICLES]}."))

    def get_num_articles_retrieved(self,
                                   query_string: str,
                                   database_name: str) -> int:
        """
        Retrieve the number of articles retrieved for a given query and database.

        :param query_string: The query string.
        :param database_name: The name of the database.
        :return: Number of articles retrieved.
        """
        query_hash = self._get_query_hash(query_string)
        sub_dir = self._get_sub_dir(query_hash, database_name)
        metadata = self._load_metadata(sub_dir)
        retrieved = metadata.get(self.METADATA_NUM_ARTICLES_RETRIEVED, 0)
        logger.debug(f"Number of articles retrieved for query '{query_string}' in database '{database_name}': {retrieved}")
        return retrieved

    def set_num_articles_retrieved(self,
                                   query_string: str,
                                   database_name: str,
                                   num_retrieved: int):
        """
        Set the number of articles retrieved for a given query and database.

        :param query_string: The query string.
        :param database_name: The name of the database.
        :param num_retrieved: Number of articles retrieved.
        """
        query_hash = self._get_query_hash(query_string)
        sub_dir = self._get_sub_dir(query_hash, database_name)
        metadata = self._load_metadata(sub_dir)
        metadata['num_articles_retrieved'] = num_retrieved
        self._save_metadata(sub_dir, metadata)
        logger.info(self._append_commit_message(f"Sett-ed number of articles retrieved for query '{query_string}' in database '{database_name}' to {num_retrieved}."))

    def _cache_articles_to_sub_dir(self,
                                   query_string: str,
                                   database_name: str,
                                   library: Library,
                                   manually_obtained: bool,
                                   additional_metadata: Dict[str, Any] = None):
        """
        Caches articles into the appropriate subdirectory and updates metadata.

        :param query_string: The query string associated with the articles.
        :param database_name: The name of the database.
        :param library: Library object to cache.
        :param manually_obtained: Boolean indicating if the articles were manually retrieved.
        :param additional_metadata: Optional dictionary of additional metadata to include.
        """
        query_hash = self._get_query_hash(query_string)
        sub_dir = self._get_sub_dir(query_hash, database_name)
        os.makedirs(sub_dir, exist_ok=True)

        # Identify existing files
        existing_files = [f for f in os.listdir(sub_dir) if f.startswith("result") and f.endswith(".bib")]
        current_file_number = max([int(f[6:-4]) for f in existing_files if f[6:-4].isdigit()],default=0)
        current_file_path = os.path.join(sub_dir, f"result{current_file_number}.bib")

        # Load existing articles from the current file
        if os.path.exists(current_file_path):
            current_library = parse_file(current_file_path)
        else:
            current_library = Library()

        # Add new articles and split into files
        articles_to_add = library.entries
        while articles_to_add:
            available_space = self.ARTICLE_LIMIT - len(current_library.entries)

            # Add as many articles as possible to the current file
            current_library = self.merge_entries(current_library, articles_to_add[:available_space])
            articles_to_add = articles_to_add[available_space:]

            # Save the current file
            write_file(file=current_file_path,
                       library=current_library,
                       parse_stack=[MonthAbbreviationMiddleware(),
                                    AddEnclosingMiddleware(reuse_previous_enclosing=False,
                                                           enclose_integers=False,
                                                           default_enclosing="{"),
                                    SortFieldsAlphabeticallyMiddleware()])
            logger.info(
                self._append_commit_message(f"Cached {len(current_library.entries)} articles to {current_file_path}."))

            # If there are more articles, prepare a new file
            if articles_to_add:
                current_file_number += 1
                current_file_path = os.path.join(sub_dir, f"result{current_file_number}.bib")
                current_library = Library()

        # Update metadata
        metadata = self._load_metadata(sub_dir)
        metadata[self.METADATA_NUM_ARTICLES_RETRIEVED] = len(library.entries)
        metadata[self.METADATA_GENERAL_QUERY_STRING] = query_string
        metadata[self.METADATA_MANUALLY_OBTAINED] = manually_obtained
        metadata[self.METADATA_LAST_API_CALL_TIME] = datetime.now(timezone.utc).isoformat()
        # Include any additional metadata
        if additional_metadata:
            metadata.update(additional_metadata)

        self._save_metadata(sub_dir, metadata)
        logger.info(self._append_commit_message(f"Metadata file updated in {sub_dir}."))

    def cache_union_articles(self,
                             articles: Library,
                             query: str):
        """
        Cache the results as a BibTeX file in the slrquerytester-union directory.

        :param articles: bibtexparser.library.Library object.
        :param query: The query Tree or general query string associated with the articles.
        """
        self._cache_articles_to_sub_dir(
            query_string=query,
            database_name=self.UNION_DIRECTORY_NAME,
            library=articles,
            manually_obtained=False,  # Automatically obtained data
        )

    def cache_api_articles(self,
                           articles: Library,
                           query: Tree,
                           database_name: str,
                           expected_num_articles: int):
        """
        Cache the results as a BibTeX file in the cache directory and updates metadata.

        :param articles: bibtexparser.library.Library object.
        :param query: The query Tree object associated with the articles.
        :param database_name: The name of the database from which articles were retrieved.
        :param expected_num_articles: Total number of articles expected from the query.
        """
        base_transformer = BaseTransformer()
        query_string = base_transformer.transform(query)
        self._cache_articles_to_sub_dir(
            query_string=query_string,
            database_name=database_name,
            library=articles,
            manually_obtained=False,  # Automatically obtained data
            additional_metadata={
                self.METADATA_TRANSLATED_QUERY_STRING: translate_query(query, database_name),
                self.METADATA_EXPECTED_NUM_ARTICLES: expected_num_articles,
            }
        )

    def cache_manual_articles(self, manual_articles_directory: str):
        """
        Read manually retrieved articles from the manual_articles_directory and caches them
        into the cache directory.

        Updates metadata to include a 'manually_obtained' field indicating the source of data.

        :param manual_articles_directory: Path to the directory containing manually retrieved articles.
        """
        if not os.path.exists(manual_articles_directory):
            logger.warning(f"Manual articles directory does not exist: {manual_articles_directory}")
            return

        # Iterate over the query directories in manual_articles_directory
        for query_dir_name in os.listdir(manual_articles_directory):
            query_dir = os.path.join(manual_articles_directory, query_dir_name)
            if os.path.isdir(query_dir):
                # Iterate over the database directories within the query directory
                for database_name in os.listdir(query_dir):
                    database_dir = os.path.join(query_dir, database_name)
                    if os.path.isdir(database_dir):
                        metadata_path = os.path.join(database_dir, self.METADATA_FILENAME)
                        if not os.path.exists(metadata_path):
                            logger.warning(f"No metadata.json found in {database_dir}. Skipping.")
                            continue

                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)

                        general_query_string = metadata.get(self.METADATA_GENERAL_QUERY_STRING, query_dir_name)

                        # Delete the currently cached results
                        query_hash = self._get_query_hash(general_query_string)
                        sub_dir = self._get_sub_dir(query_hash, database_name)
                        if os.path.exists(sub_dir):
                            shutil.rmtree(sub_dir)

                        articles = FileManager.read_bibtex_directory(database_dir)

                        # Use the helper method for caching
                        self._cache_articles_to_sub_dir(
                            query_string=general_query_string,
                            database_name=database_name,
                            library=articles,
                            manually_obtained=True,  # Manually obtained data
                        )

    def _append_commit_message(self, message: str):
        """
        Append a message to the git commit message file in the repository path.

        :param message: The message to append.
        """
        if self.autogit and self.repository_path:
            with self.commit_message_lock:
                with open(self.commit_message_file, 'a', encoding='utf-8') as f:
                    f.write(message)
        return message

    def is_result_stale(self,
                        query_string: str,
                        database_name: str) -> bool:
        """
        Determine if the cached data is stale based on the last API call time.

        :param query_string: The query string.
        :param database_name: The name of the database.
        :return: True if stale, False otherwise.
        """
        query_hash = self._get_query_hash(query_string)
        sub_dir = self._get_sub_dir(query_hash, database_name)
        metadata = self._load_metadata(sub_dir)
        if metadata.get(self.METADATA_MANUALLY_OBTAINED):
            logger.debug(f"Cache for query '{query_string}' in {sub_dir} is manually obtained and hence not deleted.")
            return False
        last_call = metadata.get(self.METADATA_LAST_API_CALL_TIME)
        if not last_call:
            logger.debug(f"Cache for query '{query_string}' in {sub_dir} is ASSUMED stale.")
            return True  # No data means it's stale
        last_call_time = datetime.fromisoformat(last_call)
        is_stale = datetime.now(timezone.utc) - last_call_time > timedelta(days=self._STALE_AFTER_DAYS)
        logger.debug(f"Cache staleness for query '{query_string}' in database '{database_name}': {is_stale}")
        return is_stale

    def is_result_partial(self,
                          query_string: str,
                          database_name: str) -> bool:
        """
        Check if the cached result is incomplete.
        A result is considered partial if the number of articles retrieved is less than the expected number.

        :param query_string: The query string.
        :param database_name: The name of the database.
        :return: True if partial, False otherwise.
        """
        expected = self.get_expected_num_articles(query_string, database_name)
        retrieved = self.get_num_articles_retrieved(query_string, database_name)
        is_partial = retrieved < expected and expected > 0
        logger.debug(f"Result partiality for query '{query_string}' in database '{database_name}': {is_partial}")
        return is_partial

    def is_result_present(self,
                          query_string: str,
                          database_name: str) -> bool:
        """
        Check if the result for a given query and database is present in the cache.

        :param query_string: The query string.
        :param database_name: The name of the database.
        :return: True if the cached BibTeX file exists, False otherwise.
        """
        query_hash = self._get_query_hash(query_string)
        sub_dir = self._get_sub_dir(query_hash, database_name)
        bib_file_path = os.path.join(sub_dir, "result0.bib")
        is_present = os.path.exists(bib_file_path)
        logger.debug(f"Result presence for query '{query_string}' in database '{database_name}': {is_present}")
        return is_present

    def clear_result_cache(self,
                           query_string: str,
                           database_name: str):
        """
        Clear the cached results for a given query and database.

        :param query_string: The query string.
        :param database_name: The name of the database.
        """
        query_hash = self._get_query_hash(query_string)
        sub_dir = self._get_sub_dir(query_hash, database_name)
        if os.path.exists(sub_dir):
            # Remove all files in the subdirectory
            for filename in os.listdir(sub_dir):
                file_path = os.path.join(sub_dir, filename)
                os.unlink(file_path)
            os.rmdir(sub_dir)
            logger.warning(self._append_commit_message(f"Cleared cache for query '{query_string}' in database '{database_name}'"))

    def get_cached_queries_data(self) -> Dict[str, Dict]:
        """
        Retrieve cached queries and their associated data from the cache directory.

        :return: A mapping from general_query_string to its data.
        """
        queries_data = defaultdict(lambda: {'databases': {}})

        for query_hash in os.listdir(self.cache_dir):
            query_hash_dir = os.path.join(self.cache_dir, query_hash)
            if os.path.isdir(query_hash_dir):
                logger.info(f"Getting cached data for query with hash {query_hash}")
                # For each database in this query_hash
                for database_name in os.listdir(query_hash_dir):
                    if database_name == self.UNION_DIRECTORY_NAME:
                        continue
                    database_dir = os.path.join(query_hash_dir, database_name)
                    metadata = self._load_metadata(database_dir)
                    general_query_string = metadata.get(self.METADATA_GENERAL_QUERY_STRING)
                    translated_query_string = metadata.get(self.METADATA_TRANSLATED_QUERY_STRING)
                    num_articles_retrieved = metadata.get(self.METADATA_NUM_ARTICLES_RETRIEVED, 0)
                    library = FileManager.read_bibtex_directory(database_dir)
                    query_data = queries_data[general_query_string]
                    query_data['databases'][database_name] = {
                        self.METADATA_TRANSLATED_QUERY_STRING: translated_query_string,
                        self.METADATA_NUM_ARTICLES_RETRIEVED: num_articles_retrieved,
                        'articles': library
                    }
                logger.info(f"Finished getting cached data for query with hash {query_hash}")

        return queries_data

    def get_cached_database_names(self) -> List[str]:
        """
        Dynamically retrieve a list of all available database names from the cache.

        :return: List of unique database names found in the cache.
        """
        database_names = set()
        # Iterate over query hash directories in the cache
        for query_hash in os.listdir(self.cache_dir):
            query_hash_dir = os.path.join(self.cache_dir, query_hash)
            if os.path.isdir(query_hash_dir):
                # Add all subdirectory names (database names) to the set
                database_names.update([db_name for db_name in os.listdir(query_hash_dir) if db_name != self.UNION_DIRECTORY_NAME])

        return list(database_names)

    def count_matching_entries(self, library1: Library, library2: Library) -> int:
        """
        Count how many articles in library1 are also present in library2 based on matching criteria.

        :param library1: First library of entries.
        :param library2: Second library of entries.
        :return: Number of matching entries.
        """
        return len(self.get_matching_entries(library1, library2).entries)

    def get_matching_entries(self, library1: Library, library2: Library) -> Library:
        """
        Find and return matching entries between two libraries based on DOI and fuzzy matching.

        :param library1: First library of entries.
        :param library2: Second library of entries.
        :return: A Library object containing matching entries.
        """
        return_library = Library()
        logger.debug("Beginning pre-filter")
        # Pre-filter to reduce comparisons
        filtered_pairs = self._pre_filter_entries(library1, library2)
        logger.debug("Finished pre-filter")
        # Use ProcessPoolExecutor for parallel processing
        with ProcessPoolExecutor() as executor:
            tasks = [
                (entry1, entry2, self._normalize_entry, self._compare_entries)
                for entry1, entry2 in filtered_pairs
            ]
            results = list(executor.map(self._compare_entries_wrapper, tasks))

        # Collect matches
        for index, (entry1, _) in enumerate(filtered_pairs):
            if results[index] > self._MIN_FUZZ_COMPARISON_SCORE:
                return_library.add(entry1)

        return return_library

    @staticmethod
    def _pre_filter_entries(library1: Library, library2: Library) -> List[tuple]:
        """
        Pre-filter entries by checking DOI first before using fuzzy matching.

        :param library1: First library of entries.
        :param library2: Second library of entries.
        :return: List of (entry1, entry2) pairs that should be compared.
        """
        filtered_pairs = []

        # Create a DOI lookup for library2
        library2_doi_index = {}
        for entry2 in library2.entries:
            doi_field = entry2.get("doi", "")
            if isinstance(doi_field, Field):
                doi_norm = doi_field.value.lower().strip()
                if doi_norm:
                    library2_doi_index[doi_norm] = entry2

        # For each entry in library1
        for entry1 in library1.entries:
            doi1_field = entry1.get("doi", "")
            doi1_norm = None
            if isinstance(doi1_field, Field):
                doi1_norm = doi1_field.value.lower().strip()

            # If library1's DOI is in library2's DOI index, we do an exact match
            if doi1_norm and doi1_norm in library2_doi_index:
                filtered_pairs.append((entry1, library2_doi_index[doi1_norm]))
            else:
                # Fallback: If library1's DOI is missing or no match, fuzzy-compare
                # only with library2 entries that have no DOI
                for entry2 in library2.entries:
                    doi2_field = entry2.get("doi", "")
                    if not doi2_field:  # or if it's empty
                        filtered_pairs.append((entry1, entry2))

        return filtered_pairs

    @staticmethod
    def _compare_entries_wrapper(args):
        """
        Worker function for parallel fuzzy comparison.

        :param args: Tuple containing the entries and functions for comparison.
        :return: Similarity score between the entries.
        """
        entry1, entry2, _, compare_function = args  # We ignore the clean_function here
        return compare_function(entry1, entry2)

    def _compare_entries(self, entry1: Entry, entry2: Entry) -> int:
        """
        Compute a similarity score (0–100) between two robustly normalized BibTeX entries.

        :param entry1: First BibTeX entry.
        :param entry2: Second BibTeX entry.
        :return: Fuzzy similarity score between the entries.
        """
        return fuzz.ratio(self._normalize_entry(entry1), self._normalize_entry(entry2))

    def _clean_text(self, text: str) -> str:
        """
        Normalize text by converting to lowercase, stripping whitespace, removing special characters, and expanding abbreviations.

        :param text: The text to normalize.
        :return: The normalized text.
        """
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)  # Remove special characters
        words = text.split()
        words = [self._ABBREVIATION_MAP.get(word, word) for word in words]
        return " ".join(words)

    # TODO: test with venue
    def _normalize_entry(self, entry: Entry) -> str:
        """
        Convert a BibTeX entry into a normalized string using key fields like author, title, and year.

        :param entry: The BibTeX entry to normalize.
        :return: Normalized string representation of the entry.
        """
        normalized_fields = []
        for key, field_obj in sorted(entry.fields_dict.items()):
            if key not in ("author", "title", "year"):
                continue
            clean_key = self._clean_text(key)
            clean_value = self._clean_text(field_obj.value)
            normalized_fields.append(f"{clean_key}: {clean_value}")

        return " | ".join(normalized_fields)

    def merge_entries(self,
                      library1: Union[Library, List[Entry], Entry],
                      library2: Union[Library, List[Entry], Entry]) -> Library:
        """
        Merge library2 into library1 while avoiding duplicates based on matching criteria.

        :param library1: First library or list of entries.
        :param library2: Second library or list of entries.
        :return: A merged Library object.
        """
        dict1 = self._library_to_dict(library1)
        dict2 = self._library_to_dict(library2)

        # Build a block index for entries in dict1
        # block_index[title_prefix] = [Entry, Entry, ...]
        block_index = {}
        for e1 in dict1.values():
            prefix = self._block_key(e1)
            block_index.setdefault(prefix, []).append(e1)

        # Start merged as dict1
        merged_dict = dict1.copy()

        for k2, e2 in dict2.items():
            # 1) If the key already exists, we consider it a duplicate (skip)
            if k2 in merged_dict:
                continue

            # 2) Check for matching DOI in merged_dict
            e2_doi = self._get_normalized_doi(e2)
            if e2_doi:
                found_doi_match = False
                for mkey, mval in merged_dict.items():
                    mval_doi = self._get_normalized_doi(mval)
                    if mval_doi and mval_doi == e2_doi:
                        found_doi_match = True
                        break
                if found_doi_match:
                    # We found a duplicate by DOI, skip adding e2
                    continue

            # 3) If still unmatched, do a fuzzy check only on the matching block
            prefix2 = self._block_key(e2)
            possible_dups = block_index.get(prefix2, [])

            duplicate_found = False
            for candidate in possible_dups:
                score = self._compare_entries(candidate, e2)
                if score > self._MIN_FUZZ_COMPARISON_SCORE:
                    duplicate_found = True
                    break

            if not duplicate_found:
                # Add e2 to merged_dict and also to the block_index
                merged_dict[k2] = e2
                block_index.setdefault(prefix2, []).append(e2)

        # Return a Library from merged_dict
        return Library(blocks=list(merged_dict.values()))

    @staticmethod
    def _library_to_dict(maybe_lib: Union[Library, List[Entry], Entry, None]) -> Dict[str, Entry]:
        """
        Convert a Library, list of entries, or a single entry into a dictionary keyed by entry key.

        :param maybe_lib: Library, list of entries, or single entry.
        :return: Dictionary representation of the entries.
        """
        result = {}
        if not maybe_lib:
            return result

        if isinstance(maybe_lib, Library):
            for e in maybe_lib.entries:
                if e.key:
                    result[e.key] = e
        elif isinstance(maybe_lib, list):
            for e in maybe_lib:
                if e.key:
                    result[e.key] = e
        else:  # single Entry
            if maybe_lib.key:
                result[maybe_lib.key] = maybe_lib

        return result

    @staticmethod
    def _block_key(entry: Entry, length: int = 10) -> str:
        """
        Generate a short, normalized prefix from the entry's title for blocking.

        :param entry: The BibTeX entry.
        :param length: Length of the prefix.
        :return: Normalized prefix from the title.
        """
        title_field = entry.get("title")
        if not title_field:
            return ""
        title_text = title_field.value
        if not title_text:
            return ''
        else:
            title_text = title_text.lower().strip()
        # remove punctuation
        title_text = re.sub(r"[^\w\s]", "", title_text)
        return title_text[:length]  # first N characters

    @staticmethod
    def _get_normalized_doi(entry: Entry) -> str:
        """
        Retrieve and normalize the DOI value from an entry.

        :param entry: The BibTeX entry.
        :return: Normalized DOI value or an empty string.
        """
        doi_field = entry.get("doi")
        if isinstance(doi_field, Field):
            return doi_field.value.strip().lower()
        return ""

    @staticmethod
    def _to_library(entries: Union[Library, List[Entry], Entry]) -> Library:
        """
        Safely convert entries into a Library object.

        :param entries: Library, list of entries, or a single entry.
        :return: A Library object containing the entries.
        """
        if isinstance(entries, Library):
            return entries
        elif isinstance(entries, list):
            return Library(blocks=entries)
        elif isinstance(entries, Entry):
            return Library(blocks=[entries])
        else:
            # None or unknown
            return Library()