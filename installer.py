import sys, os, requests, shutil, stat
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QErrorMessage, QMessageBox
from PyQt6.QtCore import Qt

USER = os.getlogin()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyaiiTTS Installer")
        self.setFixedSize(self.minimumSize())
        self.platName = "win" if sys.platform == "win32" else sys.platform
        self.def_loc = f"/home/{USER}/.local/share" if sys.platform != "win32" else f"C:/Users/{USER}/AppData/Local/Programs"
        self.dir = self.def_loc
        
        self.choosedir = QPushButton("Choose Program Directory ("+self.dir+")")
        self.choosedir.clicked.connect(self.set_dir)
        
        install = QPushButton("Install PyaiiTTS")
        install.clicked.connect(self.install)
        
        update = QPushButton("Update PyaiiTTS")
        update.clicked.connect(self.update)
        
        uninstall = QPushButton("Uninstall PyaiiTTS")
        uninstall.clicked.connect(self.uninstall)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.choosedir)
        layout.addWidget(install)
        layout.addWidget(update)
        layout.addWidget(uninstall)
        
        self.setLayout(layout)
        
        self.em = QErrorMessage(self)
        self.em.setWindowTitle("PyaiiTTS Installer | Error")
    
    def error(self,e:Exception|str):
        if type(e) != str:
            self.em.showMessage(str(e))
        else:
            QMessageBox.critical(self,"PyaiiTTS Installer | Error",e,QMessageBox.StandardButton.Ok)
    
    def update(self):
        try:
            p = self.def_loc+"/PyaiiTTS/"
            if not os.path.exists(p): p = self.dir+"/PyaiiTTS/"
            if not os.path.exists(p): self.error("Error: No valid directory found."); return
            exec_file,exec_name = self.dl_exec()
            with open(p+exec_name,"wb") as f:
                f.write(exec_file)
            if sys.platform != "win32":
                st = os.stat(p+exec_name)
                os.chmod(p+exec_name, st.st_mode | 0o111)
            for x in os.scandir(p):
                if x.is_file() and x.name != exec_name and x.name.find(self.platName) != -1:
                    os.remove(x.path)
            if os.path.exists(p+"assets"):
                shutil.rmtree(p+"assets")
            self.dl_assets()
            QMessageBox.information(self,"PyaiiTTS Installer | Update","Update successfully installed!",QMessageBox.StandardButton.Ok)
        except Exception as e:
            self.error(e)
    
    def set_dir(self):
        x = QFileDialog.getExistingDirectory(self,"Choose a directory to install PyaiiTTS to.",self.dir)
        if x:
            self.dir = x
        self.choosedir.setText("Choose Program Directory ("+self.dir+")")
    
    def install(self):
        try:
            exec_file,exec_name = self.dl_exec()
            if not os.path.exists(self.dir+"/PyaiiTTS"):
                os.mkdir(self.dir+"/PyaiiTTS")
            with open(self.dir+"/PyaiiTTS/"+exec_name,"wb") as f:
                f.write(exec_file)
            if sys.platform != "win32":
                st = os.stat(self.dir+"/PyaiiTTS/"+exec_name)
                os.chmod(self.dir+"/PyaiiTTS/"+exec_name, st.st_mode | 0o111)
            os.mkdir(self.dir+"/PyaiiTTS/output")
            self.dl_assets()
            QMessageBox.information(self,"PyaiiTTS Installer | Install","PyaiiTTS successfully installed!",QMessageBox.StandardButton.Ok)
        except Exception as e:
            self.error(e)
    
    def uninstall(self):
        try:
            x = QMessageBox.question(self,"PyaiiTTS Installer | Uninstall","Are you sure you want to uninstall PyaiiTTS?",QMessageBox.StandardButton.Yes,QMessageBox.StandardButton.No)
            if x != QMessageBox.StandardButton.Yes: return
            p = self.def_loc+"/PyaiiTTS"
            if not os.path.exists(p): p = self.dir+"/PyaiiTTS"
            if not os.path.exists(p): return
            shutil.rmtree(self.dir+"/PyaiiTTS")
            QMessageBox.information(self,"PyaiiTTS Installer | Uninstall","PyaiiTTS successfully uninstalled!",QMessageBox.StandardButton.Ok)
        except Exception as e:
            self.error(e)
    
    def dl_assets(self,path:str|None=None,subdir:str=""):
        try:
            if not path:
                path = self.dir+"/PyaiiTTS/assets/"
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
        api_url = f"https://api.github.com/repos/DatBogie/PyaiiTTS/releases/latest"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            release_info = response.json()
            asset_url = None
            asset_name = ""
            for asset in release_info["assets"]:
                if (asset["name"].find("win") != -1 and sys.platform == "win32") or (asset["name"].find(sys.platform) != -1 and sys.platform != "win32"):
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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())