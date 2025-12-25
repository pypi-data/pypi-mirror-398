import os


def update_path(path_input: str):
    return os.path.expandvars(os.path.expanduser(path_input))


LOCAL_OPTIONS = {
    "full_json_c": update_path(os.path.join("", "conferences.json")),
    "full_json_j": update_path(os.path.join("", "journals.json")),
    "zotero_biblatex": update_path(""),
    "zotero_bibtex": update_path(""),
    "path_spidered_bibs": update_path(""),
    "path_spidering_bibs": update_path(""),
    "path_input": update_path(""),
}
