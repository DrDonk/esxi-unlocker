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
"""

# Note to self:
# This is crap code used in place of a shell script
# GNU tar and ar must be used and not BSD version or error loading the tardisk in ESXi:
# brew install gnu-tar binutils

import datetime
from string import Template
import subprocess
import sys


if sys.version_info < (3, 6):
    sys.stderr.write('You need Python 3.6 or later\n')
    sys.exit(1)

# TODO: Change for a new release
VERSION = '3.0.1'
FILEVER = '301'
FILENAME = 'build/esxi-unlocker-301.tgz'

# Constants used in creating the VIB
NOW = datetime.datetime.now()
FILETIMESTAMP = f'{NOW:%Y%m%d%H%M.%S}'
VIBTIMESTAMP = (NOW.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'))
TOUCH = 'touch -t ' + FILETIMESTAMP
UNLOCKERTAR = '/usr/local/bin/gtar cvf build/unlocker.tar etc'
UNLOCKERTGZ = 'gzip -S .tgz -k build/unlocker.tar'
UNLOCKERMV = 'mv -vf build/unlocker.tar.tgz build/unlocker.tgz'
UNLOCKERVIB = 'agar qDv esxi-unlocker-301.vib descriptor.xml sig.pkcs7 unlocker.tgz'

# Template for the descriptor.xml file
DESCRIPTOR = Template(
    """<vib version="5.0">
	<type>bootbank</type>
	<name>esxi-unlocker</name>
	<version>$version</version>
	<vendor>unlocker</vendor>
	<summary>macOS Enabler for ESXi</summary>
	<description>macOS Enabler for ESXi</description>
	<release-date>$timestamp</release-date>
	<urls>
		<url key="kb">https://github.com/DrDonk/esxi-unlocker</url>
	</urls>
	<relationships>
		<depends></depends>
		<conflicts/>
		<replaces/>
		<provides/>
		<compatibleWith/>
	</relationships>
	<software-tags></software-tags>
	<system-requires>
		<maintenance-mode>true</maintenance-mode>
	</system-requires>
	<file-list>
		<file>etc/rc.local.d/unlocker.py</file>
	</file-list>
	<acceptance-level>community</acceptance-level>
	<live-install-allowed>false</live-install-allowed>
	<live-remove-allowed>false</live-remove-allowed>
	<cimom-restart>false</cimom-restart>
	<stateless-ready>true</stateless-ready>
	<overlay>false</overlay>
	<payloads>
		<payload name="unlocker.tgz" type="tgz" size="4105">
			<checksum checksum-type="sha-256">$sha256sum</checksum>
			<checksum checksum-type="sha-1" verify-process="gunzip">$sha1sum</checksum>
		</payload>
	</payloads>
</vib>
""")

def main():

    # Timestamp files for release
    print('\nTimestamping files...')
    subprocess.call(TOUCH + ' etc', shell=True)
    subprocess.call(TOUCH + ' etc/rc.local.d', shell=True)
    subprocess.call(TOUCH + ' etc/rc.local.d/unlocker.py', shell=True)

    # Build the gzipped tar file unlocker.tgz
    print('\nCreating unlocker.tgz...')
    subprocess.call(UNLOCKERTAR, shell=True)
    subprocess.call(TOUCH + ' unlocker.tar', shell=True)
    subprocess.call(UNLOCKERTGZ, shell=True)
    subprocess.call(UNLOCKERMV, shell=True)
    subprocess.call(TOUCH + ' unlocker.tgz', shell=True)

    # Get the sha1 and sha256 checksums needed for the VIB descriptor.xml
    sha1sum = subprocess.check_output('sha1sum build/unlocker.tar | cut -d " " -f 1', shell=True).decode().strip('\n')
    sha256sum = subprocess.check_output('sha256sum build/unlocker.tgz | cut -d " " -f 1', shell=True).decode().strip('\n')

    # Create a blank signing file
    subprocess.call(TOUCH + ' build/sig.pkcs7', shell=True)

    # Create the descriptor.xml filke
    d = dict()
    d['version'] = '3.0.1'
    d['timestamp'] = VIBTIMESTAMP
    d['sha256sum'] = sha256sum
    d['sha1sum'] = sha1sum

    descriptor_xml = DESCRIPTOR.substitute(d)
    with open('build/descriptor.xml', 'w') as f:
        f.write(descriptor_xml)
    subprocess.call(TOUCH + ' build/descriptor.xml', shell=True)

    # '/usr/local/bin/gtar czvf unlocker.tgz etc'
    # Build the distribution file esxi-unlocker-VER.tgz
    # print('\nCreating ' + FILENAME + '...')
    # subprocess.call(UNLOCKERVIB, shell=True)
    # subprocess.call(TOUCH + ' ' + FILENAME, shell=True)
    return

if __name__ == '__main__':
    if sys.platform == 'darwin':
        print('ESXi-Build for macOS')
        main()
    else:
        print('ESXi-Build only supported on macOS')
