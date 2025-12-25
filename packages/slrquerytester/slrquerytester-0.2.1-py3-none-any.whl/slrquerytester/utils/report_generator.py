import csv
import os
from typing import Dict, List

from bibtexparser.model import Field
from bibtexparser import Library

from .cache_manager import CacheManager
from .. import logger

class ReportGenerator:
    """
    .. include:: ../../docs/reports.md
    """

    def __init__(self, report_directory: str, cache_manager: CacheManager):
        self.report_directory = report_directory
        os.makedirs(report_directory, exist_ok=True)
        self.cache_manager = cache_manager

    def generate_reports(self,
                         queries_json: List[Dict],
                         golden_articles: Library,
                         output_merge: bool):
        """
        Generate the report and writes it to a CSV file.
        """
        queries_data = self.cache_manager.get_cached_queries_data()

        # Ensure all queries from queries.json are included
        for query_entry in queries_json:
            query_string = query_entry["query"]
            if query_string not in queries_data:
                queries_data[query_string] = {"databases": {}}

        # Prepare the report data
        report_rows = []
        logger.info("Generating reports.")

        for idx, (query_string, query_data) in enumerate(queries_data.items(), start=1):
            row = {
                "Serial Number": idx,
                "Query String": query_string
            }
            all_articles = Library()
            union_golden_matches = Library()
            # For each database
            for database_name, database_data in query_data["databases"].items():
                logger.info(
                    f"Computing main report statistics of database '{database_name}' "
                    f"for query: {query_string}."
                )

                translated_query_string = database_data.get(
                    self.cache_manager.METADATA_TRANSLATED_QUERY_STRING, ""
                )
                num_articles_retrieved = database_data.get(
                    self.cache_manager.METADATA_NUM_ARTICLES_RETRIEVED, 0
                )
                articles: Library = database_data.get("articles", Library())

                # Compare with golden solution
                logger.info(f"Counting golden matches for database {database_name}")
                golden_matches: Library = self.cache_manager.get_matching_entries(articles, golden_articles)
                logger.info(f"Finished counting golden matches for database {database_name}")
                query_data["databases"][database_name]["golden_matches"] = golden_matches

                logger.info(f"Merging golden matches from {database_name} into union-set")
                union_golden_matches = self.cache_manager.merge_entries(golden_matches, union_golden_matches)
                logger.info(f"Finished merging golden matches from {database_name} into union-set")

                # Merge articles
                logger.info(f"Merging articles from {database_name} into union-set")
                all_articles = self.cache_manager.merge_entries(all_articles, articles)
                logger.info(f"Finished merging articles from {database_name} into union-set")

                # Add data to row
                row[f"{database_name} - Translated Query"] = translated_query_string
                row[f"{database_name} - Articles Retrieved"] = num_articles_retrieved
                row[f"{database_name} - Golden Matches"] = len(golden_matches.entries)

            row["Total Unique Articles"] = len(all_articles.entries)
            row["Total Golden Matches"] = len(union_golden_matches.entries)

            report_rows.append(row)

            # Generate secondary report for this query
            self._generate_secondary_report(
                idx, query_string, query_data["databases"], golden_articles
            )

            if output_merge:
                self.cache_manager.cache_union_articles(all_articles, query_string)

        # Get list of all database names to create the CSV header
        database_names = self.cache_manager.get_cached_database_names()

        # Prepare CSV header
        headers = ["Serial Number", "Query String"]
        for database_name in sorted(database_names):
            headers.extend([
                f"{database_name} - Translated Query",
                f"{database_name} - Articles Retrieved",
                f"{database_name} - Golden Matches"
            ])
        headers.extend(["Total Unique Articles", "Total Golden Matches"])

        # Write to main CSV file
        main_csv_file = os.path.join(self.report_directory, "main.csv")
        with open(main_csv_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for row in report_rows:
                writer.writerow(row)

        logger.info(f"Main report generated and saved to {main_csv_file}")

    def _generate_secondary_report(
        self,
        serial_number: int,
        query_string: str,
        databases_data: Dict[str, Dict],
        golden_articles: Library
    ):
        """
        Generate a secondary report CSV file for a single query.

        The secondary report lists all golden solution articles and indicates whether each
        article was found in the results from each database.
        """
        # Prepare the filename
        logger.info(
            f"Generating secondary report for query with serial number {serial_number}"
        )
        secondary_csv_file = os.path.join(
            self.report_directory, f"{serial_number}.csv"
        )

        # Prepare the header
        database_names = sorted(databases_data.keys())
        headers = ["Article Title"] + database_names

        # Prepare the data rows
        rows = []
        for article in golden_articles.entries:
            # Safely get the article title
            article_title = ""
            title_field = article.get("title")
            if isinstance(title_field, Field):
                article_title = title_field.value

            row = {"Article Title": article_title}

            for database_name in database_names:
                database_golden_matches = databases_data[database_name].get(
                    "golden_matches", Library()
                )
                # Check if article is present in the golden matches for that database
                if self.cache_manager.count_matching_entries(
                    Library([article]), Library(database_golden_matches.entries)
                ):
                    row[database_name] = "Yes"
                else:
                    row[database_name] = "No"

            rows.append(row)

        # Write to secondary CSV file
        with open(secondary_csv_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        logger.info(
            f"Secondary report for query '{query_string}' generated and saved to {secondary_csv_file}"
        )
