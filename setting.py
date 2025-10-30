import json
import os


class SettingData:
    def __init__(self, path="settings.json"):
        self.path = path
        self.data = {
            "port": 19995,
            "withdraw_password": "868686",  # mật khẩu rút tiền
            "total_thread": 1         # tổng số thread
        }
        self.load()

    def load(self):
        if os.path.exists(self.path):
            self.data.update(json.load(open(self.path, "r", encoding="utf-8")))

    def save(self):
        json.dump(self.data, open(self.path, "w", encoding="utf-8"), indent=4)

setting_data = SettingData()