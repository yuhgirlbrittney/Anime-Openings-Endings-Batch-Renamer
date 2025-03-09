import sys
import os
import re
import requests
import webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets

# Worker thread for file renaming or previewing
class RenameWorker(QtCore.QThread):
    logSignal = QtCore.pyqtSignal(str)
    progressSignal = QtCore.pyqtSignal(int)
    finishedSignal = QtCore.pyqtSignal()

    def __init__(self, folder, title_preference, functions, previewMode=False, parent=None):
        super().__init__(parent)
        self.folder = folder
        self.title_preference = title_preference
        self.previewMode = previewMode
        # Dictionary of function references from the main window
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


# Preview Dialog Window
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


class AnimeRenamerWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anime Openings & Endings Batch Renamer")
        self.setFixedSize(950, 600)

        if os.path.exists("mascot.png"):
            self.setWindowIcon(QtGui.QIcon("mascot.png"))

        self.appFont = QtGui.QFont("AtkinsonHyperlegibleMono-Bold", 18)
        self.setFont(self.appFont)
        self.darkMode = True

        self.headerLabel = QtWidgets.QLabel("Anime Openings & Endings Batch Renamer")
        self.headerLabel.setFont(QtGui.QFont("AtkinsonHyperlegibleMono-Bold", 24))
        self.headerLabel.setAlignment(QtCore.Qt.AlignCenter)

        # Create a toolbar in the upper left for the theme toggle
        self.toolbar = QtWidgets.QToolBar("Theme")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QtCore.QSize(24, 24))
        # Add the toolbar to the left side
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbar)
        self.themeAction = QtWidgets.QAction("Toggle Theme", self)
        self.themeAction.setCheckable(True)
        self.themeAction.setChecked(True)  # Dark mode is default
        self.themeAction.setText("🌙")  # Use moon icon for dark mode
        self.themeAction.triggered.connect(self.toggleTheme)
        self.toolbar.addAction(self.themeAction)

        centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QtWidgets.QVBoxLayout(centralWidget)
        mainLayout.setContentsMargins(20, 20, 20, 5)
        mainLayout.setSpacing(20)

        mainLayout.addWidget(self.headerLabel)

        folderLayout = QtWidgets.QHBoxLayout()
        self.folderDisplay = QtWidgets.QLabel("No folder selected")
        self.folderDisplay.setFont(self.appFont)
        self.folderDisplay.setStyleSheet(
            "background-color: #333; padding: 12px; border-radius: 10px; "
            "border: 2px solid #555; min-width: 420px; color: white;"
        )
        browseBtn = QtWidgets.QPushButton("Select Folder")
        browseBtn.setFixedSize(180, 65)
        browseBtn.setFont(self.appFont)
        browseBtn.setToolTip("Select a folder containing your anime .webm files")
        browseBtn.clicked.connect(self.browseFolder)
        folderLayout.addWidget(self.folderDisplay)
        folderLayout.addWidget(browseBtn)
        mainLayout.addLayout(folderLayout)

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

        # Horizontal layout for Preview and Start buttons
        buttonLayout = QtWidgets.QHBoxLayout()
        self.previewButton = QtWidgets.QPushButton("Preview Filenames")
        self.previewButton.setFixedSize(260, 55)
        self.previewButton.setFont(self.appFont)
        self.previewButton.setToolTip("Click to preview new filenames without renaming")
        self.previewButton.clicked.connect(self.previewFilenames)
        buttonLayout.addWidget(self.previewButton, alignment=QtCore.Qt.AlignLeft)

        self.startBtn = QtWidgets.QPushButton("Start Renaming")
        self.startBtn.setFixedSize(260, 55)
        self.startBtn.setFont(self.appFont)
        self.startBtn.setToolTip("Click to start renaming your files")
        self.startBtn.setEnabled(False)
        self.startBtn.clicked.connect(self.startRenaming)
        buttonLayout.addWidget(self.startBtn, alignment=QtCore.Qt.AlignRight)
        mainLayout.addLayout(buttonLayout)

        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setFixedHeight(25)
        self.progressBar.setValue(0)
        self.progressBar.setStyleSheet("QProgressBar { background-color: #333; border: 2px solid #555; border-radius: 10px; text-align: center; color: white; } QProgressBar::chunk { background-color: #007acc; border-radius: 8px; }")
        mainLayout.addWidget(self.progressBar)

        self.logTextEdit = QtWidgets.QTextEdit()
        self.logTextEdit.setReadOnly(True)
        self.logTextEdit.setFixedHeight(100)
        self.logTextEdit.setFont(self.appFont)
        self.logTextEdit.setStyleSheet("border: 2px solid #555; padding: 12px; background-color: #252526; color: white;")
        mainLayout.addWidget(self.logTextEdit)

        mainLayout.addSpacing(20)

        bottomLayout = QtWidgets.QHBoxLayout()
        self.tipButton = QtWidgets.QPushButton("Support me on Ko-fi")
        self.tipButton.setFont(QtGui.QFont("AtkinsonHyperlegibleMono-Bold", 16, QtGui.QFont.Bold))
        self.tipButton.setFixedSize(260, 55)
        self.tipButton.setToolTip("Click to support me on Ko-fi!")
        self.tipButton.clicked.connect(self.openDonationPage)
        self.tipButton.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: white;
                border-radius: 12px;
                padding: 14px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7b1fa2;
            }
        """)
        bottomLayout.addWidget(self.tipButton, alignment=QtCore.Qt.AlignLeft)
        bottomLayout.addStretch()
        self.versionLabel = QtWidgets.QLabel("Version 1.0.0")
        self.versionLabel.setFont(QtGui.QFont("AtkinsonHyperlegibleMono-Bold", 14))
        self.versionLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.versionLabel.setStyleSheet("color: #888;")
        bottomLayout.addWidget(self.versionLabel, alignment=QtCore.Qt.AlignRight)
        mainLayout.addLayout(bottomLayout)

        self.mascotLabel = QtWidgets.QLabel(self)
        self.mascotLabel.setScaledContents(False)
        self.mascotLabel.setStyleSheet("background: transparent;")
        self.mascotLabel.setGeometry(520, 107, 200, 310)
        if os.path.exists("mascot.png"):
            pixmap = QtGui.QPixmap("mascot.png")
            scaled_pixmap = pixmap.scaled(200, 150, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.mascotLabel.setPixmap(scaled_pixmap)

        self.applyDarkStyle()

        self.lowercase_words = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "nor",
                                "of", "on", "or", "so", "the", "to", "up", "yet"}

        self.worker = None

    def toggleTheme(self):
        self.darkMode = not self.darkMode
        if self.darkMode:
            self.applyDarkStyle()
            self.themeAction.setText("🌙")
            self.themeAction.setChecked(True)
        else:
            self.applyLightStyle()
            self.themeAction.setText("🌞")
            self.themeAction.setChecked(False)
            
    def applyDarkStyle(self):
        self.headerLabel.setStyleSheet("color: white;")
        self.folderDisplay.setStyleSheet("background-color: #333; padding: 12px; border-radius: 10px; border: 2px solid #555; min-width: 420px; color: white;")
        self.progressBar.setStyleSheet("QProgressBar { background-color: #333; border: 2px solid #555; border-radius: 10px; text-align: center; color: white; } QProgressBar::chunk { background-color: #007acc; border-radius: 8px; }")
        self.logTextEdit.setStyleSheet("border: 2px solid #555; padding: 12px; background-color: #252526; color: white;")
        styleSheet = """
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
        """
        self.setStyleSheet(styleSheet)

    def applyLightStyle(self):
        self.headerLabel.setStyleSheet("color: black;")
        self.folderDisplay.setStyleSheet("background-color: #e0e0e0; padding: 12px; border-radius: 10px; border: 2px solid #ccc; min-width: 420px; color: black;")
        self.progressBar.setStyleSheet("QProgressBar { background-color: #e0e0e0; border: 2px solid #ccc; border-radius: 10px; text-align: center; color: black; } QProgressBar::chunk { background-color: #007acc; border-radius: 8px; }")
        self.logTextEdit.setStyleSheet("border: 2px solid #ccc; padding: 12px; background-color: #f5f5f5; color: black;")
        styleSheet = """
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
        """
        self.setStyleSheet(styleSheet)

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

    def openDonationPage(self):
        webbrowser.open("https://ko-fi.com/yuhgirlbrittney")

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
        lowercase_words = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "nor", "of", "on", "or", "so", "the", "to", "up", "yet"}
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


if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.FreeConsole()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = AnimeRenamerWindow()
    window.show()
    sys.exit(app.exec_())
