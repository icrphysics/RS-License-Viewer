# RS-License-Viewer
Display the live RayStation license usage to users overlaid onto the desktop

Utility uses bgInfo utility from SysInternals and lmxendutil.exe utility.
Note lmxendutil.exe is not included in this repository and should be obtained from the LMX installation folder.

The output of lmxendutil is parsed and sorted by a python script and bgInfo with a custom config is used to map this onto the desktop.
