import keyboard
import time
import winreg

def toggle_focus():
    keyboard.press_and_release('win+n')
    time.sleep(1.5)
    keyboard.press_and_release('enter')
    keyboard.press_and_release('win+n')
    time.sleep(0.5)
    print('Режим «Не беспокоить» успешно переключён!')

def toggle_notify_icon_on_the_taskbar(state):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ShowNotificationIcon", 0, winreg.REG_DWORD, int(state))
        winreg.CloseKey(key)
        print(f"Иконка уведомления успешно {'включена' if state else 'отключена'}!")
        return True
    except PermissionError:
        raise PermissionError("Нет прав администратора. Запустите скрипт от имени администратора") from None
    except Exception as e:
        raise RuntimeError(f"Ошибка при работе с иконкой: {e}") from None