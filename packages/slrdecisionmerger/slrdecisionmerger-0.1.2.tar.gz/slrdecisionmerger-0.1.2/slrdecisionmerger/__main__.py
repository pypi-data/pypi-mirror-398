import argparse
import logging
import sys

from .utils.paper_divider import PaperDivider
from .utils.file_manager import FileManager
from .utils.decision_merger import DecisionMerger
from . import logger


def main():
    """
    Main function that orchestrates the paper division and decision merging.
    """

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='SLR Decision Merger')
    parser.add_argument('--config',
                        type=str,
                        help='Path to the configuration JSON file.',
                        default='config.json')
    parser.add_argument('--divide',
                        action='store_true',
                        help='If flag is set, divide papers among reviewers.')
    parser.add_argument('--merge',
                        action='store_true',
                        help='If flag is set, merge reviewer decisions and generate reports.')
    parser.add_argument('--merge_strat',
                        type=str,
                        choices=['conservative', 'liberal', 'consensus'],
                        default='consensus',
                        help='The merge strategy to use (default: consensus).')
    parser.add_argument('--debug',
                        action='store_true',
                        help='If flag is set, log debug messages.')
    args = parser.parse_args()
    if args.divide and args.merge:
        parser.error("Cannot set both --divide and --merge flags!")
    elif not (args.divide or args.merge):
        parser.error("One of --divide or --merge flags must be set!")

    # Set logging level
    logger.setLevel(logging.DEBUG if '--debug' in sys.argv else logging.INFO)

    # Read configuration
    config_file: str = args.config
    (reviewers,
     reviewers_per,
     cache_directory,
     division_directory,
     review_directory,
     report_directory) = FileManager.read_config(filename=config_file)

    if args.divide:
        library = FileManager.read_bibtex_directory(cache_directory)
        paper_divider = PaperDivider(reviewers=reviewers,
                                     reviewers_per=reviewers_per)
        paper_divider.divide_papers(library=library,
                                    division_directory=division_directory)

    if args.merge:
        DecisionMerger.merge_decisions(review_directory=review_directory,
                                       strategy=args.merge_strat,
                                       report_directory=report_directory)

if __name__ == "__main__":
    main()
