# -*- coding: utf-8 -*-
"""
Helpers for file handling, e.g. copy the actual py-File after
adding the actual date-time and copy it to a directory


Created on Thu Feb  1 16:18:03 2024

@author: atakan
"""
import os
import shutil
import datetime

# print(__file__)


def copy_script_add_date(file_name_end, source_file, directory):
    """
    File handling, copy the actual py-File after
    adding the actual date-time and copy it to a directory which is also named
    date-time - file_name_end
    return the date-time for further usage

    Parameters
    ----------
    file_name_end : string
        the file name to be added to the date, also for the directory name.
    source_file : string
        The source file to copy (from __file__).
    directory : string
        The directory to copy to.

    Returns
    -------
    directory : String
        The new directory name and the file name(s) without extension.

    """
    py_name = source_file.rsplit("\\", maxsplit=1)[-1]
    access = 0o777
    current_date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")

    output_folder = f"{current_date}-{file_name_end}"
    
    directory = os.path.join(directory,output_folder)
    os.makedirs(directory, access)
    os.chdir(directory)
    
    destination_file = os.path.join(directory, current_date + py_name)
    shutil.copy(__file__, destination_file)
    return os.path.join(directory,output_folder)


if __name__ == "__main__":
    
    from carbatpy import _RESULTS_DIR
    END_NAME = "test"
    print(copy_script_add_date(END_NAME, __file__, _RESULTS_DIR))
