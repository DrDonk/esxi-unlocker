# Changes

All dates are UK format.

## 15/09/22 4.0.3
Thanks to an _anonymous_ tester.
* Revert to binary file read/writes in patchsmc instead of using mmap, which caused silent errors during the patching 
process leading to failed patches.

## 12/08/22 4.0.2
Thanks to _lucaskamp_ for testing.

_drdonk:_
* Modified VMTAR format from PSIGNED-XZ to GZIP
* Commands are now required to be run each boot of ESXi to avoid possible "Purple Screens of Death" (PSOD).

## 26/01/22 4.0.1
_drdonk:_
* Fix missing +x bit on checksmc, dumpsmc and relock

## 03/08/22 4.0.0
* Initial release
