#define MyAppName "ReportChecker"
#define MyAppVersion "1.0"
#define MyAppPublisher "Glenn Stolen"
#define MyAppURL "https://github.com/glennstolen/reportchecker"
#define MyInstallDir "{localappdata}\ReportChecker"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={#MyInstallDir}
DisableDirPage=yes
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=ReportChecker-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "norwegian"; MessagesFile: "compiler:Languages\Norwegian.isl"

[Files]
Source: "..\docker-compose.prod.yml"; DestDir: "{app}"; Flags: ignoreversion
Source: "start.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "stop.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Start ReportChecker"; Filename: "{app}\start.bat"; IconFilename: "{app}\start.bat"
Name: "{group}\Stopp ReportChecker"; Filename: "{app}\stop.bat"
Name: "{commondesktop}\Start ReportChecker"; Filename: "{app}\start.bat"; Tasks: desktopicon
Name: "{commondesktop}\Stopp ReportChecker"; Filename: "{app}\stop.bat"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Opprett snarveier pa skrivebordet"; GroupDescription: "Tilleggsvalg:"

[Code]
var
  ApiKeyPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  // Custom page for Anthropic API key
  ApiKeyPage := CreateInputQueryPage(wpWelcome,
    'Anthropic API-nokkel',
    'Skriv inn din Anthropic API-nokkel',
    'API-nokkelen er nodvendig for at ReportChecker skal kunne bruke Claude AI.' + #13#10 +
    'Du finner nokkelen pa https://console.anthropic.com/');
  ApiKeyPage.Add('API-nokkel (starter med sk-ant-):', False);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = ApiKeyPage.ID then
  begin
    if Trim(ApiKeyPage.Values[0]) = '' then
    begin
      MsgBox('Du ma oppgi en API-nokkel for a fortsette.', mbError, MB_OK);
      Result := False;
    end
    else if Copy(Trim(ApiKeyPage.Values[0]), 1, 7) <> 'sk-ant-' then
    begin
      if MsgBox('API-nokkelen ser ikke ut til a vaere en gyldig Anthropic-nokkel (starter vanligvis med "sk-ant-"). Vil du fortsette likevel?',
        mbConfirmation, MB_YESNO) = IDNO then
        Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvFile: String;
  ApiKey: String;
begin
  if CurStep = ssPostInstall then
  begin
    ApiKey := Trim(ApiKeyPage.Values[0]);
    EnvFile := ExpandConstant('{app}\.env');
    SaveStringToFile(EnvFile, 'ANTHROPIC_API_KEY=' + ApiKey + #13#10, False);
  end;
end;

function CheckDockerInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('docker', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if not CheckDockerInstalled then
  begin
    if MsgBox(
      'Docker Desktop er ikke installert eller ikke startet.' + #13#10#13#10 +
      'ReportChecker krever Docker Desktop for a kjore.' + #13#10 +
      'Last ned fra: https://www.docker.com/products/docker-desktop/' + #13#10#13#10 +
      'Installer Docker Desktop, start det, og kj"r dette installasjons-programmet pa nytt.' + #13#10#13#10 +
      'Vil du apne nedlastingssiden na?',
      mbConfirmation, MB_YESNO) = IDYES then
    begin
      ShellExec('open', 'https://www.docker.com/products/docker-desktop/', '', '', SW_SHOW, ewNoWait, 0);
    end;
    Result := 'Docker Desktop ma vaere installert og startet for ReportChecker kan installeres.';
  end;
end;
