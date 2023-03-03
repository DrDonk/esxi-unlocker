# Troubleshooting Notes

## Patch checker
It is important to re-patch ESXi after any upgrade or patches have been deployed. The status of the unlocker patches 
can be checked using the `check` command in the unlocker folder.

If the patch is installed and matches the current ESXi version, the output would look like this but the version numbers
may differ on your host depending on any patches installed. 
```
VMware ESXi Unlocker 4.0.3
==========================
(c) 2011-2022 David Parsons

Checking unlocker...
Current version of ESXi: VMware ESXi 7.0.3 build-20328353
Patch built for ESXi: VMware ESXi 7.0.3 build-20328353
Checking VMTAR loaded...
apple.v00 loaded
Checking vmx vSMC status...
/bin/vmx
/bin/vmx-debug
/bin/vmx-stats
vmx patched
Checking smcPresent status...
smcPresent = true
```
If the patch is installed and does _*NOT*_ match the current ESXi version, the output would look like this and an error 
is displayed. You must relock, reboot and unlock the host to ensure patches are applied to the correct version.

```
VMware ESXi Unlocker 4.0.3
==========================
(c) 2011-2022 David Parsons

Checking unlocker...
Current version of ESXi: VMware ESXi 7.0.3 build-20328353
Patch built for ESXi: VMware ESXi 7.0.3 build-20036589
>>> ERROR: Mis-matched files please relock/unlock to update patches <<<
```

## VMware vCenter
The unlocker from 4.0.3 should allow macOS guests to be started from vCenter on the patched host. If you get an error
in vCenter you may need to do the following:
1. Disconnect and reconnect the ESXi host in vCenter
2. Remove and re-add the ESXi host in vCenter

## Set a specific macOS Guest resolution

Installing the VMWare Tools should allow different video modes to be selected. If you have already installed them and still does not change resolution you can try this. Open Terminal and run:

`sudo /Library/Application Support/VMware Tools/vmware-resolutionSet <width> <height>`

where width and height are the pixel size you want. For example to get 1440x900:

`sudo /Library/Application Support/VMware Tools/vmware-resolutionSet 1440 900`

## AMD CPUs
The ESXi Unlocker does not add support for AMD CPUs, that has to be done via settings for the macOS guest runnning on 
a modern AMD CPU. These settings may allow macOS to run based on tests reported back to the project, but there is no 
formal support for AMD CPUs with the unlocker.

A patched macOS AMD kernel or OpenCore must be used to run on older AMD systems.

1. Read this KB article to learn how to edit a guest's VMX file safely https://kb.vmware.com/s/article/2057902
2. Add the following lines were to the VMX file:
```
cpuid.0.eax = "0000:0000:0000:0000:0000:0000:0000:1011"
cpuid.0.ebx = "0111:0101:0110:1110:0110:0101:0100:0111"
cpuid.0.ecx = "0110:1100:0110:0101:0111:0100:0110:1110"
cpuid.0.edx = "0100:1001:0110:0101:0110:1110:0110:1001"
cpuid.1.eax = "0000:0000:0000:0001:0000:0110:0111:0001"
cpuid.1.ebx = "0000:0010:0000:0001:0000:1000:0000:0000"
cpuid.1.ecx = "1000:0010:1001:1000:0010:0010:0000:0011"
cpuid.1.edx = "0000:0111:1000:1011:1111:1011:1111:1111"
vhv.enable = "FALSE"
vpmc.enable = "FALSE"
vvtd.enable = "FALSE"
```
3. Make sure there are no duplicate lines in the VMX file or the guest will not start and a dictionary error will
   be displayed by VMware.
4. You can now install and run macOS as a guest.
