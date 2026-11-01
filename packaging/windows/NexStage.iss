#define MyAppName "NexStage"
#define MyAppVersion "0.5.0"
#define MyAppPublisher "Natan Gabriel"
#define MyAppURL "https://github.com/Natan-Tec/NexStage"
#define MyAppExeName "NexStage.exe"

[Setup]
AppId={{B2D38FD7-D122-4EB8-A3DD-75E82154435D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Instalador do NexStage
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
DefaultDirName=C:\NexStage
DefaultGroupName=NexStage
DisableProgramGroupPage=yes
UsePreviousAppDir=no
DirExistsWarning=no
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\release
OutputBaseFilename=NexStage-Setup
SetupIconFile=..\..\web\favicon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallFilesDir={app}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
AppMutex=Local\NexStage_NatanGabriel
LicenseFile=..\..\LICENSE.txt

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "..\..\dist\NexStage\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\data"; Permissions: users-modify; Flags: uninsneveruninstall
Name: "{app}\data\bibles"; Permissions: users-modify; Flags: uninsneveruninstall
Name: "{app}\data\fonts"; Permissions: users-modify; Flags: uninsneveruninstall
Name: "{app}\media"; Permissions: users-modify; Flags: uninsneveruninstall

[Icons]
Name: "{autodesktop}\NexStage"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\NexStage\NexStage"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\NexStage\Desinstalar NexStage"; Filename: "{uninstallexe}"
Name: "{userdocs}\NexStage"; Filename: "{app}"; WorkingDir: "{app}"; Comment: "Abrir a pasta do NexStage"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir o NexStage"; Flags: nowait postinstall skipifsilent

[Messages]
ConfirmUninstall=Tem certeza de que deseja remover o NexStage? Suas musicas, Biblias, fontes, midias e configuracoes serao preservadas em C:\NexStage.
