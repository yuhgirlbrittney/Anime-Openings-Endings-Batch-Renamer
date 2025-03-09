; -------------------- setup.iss --------------------
[Setup]
; Basic installer settings
AppName=Anime Openings & Endings Batch Renamer
AppVersion=1.10
DefaultDirName={pf}\Anime Openings & Endings Batch Renamer
DefaultGroupName=Anime Openings & Endings Batch Renamer
OutputBaseFilename=Anime Openings & Endings Batch Renamer Installer
Compression=lzma
SolidCompression=yes

[Files]
; Copy the main executable (built with PyInstaller) and all resource files
Source: "dist/Anime Openings & Endings Batch Renamer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "/dist/Anime Openings & Endings Batch Renamer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "large_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "mascot.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "mad.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "sad.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "pat.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "kofi_symbol.png"; DestDir: "{app}"; Flags: ignoreversion



[Icons]
; Start Menu shortcut (using the same custom icon)
Name: "{group}\Anime Openings & Endings Batch Renamer"; \
    Filename: "{app}\Anime Openings & Endings Batch Renamer.exe"; \
    IconFilename: "{app}\large_icon.ico"

; Desktop shortcut (using the same custom icon)
Name: "{commondesktop}\Anime Openings & Endings Batch Renamer"; \
    Filename: "{app}\Anime Openings & Endings Batch Renamer.exe"; \
    Tasks: desktopicon; \
    IconFilename: "{app}\large_icon.ico"

[Tasks]
; Optional task for creating a desktop icon
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked
