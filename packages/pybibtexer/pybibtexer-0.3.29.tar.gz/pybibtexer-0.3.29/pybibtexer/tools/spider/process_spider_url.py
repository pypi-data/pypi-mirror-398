import os
import re

from pyadvtools import IterateSortDict, read_list, sort_int_str, write_list


class ProcessSpiderUrl:
    """Process spider URL.

    Args:
        path_abbr (str): path to abbreviation
        abbr_standard (str): abbreviation standard

    Attributes:
        path_abbr (str): path to abbreviation
        abbr_standard (str): abbreviation standard
    """

    def __init__(self, path_abbr, abbr_standard: str) -> None:
        self.path_abbr = os.path.expandvars(os.path.expanduser(path_abbr))
        self.abbr_standard = abbr_standard

    def check_spider_url(
        self,
        folder_start_swith: str = "url",
        extension: str = ".txt",
        write_flag: bool = False,
        iterate_check_url: bool = False,
    ) -> None:
        if os.path.exists(self.path_abbr):
            for i in [f for f in os.listdir(self.path_abbr) if f.startswith(folder_start_swith)]:
                ll = os.path.join(os.path.basename(self.path_abbr), i)
                print("*" * 5 + f" Check *{extension} .{os.sep}{ll}")
                self._check_delete(os.path.join(self.path_abbr, i), extension, write_flag, iterate_check_url)

    def _check_delete(
        self, path_storage: str, extension: str = ".txt", write_flag: bool = False, iterate_check_url: bool = False
    ) -> None:
        data_dict: dict[str, dict[str, list[str]]] = {}
        files = [f for f in os.listdir(path_storage) if f.endswith(extension)]
        for f in files:
            mch = re.match(r"([a-zA-Z]+)_([\w\-]+)", f)
            if mch:
                a, b = mch.groups()
                data_dict.setdefault(a, {}).setdefault(b, []).extend(read_list(f, "r", path_storage))

        for a in IterateSortDict(False).dict_update(data_dict):
            b_list = sort_int_str(list(data_dict[a].keys()))

            for b in b_list:
                new_temp_list: list[str] = []
                duplicate_dict: dict[str, list[str]] = {}
                for line in data_dict[a][b]:
                    line_flag = False
                    if iterate_check_url:
                        for bb in b_list[: b_list.index(b)]:
                            if line in data_dict[a][bb]:
                                duplicate_dict.setdefault(f"{a}_{b} and {a}_{bb}", []).append(line.strip())
                                line_flag = True
                                break

                    if (not line_flag) and (line not in new_temp_list):
                        new_temp_list.append(line)
                    elif line in new_temp_list:
                        print(f"Duplicate item {line.strip()} in {a}_{b}{extension}.\n")

                data_dict[a][b] = new_temp_list

                if duplicate_dict:
                    print(f"Duplicate items in {extension}:\n", duplicate_dict)

                if write_flag:
                    write_list(new_temp_list, f"{a}_{b}{extension}", "w", path_storage, False, True, True, True)
        return None
