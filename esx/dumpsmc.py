#!/usr/bin/env python3
# coding=utf-8

# SPDX-FileCopyrightText: © 2014-2021 David Parsons
# SPDX-License-Identifier: MIT

"""
vSMC Header Structure
=====================
Offset  Length  Struct Type Description
----------------------------------------
0x00/00 0x08/08 Q      ptr  Offset to key table
0x08/08 0x04/4  I      int  Number of private keys
0x0C/12 0x04/4  I      int  Number of public keys

vSMC Key Data Structure
Offset  Length  Struct Type Description
----------------------------------------
0x00/00 0x04/04 4s     int  Key name (byte reversed e.g. #KEY is YEK#)
0x04/04 0x01/01 B      byte Length of returned data
0x05/05 0x04/04 4s     int  Data type (byte reversed e.g. ui32 is 23iu)
0x09/09 0x01/01 B      byte Flag R/W
0x0A/10 0x06/06 6x     byte Padding
0x10/16 0x08/08 Q      ptr  Internal VMware routine
0x18/24 0x30/48 48B    byte Data

The internal VMware routines point to 4 variants:
AppleSMCHandleDefault
AppleSMCHandleNTOK
AppleSMCHandleNumKeys
AppleSMCHandleOSK
"""

import mmap
import os.path
import struct
import sys

# Constants for header and key access
HDR_PACK = '=QII'
HDR_LENGTH = 16
KEY_PACK = '=4sB4sB6xQ'
KEY_LENGTH = 24
DATA_LENGTH = 48
ROW_LENGTH = KEY_LENGTH + DATA_LENGTH

# Setup hex string for vSMC headers
# These are the private and public key counts
SMC_HEADER_V0 = b'\xF2\x00\x00\x00\xF0\x00\x00\x00'
SMC_HEADER_V1 = b'\xB4\x01\x00\x00\xB0\x01\x00\x00'

# Keys we use
KEY_KEY = b'YEK#'
LKS_KEY = b'SKL+'
OSK0_KEY = b'0KSO'
OSK1_KEY = b'1KSO'

if sys.version_info < (3, 6):
    sys.stderr.write('You need Python 3.6 or later\n')
    sys.exit(1)


def bytetohex(data):
    return ''.join('{:02X}'.format(c) for c in data).lower()


def printhdr(offset, hdr):
    print(f'File Offset : 0x{offset:08x}')
    print(f'Keys Offset : 0x{hdr[0]:08x}')
    print(f'Private Keys: 0x{hdr[1]:04x}/{hdr[1]}')
    print(f'Public Keys : 0x{hdr[2]:04x}/{hdr[2]}')
    return


def printkey(offset, smc_key, smc_data):
    # Format smc_type as cannot use \ in f-strings
    smc_type = smc_key[2][::-1].replace(b'\x00', b' ').decode('UTF-8')
    print(f'0x{offset:08x} '
          f'{smc_key[0][::-1].decode("UTF-8")} '
          f'{smc_key[1]:02d}  '
          f'{smc_type} '
          f'0x{smc_key[3]:02x} '
          f'0x{smc_key[4]:08x} '
          f'{bytetohex(smc_data)}')
    return


def gethdr(vmx, offset):
    # Read header into struct
    vmx.seek(offset)
    hdr = struct.unpack(HDR_PACK, vmx.read(HDR_LENGTH))
    vmx.seek(offset)
    return hdr


def getkey(vmx, offset):
    # Read key into struct
    vmx.seek(offset)
    smc_key = struct.unpack(KEY_PACK, vmx.read(KEY_LENGTH))
    vmx.seek(offset)
    return smc_key


def getdata(vmx, offset, smc_key):
    # Read data for key
    vmx.seek(offset + KEY_LENGTH)
    smc_data = vmx.read(smc_key[1])
    vmx.seek(offset)
    return smc_data


def dumpkeys(vmx, offset, count):

    print('Offset     Name Len Type Flag FuncPtr    Data')
    print('-------    ---- --- ---- ---- -------    ----')

    for i in range(count):

        # Read key into struct str and data byte str
        smc_key = getkey(vmx, offset)
        smc_data = getdata(vmx, offset, smc_key)

        # Dump entry
        printkey(offset, smc_key, smc_data)
        offset = offset + ROW_LENGTH

    return


def dumpsmc(name):

    with open(name, 'r+b') as f:

        # Memory map file
        vmx = mmap.mmap(f.fileno(), 0)

        print('File: ' + name)

        # Find the vSMC headers
        smc0_header = vmx.find(SMC_HEADER_V0) - 8
        smc1_header = vmx.find(SMC_HEADER_V1) - 8

        # Find '#KEY' keys
        smc0_key = vmx.find(KEY_KEY, smc0_header)
        smc1_key = vmx.find(KEY_KEY, smc1_header)

        # Dump first vSMC table
        print('\nappleSMCTableV0 (smc.version = "0")')
        hdr = gethdr(vmx, smc0_header)
        printhdr(smc0_header, hdr)
        dumpkeys(vmx, smc0_key, hdr[1])

        # Dump second vSMC table
        print('\nappleSMCTableV1 (smc.version = "1")')
        hdr = gethdr(vmx, smc1_header)
        printhdr(smc1_header, hdr)
        dumpkeys(vmx, smc1_key, hdr[1])

        # Tidy up
        vmx.close()
        f.close()

    return


def main():
    print('dumpsmc')
    print('-------')

    if len(sys.argv) >= 2:
        vmx_path = sys.argv[1]
    else:
        print('Please pass file name!')
        return

    if os.path.exists(vmx_path):
        dumpsmc(vmx_path)
    else:
        print('Cannot find file ' + vmx_path)
    return


if __name__ == '__main__':
    main()
