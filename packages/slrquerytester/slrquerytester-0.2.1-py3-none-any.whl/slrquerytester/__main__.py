import argparse
import logging
import os
import subprocess
import sys
import traceback
from typing import List

from bibtexparser import Library

from .utils.document_generator import generate_documentation
from .utils.report_generator import ReportGenerator
from .utils.query_processor import QueryProcessor
from .utils.connector_manager import ConnectorManager
from .utils.cache_manager import CacheManager
from .utils.file_manager import FileManager
from . import logger


def main():
    """
    Main function that orchestrates the search, comparison, and reporting.
    """

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='SLR Query Tester')
    parser.add_argument('--config',
                        type=str,
                        help='Path to the configuration JSON file.',
                        default='config.json')
    parser.add_argument('--query',
                        action='store_true',
                        help='If flag is set, query databases.')
    parser.add_argument('--manual',
                        action='store_true',
                        help='If flag is set, import manual articles from manual_directory.')
    parser.add_argument('--report',
                        action='store_true',
                        help='If set, generate golden solution comparison reports.')
    parser.add_argument('--output_merge',
                        action='store_true',
                        help='If set with --report, output merged results.')
    parser.add_argument('--git',
                        action='store_true',
                        help='If flag is set, automatically commit and push data to git. Requires "repository" definition in config.')
    parser.add_argument('--debug',
                        action='store_true',
                        help='If flag is set, log debug messages.')
    parser.add_argument('--docs',
                        action='store_true',
                        help='If set, generate documentation using Sphinx and open the browser.')
    args = parser.parse_args()
    if args.output_merge and not args.report:
        parser.error("--output_merge can only be used when --report is set.")

    logger.setLevel(logging.DEBUG if '--debug' in sys.argv else logging.INFO)

    if args.docs:
        generate_documentation()
        sys.exit(0)

    # Read configuration
    config_file : str = args.config
    (api_keys,
     cache_directory,
     golden_solution_directory,
     report_directory,
     threshold_days,
     queries_file,
     repository_path,
     manual_articles_directory,
     language) = FileManager.read_config(filename=config_file)

    # Create cache manager
    if args.git:
        if repository_path:
            cache_manager : CacheManager = CacheManager(cache_dir=cache_directory,
                                                        repository_path=repository_path,
                                                        stale_after_days=threshold_days,
                                                        autogit=True)
        else:
            logger.error("Git repository not specified in config but --git flag is enabled!")
            raise ValueError("Git repository not specified in config but --git flag is enabled!")
    else:
        cache_manager : CacheManager = CacheManager(cache_dir=cache_directory,
                                                    repository_path=None,
                                                    stale_after_days=threshold_days,
                                                    autogit=False)

    if args.manual:
        # Try caching manually retrieved articles
        cache_manager.cache_manual_articles(manual_articles_directory=manual_articles_directory)

    # Read queries from the queries file
    queries_json : List[dict] = FileManager.read_queries_json(filename=queries_file)

    if args.query:
        # Query the available connectors with outdated/incomplete cached results
        # Prepare database connectors
        connector_manager : ConnectorManager = ConnectorManager(api_keys)
        # Process each query
        QueryProcessor.process_queries(queries_json=queries_json,
                                       connector_manager=connector_manager,
                                       cache_manager=cache_manager,
                                       language=language)

    if args.report:
        # Regenerate the report
        # Try loading the golden solution
        golden_articles: Library = Library()
        try:
            logger.info("Loading golden solution articles.")
            golden_articles = FileManager.read_bibtex_directory(bibtex_directory=golden_solution_directory)
            logger.info("Finished loading golden solution articles.")
        except RuntimeError as e:
            logger.error(f"No golden solutions found: {traceback.format_exc()}")
            raise RuntimeError(e)
        if len(golden_articles.entries):
            report_generator : ReportGenerator = ReportGenerator(report_directory, cache_manager)
            report_generator.generate_reports(queries_json=queries_json,
                                              golden_articles=golden_articles,
                                              output_merge=args.output_merge)

    if args.git:
        # Automatically commit changes.
        if os.path.exists(path=cache_manager.commit_message_file):
            try:
                # Add the updated file to staging
                subprocess.run(args=["git", "-C", repository_path, "add", "."], check=True)

                # Read commit message
                with open(cache_manager.commit_message_file, 'r', encoding='utf-8') as f:
                    commit_message = f.read()

                # Commit the changes
                subprocess.run(args=["git", "-C", repository_path, "commit", "-m", commit_message], check=True)

                # Push the changes to the remote repository
                subprocess.run(args=["git", "-C", repository_path, "push"], check=True)

                logger.info("Cache updated and pushed successfully!")

                # Delete the commit message file
                os.remove(cache_manager.commit_message_file)
            except subprocess.CalledProcessError as e:
                logger.error(f"Git operation failed: {e}")
        else:
            logger.info("No new data to commit.")

if __name__ == '__main__':
    main()
