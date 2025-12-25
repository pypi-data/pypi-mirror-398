import os
import csv
import copy
from typing import Dict, List
from itertools import combinations

import bibtexparser
from bibtexparser import Library
from bibtexparser.middlewares import MonthAbbreviationMiddleware, AddEnclosingMiddleware, \
    SortFieldsAlphabeticallyMiddleware, LatexDecodingMiddleware

from .. import logger

class DecisionMerger:
    """
    Handles the merging of reviewer decisions based on different strategies.
    """

    @staticmethod
    def merge_decisions(review_directory: str, report_directory: str, strategy: str):
        """
        Reads reviewer files, merges decisions based on a strategy, and generates reports.

        :param review_directory: Directory containing BibTeX files from reviewers.
        :param report_directory: Directory where output reports will be saved.
        :param strategy: The merge strategy ('conservative', 'liberal', 'consensus').
        """
        logger.debug(f"Starting decision merge with strategy: {strategy}")

        # 1. Read all reviewer files
        reviewer_libs = DecisionMerger._load_reviewer_libraries(review_directory)
        if not reviewer_libs:
            logger.warning("No reviewer files found. Nothing to merge.")
            return

        accepted_library = Library()
        conflicted_library = Library()
        conflict_report_data = []
        accepted_report_data = []
        reviewers = sorted(reviewer_libs.keys())
        # Track: conflict_matrix[r1][r2] = (r1_accepts, total_conflicts)
        conflict_matrix = {r1: {r2: {'accepts': 0, 'total': 0} for r2 in reviewers} for r1 in reviewers}
        processed_keys = set()

        # 2. Process each paper iteratively
        for reviewer_main, lib_main in reviewer_libs.items():
            for entry_main in lib_main.entries:
                key = entry_main.key
                if key in processed_keys:
                    continue  # Already processed this paper

                # Found a new paper to process
                processed_keys.add(key)
                decisions: Dict[str, str] = {}
                paper_entry_original = None

                # Gather all decisions for this specific paper from all reviewers
                for reviewer_lookup, lib_lookup in reviewer_libs.items():
                    entry = lib_lookup.entries_dict.get(key)
                    if entry:
                        # Safer check for decision
                        groups_field = entry.get("groups")
                        decisions[reviewer_lookup] = "accept" if groups_field and groups_field.value == "relevant" else "reject"
                        if not paper_entry_original:
                            paper_entry_original = entry  # Keep a reference to the first-found entry
                
                if not paper_entry_original:
                    continue

                # Create a clean, deep copy for modification and adding to new libraries
                paper_entry = copy.deepcopy(paper_entry_original)
                if "groups" in paper_entry:
                    paper_entry.pop("groups")

                # Warn if there is only one review
                if len(decisions.keys()) == 1:
                    logger.warning(f"Only one decision found for paper with key {key} in reviewer {reviewer_main}.bib !!")

                # Helper function to extract field values
                def get_value(entry, key):
                    field = entry.get(key)
                    return field.value if field else ''

                # 3. Apply the chosen strategy for the current paper
                if strategy == 'conservative':
                    if "accept" in decisions.values():
                        accepted_library.add(paper_entry)
                        accepted_report_data.append({
                            'key': paper_entry.key,
                            'title': get_value(paper_entry, 'title'),
                            'author': get_value(paper_entry, 'author'),
                            'year': get_value(paper_entry, 'year'),
                            'doi': get_value(paper_entry, 'doi'),
                            'url': get_value(paper_entry, 'url')
                        })
                
                elif strategy == 'liberal':
                    if "reject" not in decisions.values() and "accept" in decisions.values():
                        accepted_library.add(paper_entry)
                        accepted_report_data.append({
                            'key': paper_entry.key,
                            'title': get_value(paper_entry, 'title'),
                            'author': get_value(paper_entry, 'author'),
                            'year': get_value(paper_entry, 'year'),
                            'doi': get_value(paper_entry, 'doi'),
                            'url': get_value(paper_entry, 'url')
                        })

                elif strategy == 'consensus':
                    has_accept = "accept" in decisions.values()
                    has_reject = "reject" in decisions.values()

                    if has_accept and not has_reject:
                        accepted_library.add(paper_entry)
                        accepted_report_data.append({
                            'key': paper_entry.key,
                            'title': get_value(paper_entry, 'title'),
                            'author': get_value(paper_entry, 'author'),
                            'year': get_value(paper_entry, 'year'),
                            'doi': get_value(paper_entry, 'doi'),
                            'url': get_value(paper_entry, 'url')
                        })
                    elif has_accept and has_reject:
                        # Conflict: store detailed review info
                        conflicted_library.add(paper_entry)

                        report_row = {
                            'key': paper_entry.key,
                            'title': get_value(paper_entry, 'title'),
                            'author': get_value(paper_entry, 'author'),
                            'year': get_value(paper_entry, 'year'),
                            'doi': get_value(paper_entry, 'doi'),
                            'url': get_value(paper_entry, 'url')
                        }
                        for r in reviewers:
                            decision = decisions.get(r)
                            report_row[r] = decision if decision in ['accept', 'reject'] else '-'
                        conflict_report_data.append(report_row)
                        
                        # Update conflict matrix with detailed accept/reject tracking
                        conflicting_reviewers = [r for r, d in decisions.items() if d in ['accept', 'reject']]
                        for r1, r2 in combinations(conflicting_reviewers, 2):
                            if decisions[r1] != decisions[r2]:
                                # Increment total conflicts for both
                                conflict_matrix[r1][r2]['total'] += 1
                                conflict_matrix[r2][r1]['total'] += 1
                                # Track who accepted
                                if decisions[r1] == 'accept':
                                    conflict_matrix[r1][r2]['accepts'] += 1
                                if decisions[r2] == 'accept':
                                    conflict_matrix[r2][r1]['accepts'] += 1
        
        # 4. Write output files from the collected results
        logger.debug(f"Processed {len(processed_keys)} unique papers.")
        if accepted_library.entries:
            accepted_path = os.path.join(report_directory, "accepted.bib")
            logger.debug(f"Writing {len(accepted_library.entries)} accepted papers to {accepted_path}")
            bibtexparser.write_file(file=accepted_path,
                                    library=accepted_library,
                                    parse_stack=[MonthAbbreviationMiddleware(),
                                                 AddEnclosingMiddleware(reuse_previous_enclosing=False,
                                                                        enclose_integers=False,
                                                                        default_enclosing="{"),
                                                 SortFieldsAlphabeticallyMiddleware()])
            DecisionMerger._write_accepted_report(report_directory, accepted_report_data)

        if strategy == 'consensus' and conflict_report_data:
            conflicted_path = os.path.join(report_directory, "conflicted.bib")
            bibtexparser.write_file(file=conflicted_path,
                                    library=conflicted_library,
                                    parse_stack=[MonthAbbreviationMiddleware(),
                                                 AddEnclosingMiddleware(reuse_previous_enclosing=False,
                                                                        enclose_integers=False,
                                                                        default_enclosing="{"),
                                                 SortFieldsAlphabeticallyMiddleware()])
            DecisionMerger._write_conflict_report(report_directory, conflict_report_data, reviewers)
            DecisionMerger._write_conflict_matrix(report_directory, conflict_matrix, reviewers)
        
        logger.debug("Decision merge process completed.")


    @staticmethod
    def _load_reviewer_libraries(review_directory: str) -> Dict[str, Library]:
        """Loads all BibTeX files from a directory into a dictionary of Libraries."""
        reviewer_libs = {}
        for filename in os.listdir(review_directory):
            if filename.lower().endswith(".bib"):
                reviewer_name = os.path.splitext(filename)[0]
                filepath = os.path.join(review_directory, filename)
                try:
                    library = bibtexparser.parse_file(path=filepath,
                                                      parse_stack=None,
                                                      append_middleware=[LatexDecodingMiddleware()])
                    reviewer_libs[reviewer_name] = library
                    logger.debug(f"Loaded {len(library.entries)} entries for reviewer '{reviewer_name}'")
                except Exception as e:
                    logger.error(f"Could not parse file {filename}: {e}")
        return reviewer_libs

    @staticmethod
    def _write_accepted_report(report_dir: str, data: List[Dict]):
        """Writes the accepted papers CSV file."""
        filepath = os.path.join(report_dir, "accepted.csv")
        headers = ['key', 'title', 'author', 'year', 'doi', 'url']
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        logger.debug(f"Accepted papers report written to {filepath}")

    @staticmethod
    def _write_conflict_report(report_dir: str, data: List[Dict], reviewers: List[str]):
        """Writes the conflict report CSV file."""
        filepath = os.path.join(report_dir, "conflicts.csv")
        headers = ['key', 'title', 'author', 'year', 'doi', 'url'] + reviewers
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        logger.debug(f"Conflict report written to {filepath}")

    @staticmethod
    def _write_conflict_matrix(report_dir: str, matrix: Dict, reviewers: List[str]):
        """Writes the conflict matrix CSV file with accept/total format."""
        filepath = os.path.join(report_dir, "conflict_matrix.csv")
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([''] + reviewers) # Header row
            for r1 in reviewers:
                row = [r1]
                for r2 in reviewers:
                    if r1 == r2:
                        row.append('0 / 0')  # Diagonal: no self-conflicts
                    else:
                        accepts = matrix[r1][r2]['accepts']
                        total = matrix[r1][r2]['total']
                        row.append(f'{accepts} / {total}')
                writer.writerow(row)
        logger.debug(f"Conflict matrix written to {filepath}")
