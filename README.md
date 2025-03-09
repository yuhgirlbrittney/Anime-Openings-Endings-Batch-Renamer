# Anime Openings & Endings Batch Renamer
## Made by: yuhgirlbrittney

### Version 1.10 (Future Updates to Come)
A user-friendly PyQt-based application that automatically renames your anime opening and ending files to more standardized and descriptive titles. This tool leverages AniList and MAL APIs to retrieve the proper anime titles based on your chosen language preference.

## Overview
Anime Openings & Endings Batch Renamer makes it easy to:
- Batch Process Files: Quickly rename multiple .webm, .mp4, .mkv, and .avi files.
- Standardize File Names: Replace inconsistent file names with a uniform format.
- Choose Title Language: Select between English or Japanese titles for your files.
- Preview Changes: Preview the new filenames before making any changes.
- Customize Appearance: Switch between dark and light themes through the settings.
- Support the Developer: A built-in Ko‑fi button lets you support further development.

## Features
- Automatic Renaming: Uses AniList and MAL to find the correct anime title.
- Preview Mode: View a before-and-after list of filenames before applying changes.
- Theme Support: Easily switch between Dark and Light modes via the Settings dialog.
- Accessible UI: Designed with accessibility in mind (screen reader integration and clear controls).
- Resource Bundling: All images and resources are bundled with the application.

## Installation
##For End Users (One‑Click Installer)
# 1. Download the Installer:
Download the AnimeRenamerInstaller.exe from our website or repository.
# 2. Run the Installer:
Double-click the installer to launch it. Follow the on-screen instructions:
- Choose the installation folder (the default is typically fine).
- Optionally, select to create a desktop shortcut.
- Click "Install" to complete the installation.
# 3. Launch the Application:
Once the installation is complete, you can launch the application from the Start menu or desktop shortcut. The app works out of the box—no additional setup is required.

## For Developers
If you need to build or modify the application yourself, follow these steps:
# 1. Set Up Your Development Environment:
- Ensure you have Python 3.x installed.
- Download or clone the project folder.
# 2. Install Dependencies:
- Open a command prompt in the project directory.
- (Optional) Create and activate a virtual environment:
```
python -m venv venv
venv\Scripts\activate
```
(If you encounter a script execution policy error in PowerShell, see this guide: https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.security/set-executionpolicy)
- Run the dependency installation script:
```
python install_dependencies.py
```
- This will install required packages (e.g., PyQt5 and requests).
# 3. Run the Application from Source:
```
python anime_renamer.py
```
# 4. Package the Application with PyInstaller:
- Install PyInstaller if you haven’t already:
```
pip install pyinstaller
```
- Run PyInstaller (make sure all resource files are in the same directory):
```
pyinstaller --onefile --windowed --icon "myicon.ico" --add-data "mascot.png;." --add-data "mad.png;." --add-data "sad.png;." --add-data "pat.png;." --add-data "kofi_symbol.png;." anime_renamer.py
```
- The executable will be created in the dist folder.
# 5. Create a One‑Click Installer with Inno Setup:
- Download and install Inno Setup.
- Create an Inno Setup script (e.g., setup.iss) using the provided template.
- Open Inno Setup Compiler, load your script, and compile it to produce AnimeRenamerInstaller.exe.

## Usage
# 1. Launch the Application:
Run the executable or the source file.
# 2. Select a Folder:
Click on the "Select Folder" button to choose a directory containing your anime .webm files.
# 3. Choose Title Language:
Select your preferred title language (English or Japanese) from the dropdown.
# 4. Preview Changes (Optional):
Click "Preview Filenames" to view the proposed new names.
# 5. Start Renaming:
Once satisfied with the preview, click "Start Renaming" to apply the changes.
# 6. Support the Developer:
Click the Ko‑fi button to support further development.

## Note
# Thank you so much for checking out my software. I hope I was able to help you out - even if it was just a little bit! Happy renaming & have a fantastic day! :)

## License
# MIT License

Copyright (c) 2025 yuhgirlbrittney

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
