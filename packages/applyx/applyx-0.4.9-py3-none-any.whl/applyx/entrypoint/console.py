# coding=utf-8

import os
import sys
import shutil
import argparse

import applyx


def create_workspace(args: argparse.Namespace):
    workspace_dir = os.path.join(os.getcwd(), args.name)
    if os.path.exists(workspace_dir):
        print(f'workspace directory {args.name} already exists')
        return

    template_dir = os.path.join(applyx.__path__[0], 'entrypoint/workspace')
    shutil.copytree(template_dir, workspace_dir)
    print('workspace created')


def main():
    parser = argparse.ArgumentParser(description=f"help for applyx")
    parser.add_argument("--version", action="version", version=applyx.__version__)
    subparser = parser.add_subparsers(dest="cmd")

    # create
    create_parser = subparser.add_parser("create", help="create workspace")
    create_parser.add_argument("-n", "--name", type=str, help="workspace name")

    argv = sys.argv[1:] if len(sys.argv[1:]) else ["-h"]
    args = parser.parse_args(argv)
    cmd = args.__dict__.pop("cmd")

    if cmd == "create":
        create_workspace(args)
