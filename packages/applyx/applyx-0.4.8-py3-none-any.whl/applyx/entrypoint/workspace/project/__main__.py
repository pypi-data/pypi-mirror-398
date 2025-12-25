# coding=utf-8

import os
import sys

from applyx.command.base import Manager
import project


if __name__ == '__main__':
    if sys.version_info < (3, 10):
        print('Python 3.10+ is required')
        sys.exit(0)

    os.environ.setdefault('PYTHONBREAKPOINT', 'ipdb.set_trace')

    # monkey = import_module('gevent.monkey')
    # monkey.patch_all()

    Manager(project).run()
