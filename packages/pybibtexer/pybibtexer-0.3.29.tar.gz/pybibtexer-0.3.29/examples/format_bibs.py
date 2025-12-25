import os
from typing import Any

from local_config import LOCAL_OPTIONS
from pyadvtools import delete_python_cache

from pybibtexer.tools import (
    format_bib_to_save_mode_by_entry_type,
    generate_standard_publisher_abbr_options_dict,
    generate_statistic_information,
)


class FormatAllConferenceOrJournalPapers:
    def __init__(self, path_storage: str, path_output: str) -> None:
        self.path_storage = path_storage
        self.path_output = path_output

    def run(self, options: dict[str, Any]) -> None:
        publisher_abbr_dict = generate_standard_publisher_abbr_options_dict(self.path_storage, options)
        for publisher in publisher_abbr_dict:
            for abbr_standard in publisher_abbr_dict[publisher]:
                new_options = publisher_abbr_dict[publisher][abbr_standard]
                path_storage = os.path.join(self.path_storage, os.path.join(publisher.lower(), abbr_standard))
                path_output = os.path.join(self.path_output, os.path.join(publisher.lower(), abbr_standard))

                print(f"Format and save `{publisher}-{abbr_standard}` ...")
                format_bib_to_save_mode_by_entry_type(abbr_standard, path_output, path_storage, options=new_options)
                generate_statistic_information(path_output)
                print("Successful.\n")


if __name__ == "__main__":
    options: dict[str, Any] = {}
    options = {
        "include_publisher_list": [],
        "include_abbr_list": [],
        "exclude_publisher_list": [],
        "exclude_abbr_list": [],
    }
    options["full_json_c"] = LOCAL_OPTIONS["full_json_c"]
    options["full_json_j"] = LOCAL_OPTIONS["full_json_j"]

    for i, j in zip(["Journals", "Conferences"], ["Journals", "Conferences"], strict=True):
        path_storage = os.path.join(LOCAL_OPTIONS["path_spidered_bibs"], i)
        path_output = os.path.join(LOCAL_OPTIONS["path_output"], os.path.join("Format_Local_All", j))
        FormatAllConferenceOrJournalPapers(path_storage, path_output).run(options)

    # delete caches
    delete_python_cache(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
