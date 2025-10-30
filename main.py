import json
import os
import random
import sys

import requests
from PySide6 import QtWidgets
from PySide6.QtCore import QRunnable, QObject, Signal, QTimer, QThreadPool
from PySide6.QtWidgets import QApplication
from untitled import Ui_MainWindow
from setting import setting_data
ROOTPATH = os.getcwd()
os.system(
    f"pyside6-uic {os.path.join(ROOTPATH, 'untitled.ui')} -o {os.path.join(ROOTPATH, 'untitled.py')}"
)

class RenameSignal(QObject):
    rename_finished_signal = Signal(object, object, object, object)


class Application(QtWidgets.QMainWindow, Ui_MainWindow):
    is_running = False

    def __init__(self):
        super(Application, self).__init__()
        self.global_threads = {}

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(12)

        self.setWindowTitle("Remove Proxy GPM - TG: @liquidape")

        self.ui.pushButton.clicked.connect(self.run)
        self.ui.lineEdit.textChanged.connect(self.on_port_changed)

        self.ui.lineEdit.setText(str(setting_data.data["port"]))
        
    def on_port_changed(self, text):
        try:
            port = int(text)
            setting_data.data["port"] = port
            setting_data.save()  # nếu m có hàm save() để lưu ra file thì gọi ở đây
            print(f"[INFO] Port updated to {port}")
        except ValueError:
            print("[WARN] Port không hợp lệ")

    def run(self):
        list_profile_id: list[str] = self.ui.plainTextEdit.toPlainText().splitlines()
        queue_profile_id = iter(list_profile_id)

        index = 1
        run_timer = QTimer()

        def on_thread_finished(idx: int,  profile_id: str, status: str, message: str):
            self.ui.textBrowser.append(f"{idx} - {profile_id} - {message}")
            if status == "fail":
                self.ui.textBrowser_2.append(profile_id)

        def start_next_thread():
            nonlocal index
            try:
                thread = RenameRunnable(index=index, profile_id=next(queue_profile_id))
                thread.signal.rename_finished_signal.connect(on_thread_finished)
                self.global_threads[index] = thread
                self.pool.start(thread)
                index += 1
            except StopIteration:
                run_timer.stop()

        run_timer.timeout.connect(start_next_thread)
        run_timer.start(100)


class RenameRunnable(QRunnable):
    def __init__(self, index: int, profile_id: str):
        QRunnable.__init__(self)
        self.index = index
        self.profile_id = profile_id
        self.signal = RenameSignal()

    def run(self):
        _message = ""
        _status = "success"
        try:
            _port = setting_data.data["port"]
            _response = requests.post(
                f"http://127.0.0.1:{_port}/api/v3/profiles/update/{self.profile_id}",
                data=json.dumps({
                    "raw_proxy": ""
                })
            )
            print(_response)
            print(_response.text)
            if _response.status_code == 200:
                _message = "Thành công"
            else:
                _message = "Thất bại"
                _status = "fail"
        except:
            _message = "Thất bại"
            _status = "fail"
        finally:
            self.signal.rename_finished_signal.emit(
                self.index,
                self.profile_id,
                _status,
                _message
            )

if __name__ == "__main__":
    app = QApplication([])
    window = Application()
    window.show()
    sys.exit(app.exec())
