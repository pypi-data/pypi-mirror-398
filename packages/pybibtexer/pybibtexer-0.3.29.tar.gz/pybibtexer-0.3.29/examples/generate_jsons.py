from pybibtexer.scripts import run_generate_jsons

from .local_config import LOCAL_OPTIONS

if __name__ == "__main__":
    default_full_json_c = "pybibtexer/data/templates/abbr_full/conferences.json"
    default_full_json_j = "pybibtexer/data/templates/abbr_full/journals.json"
    full_biblatex = LOCAL_OPTIONS["zotero_biblatex"]
    user_full_json_c = LOCAL_OPTIONS["full_json_c"]
    user_full_json_j = LOCAL_OPTIONS["full_json_j"]

    # Create instance and run the process
    run_generate_jsons(
        default_full_json_c, default_full_json_j, full_biblatex, user_full_json_c, user_full_json_j, merge_json=True
    )
