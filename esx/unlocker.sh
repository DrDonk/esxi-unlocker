#!/bin/ash
set -x

# Absolute path to this script
SCRIPT=$(readlink -f "$0")
echo "$SCRIPT"

# Absolute folder to this script
SCRIPTPATH=$(dirname "$SCRIPT")
echo "$SCRIPTPATH"

# Change to script folder for processing
cd "$SCRIPTPATH"

# Get the GZIP/XZ/VMTAR'd VisorFS file from main bootbank (BOOTBANK1)
cp -fv /bootbank/vmx.v00 vmx.gz

# Extract XZ file from GZIP file
pigz -d -k vmx.gz
mv -fv vmx vmx.xz

# Extract VMTAR file from XZ file
xz -d --single-stream < vmx.xz > vmx.vtar

# Extract TAR file from VMTAR file
vmtar -x vmx.vtar -o vmx.tar

# Create a tmp folder for processing the TAR disk contents and extract files
mkdir -p ./tmp
tar xvf vmx.tar -C ./tmp

# Cleanup copied/extracted files
rm -fv vmx*

# Do the unlocking stuff
cd ./tmp

#  Compress files to TAR file
tar cvf ../vmx.tar *
cd ..

# Create VMTAR from TAR file
vmtar -c vmx.tar -v -o vmx.vtar

# Compress VMTAR into XZ file and add signature
xz --compress --stdout --lzma2=dict=2048KiB --check=crc32 --threads=8 vmx.vtar > vmx.xz
cat /usr/share/weasel/s.sigblob >> vmx.xz

# Compress XZ-sig to GZIP file
pigz -9 -p 60 -n -T -k -S .v00 vmx.xz
mv -fv vmx.xz.v00 vmx.v00

# Copy to main bootbank (BOOTBANK1)
#cp vmx.v00 /bootbank/vmx.v00
