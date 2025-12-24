#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from nextnextping.grammer.ttl_parser_worker import TtlPaserWolker
from nextnextping.grammer.version import VERSION


class MyTtlPaserWolker(TtlPaserWolker):
    """ my TtlPaserWolker  """
    def __init__(self):
        super().__init__()

    def setLog(self, strvar):
        """ log setting """
        print(strvar, end="")


HELP = """Usage: pyttl [-c][-r][-h][--check][--result][--hrlp] FILE [OPTION]...

Runs ttl macro
positional arguments:
  FILE               ttl macro filename

options:
 -c, --check         don't make any changes; instead, try to predict some of the changes that may occur
 -r, --result        If this flag is set, an error occurs when result==0.
 -h, --help          This test.
"""


def pyttl(argv) -> TtlPaserWolker:
    ttlPaserWolker = None
    next = 1
    if len(argv) <= next:
        print(HELP)
        return None

    checkmode = False
    ignore_result = True
    flag = True
    while flag:
        flag = False
        if (argv[next] == "--check") or (argv[next] == "-c"):
            checkmode = True
            next = next + 1
            flag = True
        elif (argv[next] == "--result") or (argv[next] == "-r"):
            ignore_result = False
            next = next + 1
            flag = True
        elif (argv[next] == "-h") or (argv[next] == "--help"):
            print(HELP)
            return None
        elif (argv[next] == "-v") or (argv[next] == "--version"):
            print(f"pyttl {VERSION}.1")
            return None
        if len(argv) <= next:
            print(HELP)
            return None

    filename = argv[next]
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"filename:{filename} not found\n")

    try:
        ttlPaserWolker = MyTtlPaserWolker()
        if not checkmode:
            # this is not check mode
            ttlPaserWolker.execute(filename, argv[next:], ignore_result=ignore_result)
        else:
            # this is check mode
            ttlPaserWolker.include_only(filename)
    finally:
        if ttlPaserWolker is not None:
            # No matter what, the worker will be killed.
            ttlPaserWolker.stop()
    return ttlPaserWolker


def main():
    pyttl(sys.argv)


if __name__ == "__main__":
    pyttl()
    #
