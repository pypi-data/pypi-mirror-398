from pathlib import Path
import time
import pyautogui

pyautogui.useImageNotFoundException()

from PIL import Image

# path = Path(__file__).parent

# DEM = Image.open(path / "dem.png")
# DH_NO_LABEL = Image.open(path / "dh_no_label.png")
# NEXT_RECORD = Image.open(path / "next_record.png")
# DELETE_RECORD = Image.open(path / "delete_record.png")

while True:
    try:
        x, y = pyautogui.locateCenterOnScreen("dem.png", grayscale=True)
    except:
        pass
    else:
        # try:
        #     x2, y2 = pyautogui.locateCenterOnScreen("gpsds.png", grayscale=True)
        # except:
        #     pass
        # else:
        pyautogui.click(x=x, y=y)
        x, y = pyautogui.locateCenterOnScreen("delete_record.png", grayscale=True)
        pyautogui.click(x=x, y=y)
        pyautogui.hotkey("ctrl", "s")
        time.sleep(1)

    x, y = pyautogui.locateCenterOnScreen("parent_label.png", grayscale=True)
    pyautogui.click(x=x - 60, y=y)

    try:
        x, y = pyautogui.locateCenterOnScreen("next_record.png", grayscale=True)
    except:
        break
    else:
        pyautogui.click(x=x, y=y)
