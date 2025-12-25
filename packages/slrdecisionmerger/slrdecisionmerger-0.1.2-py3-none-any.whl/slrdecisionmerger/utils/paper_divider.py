import random
import os
import shutil
from typing import List, Dict

import bibtexparser
from bibtexparser import Library
from bibtexparser.middlewares import MonthAbbreviationMiddleware, AddEnclosingMiddleware, \
    SortFieldsAlphabeticallyMiddleware

from .. import logger


class PaperDivider:
    """
    Handles the division of papers among reviewers with balanced assignment.
    """

    def __init__(self, reviewers: List[str], reviewers_per: int):
        """
        Initialize the PaperDivider.

        :param reviewers: List of reviewer names
        :param reviewers_per: Number of reviewers that should review each paper
        """
        self.reviewers = reviewers
        self.reviewers_per = reviewers_per
        self.reviewer_counters: Dict[str, int] = {reviewer: 0 for reviewer in reviewers}
        self.current_libraries: Dict[str, Library] = {reviewer: Library() for reviewer in reviewers}
        self.file_counters: Dict[str, int] = {reviewer: 1 for reviewer in reviewers}
        logger.debug(f"PaperDivider initialized for {len(self.reviewers)} reviewers, with {self.reviewers_per} reviewers per paper.")

    def divide_papers(self, library: Library, division_directory: str) -> None:
        """
        Divide papers among reviewers with balanced assignment.

        :param library: Library containing all papers to be divided
        :param division_directory: Directory where reviewer directories will be created
        """
        # Create reviewer directories
        for reviewer in self.reviewers:
            reviewer_dir = os.path.join(division_directory, reviewer)
            os.makedirs(reviewer_dir, exist_ok=True)
        logger.debug(f"Created reviewer directories in {division_directory}")

        # For each paper, assign to reviewers with lowest counts
        for i, entry in enumerate(library.entries):
            # Find reviewers with minimum count
            min_count = min(self.reviewer_counters.values())
            candidates = [r for r, count in self.reviewer_counters.items() if count == min_count]
            
            # Randomly select from candidates
            selected_reviewers = random.sample(candidates, min(self.reviewers_per, len(candidates)))
            
            # If we need more reviewers, get from next lowest count
            while len(selected_reviewers) < self.reviewers_per:
                remaining_needed = self.reviewers_per - len(selected_reviewers)
                available = [r for r in self.reviewers if r not in selected_reviewers]
                next_min = min(self.reviewer_counters[r] for r in available)
                next_candidates = [r for r in available if self.reviewer_counters[r] == next_min]
                additional = random.sample(next_candidates, min(remaining_needed, len(next_candidates)))
                selected_reviewers.extend(additional)

            # Assign paper to selected reviewers
            logger.debug(f"Assigning paper '{entry.key}' to: {', '.join(selected_reviewers)}")
            for reviewer in selected_reviewers:
                self.current_libraries[reviewer].add(entry)
                self.reviewer_counters[reviewer] += 1
                
                # Save if reached 500 papers
                if len(self.current_libraries[reviewer].entries) >= 500:
                    self._save_batch(reviewer=reviewer,
                                     division_directory=division_directory)

        # Save remaining papers for all reviewers
        for reviewer in self.reviewers:
            if self.current_libraries[reviewer]:
                self._save_batch(reviewer=reviewer,
                                 division_directory=division_directory)

        # Create final consolidated files
        self._create_final_files(division_directory)
        logger.debug("Paper division process completed. Final counts per reviewer:")
        for reviewer, count in self.reviewer_counters.items():
            logger.debug(f"  - {reviewer}: {count} papers")

    def _save_batch(self, reviewer: str, division_directory: str):
        """Save current batch of papers for a reviewer."""
        reviewer_dir = os.path.join(division_directory, reviewer)
        filename = f"batch_{self.file_counters[reviewer]:03d}.bib"
        filepath = os.path.join(reviewer_dir, filename)
        
        logger.debug(f"Saving batch file {filename} for {reviewer} with {len(self.current_libraries[reviewer].entries)} papers.")
        # Write entries as string
        bibtexparser.write_file(file=filepath,
                                library=self.current_libraries[reviewer],
                                parse_stack=[MonthAbbreviationMiddleware(),
                                             AddEnclosingMiddleware(reuse_previous_enclosing=False,
                                                                    enclose_integers=False,
                                                                    default_enclosing="{"),
                                             SortFieldsAlphabeticallyMiddleware()])
        
        # Reset current library and increment file counter
        self.current_libraries[reviewer] = Library()
        self.file_counters[reviewer] += 1

    def _create_final_files(self, division_directory: str):
        """Create final consolidated BibTeX files for each reviewer."""
        jabref_meta = """
@Comment{jabref-meta: databaseType:bibtex;}

@Comment{jabref-meta: grouping:
0 AllEntriesGroup:;
1 StaticGroup:relevant\;0\;0\;0x008000ff\;MDI_CHECKBOX_MARKED_OUTLINE\;\;;
1 StaticGroup:non-relevant\;2\;1\;0xff0000ff\;SKULL_CROSSBONES_OUTLINE\;\;;
2 StaticGroup:NOT_ENGLISH\;0\;1\;0x0000ffff\;TEXT_TO_SPEECH_OFF\;\;;
2 StaticGroup:NO_PEER_REV\;0\;0\;0xe6804dff\;MDI_ACCOUNT_MULTIPLE_MINUS\;\;;
2 StaticGroup:OFF_TOPIC\;0\;1\;0xff00ffff\;MDI_ALERT\;\;;
2 StaticGroup:OUT_YEARS\;0\;0\;0x000000ff\;CLOCK_TIME_ELEVEN\;\;;
2 StaticGroup:MAYBE\;0\;1\;0xffff00ff\;SKULL_CROSSBONES_OUTLINE\;\;;
}
"""
        for reviewer in self.reviewers:
            reviewer_dir = os.path.join(division_directory, reviewer)
            final_file = os.path.join(division_directory, f"{reviewer}.bib")
            
            logger.debug(f"Creating final consolidated file for {reviewer} at {final_file}")
            # Concatenate all batch files
            with open(final_file, 'wb') as outfile:
                # Read all batch files in order
                batch_files = sorted([f for f in os.listdir(reviewer_dir) if f.startswith('batch_')])
                for i, batch_file in enumerate(batch_files):
                    batch_path = os.path.join(reviewer_dir, batch_file)
                    with open(batch_path, 'rb') as infile:
                        outfile.write(infile.read())
                    
                    # Add a newline between concatenated files
                    if i < len(batch_files) - 1:
                        outfile.write(b'\n\n')
                
                # Add JabRef metadata
                outfile.write(jabref_meta.encode('utf-8'))
            
            logger.debug(f"Removing temporary directory: {reviewer_dir}")
            # Remove the reviewer directory
            shutil.rmtree(reviewer_dir)