#!/usr/bin/env python
"""
The MIT License (MIT)

Copyright (c) 2014-2021 Dave Parsons & Sam Bingner

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the 'Software'), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

vSMC Header Structure
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
"""

import codecs
import os
import shutil
import struct
import subprocess
import sys

if sys.version_info < (2, 7):
    sys.stderr.write('You need Python 2.7 or later\n')
    sys.exit(1)


def bytetohex(data):
    if sys.version_info > (3, 0):
        # Python 3 code in this block
        return "".join("{:02X} ".format(c) for c in data)
    else:
        # Python 2 code in this block
        return "".join("{:02X} ".format(ord(c)) for c in data)


def joinpath(folder, filename):
    return os.path.join(folder, filename)


def printkey(i, offset, smc_key, smc_data):
    print(str(i + 1).zfill(3)
          + ' ' + hex(offset)
          + ' ' + smc_key[0][::-1].decode('UTF-8')
          + ' ' + str(smc_key[1]).zfill(2)
          + ' ' + smc_key[2][::-1].replace(b'\x00', b' ').decode('UTF-8')
          + ' ' + '{0:#0{1}x}'.format(smc_key[3], 4)
          + ' ' + hex(smc_key[4])
          + ' ' + bytetohex(smc_data))


def set_bit(value, bit):
    return value | (1 << bit)


def clear_bit(value, bit):
    return value & ~(1 << bit)


def test_bit(value, bit):
    return value & bit


E_CLASS64 = 2
E_SHT_RELA = 4


def patchelf(f, oldoffset, newoffset):
    f.seek(0)
    magic = f.read(4)
    if not magic == b'\x7fELF':
        raise Exception('Magic number does not match')

    ei_class = struct.unpack('=B', f.read(1))[0]
    if ei_class != E_CLASS64:
        raise Exception('Not 64bit elf header: ' + ei_class)

    f.seek(40)
    e_shoff = struct.unpack('=Q', f.read(8))[0]
    f.seek(58)
    e_shentsize = struct.unpack('=H', f.read(2))[0]
    e_shnum = struct.unpack('=H', f.read(2))[0]
    e_shstrndx = struct.unpack('=H', f.read(2))[0]

    print('e_shoff: 0x{:x} e_shentsize: 0x{:x} e_shnum:0x{:x} e_shstrndx:0x{:x}'.format(e_shoff, e_shentsize,
                                                                                        e_shnum, e_shstrndx))

    for i in range(0, e_shnum):
        f.seek(e_shoff + i * e_shentsize)
        e_sh = struct.unpack('=LLQQQQLLQQ', f.read(e_shentsize))
        # The name is not used.
        # e_sh_name = e_sh[0]
        e_sh_type = e_sh[1]
        e_sh_offset = e_sh[4]
        e_sh_size = e_sh[5]
        e_sh_entsize = e_sh[9]
        if e_sh_type == E_SHT_RELA:
            e_sh_nument = int(e_sh_size / e_sh_entsize)
            # print 'RELA at 0x{:x} with {:d} entries'.format(e_sh_offset, e_sh_nument)
            for j in range(0, e_sh_nument):
                f.seek(e_sh_offset + e_sh_entsize * j)
                rela = struct.unpack('=QQq', f.read(e_sh_entsize))
                r_offset = rela[0]
                r_info = rela[1]
                r_addend = rela[2]
                if r_addend == oldoffset:
                    r_addend = newoffset
                    f.seek(e_sh_offset + e_sh_entsize * j)
                    f.write(struct.pack('=QQq', r_offset, r_info, r_addend))
                    print('Relocation modified at: ' + hex(e_sh_offset + e_sh_entsize * j))


def patchkeys(f, key):
    # Setup struct pack string
    key_pack = '=4sB4sB6xQ'
    # smc_old_memptr = 0
    smc_new_memptr = 0

    # Do Until OSK1 read
    i = 0
    while True:

        # Read key into struct str and data byte str
        offset = key + (i * 72)
        f.seek(offset)
        smc_key = struct.unpack(key_pack, f.read(24))
        smc_data = f.read(smc_key[1])

        # Reset pointer to beginning of key entry
        f.seek(offset)

        if smc_key[0] == b'SKL+':
            # Use the +LKS data routine for OSK0/1
            smc_new_memptr = smc_key[4]
            print('+LKS Key: ')
            printkey(i, offset, smc_key, smc_data)

        elif smc_key[0] == b'0KSO':
            # Write new data routine pointer from +LKS
            print('OSK0 Key Before:')
            printkey(i, offset, smc_key, smc_data)
            # smc_old_memptr = smc_key[4]
            f.seek(offset)
            f.write(struct.pack(key_pack, smc_key[0], smc_key[1], smc_key[2], smc_key[3], smc_new_memptr))
            f.flush()

            # Write new data for key
            f.seek(offset + 24)
            smc_new_data = codecs.encode('bheuneqjbexolgurfrjbeqfthneqrqcy', 'rot_13')
            f.write(smc_new_data.encode('UTF-8'))
            f.flush()

            # Re-read and print key
            f.seek(offset)
            smc_key = struct.unpack(key_pack, f.read(24))
            smc_data = f.read(smc_key[1])
            print('OSK0 Key After:')
            printkey(i, offset, smc_key, smc_data)

        elif smc_key[0] == b'1KSO':
            # Write new data routine pointer from +LKS
            print('OSK1 Key Before:')
            printkey(i, offset, smc_key, smc_data)
            smc_old_memptr = smc_key[4]
            f.seek(offset)
            f.write(struct.pack(key_pack, smc_key[0], smc_key[1], smc_key[2], smc_key[3], smc_new_memptr))
            f.flush()

            # Write new data for key
            f.seek(offset + 24)
            smc_new_data = codecs.encode('rnfrqbagfgrny(p)NccyrPbzchgreVap', 'rot_13')
            f.write(smc_new_data.encode('UTF-8'))
            f.flush()

            # Re-read and print key
            f.seek(offset)
            smc_key = struct.unpack(key_pack, f.read(24))
            smc_data = f.read(smc_key[1])
            print('OSK1 Key After:')
            printkey(i, offset, smc_key, smc_data)

            # Finished so get out of loop
            break

        else:
            pass

        i += 1
    return smc_old_memptr, smc_new_memptr


def patchsmc(name, sharedobj):
    with open(name, 'r+b') as f:

        smc_old_memptr = 0
        smc_new_memptr = 0

        # Read file into string variable
        vmx = f.read()

        print('File: ' + name + '\n')

        # Setup hex string for vSMC headers
        # These are the private and public key counts
        smc_header_v0 = b'\xF2\x00\x00\x00\xF0\x00\x00\x00'
        smc_header_v1 = b'\xB4\x01\x00\x00\xB0\x01\x00\x00'

        # Setup hex string for #KEY key
        key_key = b'\x59\x45\x4B\x23\x04\x32\x33\x69\x75'

        # Setup hex string for $Adr key
        adr_key = b'\x72\x64\x41\x24\x04\x32\x33\x69\x75'

        # Find the vSMC headers
        smc_header_v0_offset = vmx.find(smc_header_v0) - 8
        smc_header_v1_offset = vmx.find(smc_header_v1) - 8

        # Find '#KEY' keys
        smc_key0 = vmx.find(key_key)
        smc_key1 = vmx.rfind(key_key)

        # Find '$Adr' key only V1 table
        smc_adr = vmx.find(adr_key)

        # Print vSMC0 tables and keys
        print('appleSMCTableV0 (smc.version = "0")')
        print('appleSMCTableV0 Address      : ' + hex(smc_header_v0_offset))
        print('appleSMCTableV0 Private Key #: 0xF2/242')
        print('appleSMCTableV0 Public Key  #: 0xF0/240')

        if (smc_adr - smc_key0) != 72:
            print('appleSMCTableV0 Table        : ' + hex(smc_key0))
            smc_old_memptr, smc_new_memptr = patchkeys(f, smc_key0)
        elif (smc_adr - smc_key1) != 72:
            print('appleSMCTableV0 Table        : ' + hex(smc_key1))
            smc_old_memptr, smc_new_memptr = patchkeys(f, smc_key1)

        print()

        # Print vSMC1 tables and keys
        print('appleSMCTableV1 (smc.version = "1")')
        print('appleSMCTableV1 Address      : ' + hex(smc_header_v1_offset))
        print('appleSMCTableV1 Private Key #: 0x01B4/436')
        print('appleSMCTableV1 Public Key  #: 0x01B0/432')

        if (smc_adr - smc_key0) == 72:
            print('appleSMCTableV1 Table        : ' + hex(smc_key0))
            smc_old_memptr, smc_new_memptr = patchkeys(f, smc_key0)
        elif (smc_adr - smc_key1) == 72:
            print('appleSMCTableV1 Table        : ' + hex(smc_key1))
            smc_old_memptr, smc_new_memptr = patchkeys(f, smc_key1)

        print()

        # Find matching RELA record in .rela.dyn in ESXi ELF files
        # This is temporary code until proper ELF parsing written
        if sharedobj:
            print('Modifying RELA records from: ' + hex(smc_old_memptr) + ' to ' + hex(smc_new_memptr))
            patchelf(f, smc_old_memptr, smc_new_memptr)

        # Tidy up
        f.flush()
        f.close()


def patchvmkctl(name):
    # Patch file
    print('smcPresent Patching: ' + name)
    f = open(name, 'r+b')

    # Read file into string variable
    vmkctl = f.read()
    applesmc = vmkctl.find(b'applesmc')
    f.seek(applesmc)
    f.write(b'vmkernel')

    # Tidy up
    f.flush()
    f.close()
    print('smcPresent Patched: ' + name)


def main():

    # Stop the hostd service
    subprocess.call('/etc/init.d/hostd stop', shell=True)

    # Current folder
    currdir = os.getcwd()

    # Source files
    srcvmx = '/bin/vmx'
    srclib32 = '/lib/libvmkctl.so'
    srclib64 = '/lib64/libvmkctl.so'

    # Destination files cuurently tmp but may use scratch
    basefolder = '/tmp/'
    destfolder = joinpath(basefolder, 'unlocker')
    destvmx = joinpath(destfolder, 'bin/vmx')
    destlib32 = joinpath(destfolder, 'lib/libvmkctl.so')
    destlib64 = joinpath(destfolder, 'lib64/libvmkctl.so')

    # Remove files & folder if they exist
    if os.path.isdir(destfolder):
        shutil.rmtree(destfolder, True)

    # Create the base folder
    os.makedirs(destfolder)
    os.chdir(destfolder)

    # Patch the vmx executable
    os.makedirs(joinpath(destfolder, 'bin'))
    shutil.copy2(srcvmx, destvmx)
    patchsmc(destvmx, True)

    # Patch 32-bit libvmkctl to return Apple SMC present
    if os.path.isfile(srclib32):
        os.makedirs(joinpath(destfolder, 'lib'))
        shutil.copy2(srclib32, destlib32)
        patchvmkctl(destlib32)

    # Patch 64-bit libvmkctl to return Apple SMC present
    if os.path.isfile(srclib64):
        os.makedirs(joinpath(destfolder, 'lib64'))
        shutil.copy2(srclib64, destlib64)
        patchvmkctl(destlib64)

    # Build the gzipped tar file macos.tgz
    print('\nCreating macos.tgz...')
    subprocess.call('/bin/tar czvf macos.tgz bin lib lib64', shell=True)

    # Build the vmtar file macos.vmtar
    print('\nCreating macos.vmtar...')
    subprocess.call('/bin/vmtar -v -c macos.tgz -o macos.vmtar', shell=True)

    # Build the gzipped vmtar file macos.vgz
    print('\nCreating macos.vgz...')
    subprocess.call('/bin/gzip < macos.vmtar > macos.vgz', shell=True)
    subprocess.call('/bin/vmtar -v -t < macos.vgz', shell=True)

    # Load the tardisk
    subprocess.call('vmkramdisk macos.vgz', shell=True)

    # Return to script folder
    os.chdir(currdir)

    # Start the rhttp & hostd services
    subprocess.call('/etc/init.d/rhttp restart', shell=True)
    subprocess.call('/etc/init.d/hostd restart', shell=True)


if __name__ == '__main__':
    # Check boot options specified
    bootoptions = subprocess.check_output(['/bin/bootOption', '-a'])
    if bootoptions.find(b'nounlocker') == -1:
        # Run unlocker code
        main()
    else:
        # Exit if "nounlocker" boot option specified
        print('Unlocker disabled by boot option')
