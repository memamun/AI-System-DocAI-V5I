; Inno Setup Script for AI-System-DocAI V5I
; Enterprise Edition Installer for Windows
; NOTE: This installer expects a PyInstaller build in dist/AI-System-DocAI-V5I/
; Build with: pyinstaller --collect-all=PyQt6 AI-System-DocAI-V5I.spec
;
; Prerequisites:
; 1. PyInstaller build must be completed: pyinstaller AI-System-DocAI-V5I.spec
; 2. Build output should be in: dist/AI-System-DocAI-V5I/
; 3. Icon file should exist: assets/app-icon.ico

#define MyAppName "AI-System-DocAI"
#define MyAppVersion "5I.2025"
#define MyAppPublisher "AI-System-Solutions"
#define MyAppURL "https://github.com/ai-system-solutions/docai-v5i"
#define MyAppExeName "AI-System-DocAI-V5I.exe"
#define MyAppBuildDir "..\dist\AI-System-DocAI-V5I"

[Setup]
; NOTE: The value of AppId uniquely identifies this application
AppId={{8B4F3C2A-9D7E-4F1B-A5C3-2E8D6F1A9B4C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=AI-System-DocAI-V5I-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
SetupIconFile=..\assets\app-icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
; Create user data directory during install
DefaultUserDataDir={localappdata}\{#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; PyInstaller build output - all files from the build directory
; This includes: executable, DLLs, Python files, src/, assets/, etc.
Source: "{#MyAppBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: PyInstallerBuildExists

; Documentation files
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('{src}\..\README.md'))
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion isreadme; Check: FileExists(ExpandConstant('{src}\..\LICENSE'))

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec; Check: PyInstallerBuildExists

[Code]
var
  PyInstallerBuildPath: String;
  UserDataDir: String;

// Validate PyInstaller build exists before installer starts
function InitializeSetup(): Boolean;
begin
  PyInstallerBuildPath := ExpandConstant('{src}\{#MyAppBuildDir}');
  Result := DirExists(PyInstallerBuildPath);
  
  if not Result then
  begin
    MsgBox('PyInstaller build not found!' + #13#10 + #13#10 +
           'Expected location: ' + PyInstallerBuildPath + #13#10 + #13#10 +
           'Please build the application first:' + #13#10 +
           '  pyinstaller --collect-all=PyQt6 AI-System-DocAI-V5I.spec',
           mbError, MB_OK);
  end
  else
  begin
    // Check if main executable exists
    if not FileExists(PyInstallerBuildPath + '\{#MyAppExeName}') then
    begin
      Result := False;
      MsgBox('Main executable not found!' + #13#10 + #13#10 +
             'Expected: ' + PyInstallerBuildPath + '\{#MyAppExeName}' + #13#10 + #13#10 +
             'Please rebuild the application.',
             mbError, MB_OK);
    end;
  end;
end;

// Check if PyInstaller build exists (called during file copying)
function PyInstallerBuildExists(): Boolean;
begin
  Result := DirExists(ExpandConstant('{src}\{#MyAppBuildDir}'));
end;

// Create user data directory structure during installation
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create user data directories that the app will use
    // Index, logs, cache will be created here instead of installation directory
    UserDataDir := ExpandConstant('{localappdata}\{#MyAppName}');
    
    // Create directory structure (app will create subdirectories on first run)
    CreateDir(UserDataDir);
    CreateDir(UserDataDir + '\faiss_index');
    CreateDir(UserDataDir + '\logs');
    CreateDir(UserDataDir + '\cache');
    CreateDir(UserDataDir + '\models');
    
    // Log installation
    SaveStringToFile(UserDataDir + '\logs\install.log',
      Format('Installation completed: %s' + #13#10 +
             'Installed to: %s' + #13#10 +
             'User data: %s' + #13#10,
             [GetDateTimeString('yyyy-mm-dd hh:nn:ss', '-', ':'),
              ExpandConstant('{app}'),
              UserDataDir]),
      False);
  end;
end;

// Clean up on uninstall
procedure CurUninstallStepChanged(CurUninstallStep: TUnUninstallStep);
var
  UserDataDir: String;
  DeleteUserData: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    UserDataDir := ExpandConstant('{localappdata}\{#MyAppName}');
    
    // Ask if user wants to keep their data (indexes, logs, etc.)
    DeleteUserData := MsgBox('Do you want to delete all user data (indexes, logs, cache)?' + #13#10 + #13#10 +
                            'Location: ' + UserDataDir + #13#10 + #13#10 +
                            'Click Yes to delete, No to keep the data.',
                            mbConfirmation, MB_YESNO or MB_DEFBUTTON2);
    
    if DeleteUserData = IDYES then
    begin
      if DirExists(UserDataDir) then
      begin
        DelTree(UserDataDir, True, True, True);
      end;
    end;
  end;
end;

