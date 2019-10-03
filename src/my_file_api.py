# uncompyle6 version 3.2.5
# Python bytecode 2.7 (62211)
# Decompiled from: Python 3.5.2 (default, Nov 12 2018, 13:43:14) 
# [GCC 5.4.0 20160609]
# Embedded file name: /home/zongfu/workspace/remoteServ/zf.working/workspace/ssd_fp_feature/ssd_fp_192_hard22k_random28k_wi_night/my_file_api.py
# Compiled at: 2019-03-21 13:33:51
r"""Crop images accroding to the ROI

Author: ZF Hsieh
Date: 2/7/2019
Example usage:
    python blend_data_set.py \
        --data_dir=/home/user/dataset/trainset \
        --shuffle=True
"""
import os, re, json
from collections import defaultdict

def get_file_body_name(full_path):
    return os.path.splitext(os.path.basename(full_path))[0]


def get_file_list(data_dir_or_file_list):
    if os.path.isdir(data_dir_or_file_list):
        file_full_path_list = [ os.path.join(data_dir_or_file_list, x) for x in get_files(data_dir_or_file_list) ]
    else:
        file_full_path_list = reader(data_dir_or_file_list)
    return file_full_path_list


def write_json(content, full_path):
    with open(full_path, 'w') as (out_fd):
        json.dump(content, out_fd, indent=4)


def read_json(full_path):
    with open(full_path, 'r') as (read_file):
        data = json.load(read_file)
    return data


def load_json(data_dir_or_a_file):
    if os.path.isdir(data_dir_or_a_file):
        file_list = fapi.get_file_list(data_dir_or_a_file)
        res = defaultdict(dict)
        for each_path in file_list:
            if re.match('(.*)json', each_path, re.I):
                res_dict = fapi.read_json(each_path)
                f_name = fapi.get_file_body_name(each_path)
                res[f_name] = res_dict

        return res
    file_full_path = data_dir_or_a_file
    if re.match('(.*)json', file_full_path, re.I):
        return read_json(file_full_path)
    return
    return


def get_files(path):
    return [ x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x)) ]


def create_folder(x):
    if not os.path.exists(x):
        os.makedirs(x)


def get_subdir(path):
    return [ os.path.join(path, x) for x in os.listdir(path) if os.path.isdir(os.path.join(path, x)) ]


def explore_dir(path, out_list):
    subdirs = get_subdir(path)
    if len(subdirs) == 0:
        out_list.append(path)
        return
    for sub_dir in subdirs:
        explore_dir(sub_dir, out_list)


def get_dir_name(file_path):
    dir_name = os.path.basename(os.path.dirname(file_path))
    return dir_name


def writer(content, file_full_path):
    with open(file_full_path, 'w') as (f):
        for line in content:
            if isinstance(line, str):
                line = line.rstrip()
                f.write(line + '\n')
            else:
                f.write(line)


def reader(file_name):
    with open(file_name, 'r') as (f):
        content = f.readlines()
    return content


def search_and_replace_in_a_file(file_path, pattern, replacement):
    with open(file_path, 'r') as (f):
        filedata = f.read()
    filedata = search_and_replace(filedata, pattern, replacement)
    with open(file_path, 'w') as (f):
        f.write(filedata)


def search_and_replace(filedata, pattern, replacement):
    for i in range(len(pattern)):
        pat = pattern[i]
        repl = replacement[i]
        filedata = re.sub(pat, repl, filedata)

    return filedata


def convert_string_to_list(str_in):
    """
    input format:
        ["file1","file2","file3"] or
        "file1"
    """
    if '[' in str_in:
        str_in = str_in.replace('[', '')
    if ']' in str_in:
        str_in = str_in.replace(']', '')
    if '"' in str_in:
        str_in = str_in.replace('"', '')
    str_in = str_in.replace(' ', '')
    return str_in.split(',')


from shutil import copyfile

def file_copy(src, dst):
    copyfile(src, dst)


def show_stat(cnt, step):
    if cnt % step == 0:
        print ('completed: ', cnt)


from argparse import ArgumentParser
from functools import wraps
import inspect

def ioframe(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        parser = ArgumentParser()
        parser.add_argument('-in_dir', '--in_dir', default=[])
        parser.add_argument('-out_dir', '--out_dir', default=[])
        parser.add_argument('-in_path', '--in_path', default=[])
        parser.add_argument('-out_path', '--out_path', default=[])
        parser.add_argument('-ref_path', '--ref_path', default=[])
        pargs = parser.parse_args()
        in_path = pargs.in_path
        out_path = pargs.out_path
        ref_path = pargs.ref_path
        in_dir = pargs.in_dir
        out_dir = pargs.out_dir
        if 'out_path' in inspect.getfullargspec(func).args:
            kwargs['out_path'] = out_path
        if 'in_path' in inspect.getfullargspec(func).args:
            kwargs['in_path'] = in_path
        if 'in_dir' in inspect.getfullargspec(func).args:
            kwargs['in_dir'] = in_dir
        if 'out_dir' in inspect.getfullargspec(func).args:
            kwargs['out_dir'] = out_dir
        if 'ref_path' in inspect.getfullargspec(func).args:
            kwargs['ref_path'] = ref_path
        return func(*args, **kwargs)

    return wrapper


if __name__ == '__main__':
    sub_list = []
    explore_dir('./test', sub_list)
    print(sub_list)
# okay decompiling my_file_api.pyc
