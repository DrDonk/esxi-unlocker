#!/usr/bin/env python3
# coding=utf-8

# SPDX-FileCopyrightText: © 2014-2021 David Parsons
# SPDX-License-Identifier: MIT

import os
import sys

# These are the private and public key counts
APPLESMC = b'applesmc'
VMKERNEL = b'vmkernel'


if sys.version_info < (3, 6):
    sys.stderr.write('You need Python 3.6 or later\n')
    sys.exit(1)


def patchvmkctl(name):
    # Patch file
    print('smcPresent Patching: ' + name)
    f = open(name, 'r+b')

    # Read file into string variable
    vmkctl = f.read()
    applesmc = vmkctl.find(APPLESMC)
    f.seek(applesmc)
    f.write(VMKERNEL)

    # Tidy up
    f.flush()
    f.close()
    print('smcPresent Patched: ' + name)
    return


def main():
    print('patchvmkctl')
    print('-----------')

    if len(sys.argv) >= 2:
        filename = sys.argv[1]
    else:
        print('Please pass file name!')
        return

    if os.path.isfile(filename):
        patchvmkctl(filename)
    else:
        print('Cannot find file ' + filename)
    return


if __name__ == '__main__':
    main()
