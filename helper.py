# Author: charlessodre
# Github: https://github.com/charlessodre/
# Create: 2019/07
# Info: Miscellaneous support functions

# import necessary packages
import os
import shutil
import glob
import time
from PIL import Image
from collections import deque


def rename(name, newname):
    """
    Rename a file or directory.
    :param name:
    :param newname:
        """
    os.rename(name, newname)


def file_exists(path):
    """
    Test whether a file exists ou whether path is file.
    :param path: path
    :return: Returns True whether file exists ou False whether file not exists.
    """
    return os.path.isfile(path)


def path_exists(path):
    """
    Test whether a path exists.
    :param path: path
    :return: Returns False for broken symbolic links
    """
    return os.path.exists(path)


def move_file(source_path, dest_path, remove=True):
    """
    :param str source_path: path source files.
    :param str dest_path: path destiny files.
    :param remove: remove file source
    :return:
    """
    file_copy(source_path, dest_path)
    if remove:
        remove_file(source_path)


def remove_file(path):
    """
    Remove file
    :param path: file path

    """
    os.remove(path)


def path_join(path, paths):
    """
    Join two (or more) paths.
    :param path:
    :param paths:
    :return: string join  paths
    """
    return os.path.join(path, paths)


def read_file(file_name, mode='r'):
    """
    read content file and return list
    :param str file_name: name file.
    :param str mode: mode open file.
    :return list with content of file
    mode options:

    r - Open for reading plain text
    w - Open for writing plain text
    a - Open an existing file for appending plain text
    rb - Open for reading binary data
    wb -Open for writing binary data

    """

    with open(file_name, mode) as f:
        content = f.readlines()
    content = [x.strip() for x in content]

    return content


def read_last_lines_file(file_name, n_lines, mode='r'):
    """
    read content file and return list
    :param str file_name: name file.
    :param int n_lines: n_lines number lines returned
    :param str mode: mode open file.
    :return list with content of file
    mode options:

    r - Open for reading plain text
    w - Open for writing plain text
    a - Open an existing file for appending plain text
    rb - Open for reading binary data
    wb -Open for writing binary data

    """

    with open(file_name, mode) as f:
        content = deque(f, n_lines)
    content = [x.strip() for x in content]

    return content


def save_list_to_file(file_name, content_list, mode='a'):
    """
           save content file
           :param str file_name: name file.
           :param str content_list: content list
           :param str mode: mode write file.
           :return list with content of file
           mode options:

            r - Open for reading plain text
            w - Open for writing plain text
            a - Open an existing file for appending plain text
            rb - Open for reading binary data
            wb -Open for writing binary data

            """
    save_file(file_name, ['{}\n'.format(l) for l in content_list], mode)


def save_file(file_name, content, mode='a'):
    """
           save content file
           :param str file_name: name file.
           :param str content: file content
           :param str mode: mode write file.
           :return list with content of file
           mode options:

            r - Open for reading plain text
            w - Open for writing plain text
            a - Open an existing file for appending plain text
            rb - Open for reading binary data
            wb -Open for writing binary data

            """

    with open(file_name, mode) as f:
        f.writelines(content)
        f.close()


def remove_dir(dir_path):
    """
    Remove directory and all content
    :param str dir_path: path dir

    """
    shutil.rmtree(dir_path)


def delete_files(files_path, extension_file='*'):
    """
    Delete files by extension
    :param str files_path: path where are files.
    :param str extension_file: extension files.
    """
    files = get_files_all_dirs(files_path, extension_file)
    for file in files:
        os.remove(file)


def make_dirs(path, recursive=False):
    """
    Create directories if not exists.
    :param str path: directory path that will be create..
    :param bool recursive: indicate whether will be created  directories tree.
    """
    if not os.path.exists(path):
        if recursive:
            os.makedirs(path)
        else:
            os.mkdir(path)


def get_files_dir(dir_path, extension_file='*'):
    """

    :param dir_path: directory path
    :param extension_file:  extension files.
    :return files list:
    """
    return glob.glob(os.path.join(dir_path, extension_file))


def get_files_all_dirs(files_path, extension_file='*'):
    """
    Return all files in directories.
    :param str files_path: path where are files.
    :param str extension_file: extension files.
    :return files list
    """
    list_files = []

    for root, dirs, files in os.walk(files_path):
        for file in glob.glob(os.path.join(root, extension_file)):
            list_files.append(file)
    return list_files


def move(source_path, dest_path):
    """
    Move file
    :param str source_path: path source files.
    :param str dest_path: path destiny files.
    """
    shutil.move(source_path, dest_path)


def file_copy(source_path, dest_path):
    """
    Copy file
    :param str source_path: path source files.
    :param str dest_path: path destiny files.
    """
    shutil.copy(source_path, dest_path)


def get_current_hour():
    """
    Return current hour.
    :return str current hour
    """
    return time.strftime("%H:%M:%S")


def format_seconds_hhmmss(seconds):
    """
     Format seconds to hh:mm:ss.
    :param float seconds: seconds.
    :return str second format

    """
    return time.strftime('%H:%M:%S', time.gmtime(seconds))


def resize_image(image, width, height=None):
    """
    Move file
    :param str image: path image to resize.
    :param int width: width size in pixels.
    :param int height: height size in pixels.
    :return Image: image resized
    """
    img = Image.open(image)

    if height is None:
        wpercent = (width / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img_resized = img.resize((width, hsize), Image.ANTIALIAS)

    else:
        img_resized = img.resize((width, height), Image.ANTIALIAS)

    return img_resized


def get_current_hour_str():
    """
    Get string of current hour in format hh:mm:ss
    :return: Return current hour in format hh:mm:ss
    """
    return time.strftime("%H:%M:%S")


def get_current_date_str():
    """
    Get string of current date in format d/M/Y
    :return: Return current date in format d/M/Y
    """
    return time.strftime("%d/%m/%Y")


def get_current_date_hour_str():
    """
       Get string of current date in format d/M/Y hh:mm:ss
       :return: Return current date in format d/M/Y hh:mm:ss
       """
    return time.strftime("%d/%m/%Y %H:%M:%S")


def get_hour_str():
    """
    Get string of current hour in format H
    :return: Return current hour in format H
    """
    return time.strftime("%H")


def get_current_number_weekday():
    """
    Get number of current number weekday  [0 (Sunday), 1 (Monday) ... 6 (Saturday)].
    :return: Return current number weekday  [0 (Sunday), 1 (Monday) ... 6 (Saturday)].
    """
    return int(time.strftime("%w"))


def set_sleep(seconds):
    """
    Wait some seconds
    :param seconds:
    """
    time.sleep(seconds)


def change_decimal_separator_BR(string):
    if ',' in string:
        string = str(string).replace(',', 'v')
        string = string.replace('.', ',')
        string = string.replace('v', '.')

    return string
