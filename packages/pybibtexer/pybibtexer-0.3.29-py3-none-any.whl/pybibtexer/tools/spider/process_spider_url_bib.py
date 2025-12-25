import os
from typing import Any

from pyadvtools import standard_path

from ..experiments_base import generate_standard_publisher_abbr_options_dict
from ..spider.process_spider_bib import ProcessSpiderBib
from ..spider.process_spider_url import ProcessSpiderUrl


class CheckDeleteFormatMoveSpideredBibs:
    """Experiment for check.

    Args:
        path_storage (str): path to storage
        path_shutil (str): path to shutil
        options (dict[str, Any]): options for check, delete, format

    Attributes:
        path_storage (str): path to storage
        path_shutil (str): path to shutil
        publisher_abbr_dict (dict[str, dict[str, Any]]): publisher abbreviation options dict
    """

    def __init__(self, path_storage: str, path_shutil: str, options: dict[str, Any]) -> None:
        self.path_storage = standard_path(path_storage)
        self.path_shutil = standard_path(path_shutil)
        self.publisher_abbr_dict = generate_standard_publisher_abbr_options_dict(self.path_storage, options)

    def check_delete_format_move(self) -> None:
        publisher_abbr_dict = self.publisher_abbr_dict
        for publisher in self.publisher_abbr_dict:
            for abbr_standard in publisher_abbr_dict[publisher]:
                self._check_format_check_move(publisher, abbr_standard, publisher_abbr_dict[publisher][abbr_standard])

    def _check_format_check_move(self, publisher: str, abbr_standard: str, options: dict[str, Any]) -> None:
        path_abbr = os.path.join(self.path_storage, f"{publisher.lower()}/{abbr_standard}")

        # for urls
        if options.get("check_duplicate_url", False) is True:
            ddu = options.get("delete_duplicate_url", False)
            icdu = options.get("iterate_check_duplicate_url", False)
            for extension in [".txt", ".csv"]:
                ProcessSpiderUrl(path_abbr, abbr_standard).check_spider_url("url", extension, ddu, icdu)

        # for bibs
        if options.get("format_bib", False) is True:
            wb = options.get("write_bib", False)
            ProcessSpiderBib(path_abbr, abbr_standard).format_spider_bib(wb)

        if options.get("check_duplicate_bib", False) is True:
            ddb = options.get("delete_duplicate_bib", False)
            ProcessSpiderBib(path_abbr, abbr_standard).check_spider_bib(ddb)

        if options.get("move_bib", False) is True:
            ps = os.path.join(self.path_shutil, publisher.lower())
            ProcessSpiderBib(path_abbr, abbr_standard).move_spider_bib(ps)

        # for early access
        if options.get("early_access", False):
            ProcessSpiderBib(path_abbr, abbr_standard).simplify_early_access()
        return None
