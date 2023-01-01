# Changes

All dates are UK format.

## xx/01/23 4.0.4
_drdonk:_
* `check` command correctly reports if system not patched
* `unlock` command checks for free disk space before patching
* `unlock`  command checks for previous V3 installation before patching
* Fixed error if libvmkctl.so already patched
* Removed an unused unlocker flag (KPPW/KPST) to match Go version
* Update all copyright dates to 2023
* Make sure the files to be patched have write permissions before patching

## 22/10/22 4.0.3
_drdonk:_
* Reinstate libvmkctl patch to allow vCenter to boot macOS VMs on ESXi host
* Reinstate boot time load so the libvmkctl patch is loaded when hostd starts
* Store ESXi version with patched files
* `check` command compares current and stored ESXi versions

## 22/09/22 4.0.2
Thanks to _lucaskamp_ and an _anonymous_ tester for testing.
 
_drdonk:_
* Revert to binary file read/writes in patchsmc instead of using mmap, which caused silent errors during the patching 
process leading to failed patches.
* Modified VMTAR format from PSIGNED-XZ to GZIP
* Commands are now required to be run each boot of ESXi to avoid possible "Purple Screens of Death" (PSOD).
* Ensure vmx files have correct permissions, 4555/-r-sr-xr-x,  in apple.v00 archive

## 26/01/22 4.0.1
_drdonk:_
* Fix missing +x bit on checksmc, dumpsmc and relock

## 03/08/22 4.0.0
* Initial release
