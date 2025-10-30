import asyncio
import os
import random
import sys
import traceback

from playwright.async_api import async_playwright

ROOTPATH = os.getcwd()
os.system(
    f"pyside6-uic {os.path.join(ROOTPATH, 'untitled.ui')} -o {os.path.join(ROOTPATH, 'untitled.py')}"
)
import requests
from PySide6 import QtWidgets
from PySide6.QtCore import QThread, QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication
from untitled import Ui_MainWindow
from setting import setting_data


class RenameSignal(QObject):
    rename_finished_signal = Signal(object, object, object, object)


def generate_mock_bidv_account(length=14):
    if length < 6:
        raise ValueError("length nên >= 6")
    digits = ''.join(str(random.randint(0, 9)) for _ in range(length))
    return f"{digits}"


class Application(QtWidgets.QMainWindow, Ui_MainWindow):
    is_running = False

    def __init__(self):
        super(Application, self).__init__()
        self.global_threads = {}

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.occupied_threads_by_slot: dict[int, RenameThread] = {}

        self.setWindowTitle("Link Bank 566 - TG: @liquidape")

        self.ui.pushButton.clicked.connect(self.run)
        self.ui.lineEdit.textChanged.connect(self.on_port_changed)
        self.ui.line_edit_password_withdraw.setText(str(setting_data.data.get("withdraw_password", "")))
        self.ui.spin_box_total_thread.setValue(int(setting_data.data.get("total_thread", 1)))
        self.ui.line_edit_password_withdraw.textChanged.connect(self.on_withdraw_password_changed)
        self.ui.spin_box_total_thread.valueChanged.connect(self.on_total_thread_changed)

        self.ui.lineEdit.setText(str(setting_data.data["port"]))

    @staticmethod
    def on_port_changed(text):
        try:
            port = int(text)
            setting_data.data["port"] = port
            setting_data.save() 
            print(f"[INFO] Port updated to {port}")
        except ValueError:
            print("[WARN] Port không hợp lệ")

    @staticmethod
    def on_withdraw_password_changed(text):
        setting_data.data["withdraw_password"] = text
        setting_data.save()
        print(f"[INFO] Mật khẩu rút updated to {text}")

    @staticmethod
    def on_total_thread_changed(value):
        setting_data.data["total_thread"] = value
        setting_data.save()
        print(f"[INFO] Tổng thread updated to {value}")

    def run(self):
        list_profile_id: list[str] = self.ui.plainTextEdit.toPlainText().splitlines()
        queue_profile_id = iter(list_profile_id)

        index = 1
        total_thread = int(setting_data.data.get("total_thread", 1))
        available_slots = list(range(0, total_thread))
        exhausted = False  # đã hết job trong queue

        self.ui.pushButton.setEnabled(False)

        def make_on_thread_finished(slot: int):
            def _on_thread_finished(idx: int, profile_id: str, status: str, message: str):
                self.ui.textBrowser.append(f"{idx} - {profile_id} - {message}")
                if status == "fail":
                    self.ui.textBrowser_2.append(profile_id)
                if slot in self.occupied_threads_by_slot:
                    del self.occupied_threads_by_slot[slot]
                if slot not in available_slots:
                    available_slots.append(slot)
                    available_slots.sort()
                start_next_thread()
                if exhausted and not self.occupied_threads_by_slot:
                    self.ui.pushButton.setEnabled(True)
            return _on_thread_finished

        def start_next_thread():
            nonlocal index
            nonlocal exhausted
            try:
                if len(self.occupied_threads_by_slot) >= total_thread:
                    return
                if not available_slots:
                    return
                profile_id = next(queue_profile_id)
                slot = available_slots.pop(0)

                def launch_one(profile_id_=profile_id, slot_=slot, idx_=index):
                    nonlocal index
                    thread = RenameThread(index=idx_, profile_id=profile_id_, slot=slot_)
                    thread.signal.rename_finished_signal.connect(make_on_thread_finished(slot_))
                    self.occupied_threads_by_slot[slot_] = thread
                    thread.start()
                    index += 1
                    if len(self.occupied_threads_by_slot) < total_thread:
                        start_next_thread()

                QTimer.singleShot(2000, launch_one)
            except StopIteration:
                exhausted = True
                if not self.occupied_threads_by_slot:
                    self.ui.pushButton.setEnabled(True)
                return

        start_next_thread()


class RenameThread(QThread):
    def __init__(self, index: int, profile_id: str, slot: int):
        QThread.__init__(self)
        self.index = index
        self.profile_id = profile_id
        self.slot = slot 
        self.signal = RenameSignal()

    async def boot(self):
        _pass_withdraw = setting_data.data.get("withdraw_password", "")
        _bank_number = generate_mock_bidv_account()
        _real_name = None

        async def _close_a_ads_or_get_red_bin(index: int, sleep_before = 1):
            await asyncio.sleep(sleep_before)
            print(f"xử lý lần {index}")
            await _page_instance.wait_for_load_state("domcontentloaded", timeout=15000)
            _red_bin_parent_element = _page_instance.locator('xpath=//div[contains(@class, "red-pocket-mask-style-0")]')
            _reward_locator = _page_instance.locator('xpath=(//div[@class="draw-item"])[1]')
            if await _red_bin_parent_element.count() > 0:
                print("có lì xì")
                _red_bin_element = _page_instance.locator('xpath=//div[@class="redpocket-collet-normal"]')
                await _red_bin_element.wait_for(state='visible', timeout=15000)
                await _red_bin_element.click(force=True)
                await _page_instance.wait_for_timeout(2000)
                await _page_instance.locator(
                    'xpath=(//div[@class="lobby-image lobby-image lobby-image--use-bg background-image"])[2]'
                ).click()
                print("nhận lì xì thành công")
            elif await _reward_locator.count() > 0:
                await _reward_locator.wait_for(timeout=1000, state="visible")
                await _reward_locator.click()
                print("nhận quà thành công")
                await asyncio.sleep(5)
                await _page_instance.locator('xpath=//i[@class="ui-dialog-close-box__icon"]').click()
            else:
                _close_ads_locator = _page_instance.locator('xpath=//i[@class="ui-dialog-close-box__icon"]')
                if await _close_ads_locator.count() > 0:
                    await _close_ads_locator.wait_for(timeout=5000, state="visible")
                    await _close_ads_locator.click()
                print("đóng ads thành công")
            await asyncio.sleep(1)

        _message = "Thất bại"
        _status = "fail"
        try:
            _port = setting_data.data["port"]
            _win_width, _win_height = 400, 800
            _gap_x, _gap_y = 10, 10
            _pos_x = self.slot * (_win_width + _gap_x)
            _pos_y = 0
            _response = requests.get(
                f"http://127.0.0.1:{_port}/api/v3/profiles/start/{self.profile_id}",
                params={
                    "win_size": f"{_win_width},{_win_height}",
                    "win_pos": f"{_pos_x},{_pos_y}",
                    "win_scale": 0.7
                }

            )
            if _response.status_code == 200:
                _remote_host_port = _response.json()["data"]["remote_debugging_address"]
                print(f"_remote_host_port: {_remote_host_port}")
                async with async_playwright() as p:
                    _browser = await p.chromium.connect_over_cdp(
                        f"http://{_remote_host_port}" # noqa
                    )
                    if _browser.contexts:
                        _context = _browser.contexts[0]
                    if _context.pages:
                        _page_instance = _context.pages[0]
                    else:
                        _page_instance = await _context.new_page()

                    await _page_instance.goto("https://d3qpsv6l9dy9zi.cloudfront.net/?id=717976517")
                    await _page_instance.wait_for_load_state("domcontentloaded", timeout=15000)
                    await _close_a_ads_or_get_red_bin(index=1, sleep_before=5)
                    await _close_a_ads_or_get_red_bin(index=2)
                    await _close_a_ads_or_get_red_bin(index=3)
                    await _close_a_ads_or_get_red_bin(index=4)

                    await _page_instance.locator('xpath=//div[@role="button" and .//span[text()="Rút Tiền"]]').click()
                    # Xử lý thông tin mật khẩu rút

                    _first_input_withdraw_password = _page_instance.locator(
                        'xpath=(//ul[@class="ui-password-input__security hairline--surround"])[1]')
                    await _first_input_withdraw_password.wait_for(state='visible', timeout=15000)
                    await _first_input_withdraw_password.click()
                    for _char in _pass_withdraw:
                        await _page_instance.locator(
                            f'xpath=(//div[@class="ui-number-keyboard-key" and text()="{_char}"])[1]').click()

                    _second_input_withdraw_password = _page_instance.locator(
                        'xpath=(//ul[@class="ui-password-input__security hairline--surround"])[2]')
                    await _second_input_withdraw_password.wait_for(state='visible', timeout=15000)
                    await _second_input_withdraw_password.click()
                    for _char in _pass_withdraw:
                        await _page_instance.locator(
                            f'xpath=(//div[@class="ui-number-keyboard-key" and text()="{_char}"])[2]'
                        ).click()

                    await _page_instance.locator('xpath=//button[@type="button"]').click()
                    # Xử lý thông tin thẻ

                    await _page_instance.locator('xpath=(//div[contains(@class, "addAccountInputBtn")])[1]').click()
                    await _page_instance.locator('xpath=//div[@id="addAccountClick"]').click()
                    await _page_instance.locator(
                        'xpath=//ul[@class="ui-password-input__security hairline--surround"]').click()
                    for _char in _pass_withdraw:
                        await _page_instance.locator(
                            f'xpath=(//div[@class="ui-number-keyboard-key" and text()="{_char}"])[1]'
                        ).click()


                    await _page_instance.locator('xpath=//button[@type="submit"]').click()

                    await _page_instance.locator(
                        'xpath=//input[@placeholder="Vui lòng nhập số tài khoản ngân hàng"]').fill(
                        value=_bank_number
                    )
                    _real_name_locator = _page_instance.locator('xpath=//input[@data-input-name="realName"]')
                    _real_name = await _real_name_locator.input_value()
                    await _page_instance.locator('xpath=//div[@class="ui-select-input ui-select-input--hasPrefix ui-select-input--hasSuffix"]').click()
                    await _page_instance.locator('xpath=//div[./span/span[text()="BIDV"]]').click()
                    await _page_instance.locator('xpath=//button[@type="submit"]').click()
                    await asyncio.sleep(5)

                    _message = "Thành công"
                    _status = "success"

        except Exception: # noqa
            _message = "Thất bại"
            _status = "fail"
            traceback.print_exc()
        finally:
            if _status == "success":
                with open("result.txt", mode="a+", encoding="utf-8") as file:
                    file.write(f"{self.profile_id}|{_real_name}|{_bank_number}|{_pass_withdraw}\n")
            else:
                with open("error.txt", mode="a+", encoding="utf-8") as file:
                    file.write(f"{self.profile_id}\n")

            _port_close = setting_data.data["port"]
            requests.get(f"http://127.0.0.1:{_port_close}/api/v3/profiles/close/{self.profile_id}")

            self.signal.rename_finished_signal.emit(
                self.index,
                self.profile_id,
                _status,
                _message
            )

    def run(self):
        asyncio.run(self.boot())


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("WindowsVista")
    window = Application()
    window.show()
    sys.exit(app.exec())
