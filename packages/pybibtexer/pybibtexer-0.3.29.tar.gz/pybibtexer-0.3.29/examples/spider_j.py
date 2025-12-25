import os
from typing import Any

from local_config import LOCAL_OPTIONS
from pyadvtools import delete_python_cache

from pybibtexer.tools import CheckDeleteFormatMoveSpideredBibs

if __name__ == "__main__":
    options: dict[str, Any] = {}
    options = {
        # url
        "check_duplicate_url": True,
        "delete_duplicate_url": True,
        "iterate_check_duplicate_url": False,
        # bib
        "format_bib": True,
        "write_bib": True,
        "check_duplicate_bib": True,
        "delete_duplicate_bib": True,
        "move_bib": False,
        # include and exclude
        "include_publisher_list": ["IEEE"],
        "include_abbr_list": [],
        "exclude_publisher_list": [],
        "exclude_abbr_list": [],
        # for ieee
        "early_access": True,
    }
    options["full_json_c"] = LOCAL_OPTIONS["full_json_c"]
    options["full_json_j"] = LOCAL_OPTIONS["full_json_j"]

    if options["early_access"]:
        path_storage = os.path.join(LOCAL_OPTIONS["path_spidering_bibs"], "spider_j_e")
    else:
        path_storage = os.path.join(LOCAL_OPTIONS["path_spidering_bibs"], "spider_j")
    path_shutil = os.path.join(LOCAL_OPTIONS["path_spidered_bibs"], "Journals")

    CheckDeleteFormatMoveSpideredBibs(path_storage, path_shutil, options).check_delete_format_move()
    delete_python_cache(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
