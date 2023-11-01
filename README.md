# macOS Unlocker V4 for VMware ESXi

## IMPORTANT: Security Update 
VMware have [announced](https://www.vmware.com/security/advisories/VMSA-2023-0024.html) and fixed a vulnerability in 
VMware Tools across macOS, Linux and Windows guests. Please ensure that you update the guest tools which can 
be found here https://vmware.com/go/tools.


## Unlocker 2007-2023
This project is now archived.

The unlocker should continue to run as there have been few changes to the VMware code in many years.
I have stopped developemnt as I no longer use VMware but would be happy to refer to a fork if someone 
sends me an email with the relevant details.

There is also [Auto Unlocker](https://github.com/paolo-projects/auto-unlocker) which is still active.


## 1. Introduction
Unlocker 4 is designed for VMware ESXi 7.

The Unlocker enables certain flags and data tables that are required to see the macOS type when setting
the guest OS type, and modify the implmentation of the virtual SMC controller device. These capabiltiites are normally 
exposed in Fusion and ESXi when running on Apple hardware.

The patch code carries out the following modifications dependent on the product being patched:

* Patch vmx and derivatives to allow macOS to boot
* Patch libvmkctl.so to allow vCenter to boot macOS guests

It is important to understand that the Unlocker cannot add any new capabilities to VMware ESXi
but enables support for macOS that is disabled in the VMware products when run on non-Apple hardware.

The Unlocker cannot:

* add support for new versions of macOS
* add paravirtualized Apple GPU support 
* add AMD CPU support

or any other features that are not already in the VMware compiled code. 

## 2. Installing the patcher

#### The ESXi unlocker will need to be run each time the ESXi Server is upgraded. 
#### It is also best to switch ESXi to Maintanence mode and make sure you do not have any VMs running.

The code is written in Python and has no pre-requisites and should run directly from the release zip download.

* Download a binary release from https://github.com/DrDonk/esxi-unlocker/releases
* Unload the archive to a folder on the ESXi server datastore and extract the files
* Navigate to the folder with the extracted files

You will then need to run one of the following commands to patch or unpatch the ESXi software.

* unlock - apply patches to VMware ESXi
* relock - remove patches from VMware ESXi
* check  - check the patch status of your VMware installation

## 4. Thanks
Thanks to Zenith432 for originally building the C++ Unlocker and Mac Son of Knife
(MSoK) for all the testing and support.

Thanks also to Sam B for finding the solution for ESXi 6 and helping me with
debugging expertise. Sam also wrote the code for patching ESXi ELF files and
modified the Unlocker code to run on Python 3 in the ESXi 6.5 environment.

Thanks to lucaskamp for testing the new version 4 of ESXi Unlocker.
