import sys
import os
import re
import requests
import webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets

# -------------------- Worker Thread --------------------
class RenameWorker(QtCore.QThread):
    logSignal = QtCore.pyqtSignal(str)
    progressSignal = QtCore.pyqtSignal(int)
    finishedSignal = QtCore.pyqtSignal()

    def __init__(self, folder, title_preference, functions, previewMode=False, parent=None):
        super().__init__(parent)
        self.folder = folder
        self.title_preference = title_preference
        self.previewMode = previewMode
        # functions: dict with keys 'anilist', 'mal', 'title_case', 'expand_season', 'format_mal'
        self.get_anime_title_anilist = functions['anilist']
        self.get_anime_title_mal = functions['mal']
        self.format_title_case = functions['title_case']
        self.expand_season_format = functions['expand_season']
        self.format_for_mal_search = functions['format_mal']

    def run(self):
        files = [f for f in os.listdir(self.folder) if f.endswith(".webm")]
        total = len(files)
        if total == 0:
            self.logSignal.emit("⚠️ No .webm files found in this folder. Nothing to process.")
            self.finishedSignal.emit()
            return

        for idx, filename in enumerate(files):
            file_root, file_ext = os.path.splitext(filename)
            match = re.match(r"^(.*?)[-\s]+(?:OP\d*|Opening|ED\d*|Ending)", file_root, re.IGNORECASE)
            if not match:
                self.progressSignal.emit(idx + 1)
                continue

            anime_title = match.group(1).strip()
            new_anime_name = self.get_anime_title_anilist(anime_title)
            if not new_anime_name:
                new_anime_name = self.get_anime_title_mal(anime_title)
                if new_anime_name:
                    second_attempt = self.get_anime_title_anilist(new_anime_name)
                    if second_attempt:
                        new_anime_name = second_attempt
            if not new_anime_name:
                self.progressSignal.emit(idx + 1)
                continue

            if self.title_preference == "english":
                new_anime_name = self.format_title_case(new_anime_name)

            new_filename = new_anime_name + file_root[len(anime_title):]
            invalid_chars = r'[\/:*?"<>|]'
            new_filename = re.sub(invalid_chars, '', new_filename)
            new_filename = re.sub(r'\bOP(\d+)\b', r'Opening \1', new_filename, flags=re.IGNORECASE)
            new_filename = re.sub(r'\bED(\d+)\b', r'Ending \1', new_filename, flags=re.IGNORECASE)
            new_filename = self.expand_season_format(new_filename)
            new_filename = re.sub(r'(\w)(Opening|Ending)', r'\1 - \2', new_filename)
            new_filename = re.sub(r'(\S)-(\S)', r'\1 - \2', new_filename)
            new_filename = re.sub(r'(Opening \d+|Ending \d+).*', r'\1', new_filename, flags=re.IGNORECASE)
            new_filename += file_ext

            if self.previewMode:
                self.logSignal.emit(f"{filename} ➡️ {new_filename}")
            else:
                new_path = os.path.join(self.folder, new_filename)
                try:
                    os.rename(os.path.join(self.folder, filename), new_path)
                    self.logSignal.emit(f"✅ Renamed: {filename} → {new_filename}")
                except Exception as e:
                    self.logSignal.emit(f"❌ Error renaming {filename}: {e}")

            self.progressSignal.emit(idx + 1)

        self.finishedSignal.emit()


# -------------------- Preview Dialog --------------------
class PreviewDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filename Preview")
        self.resize(950, 600)
        layout = QtWidgets.QVBoxLayout(self)
        self.textArea = QtWidgets.QTextEdit()
        self.textArea.setReadOnly(True)
        layout.addWidget(self.textArea)
        closeBtn = QtWidgets.QPushButton("Close")
        closeBtn.clicked.connect(self.close)
        layout.addWidget(closeBtn, alignment=QtCore.Qt.AlignRight)

    def appendText(self, text):
        self.textArea.append(text)


# -------------------- Settings Dialog --------------------
class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(400, 250)
        layout = QtWidgets.QFormLayout(self)

        self.apiPriorityCombo = QtWidgets.QComboBox()
        self.apiPriorityCombo.addItems(["AniList", "MAL", "Auto"])
        self.apiPriorityCombo.setCurrentText(current_settings.get("api_priority", "Auto"))
        layout.addRow("API Priority:", self.apiPriorityCombo)

        self.languageCombo = QtWidgets.QComboBox()
        self.languageCombo.addItems(["English", "Spanish", "Japanese"])
        self.languageCombo.setCurrentText(current_settings.get("interface_language", "English"))
        layout.addRow("Interface Language:", self.languageCombo)

        self.themeCombo = QtWidgets.QComboBox()
        self.themeCombo.addItems(["Dark", "Light"])
        current_theme = current_settings.get("theme_mode", "Dark")
        self.themeCombo.setCurrentText(current_theme)
        layout.addRow("Theme:", self.themeCombo)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

    def getSettings(self):
        return {
            "api_priority": self.apiPriorityCombo.currentText(),
            "interface_language": self.languageCombo.currentText(),
            "theme_mode": self.themeCombo.currentText()
        }


# -------------------- Main Window --------------------
class AnimeRenamerWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anime Openings & Endings Batch Renamer")
        self.setFixedSize(1600, 800)
        self.setGeometry(100, 100, 1600, 800)

        if os.path.exists("mascot.png"):
            self.setWindowIcon(QtGui.QIcon("mascot.png"))

        self.appFont = QtGui.QFont("AtkinsonHyperlegibleMono-Bold", 18)
        self.setFont(self.appFont)

        # QSettings
        self.settings = QtCore.QSettings("MyOrganization", "AnimeRenamer")
        self.loadSettings()
        self.apiPriority = self.settings.value("api_priority", "Auto")
        self.interface_language = self.settings.value("interface_language", "English")
        self.theme_mode = self.settings.value("theme_mode", "Dark")

        self.darkMode = (self.theme_mode == "Dark")

        self.setupUI()
        if self.darkMode:
            self.applyDarkStyle()
        else:
            self.applyLightStyle()

        self.worker = None

    def setupUI(self):
        mainLayout = QtWidgets.QVBoxLayout()
        centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(centralWidget)
        centralWidget.setLayout(mainLayout)
        mainLayout.setContentsMargins(20, 20, 20, 20)
        mainLayout.setSpacing(20)

        # Header row
        headerLayout = QtWidgets.QHBoxLayout()
        self.headerLabel = QtWidgets.QLabel("Anime Openings & Endings Batch Renamer")
        self.headerLabel.setFont(QtGui.QFont("AtkinsonHyperlegibleMono-Bold", 24))
        self.headerLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.versionLabel = QtWidgets.QLabel("Version 1.10")
        self.versionLabel.setFont(QtGui.QFont("AtkinsonHyperlegibleMono-Bold", 14))
        self.versionLabel.setStyleSheet("color: #888;")
        self.versionLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        headerLayout.addWidget(self.headerLabel)
        headerLayout.addStretch()
        headerLayout.addWidget(self.versionLabel)
        mainLayout.addLayout(headerLayout)

        # Folder selection row
        folderLayout = QtWidgets.QHBoxLayout()
        self.folderDisplay = QtWidgets.QLabel("No folder selected")
        self.folderDisplay.setFont(self.appFont)
        self.folderDisplay.setStyleSheet(
            "background-color: #333; padding: 12px; border-radius: 10px; border: 2px solid #555; min-width: 500px; color: white;"
        )
        browseBtn = QtWidgets.QPushButton("Select Folder")
        browseBtn.setFixedSize(200, 65)
        browseBtn.setFont(self.appFont)
        browseBtn.setToolTip("Select a folder containing your anime .webm files")
        browseBtn.clicked.connect(self.browseFolder)
        folderLayout.addWidget(self.folderDisplay)
        folderLayout.addWidget(browseBtn)
        mainLayout.addLayout(folderLayout)

        # Title language row
        languageLayout = QtWidgets.QHBoxLayout()
        languageLabel = QtWidgets.QLabel("Title Language:")
        languageLabel.setFont(self.appFont)
        self.languageCombo = QtWidgets.QComboBox()
        self.languageCombo.addItems(["English", "Japanese"])
        self.languageCombo.setFont(self.appFont)
        self.languageCombo.setToolTip("Choose your preferred title language")
        self.languageCombo.setStyleSheet("border: 2px solid #555; padding: 10px;")
        languageLayout.addWidget(languageLabel)
        languageLayout.addWidget(self.languageCombo)
        languageLayout.addStretch()
        mainLayout.addLayout(languageLayout)

        # Bottom buttons row: Preview, Start, Settings, Ko‑fi (theme now in settings)
        bottomButtonLayout = QtWidgets.QHBoxLayout()
        self.previewButton = QtWidgets.QPushButton("Preview File Names")
        self.previewButton.setFixedSize(260, 65)
        self.previewButton.setFont(self.appFont)
        self.previewButton.setToolTip("Click to preview new filenames without renaming")
        self.previewButton.clicked.connect(self.previewFilenames)
        bottomButtonLayout.addWidget(self.previewButton)

        self.startBtn = QtWidgets.QPushButton("Start Renaming")
        self.startBtn.setFixedSize(260, 65)
        self.startBtn.setFont(self.appFont)
        self.startBtn.setToolTip("Click to start renaming your files")
        self.startBtn.setEnabled(False)
        self.startBtn.clicked.connect(self.startRenaming)
        bottomButtonLayout.addWidget(self.startBtn)

        self.settingsButton = QtWidgets.QPushButton("Settings")
        self.settingsButton.setFixedSize(180, 65)
        self.settingsButton.setFont(self.appFont)
        self.settingsButton.setToolTip("Change preferences")
        self.settingsButton.clicked.connect(self.openSettings)
        self.settingsButton.setStyleSheet("""
            QPushButton {
                background-color: #FF6433;
                color: white;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #E0552A; }
        """)
        bottomButtonLayout.addWidget(self.settingsButton)

        self.koFiButton = QtWidgets.QToolButton()
        self.koFiButton.setToolTip("Support me on Ko‑fi!")
        self.koFiButton.setFixedSize(60, 65)
        if os.path.exists("kofi_symbol.png"):
            icon = QtGui.QIcon("kofi_symbol.png")
            self.koFiButton.setIcon(icon)
            self.koFiButton.setIconSize(QtCore.QSize(60,65))
            self.koFiButton.setText("")
        else:
            self.koFiButton.setText("☕")
        self.koFiButton.setStyleSheet("QToolButton { background: transparent; border: none; }")
        self.koFiButton.clicked.connect(lambda: webbrowser.open("https://ko-fi.com/yuhgirlbrittney"))
        bottomButtonLayout.addWidget(self.koFiButton)

        bottomButtonLayout.addStretch()
        mainLayout.addLayout(bottomButtonLayout)

        # Progress bar row
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setFixedHeight(30)
        self.progressBar.setValue(0)
        self.progressBar.setStyleSheet(
            "QProgressBar { background-color: #333; border: 2px solid #555; border-radius: 10px; text-align: center; color: white; }"
            "QProgressBar::chunk { background-color: #FF6433; border-radius: 8px; }"
        )
        mainLayout.addWidget(self.progressBar)

        # Final row: Horizontal layout with Log box (left) and Mascot Interaction Panel (right)
        finalRowWidget = QtWidgets.QWidget()
        finalRowLayout = QtWidgets.QHBoxLayout(finalRowWidget)
        finalRowLayout.setContentsMargins(0, 0, 0, 0)

        # Left: Log text edit
        self.logTextEdit = QtWidgets.QTextEdit()
        self.logTextEdit.setReadOnly(True)
        self.logTextEdit.setFont(self.appFont)
        self.logTextEdit.setStyleSheet("border: 2px solid #555; padding: 12px; background-color: #252526; color: white;")
        finalRowLayout.addWidget(self.logTextEdit, stretch=3)

        # Right: Mascot Interaction Panel
        rightPanel = QtWidgets.QWidget()
        rightPanelLayout = QtWidgets.QVBoxLayout(rightPanel)
        rightPanelLayout.setContentsMargins(20, 0, 0, 0)
        rightPanelLayout.setSpacing(20)

        self.mascotDisplay = QtWidgets.QLabel()
        if os.path.exists("mascot.png"):
            pixmap = QtGui.QPixmap("mascot.png")
            scaled_pixmap = pixmap.scaled(150, 150, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.mascotDisplay.setPixmap(scaled_pixmap)
        self.mascotDisplay.setFixedSize(150, 150)
        rightPanelLayout.addWidget(self.mascotDisplay, alignment=QtCore.Qt.AlignCenter)

        buttonSize = QtCore.QSize(180, 50)
        self.pokeButton = QtWidgets.QPushButton("Poke")
        self.pokeButton.setFixedSize(buttonSize)
        self.pokeButton.clicked.connect(lambda: self.changeMascot("mad.png"))
        rightPanelLayout.addWidget(self.pokeButton, alignment=QtCore.Qt.AlignCenter)

        self.bullyButton = QtWidgets.QPushButton("Bully")
        self.bullyButton.setFixedSize(buttonSize)
        self.bullyButton.clicked.connect(lambda: self.changeMascot("sad.png"))
        rightPanelLayout.addWidget(self.bullyButton, alignment=QtCore.Qt.AlignCenter)

        self.headPatButton = QtWidgets.QPushButton("Head Pat")
        self.headPatButton.setFixedSize(buttonSize)
        self.headPatButton.clicked.connect(lambda: self.changeMascot("pat.png"))
        rightPanelLayout.addWidget(self.headPatButton, alignment=QtCore.Qt.AlignCenter)

        rightPanelLayout.addStretch()
        finalRowLayout.addWidget(rightPanel, stretch=1)

        mainLayout.addWidget(finalRowWidget, stretch=1)

    def changeMascot(self, imagePath):
        if os.path.exists(imagePath):
            pixmap = QtGui.QPixmap(imagePath)
            scaled_pixmap = pixmap.scaled(150, 150, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.mascotDisplay.setPixmap(scaled_pixmap)
            QtCore.QTimer.singleShot(1000, self.restoreMascot)

    def restoreMascot(self):
        if os.path.exists("mascot.png"):
            pixmap = QtGui.QPixmap("mascot.png")
            scaled_pixmap = pixmap.scaled(150, 150, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.mascotDisplay.setPixmap(scaled_pixmap)

    def loadSettings(self):
        font_size = self.settings.value("font_size", 18, type=int)
        self.appFont.setPointSize(font_size)
        self.setFont(self.appFont)
        self.apiPriority = self.settings.value("api_priority", "Auto")
        self.interface_language = self.settings.value("interface_language", "English")
        self.theme_mode = self.settings.value("theme_mode", "Dark")

    def openSettings(self):
        current = {
            "api_priority": self.apiPriority,
            "interface_language": self.interface_language,
            "theme_mode": self.theme_mode
        }
        dlg = SettingsDialog(current, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            new_settings = dlg.getSettings()
            self.settings.setValue("api_priority", new_settings["api_priority"])
            self.settings.setValue("interface_language", new_settings.get("interface_language", "English"))
            self.settings.setValue("theme_mode", new_settings.get("theme_mode", "Dark"))
            self.apiPriority = new_settings["api_priority"]
            self.interface_language = new_settings["interface_language"]
            self.theme_mode = new_settings["theme_mode"]
            if self.theme_mode == "Dark":
                self.darkMode = True
                self.applyDarkStyle()
            else:
                self.darkMode = False
                self.applyLightStyle()

    def toggleTheme(self):
        # This function is no longer used because theme is set in settings.
        pass

    def applyDarkStyle(self):
        self.headerLabel.setStyleSheet("color: white;")
        self.folderDisplay.setStyleSheet(
            "background-color: #333; padding: 12px; border-radius: 10px; border: 2px solid #555; min-width: 500px; color: white;"
        )
        self.progressBar.setStyleSheet(
            "QProgressBar { background-color: #333; border: 2px solid #555; border-radius: 10px; text-align: center; color: white; }"
            "QProgressBar::chunk { background-color: #FF6433; border-radius: 8px; }"
        )
        self.logTextEdit.setStyleSheet("border: 2px solid #555; padding: 12px; background-color: #252526; color: white;")
        self.setStyleSheet("""
        QMainWindow { background-color: #1e1e1e; }
        QWidget { background-color: #1e1e1e; color: white; font-family: 'AtkinsonHyperlegibleMono-Bold'; font-size: 18px; }
        QLabel { color: white; font-size: 18px; font-weight: bold; }
        QPushButton { background-color: #007acc; color: white; border-radius: 12px; padding: 14px; font-size: 18px; font-weight: bold; }
        QPushButton:hover { background-color: #005f99; }
        QComboBox { background-color: #333; color: white; border-radius: 8px; padding: 10px; font-size: 18px; }
        QTextEdit { background-color: #252526; color: white; border-radius: 8px; padding: 12px; font-size: 18px; }
        QScrollBar:vertical { background-color: #333; width: 10px; margin: 0; border: none; border-radius: 5px; }
        QScrollBar::handle:vertical { background-color: #007acc; min-height: 20px; border-radius: 5px; }
        QScrollBar::handle:vertical:hover { background-color: #005f99; }
        QScrollBar:horizontal { background-color: #333; height: 10px; margin: 0; border: none; border-radius: 5px; }
        QScrollBar::handle:horizontal { background-color: #007acc; min-width: 20px; border-radius: 5px; }
        QScrollBar::handle:horizontal:hover { background-color: #005f99; }
        """)

    def applyLightStyle(self):
        self.headerLabel.setStyleSheet("color: black;")
        self.folderDisplay.setStyleSheet(
            "background-color: #e0e0e0; padding: 12px; border-radius: 10px; border: 2px solid #ccc; min-width: 500px; color: black;"
        )
        self.progressBar.setStyleSheet(
            "QProgressBar { background-color: #e0e0e0; border: 2px solid #ccc; border-radius: 10px; text-align: center; color: black; }"
            "QProgressBar::chunk { background-color: #FF6433; border-radius: 8px; }"
        )
        self.logTextEdit.setStyleSheet("border: 2px solid #ccc; padding: 12px; background-color: #f5f5f5; color: black;")
        self.setStyleSheet("""
        QMainWindow { background-color: #ffffff; }
        QWidget { background-color: #ffffff; color: #000000; font-family: 'AtkinsonHyperlegibleMono-Bold'; font-size: 18px; }
        QLabel { color: #000000; font-size: 18px; font-weight: bold; }
        QPushButton { background-color: #007acc; color: white; border-radius: 12px; padding: 14px; font-size: 18px; font-weight: bold; }
        QPushButton:hover { background-color: #005f99; }
        QComboBox { background-color: #f0f0f0; color: black; border-radius: 8px; padding: 10px; font-size: 18px; }
        QTextEdit { background-color: #f5f5f5; color: black; border-radius: 8px; padding: 12px; font-size: 18px; }
        QScrollBar:vertical { background-color: #f0f0f0; width: 10px; margin: 0; border: none; border-radius: 5px; }
        QScrollBar::handle:vertical { background-color: #007acc; min-height: 20px; border-radius: 5px; }
        QScrollBar::handle:vertical:hover { background-color: #005f99; }
        QScrollBar:horizontal { background-color: #f0f0f0; height: 10px; margin: 0; border: none; border-radius: 5px; }
        QScrollBar::handle:horizontal { background-color: #007acc; min-width: 20px; border-radius: 5px; }
        QScrollBar::handle:horizontal:hover { background-color: #005f99; }
        """)

    def browseFolder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folderDisplay.setText(folder)
            self.startBtn.setEnabled(True)
            self.progressBar.setValue(0)
            self.logTextEdit.clear()

    def startRenaming(self):
        folder = self.folderDisplay.text().strip()
        if not folder or not os.path.isdir(folder):
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a valid folder.")
            return

        lang_choice = self.languageCombo.currentText()
        self.title_preference = "english" if lang_choice.lower() == "english" else "romaji"
        self.logTextEdit.append(f"Starting renaming in folder: {folder}")
        self.logTextEdit.append(f"Selected title language: {lang_choice}")

        files = [f for f in os.listdir(folder) if f.endswith(".webm")]
        if not files:
            self.logTextEdit.append("⚠️ No .webm files found in this folder.")
            return
        self.progressBar.setMaximum(len(files))

        functions = {
            'anilist': self.get_anime_title_anilist,
            'mal': self.get_anime_title_mal,
            'title_case': self.format_title_case,
            'expand_season': self.expand_season_format,
            'format_mal': self.format_for_mal_search
        }

        self.startBtn.setEnabled(False)
        self.worker = RenameWorker(folder, self.title_preference, functions)
        self.worker.logSignal.connect(self.appendLog)
        self.worker.progressSignal.connect(self.updateProgress)
        self.worker.finishedSignal.connect(self.onRenameFinished)
        self.worker.start()

    def previewFilenames(self):
        folder = self.folderDisplay.text().strip()
        if not folder or not os.path.isdir(folder):
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a valid folder.")
            return

        lang_choice = self.languageCombo.currentText()
        self.title_preference = "english" if lang_choice.lower() == "english" else "romaji"

        self.previewDialog = PreviewDialog(self)
        self.previewDialog.show()

        files = [f for f in os.listdir(folder) if f.endswith(".webm")]
        if not files:
            self.previewDialog.appendText("⚠️ No .webm files found in this folder.")
            return
        self.progressBar.setMaximum(len(files))

        functions = {
            'anilist': self.get_anime_title_anilist,
            'mal': self.get_anime_title_mal,
            'title_case': self.format_title_case,
            'expand_season': self.expand_season_format,
            'format_mal': self.format_for_mal_search
        }

        self.previewButton.setEnabled(False)
        self.worker = RenameWorker(folder, self.title_preference, functions, previewMode=True)
        self.worker.logSignal.connect(self.previewDialog.appendText)
        self.worker.progressSignal.connect(self.updateProgress)
        self.worker.finishedSignal.connect(self.onPreviewFinished)
        self.worker.start()

    def onPreviewFinished(self):
        self.previewDialog.appendText("Preview complete!")
        self.previewButton.setEnabled(True)

    def appendLog(self, message):
        self.logTextEdit.append(message)

    def updateProgress(self, value):
        self.progressBar.setValue(value)

    def onRenameFinished(self):
        self.logTextEdit.append("Renaming complete!")
        self.startBtn.setEnabled(True)

    def get_anime_title_anilist(self, query):
        url = "https://graphql.anilist.co"
        query_graphql = '''
        query ($search: String) {
          Media(search: $search, type: ANIME) {
            title {
              romaji
              english
            }
          }
        }
        '''
        variables = {"search": query}
        try:
            response = requests.post(url, json={"query": query_graphql, "variables": variables})
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "Media" in data["data"]:
                    titles = data["data"]["Media"]["title"]
                    return titles.get(self.title_preference) or titles.get("english") or titles.get("romaji")
        except Exception as e:
            self.logTextEdit.append(f"⚠️ AniList request failed: {e}")
        return None

    def get_anime_title_mal(self, query):
        formatted_query = self.format_for_mal_search(query)
        self.logTextEdit.append(f"🔎 Searching MAL with: {formatted_query}")
        url = f"https://api.jikan.moe/v4/anime?q={formatted_query}&limit=1"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if "data" in data and len(data["data"]) > 0:
                    return data["data"][0]["title"]
        except Exception as e:
            self.logTextEdit.append(f"⚠️ MAL request failed: {e}")
        return None

    def format_for_mal_search(self, title):
        title = re.sub(r'S(\d+)Part(\d+)', r'Season \1 Part \2', title, flags=re.IGNORECASE)
        title = re.sub(r'S(\d+)', r'Season \1', title, flags=re.IGNORECASE)
        title = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', title)
        return title.strip()

    def format_title_case(self, title):
        lowercase_words = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "nor",
                           "of", "on", "or", "so", "the", "to", "up", "yet"}
        words = title.split()
        if not words:
            return title
        formatted_words = [words[0].capitalize()]
        for word in words[1:]:
            formatted_words.append(word.lower() if word.lower() in lowercase_words else word.capitalize())
        return " ".join(formatted_words)

    def expand_season_format(self, filename):
        filename = re.sub(r'S(\d+)Part(\d+)', r'Season \1 Part \2', filename, flags=re.IGNORECASE)
        filename = re.sub(r'S(\d+)\b', r'Season \1', filename, flags=re.IGNORECASE)
        return filename

    def loadSettings(self):
        font_size = self.settings.value("font_size", 18, type=int)
        self.appFont.setPointSize(font_size)
        self.setFont(self.appFont)
        self.apiPriority = self.settings.value("api_priority", "Auto")
        self.interface_language = self.settings.value("interface_language", "English")
        self.theme_mode = self.settings.value("theme_mode", "Dark")

    def openSettings(self):
        current = {
            "api_priority": self.apiPriority,
            "interface_language": self.interface_language,
            "theme_mode": self.theme_mode
        }
        dlg = SettingsDialog(current, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            new_settings = dlg.getSettings()
            self.settings.setValue("api_priority", new_settings["api_priority"])
            self.settings.setValue("interface_language", new_settings.get("interface_language", "English"))
            self.settings.setValue("theme_mode", new_settings.get("theme_mode", "Dark"))
            self.apiPriority = new_settings["api_priority"]
            self.interface_language = new_settings["interface_language"]
            self.theme_mode = new_settings["theme_mode"]
            if self.theme_mode == "Dark":
                self.darkMode = True
                self.applyDarkStyle()
            else:
                self.darkMode = False
                self.applyLightStyle()

if __name__ == "__main__":
    # Remove console window on Windows
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.FreeConsole()
    app = QtWidgets.QApplication(sys.argv)
    window = AnimeRenamerWindow()
    window.show()
    sys.exit(app.exec_())
