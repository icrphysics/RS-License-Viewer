Dim WinScriptHost
Set WinScriptHost = CreateObject("WScript.Shell")
WinScriptHost.Run "C:\Software\Python27\python.exe C:\Software\licenseViewer\licenseViewer.py", 0, True
WinScriptHost.Run "C:\Software\licenseViewer\Bginfo.exe C:\Software\licenseViewer\rsLicenses.bgi /NOLICPROMPT /timer:0 /Silent", 0, True
Set WinScriptHost = Nothing