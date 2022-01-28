#!/usr/bin/env python3
# coding=utf-8

# NOTE: This has been simplified for possible future port to Go

# SPDX-FileCopyrightText: © 2014-2021 David Parsons & Sam Bingner
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

import codecs
import mmap
import os
import struct
import sys


# Constants for header and key access
HDR_PACK = '=QII'
HDR_LENGTH = 16
KEY_PACK = '=4sB4sB6xQ'
KEY_LENGTH = 24

# Setup hex string for vSMC headers
# These are the private and public key counts
SMC_HEADER_V0 = b'\xF2\x00\x00\x00\xF0\x00\x00\x00'
SMC_HEADER_V1 = b'\xB4\x01\x00\x00\xB0\x01\x00\x00'

# Keys we use
KEY_KEY = b'YEK#'
LKS_KEY = b'SKL+'
OSK0_KEY = b'0KSO'
OSK1_KEY = b'1KSO'
KPPW_KEY = b'WPPK'

# Haiku
OSK0 = codecs.encode('bheuneqjbexolgurfrjbeqfthneqrqcy', 'rot_13').encode('UTF-8')
OSK1 = codecs.encode('rnfrqbagfgrny(p)NccyrPbzchgreVap', 'rot_13').encode('UTF-8')

# Hogwarts
KPPW = 'SpecialisRevelio'.encode('UTF-8')

# ELF Magic
ELF_MAGIC = b'\x7fELF'

if sys.version_info < (3, 6):
    sys.stderr.write('You need Python 3.6 or later\n')
    sys.exit(1)


def bytetohex(data):
    return ''.join('{:02X} '.format(c) for c in data)


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
          f'{smc_key[1]:03d} '
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


def setkey(vmx, offset, smc_key):
    # Write key from struct
    vmx.seek(offset)
    vmx.write(struct.pack(KEY_PACK, smc_key[0], smc_key[1], smc_key[2], smc_key[3], smc_key[4]))
    vmx.flush()
    vmx.seek(offset)
    return


def getdata(vmx, offset, smc_key):
    # Read data for key
    vmx.seek(offset + KEY_LENGTH)
    smc_data = vmx.read(smc_key[1])
    vmx.seek(offset)
    return smc_data


def setdata(vmx, offset, smc_data):
    # Write data for key
    vmx.seek(offset + KEY_LENGTH)
    vmx.write(smc_data)
    vmx.flush()
    vmx.seek(offset)
    return


def patchkppw(vmx, offset, data):
    # Get the KPPW key and data
    smc_key = getkey(vmx, offset)
    smc_data = getdata(vmx, offset, smc_key)
    key = smc_key[0][::-1].decode('UTF-8')
    print(f'{key} Key Before:')
    printkey(offset, smc_key, smc_data)

    # Set the data value
    setdata(vmx, offset, data)

    # Get patched KPPW key and data
    smc_key = getkey(vmx, offset)
    smc_data = getdata(vmx, offset, smc_key)
    print(f'{key} Key After:')
    printkey(offset, smc_key, smc_data)

    return


def patchosk(vmx, offset, ptr, data):
    # Get the OSK key and data
    smc_key = getkey(vmx, offset)
    smc_data = getdata(vmx, offset, smc_key)
    key = smc_key[0][::-1].decode('UTF-8')
    smc_osk_ptr = smc_key[4]
    print(f'{key} Key Before:')
    printkey(offset, smc_key, smc_data)

    # AppleSMCHandleOSK replaced with AppleSMCHandleDefault
    temp = list(smc_key)
    temp[4] = ptr
    smc_key = tuple(temp)
    setkey(vmx, offset, smc_key)

    # Set the data value
    setdata(vmx, offset, data)

    # Get patched OSK key and data
    smc_key = getkey(vmx, offset)
    smc_data = getdata(vmx, offset, smc_key)
    print(f'{key} Key After:')
    printkey(offset, smc_key, smc_data)

    return smc_osk_ptr


def patchsmc(name):
    with open(name, 'r+b') as f:
        print('File: ' + name + '\n')

        # Memory map file
        vmx = mmap.mmap(f.fileno(), 0)

        # Find the vSMC headers
        smc0_header = vmx.find(SMC_HEADER_V0) - 8
        smc1_header = vmx.find(SMC_HEADER_V1) - 8

        # Find '#KEY' keys
        smc0_key = vmx.find(KEY_KEY)
        smc1_key = vmx.rfind(KEY_KEY)

        # Find '+LKS' key
        smc0_lks = vmx.find(LKS_KEY, smc0_key)
        smc1_lks = vmx.find(LKS_KEY, smc1_key)

        # Find 'OSK0' keys
        smc0_osk0 = vmx.find(OSK0_KEY, smc0_key)
        smc1_osk0 = vmx.find(OSK0_KEY, smc1_key)

        # Find 'OSK1' keys
        smc0_osk1 = vmx.find(OSK1_KEY, smc0_key)
        smc1_osk1 = vmx.find(OSK1_KEY, smc1_key)

        # Find 'KPPW' key
        smc1_kppw = vmx.find(KPPW_KEY, smc1_key)

        # Check to see if we have already patched the vSMC in the file
        osk0 = getdata(vmx, smc1_osk0, getkey(vmx, smc1_osk0))
        osk1 = getdata(vmx, smc1_osk1, getkey(vmx, smc1_osk1))
        kppw = getdata(vmx, smc1_kppw, getkey(vmx, smc1_kppw))

        if osk0 == OSK0 and osk1 == OSK1 and kppw == KPPW:
            print(f'File {name} is already patched')
            return

        # Patch first vSMC table
        print('\nappleSMCTableV0 (smc.version = "0")')
        hdr = gethdr(vmx, smc0_header)
        printhdr(smc0_header, hdr)

        # Get the +LKS key data routine for OSK0/1
        smc_key = getkey(vmx, smc0_lks)
        smc_default_ptr = smc_key[4]

        # Patch OSK0 key
        patchosk(vmx, smc0_osk0, smc_default_ptr, OSK0)

        # Patch OSK1 key
        patchosk(vmx, smc0_osk1, smc_default_ptr, OSK1)

        # Patch second vSMC table
        print('\nappleSMCTableV1 (smc.version = "1")')
        hdr = gethdr(vmx, smc1_header)
        printhdr(smc1_header, hdr)

        # Get the +LKS key data routine for OSK0/1
        smc_key = getkey(vmx, smc1_lks)
        smc_default_ptr = smc_key[4]

        # Patch OSK0 key
        patchosk(vmx, smc1_osk0, smc_default_ptr, OSK0)

        # Patch OSK1 key & get the output for ELF patching
        smc_osk_ptr = patchosk(vmx, smc1_osk1, smc_default_ptr, OSK1)

        # Patch KPPW key as a marker
        patchkppw(vmx, smc1_kppw, KPPW)

        # Patch relocation records if ELF executable
        vmx.seek(0)
        magic = vmx.read(4)
        if magic == ELF_MAGIC:
            # Find matching RELA record in .rela.dyn in ELF files
            print(f'\nModifying ELF RELA records from 0x{smc_osk_ptr:08x} -> 0x{smc_default_ptr:08x}')

            # Start at offset 0 and work thru file counting patches
            i = 0
            j = 0

            # Repack ints to bytes for find
            packed_old_ptr = struct.pack('=Q', smc_osk_ptr)
            packed_new_ptr = struct.pack('=Q', smc_default_ptr)

            # Loop while lower than SMC V0 #KEY offset
            while True:
                i = vmx.find(packed_old_ptr, i)
                if i != -1:
                    print(f'Relocation modified at: 0x{i:08x}')
                    vmx.seek(i)
                    vmx.write(packed_new_ptr)
                    i += 1
                    j += 1
                else:
                    break

            # There should be 4 relocation records that need patching
            if j != 4:
                print(f'ELF file RELA error count: {j}')

        # Tidy up
        vmx.flush()
        f.flush()
        vmx.close()
        f.close()


def ispatched(name):
    with open(name, 'r+b') as f:
        print('File: ' + name + '\n')

        # Memory map file
        vmx = mmap.mmap(f.fileno(), 0)

        # Is SpecialisRevelio present?
        if vmx.find(KPPW) == -1:
            flag = True
        else:
            flag = False

    # Tidy up
    vmx.close()
    f.close()
    return flag


def main():
    print('patchsmc')
    print('--------')

    if len(sys.argv) >= 2:
        filename = sys.argv[1]
    else:
        print('Please pass file name!')
        return

    if os.path.isfile(filename):
        patchsmc(filename)
    else:
        print('Cannot find file ' + filename)
    return


if __name__ == '__main__':
    main()
