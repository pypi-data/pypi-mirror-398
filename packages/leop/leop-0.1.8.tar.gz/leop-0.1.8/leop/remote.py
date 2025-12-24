import pyautogui
def keyboard(key):
    pyautogui.press(key)
def mousemove(x, y):
    pyautogui.moveTo(x, y)
def mouseclick(button='left',times=2):
    pyautogui.click(button=button,clicks=times)
def mousewheel(direction='up',times=2):
    pyautogui.scroll(amount=times*50, direction=direction)
def hotkey(keya,keyb):
    pyautogui.hotkey(keya,keyb)
def screenshot(filename):
    im = pyautogui.screenshot()
    im.save(filename)
def findmouse():
    return pyautogui.position()
def screensize():
    return pyautogui.size()