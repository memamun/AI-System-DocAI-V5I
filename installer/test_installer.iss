; Test Inno Setup Script - Validates paths and structure before building
; Run this to verify all paths exist before building the full installer

[Setup]
AppName=AI-System-DocAI-V5I-Test
AppVersion=5I.2025
OutputDir=..\dist
OutputBaseFilename=AI-System-DocAI-V5I-Test-Installer

[Files]
; Check if PyInstaller build exists
Source: "..\dist\AI-System-DocAI-V5I\AI-System-DocAI-V5I.exe"; DestDir: "{app}"; Flags: ignoreversion; Check: PyInstallerBuildExists
Source: "..\assets\app-icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion; Check: IconExists

[Code]
function PyInstallerBuildExists(): Boolean;
begin
  Result := FileExists(ExpandConstant('{src}\..\dist\AI-System-DocAI-V5I\AI-System-DocAI-V5I.exe'));
  if not Result then
    MsgBox('PyInstaller build not found. Please run: pyinstaller AI-System-DocAI-V5I.spec', mbError, MB_OK);
end;

function IconExists(): Boolean;
begin
  Result := FileExists(ExpandConstant('{src}\..\assets\app-icon.ico'));
  if not Result then
    MsgBox('Icon file not found. Please check assets\app-icon.ico exists.', mbError, MB_OK);
end;

