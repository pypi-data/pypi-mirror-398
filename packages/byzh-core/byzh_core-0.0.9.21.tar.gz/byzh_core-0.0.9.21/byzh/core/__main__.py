import argparse

def b_zip():
    parser = argparse.ArgumentParser()
    parser.add_argument("dir_path")
    args = parser.parse_args()

    from .Barchive import b_archive_zip
    b_archive_zip(args.dir_path)

def b_dirtree():
    parser = argparse.ArgumentParser()
    parser.add_argument("dir_path")
    args = parser.parse_args()

    from . import B_os
    B_os.dir_tree(args.dir_path)
