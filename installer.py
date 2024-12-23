import sys, os, requests, shutil, subprocess, zipfile
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QErrorMessage, QMessageBox, QComboBox, QCheckBox, QLineEdit, QLabel
from PyQt6.QtCore import Qt

USER = os.getlogin()
print(f"Logged in as: {USER}")
if USER == "root" and sys.platform != "win32":
    USER  = os.environ.get("USER")
    print(f"Corrected; Logged in as: {USER}")

def startfile(path):
    if sys.platform == "win32":
        os.startfile(path)
    else:
        subprocess.Popen(path)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyaiiTTS Installer")
        self.setFixedSize(self.minimumSize())
        self.platName = "win" if sys.platform == "win32" else sys.platform
        if sys.platform == "darwin": self.platName = "mac"
        self.def_loc = f"/home/{USER}/.local/share" # Linux ~/.local/share
        if sys.platform != "win32" or sys.platform == "darwin":
            # Windows C:\Users\<user>\AppData\Local\Programs | macOS ~/Applications
            self.def_loc = f"C:/Users/{USER}/AppData/Local/Programs" if sys.platform == "win32" else f"/Users/{USER}/Applications"
        self.dir = self.def_loc
        
        resetdir = QPushButton("⟲")
        resetdir.setToolTip("Reset the install directory to:\n"+self.def_loc)
        resetdir.clicked.connect(self.re_dir)
        
        self.choosedir = QPushButton("Choose Program Directory ("+self.dir+")")
        self.choosedir.clicked.connect(self.set_dir)
        
        self.choosever = QComboBox()
        self.choosever.activated.connect(self.change_ver)

        self.dlassets = QCheckBox("Install Assets")
        self.dlassets.setToolTip("Install assets (required by >=v1.3-pre1 on Linux/Windows)\nAlready built-in to binaries on macOS")
        self.dlassets.clicked.connect(self.toggle_dl_assets)
        
        self.odone = QCheckBox("Open When Done")
        self.odone.setToolTip("Automatically open PyaiiTTS after it is finished installing")
        
        keylbl = QLabel("API Key:")
        
        self.key = QLineEdit()
        self.key.setPlaceholderText("Paste ElevenLabs API key here...")
        
        key_layout = QHBoxLayout()
        key_layout.addWidget(keylbl)
        key_layout.addWidget(self.key,1)
        
        check_layout = QHBoxLayout()
        check_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        check_layout.addWidget(self.dlassets)
        check_layout.addWidget(self.odone)
        
        refresh = QPushButton("⟲")
        refresh.setToolTip("Refresh version list")
        refresh.clicked.connect(self.re_vers)
        
        install = QPushButton("Install PyaiiTTS")
        install.clicked.connect(self.install)
        
        update = QPushButton("Update PyaiiTTS")
        update.clicked.connect(self.update)
        
        uninstall = QPushButton("Uninstall PyaiiTTS")
        uninstall.clicked.connect(self.uninstall)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(resetdir)
        dir_layout.addWidget(self.choosedir,1)
        
        ver_layout = QHBoxLayout()
        ver_layout.addWidget(refresh)
        ver_layout.addWidget(self.choosever,1)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addLayout(ver_layout)
        layout.addLayout(dir_layout)
        layout.addLayout(key_layout)
        layout.addLayout(check_layout)
        layout.addWidget(install)
        layout.addWidget(update)
        layout.addWidget(uninstall)
        
        self.setLayout(layout)
        
        self.em = QErrorMessage(self)
        self.em.setWindowTitle("PyaiiTTS Installer | Error")
        
        self.vers = []
        try:
            self.vers = self.get_vers()
        except Exception as e:
            self.error(e)
        self.choosever.addItems(self.vers)
        self.choosever.setCurrentIndex(0)
        self.change_ver()
    
    def toggle_dl_assets(self):
        self.DlAssets = not self.DlAssets
   
    def re_dir(self):
        self.dir = self.def_loc
        self.choosedir.setText("Choose Program Directory ("+self.dir+")")
    
    def re_vers(self):
        try:
            self.choosever.clear()
            self.vers = self.get_vers()
            self.choosever.addItems(self.vers)
            self.choosever.setCurrentIndex(0)
        except Exception as e:
            self.error(e)
    
    def get_vers(self):
        try:
            api_url = f'https://api.github.com/repos/DatBogie/PyaiiTTS/releases'
            
            response = requests.get(api_url)
            response.raise_for_status()
            
            releases = response.json()
            return [release['tag_name'] for release in releases]
        except Exception as e:
            self.error(e)
    
    def error(self,e:Exception|str):
        if type(e) != str:
            self.em.showMessage(str(e))
        else:
            QMessageBox.critical(self,"PyaiiTTS Installer | Error",e,QMessageBox.StandardButton.Ok)
    
    def change_ver(self):
        self.ver = self.choosever.currentText()
        ver = self.choosever.count()-self.choosever.currentIndex()
        mver = self.ver[1:]
        if "-" in mver:
            mver = mver[:mver.find("-")]
        if "." in mver:
            mver = mver[:mver.find(".")] + mver[mver.find(".")+1:]
        mver = float(mver)
        print(f"v{mver}, #{ver}")
        # assets already copied into exec on mac binaries
        if mver < 13.0 or sys.platform == "darwin":
            self.dlassets.setChecked(False)
            self.dlassets.setCheckable(False)
            self.DlAssets = False
        else:
            self.dlassets.setChecked(True)
            self.dlassets.setCheckable(True)
            self.DlAssets = True
        if ver <= 7:
            self.odone.setChecked(False)
            self.odone.setCheckable(False)
        else:
            self.odone.setChecked(True)
            self.odone.setCheckable(True)
        self.dlassets.setChecked(self.DlAssets)
    
    def update(self):
        try:
            p = self.dir+("/PyaiiTTS/" if sys.platform != "darwin" else "/")
            if not os.path.exists(p): p = self.def_loc+("/PyaiiTTS/" if sys.platform != "darwin" else "/")
            if not os.path.exists(p): self.error("Error: No valid directory found."); return
            exec_file,exec_name = self.dl_exec()
            with open(p+exec_name,"wb") as f:
                f.write(exec_file)
            if sys.platform == "darwin":
                with zipfile.ZipFile(p+exec_name, 'r') as zip_ref:
                    zip_ref.extractall(p)
                os.remove(p+exec_name)
                if os.path.exists(self.dir+"/__MACOSX"):
                    shutil.rmtree(self.dir+"/__MACOSX",True)
                exec_name = "PyaiiTTS.app"
            if sys.platform != "win32":
                st = os.stat(p+exec_name)
                os.chmod(p+exec_name, st.st_mode | 0o111)
            for x in os.scandir(p):
                if x.is_file() and x.name != exec_name and x.name.find(self.platName) != -1:
                    os.remove(x.path)
            if os.path.exists(p+"assets"):
                shutil.rmtree(p+"assets")
            if self.DlAssets:
                self.dl_assets(exec_name=exec_name)
            QMessageBox.information(self,"PyaiiTTS Installer | Update","Update successfully installed!",QMessageBox.StandardButton.Ok)
            if self.key.text() != "" and len(self.key.text()) > 50: # Probably valid.
                with open(self.dir+("/PyaiiTTS/" if sys.platform != "darwin" else f"/{exec_name}/Contents/MacOS/")+"key.txt","w") as f:
                    f.write(self.key.text())
            if self.odone.isChecked():
                startfile(self.dir+("/PyaiiTTS/" if sys.platform != "darwin" else "/")+exec_name+("" if sys.platform != "darwin" else "/Contents/MacOS/PyaiiTTS"))
        except Exception as e:
            self.error(e)
    
    def set_dir(self):
        x = QFileDialog.getExistingDirectory(self,"Choose a directory to install PyaiiTTS to.",self.dir)
        if x:
            self.dir = x
        self.choosedir.setText("Choose Program Directory ("+self.dir+")")
    
    def install(self):
        if sys.platform != "darwin" and os.path.exists(self.dir+"/PyaiiTTS"):
            for f in os.scandir(self.dir+"/PyaiiTTS"):
                if f.is_file() and f.name.find(self.platName) != -1:
                    self.error("Error: PyaiiTTS has already been installed here! Please update instead.")
                    return
        elif sys.platform == "darwin":
            if os.path.exists(self.dir+"/PyaiiTTS.app"):
                self.error("Error: PyaiiTTS has already been installed here! Please update insted.")
                return
        try:
            exec_file,exec_name = self.dl_exec()
            if not os.path.exists(self.dir+"/PyaiiTTS") and sys.platform != "darwin":
                os.mkdir(self.dir+"/PyaiiTTS")
            with open(self.dir+("/PyaiiTTS/" if sys.platform != "darwin" else "/")+exec_name,"wb") as f:
                f.write(exec_file)
            if sys.platform == "darwin":
                with zipfile.ZipFile(self.dir+"/"+exec_name, 'r') as zip_ref:
                    zip_ref.extractall(self.dir)
                os.remove(self.dir+"/"+exec_name)
                if os.path.exists(self.dir+"/__MACOSX"):
                    shutil.rmtree(self.dir+"/__MACOSX",True)
                exec_name = "PyaiiTTS.app"
            if sys.platform != "win32":
                st = os.stat(self.dir+("/PyaiiTTS/" if sys.platform != "darwin" else "/")+exec_name+("/Contents/MacOS/PyaiiTTS" if sys.platform == "darwin" else ""))
                os.chmod(self.dir+("/PyaiiTTS/" if sys.platform != "darwin" else "/")+exec_name+("/Contents/MacOS/PyaiiTTS" if sys.platform == "darwin" else ""), st.st_mode | 0o111)
            os.mkdir(self.dir+f"{"/PyaiiTTS/" if sys.platform != "darwin" else f"/{exec_name}/Contents/MacOS/"}output")
            if self.DlAssets:
                self.dl_assets(exec_name=exec_name)
            QMessageBox.information(self,"PyaiiTTS Installer | Install","PyaiiTTS successfully installed!",QMessageBox.StandardButton.Ok)
            if self.key.text() != "" and len(self.key.text()) > 20: # Probably valid.
                if sys.platform != "darwin":
                    with open(self.dir+"/PyaiiTTS/"+"key.txt","w") as f:
                        f.write(self.key.text())
                else:
                    with open(f"{self.dir}/{exec_name}/Contents/MacOS/key.txt","w") as f:
                        f.write(self.key.text())
            if self.odone.isChecked():
                startfile(self.dir+("/PyaiiTTS/" if sys.platform != "darwin" else "/")+exec_name+("" if sys.platform != "darwin" else "/Contents/MacOS/PyaiiTTS"))
        except Exception as e:
            self.error(e)
    
    def uninstall(self):
        try:
            x = QMessageBox.question(self,"PyaiiTTS Installer | Uninstall","Are you sure you want to uninstall PyaiiTTS?",QMessageBox.StandardButton.Yes,QMessageBox.StandardButton.No)
            if x != QMessageBox.StandardButton.Yes: return
            p = self.dir+"/PyaiiTTS"+(".app" if sys.platform == "darwin" else "")
            if not os.path.exists(p): p = self.def_loc+"/PyaiiTTS"+(".app" if sys.platform == "darwin" else "")
            if not os.path.exists(p): QMessageBox.critical(self,"PyaiiTTS Installer | Uninstall",f"PyaiiTTS was not found the specified directory:\n{self.dir}/PyaiiTTS",QMessageBox.StandardButton.Abort); return
            shutil.rmtree(self.dir+"/PyaiiTTS"+(".app" if sys.platform == "darwin" else ""))
            QMessageBox.information(self,"PyaiiTTS Installer | Uninstall","PyaiiTTS successfully uninstalled!",QMessageBox.StandardButton.Ok)
        except Exception as e:
            self.error(e)
    
    def dl_assets(self,path:str|None=None,subdir:str="",exec_name=""):
        try:
            if not path:
                path = self.dir+"/PyaiiTTS/assets/" if sys.platform != "darwin" else self.dir+"/"+exec_name+"/assets/"
            api_url = f"https://api.github.com/repos/DatBogie/PyaiiTTS/contents/assets{subdir}"
            response = requests.get(api_url)
            response.raise_for_status()
            
            assets = response.json()
            
            if not os.path.exists(path):
                os.mkdir(path)
            
            for asset in assets:
                if asset["type"] == "file":
                    asset_url = asset["download_url"]
                    asset_response = requests.get(asset_url)
                    asset_response.raise_for_status()
                    
                    asset_path = os.path.join(path,asset["name"])
                    with open(asset_path,"wb") as f:
                        f.write(asset_response.content)
                    print(f"Downloaded {asset_path}")
                elif asset["type"] == "dir":
                    self.dl_assets(os.path.join(path,asset["name"]),asset["name"])
            
        except Exception as e:
            self.error(e)
        
    def dl_exec(self) -> tuple[str,str]:
        api_url = f"https://api.github.com/repos/DatBogie/PyaiiTTS/releases/tags/{self.ver}"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            release_info = response.json()
            asset_url = None
            asset_name = ""
            for asset in release_info["assets"]:
                if asset["name"].find(self.platName) != -1 and asset["name"].find("installer") == -1: # choose which to dl | right platform and not installer
                    asset_url = asset["url"]
                    asset_name = asset["name"]
                    break
            print(asset_url,asset_name)
            if asset_url:
                headers = {'Accept': 'application/octet-stream'}
                dl_response = requests.get(asset_url, headers=headers)

                if dl_response.status_code == 200:
                    return (dl_response.content,asset_name)
                else:
                    print(dl_response.status_code)
            else:
                print(release_info["assets"])
        else:
            self.error(f"GitHub API response failed with code {response.status_code}.")
        return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    if sys.platform != "darwin": app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())