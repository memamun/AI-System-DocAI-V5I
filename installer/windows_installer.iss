; Inno Setup Script for AI-System-DocAI V5I
; Enterprise Edition Installer for Windows

#define MyAppName "AI-System-DocAI"
#define MyAppVersion "5I.2025"
#define MyAppPublisher "AI-System-Solutions"
#define MyAppURL "https://github.com/ai-system-solutions/docai-v5i"
#define MyAppExeName "launcher.bat"

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
OutputDir=..\dist
OutputBaseFilename=AI-System-DocAI-V5I-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=..\assets\app-icon.ico
UninstallDisplayIcon={app}\assets\app-icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Application files
Source: "..\main.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\launcher.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\launcher.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

; Source files
Source: "..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs

; Assets
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\app-icon.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\app-icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec

[Code]
function InitializeSetup(): Boolean;
var
  PythonPath: String;
  ResultCode: Integer;
begin
  Result := True;
  
  // Check for Python 3.8+
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Software\Python\PythonCore\3.8\InstallPath', '', PythonPath) then
  begin
    if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\Python\PythonCore\3.8\InstallPath', '', PythonPath) then
    begin
      if not RegQueryStringValue(HKEY_CURRENT_USER, 'Software\Python\PythonCore\3.9\InstallPath', '', PythonPath) then
      begin
        if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\Python\PythonCore\3.9\InstallPath', '', PythonPath) then
        begin
          if not RegQueryStringValue(HKEY_CURRENT_USER, 'Software\Python\PythonCore\3.10\InstallPath', '', PythonPath) then
          begin
            if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\Python\PythonCore\3.10\InstallPath', '', PythonPath) then
            begin
              if not RegQueryStringValue(HKEY_CURRENT_USER, 'Software\Python\PythonCore\3.11\InstallPath', '', PythonPath) then
              begin
                if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\Python\PythonCore\3.11\InstallPath', '', PythonPath) then
                begin
                  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Software\Python\PythonCore\3.12\InstallPath', '', PythonPath) then
                  begin
                    if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\Python\PythonCore\3.12\InstallPath', '', PythonPath) then
                    begin
                      if MsgBox('Python 3.8 or later is required but not found.' + #13#10 + #13#10 + 
                                'Do you want to continue installation anyway?' + #13#10 + 
                                '(You will need to install Python manually)', mbConfirmation, MB_YESNO) = IDNO then
                      begin
                        Result := False;
                      end;
                    end;
                  end;
                end;
              end;
            end;
          end;
        end;
      end;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  LogDir: String;
  LogFile: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Create logs directory
    LogDir := ExpandConstant('{app}\logs');
    if not DirExists(LogDir) then
      CreateDir(LogDir);
    
    // Create startup log
    LogFile := LogDir + '\AI-System-DocAI_Startup.log';
    SaveStringToFile(LogFile, '==============================================================================' + #13#10, False);
    SaveStringToFile(LogFile, 'AI-System-DocAI V5I - Installed via Inno Setup' + #13#10, True);
    SaveStringToFile(LogFile, 'Installation Date: ' + GetDateTimeString('yyyy-mm-dd hh:nn:ss', #0, #0) + #13#10, True);
    SaveStringToFile(LogFile, '==============================================================================' + #13#10 + #13#10, True);
    
    // Create index and cache directories
    if not DirExists(ExpandConstant('{app}\faiss_index')) then
      CreateDir(ExpandConstant('{app}\faiss_index'));
    if not DirExists(ExpandConstant('{app}\cache')) then
      CreateDir(ExpandConstant('{app}\cache'));
  end;
end;

