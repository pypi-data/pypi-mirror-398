'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-12-06 14:08:50 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2024-12-06 14:08:50 +0100
FilePath     : rename_files_by_keyword.py
Description  : 

Copyright (c) 2024 by everyone, All Rights Reserved. 
'''

import os
from typing import Optional


def _rename_files_by_keyword(directory_path: str, old_keyword: str, new_keyword: str) -> None:
    """Rename files in a single directory based on the old and new keyword."""
    for filename in os.listdir(directory_path):
        if old_keyword in filename:
            old_filepath = os.path.join(directory_path, filename)
            new_filename = filename.replace(old_keyword, new_keyword)
            new_filepath = os.path.join(directory_path, new_filename)

            try:
                os.rename(old_filepath, new_filepath)
                print(f"Renamed: {filename} -> {new_filename}")
            except Exception as e:
                print(f"Could not rename {filename} to {new_filename}: {e}")


def rename_files_by_keyword(directory_path: str, old_keyword: str, new_keyword: str, walk_subDirs: Optional[bool] = False) -> None:
    """Rename files in the directory and optionally in sub-directories based on the old and new keyword."""
    if walk_subDirs:
        for dirpath, _, _ in os.walk(directory_path):
            _rename_files_by_keyword(directory_path=dirpath, old_keyword=old_keyword, new_keyword=new_keyword)
    else:
        _rename_files_by_keyword(directory_path, old_keyword, new_keyword)


if __name__ == '__main__':

    rename_dicts = {
        "_preselected_reduced_sw2": "",
        "_PVFit_MassConsJpsi": "",
        "_826.0_861.0": "0",
        "_861.0_896.0": "1",
        "_896.0_931.0": "2",
        "_931.0_966.0": "3",
        "_-1.0_1.0": "0",
    }

    directory_path = "."

    for old_keyword, new_keyword in rename_dicts.items():
        rename_files_by_keyword(directory_path, old_keyword, new_keyword)
