import time, math, ctypes.wintypes, threading

autoclickState = False
registered_hotkeys = {}
hotkey_threads = {}

# Declare the win32 functions we will be using one time so we dont call GetProcAddress for every single win32 api call
_SendInput = ctypes.windll.user32.SendInput
_MapVirtualKeyW = ctypes.windll.user32.MapVirtualKeyW
_GetCursorPos = ctypes.windll.user32.GetCursorPos
_GetSystemMetrics = ctypes.windll.user32.GetSystemMetrics
_RegisterHotKey = ctypes.windll.user32.RegisterHotKey
_GetMessageW = ctypes.windll.user32.GetMessageW
_UnregisterHotKey = ctypes.windll.user32.UnregisterHotKey
_TranslateMessage = ctypes.windll.user32.TranslateMessage
_DispatchMessageW = ctypes.windll.user32.DispatchMessageW
_PostThreadMessageW = ctypes.windll.user32.PostThreadMessageW
_GetDC = ctypes.windll.user32.GetDC
_GetPixel = ctypes.windll.gdi32.GetPixel
_ReleaseDC = ctypes.windll.user32.ReleaseDC
_FindWindowW = ctypes.windll.user32.FindWindowW
_PostMessageW = ctypes.windll.user32.PostMessageW
_CallNextHookEx = ctypes.windll.user32.CallNextHookEx
_CallNextHookEx.restype = ctypes.c_long
_CallNextHookEx.argtypes = [ctypes.wintypes.HHOOK, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.WPARAM]
_SetWindowsHookExW = ctypes.windll.user32.SetWindowsHookExW
_SetWindowsHookExW.restype = ctypes.wintypes.HHOOK
_SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.WINFUNCTYPE(ctypes.wintypes.LPVOID, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM), ctypes.wintypes.HINSTANCE, ctypes.wintypes.DWORD]
_UnhookWindowsHookEx = ctypes.windll.user32.UnhookWindowsHookEx
_UnhookWindowsHookEx.restype = ctypes.wintypes.HHOOK
_UnhookWindowsHookEx.argtypes = [ctypes.c_int, ctypes.WINFUNCTYPE(ctypes.wintypes.LPVOID, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM), ctypes.wintypes.HINSTANCE, ctypes.wintypes.DWORD]


PAUSE = 0.1
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
MOUSEEVENTF_HWHEEL = 0x01000
MOUSEEVENTF_MIDDLECLICK = MOUSEEVENTF_MIDDLEDOWN + MOUSEEVENTF_MIDDLEUP
MOUSEEVENTF_LEFTCLICK = MOUSEEVENTF_LEFTDOWN + MOUSEEVENTF_LEFTUP
MOUSEEVENTF_RIGHTCLICK = MOUSEEVENTF_RIGHTDOWN + MOUSEEVENTF_RIGHTUP

LEFT = 'left'
RIGHT = 'right'
MIDDLE = 'middle'

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_UNICODE = 0x0004

WM_ACTIVATE = 0x6
WM_CHAR = 0x102
WA_ACTIVE = 0x1

WM_QUIT = 0x0012

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_LBUTTONCLICK = WM_LBUTTONDOWN + WM_LBUTTONUP
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_RBUTTONCLICK = WM_RBUTTONDOWN + WM_RBUTTONUP
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
WM_MBUTTONCLICK = WM_MBUTTONDOWN + WM_MBUTTONUP
WM_HOTKEY = 0x0312
WM_XBUTTONDOWN = 0x020B
WM_XBUTTONUP = 0x020C
WM_XBUTTONCLICK = WM_XBUTTONDOWN + WM_XBUTTONUP

WM_NCHITTEST = 0x0084
WM_MOUSEMOVE = 0x0200
WM_MOUSEWHEEL = 0x020A
WM_SETCURSOR = 0x0020

MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002
MK_MBUTTON = 0x0010

KEYS = {
    'escape': 0x01,
    'esc': 0x01,
    'f1': 0x3B,
    'f2': 0x3C,
    'f3': 0x3D,
    'f4': 0x3E,
    'f5': 0x3F,
    'f6': 0x40,
    'f7': 0x41,
    'f8': 0x42,
    'f9': 0x43,
    'f10': 0x44,
    'f11': 0x57,
    'f12': 0x58,
    'printscreen': 0xB7,
    'prntscrn': 0xB7,
    'prtsc': 0xB7,
    'prtscr': 0xB7,
    'scrolllock': 0x46,
    'pause': 0xC5,
    '`': 0x29,
    '1': 0x02,
    '2': 0x03,
    '3': 0x04,
    '4': 0x05,
    '5': 0x06,
    '6': 0x07,
    '7': 0x08,
    '8': 0x09,
    '9': 0x0A,
    '0': 0x0B,
    '-': 0x0C,
    '=': 0x0D,
    'backspace': 0x0E,
    'insert': 0xD2 + 1024,
    'home': 0xC7 + 1024,
    'pageup': 0xC9 + 1024,
    'pagedown': 0xD1 + 1024,
    'numlock': 0x45,
    'divide': 0xB5 + 1024,
    'multiply': 0x37,
    'subtract': 0x4A,
    'add': 0x4E,
    'decimal': 0x53,
    'tab': 0x0F,
    'q': 0x10,
    'w': 0x11,
    'e': 0x12,
    'r': 0x13,
    't': 0x14,
    'y': 0x15,
    'u': 0x16,
    'i': 0x17,
    'o': 0x18,
    'p': 0x19,
    '[': 0x1A,
    ']': 0x1B,
    '\\': 0x2B,
    'del': 0xD3 + 1024,
    'delete': 0xD3 + 1024,
    'end': 0xCF + 1024,
    'capslock': 0x3A,
    'a': 0x1E,
    's': 0x1F,
    'd': 0x20,
    'f': 0x21,
    'g': 0x22,
    'h': 0x23,
    'j': 0x24,
    'k': 0x25,
    'l': 0x26,
    ';': 0x27,
    "'": 0x28,
    'enter': 0x1C,
    'return': 0x1C,
    'shift': 0x2A,
    'left shift': 0x2A,
    'z': 0x2C,
    'x': 0x2D,
    'c': 0x2E,
    'v': 0x2F,
    'b': 0x30,
    'n': 0x31,
    'm': 0x32,
    ',': 0x33,
    '.': 0x34,
    '/': 0x35,
    'right shift': 0x36,
    'ctrl': 0x1D,
    'left ctrl': 0x1D,
    'win': 0xDB + 1024,
    'winleft': 0xDB + 1024,
    'alt': 0x38,
    'left alt': 0x38,
    ' ': 0x39,
    'space': 0x39,
    'spacebar': 0x39,
    'altright': 0xB8 + 1024,
    'winright': 0xDC + 1024,
    'apps': 0xDD + 1024,
    'right ctrl': 0x9D + 1024,
    'up arrow': _MapVirtualKeyW(0x26, 0),
    'left arrow': _MapVirtualKeyW(0x25, 0),
    'down arrow': _MapVirtualKeyW(0x28, 0),
    'right arrow': _MapVirtualKeyW(0x27, 0),
}

VK_KEYS = {
    "esc": 0x1B,
    "a": 0x41,
    "b": 0x42,
    "c": 0x43,
    "d": 0x44,
    "e": 0x45,
    "f": 0x46,
    "g": 0x47,
    "h": 0x48,
    "i": 0x49,
    "j": 0x4a,
    "k": 0x4b,
    "l": 0x4c,
    "m": 0x4d,
    "n": 0x4e,
    "o": 0x4f,
    "p": 0x50,
    "q": 0x51,
    "r": 0x52,
    "s": 0x53,
    "t": 0x54,
    "u": 0x55,
    "v": 0x56,
    "w": 0x57,
    "x": 0x58,
    "y": 0x59,
    "z": 0x5a,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
    "6": 0x36,
    "7": 0x37,
    "8": 0x38,
    "9": 0x39,
    "0": 0x30,
    "-": 0xbd,
    "=": 0xbb,
    "!": 0x131,
    "@": 0x132,
    "#": 0x133,
    "$": 0x134,
    "%": 0x135,
    "^": 0x136,
    "&": 0x137,
    "*": 0x138,
    "(": 0x139,
    ")": 0x130,
    "_": 0x1bd,
    "+": 0x1bb,
    "[": 0xdb,
    "]": 0xdd,
    "\\": 0xdc,
    "{": 0x1db,
    "}": 0x1dd,
    "|": 0x1dc,
    ";": 0xba,
    "'": 0xde,
    ":": 0x1ba,
    '"': 0x1de,
    ",": 0xbc,
    ".": 0xbe,
    "/": 0xbf,
    "<": 0x1bc,
    ">": 0x1be,
    "?": 0x1bf,
    "*": 0x138,
    "`": 0xc0,
    "~": 0x1c0,
    'backspace': 0x08,
    'tab': 0x09,
    'clear': 0x0C,
    'enter': 0x0D,
    'shift': 0x10,
    'ctrl': 0x11,
    'alt': 0x12,
    'pause': 0x13,
    'caps': 0x14,
    'spacebar': 0x20,
    'space bar': 0x20,
    'page up': 0x21,
    'page down': 0x22,
    'end': 0x23,
    'home': 0x24,
    'left arrow': 0x25,
    'up arrow': 0x26,
    'right arrow': 0x27,
    'down arrow': 0x28,
    'select': 0x29,
    'print': 0x2A,
    'execute': 0x2B,
    'print screen': 0x2C,
    'prt sc': 0x2C,
    'prntsc': 0x2C,
    'ins': 0x2D,
    'del': 0x2E,
    'help': 0x2F,
    'numpad 0': 0x60,
    'numpad 1': 0x61,
    'numpad 2': 0x62,
    'numpad 3': 0x63,
    'numpad 4': 0x64,
    'numpad 5': 0x65,
    'numpad 6': 0x66,
    'numpad 7': 0x67,
    'numpad 8': 0x68,
    'numpad 9': 0x69,
    'add': 0x6B,
    'multiply': 0x6A,
    'minus': 0xBD,
    'seperator': 0x6C,
    'subtract': 0x6D,
    'decimal': 0x6E,
    'divide': 0x6F,
    'f1': 0x70,
    'f2': 0x71,
    'f3': 0x72,
    'f4': 0x73,
    'f5': 0x74,
    'f6': 0x75,
    'f7': 0x76,
    'f8': 0x77,
    'f9': 0x78,
    'f10': 0x79,
    'f11': 0x7A,
    'f12': 0x7B,
    'f13': 0x7C,
    'f14': 0x7D,
    'f15': 0x7E,
    'f16': 0x7F,
    'f17': 0x80,
    'f18': 0x81,
    'f19': 0x82,
    'f20': 0x83,
    'f21': 0x84,
    'f22': 0x85,
    'f23': 0x86,
    'f24': 0x87,
    'num lock': 0x90,
    'scroll lock': 0x91,
    'lshift': 0xA0,
    'rshift': 0xA1,
    'lcontrol': 0xA2,
    'lctrl': 0xA2,
    'rcontrol': 0xA3,
    'rctrl': 0xA3,
    'lalt': 0xA4,
    'ralt': 0xA5,
    'tilde': 0xC0,
    'clear': 0xFE,
    'application': 0x5D,
	'browser back': 0xA6,
	'browser forward': 0xA7,
	'browser refresh': 0xA8,
	'browser stop': 0xA9,
	'browser search': 0xAA,
	'browser favorites': 0xAB,
    'home': 0xAC,
    'home': 0x24,
	'volume mute': 0xAD,
	'volume down': 0xAE,
	'volume up': 0xAF,
	'next track': 0xB0,
	'previous track': 0xB1,
	'stop media': 0xB2,
	'play/pause': 0xB3,
	'start mail': 0xB4,
	'select media': 0xB5,
	'start app 1': 0xB6,
	'start app 2': 0xB7,
	'left windows key': 0x5B,
	'right windows key': 0x5C,
    'clear': 0x0C
}


class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long),
                ("y", ctypes.c_long)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [('vkCode', ctypes.wintypes.DWORD),
                ('scanCode', ctypes.wintypes.DWORD),
                ('flags', ctypes.wintypes.DWORD),
                ('time', ctypes.wintypes.DWORD),
                ('dwExtraInfo', ctypes.POINTER(ctypes.wintypes.ULONG))]

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [('pt', POINT),
                ('mouseData', ctypes.wintypes.DWORD),
                ('flags', ctypes.wintypes.DWORD),
                ('time', ctypes.wintypes.DWORD),
                ('dwExtraInfo', ctypes.POINTER(ctypes.wintypes.ULONG))]

def run_in_thread(func):
    def wrapper(self, *args, **kwargs):
        thread = threading.Thread(target=func, args=(self,) + args, kwargs=kwargs, daemon=True)
        thread.start()
        self.thread_id = thread.native_id
    return wrapper

def getPos():
    cursor = POINT()
    _GetCursorPos(ctypes.byref(cursor))
    return cursor.x, cursor.y

def size():
    screen_width, screen_height = _GetSystemMetrics(0),  _GetSystemMetrics(1)
    return screen_width, screen_height


def dragTo(x:int=None, y:int=None, duration=0.0, _pause=True):
    """
    
    Performs a drag (mouse movement with mouse button down) to coordinates on screen

    Args:
        x (int, optional): X coordinate to move to. Defaults to None.
        y (int, optional): y coordinate to move to. Defaults to None.
        duration (float, optional): The time inbetween each mouse movement towards the new x & y coordinates, if 0 then try and move instantly. Defaults to 0.0.
        _pause (bool, optional): Sleep after the function call has finished. Defaults to True.
    """
    

    start_x, start_y = getPos()
    screen_width, screen_height = size()
    duration = duration / 100

    distance = math.hypot(x - start_x, y - start_y)

    ii_ = Input_I()
    
    ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(ctypes.c_ulong(0)))
    xx = Input(ctypes.c_ulong(0), ii_)
    _SendInput(1, ctypes.pointer(xx), ctypes.sizeof(xx))
    if _pause:
        time.sleep(PAUSE)

    for i in range(1, int(distance)+1):
        drag_x = int(start_x + (x - start_x) * i / int(distance))
        drag_y = int(start_y + (y - start_y) * i / int(distance))
        
        ii_.mi = MouseInput(int(65535 * drag_x / screen_width), int(65535 * drag_y / screen_height), 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, ctypes.pointer(ctypes.c_ulong(0)))
        xx = Input(ctypes.c_ulong(0), ii_)
        _SendInput(1, ctypes.pointer(xx), ctypes.sizeof(xx))
        if duration > 0.0:
            time.sleep(duration)

    ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(ctypes.c_ulong(0)))
    xx = Input(ctypes.c_ulong(0), ii_)
    _SendInput(1, ctypes.pointer(xx), ctypes.sizeof(xx))
    if _pause:
        time.sleep(PAUSE)


def moveTo(x:int=None, y:int=None, _pause=True):
    """

    Moves the mouse to the specified x and y coordinates

    Args:
        x (int, optional): X coordinate to move to. Defaults to None.
        y (int, optional): Y coordinate to move to. Defaults to None.
        _pause (bool, optional): Sleep after the function call has finished. Defaults to True.
    """
    
    screen_width, screen_height = size()
    ii_ = Input_I()
    ii_.mi = MouseInput(int(65535 * x / screen_width), int(65535 * y / screen_height), 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, ctypes.pointer(ctypes.c_ulong(0)))
    xx = Input(ctypes.c_ulong(0), ii_)
    _SendInput(1, ctypes.pointer(xx), ctypes.sizeof(xx))
    if _pause:
        time.sleep(PAUSE)


def moveRel(offsetX:int=0, offsetY:int=0, _pause=True):
    """

    Moves the mouse by a certain amount based off the x and y offsets

    Args:
        offsetX (int, optional): Amount of x pixels you wish to move. Defaults to 0.
        offsetY (int, optional): Amount of y pixels you wish to move. Defaults to 0.
        _pause (bool, optional): Sleep after the function call has finished. Defaults to True.
    """
    
    x, y = getPos()
    moveTo(offsetX + x, offsetY + y, _pause)

def mouseDown(x:int=None, y:int=None, interval=0.0, button=LEFT, _pause=True):
    """

    Performes a mouse down event at the specified coordinates, if not coordinates are specified then the event it sent at your current mouse location

    Args:
        x (int, optional): X coordinate to move to. Defaults to None.
        y (int, optional): Y coordinate to move to. Defaults to None.
        interval (float, optional): The sleep after the mouse button has been held down. Defaults to 0.0.
        button (_type_, optional): The mouse button that you wish to hold down. Defaults to LEFT.
        _pause (bool, optional): Sleep after the function call has finished. Defaults to True.
    """
    if x and y:
        moveTo(x,y)

    if button == LEFT:
        event = MOUSEEVENTF_LEFTDOWN
    elif button == RIGHT:
        event = MOUSEEVENTF_RIGHTDOWN
    elif button == MIDDLE:
        event = MOUSEEVENTF_MIDDLEDOWN

    ii_ = Input_I()

    if x and y:
        ii_.mi = MouseInput(x,y, 0, event, 0, ctypes.pointer(ctypes.c_ulong(0)))
    else:
        ii_.mi = MouseInput(0,0, 0, event, 0, ctypes.pointer(ctypes.c_ulong(0)))
    xx = Input(ctypes.c_ulong(0), ii_)
    _SendInput(1, ctypes.pointer(xx), ctypes.sizeof(xx))
    time.sleep(interval)

    if _pause:
        time.sleep(PAUSE)


def mouseUp(x:int=None, y:int=None, interval=0.0, button=LEFT, _pause=True):
    """

    Performes a mouse up event at the specified coordinates, if not coordinates are specified then the event it sent at your current mouse location

    Args:
        x (int, optional): X coordinate to move to. Defaults to None.
        y (int, optional): Y coordinate to move to. Defaults to None.
        interval (float, optional): The sleep after the mouse button has been released. Defaults to 0.0.
        button (_type_, optional): The mouse button that you wish to release. Defaults to LEFT.
        _pause (bool, optional): Sleep after the function call has finished. Defaults to True.
    """
    if x and y:
        moveTo(x,y)

    if button == LEFT:
        event = MOUSEEVENTF_LEFTUP
    elif button == RIGHT:
        event = MOUSEEVENTF_RIGHTUP
    elif button == MIDDLE:
        event = MOUSEEVENTF_MIDDLEUP

    ii_ = Input_I()

    if x and y:
        ii_.mi = MouseInput(x,y, 0, event, 0, ctypes.pointer(ctypes.c_ulong(0)))
    else:
        ii_.mi = MouseInput(0,0, 0, event, 0, ctypes.pointer(ctypes.c_ulong(0)))
    xx = Input(ctypes.c_ulong(0), ii_)
    _SendInput(1, ctypes.pointer(xx), ctypes.sizeof(xx))
    time.sleep(interval)

    if _pause:
        time.sleep(PAUSE)

def click(x:int=None, y:int=None, interval=0.0, clicks=1, button=LEFT, _pause=True):
    """

    Performs a mouse click at the specified x and y coordinates

    Args:
        x (int, optional): X coordinate to move to. Defaults to None.
        y (int, optional): Y coordinate to move to. Defaults to None.
        interval (float, optional): The sleep after the mouse button has been released. Defaults to 0.0.
        clicks (int, optional): The amount of clicks you wish to send. Defaults to 1.
        button (_type_, optional): The mouse button that you wish to click. Defaults to LEFT.
        _pause (bool, optional): Sleep after the function call has finished. Defaults to True.
    """
    
    if x and y:
        moveTo(x,y)

    if button == LEFT:
        event = MOUSEEVENTF_LEFTCLICK
    elif button == RIGHT:
        event = MOUSEEVENTF_RIGHTCLICK
    elif button == MIDDLE:
        event = MOUSEEVENTF_MIDDLECLICK

    ii_ = Input_I()
    for i in range(clicks):
        if x and y:
            ii_.mi = MouseInput(x,y, 0, event, 0, ctypes.pointer(ctypes.c_ulong(0)))
        else:
            ii_.mi = MouseInput(0,0, 0, event, 0, ctypes.pointer(ctypes.c_ulong(0)))
        xx = Input(ctypes.c_ulong(0), ii_)
        _SendInput(1, ctypes.pointer(xx), ctypes.sizeof(xx))
        time.sleep(interval)

    if _pause:
        time.sleep(PAUSE)


def autoclick(button=LEFT):
    """

    Starts a auto clicker in a seperate daemon thread at your current mouse location and clicks the specified button at roughly 200cps

    USE WITH CAUTION:
    -----
    Make sure you can call this function with a hotkey or another way because it will not automatically toggle of

    Args:
        button (_type_, optional): The mouse button that you wish to click. Defaults to LEFT.
    """
    
    global autoclickState
    autoclickState = not autoclickState
    def autoclick():
        while autoclickState:
            click(None, None, 0.004, 1, button, False)
    if autoclickState:
        autoclick_thread = threading.Thread(target=autoclick)
        autoclick_thread.daemon = True
        autoclick_thread.start()


def doubleClick(x:int=None, y:int=None, interval=0.0, button=LEFT, _pause=True):
    """

    Sends 2 click inputs as if you were double clicking your mouse

    Args:
        x (int, optional): X coordinate to move to. Defaults to None.
        y (int, optional): Y coordinate to move to. Defaults to None.
        interval (float, optional): The sleep after the mouse button has been released. Defaults to 0.0.
        button (_type_, optional): The mouse button that you wish to click. Defaults to LEFT.
        _pause (bool, optional): Sleep after the function call has finished. Defaults to True.
    """
    click(x, y, interval, 2, button, _pause)

def tripleClick(x:int=None, y:int=None, interval=0.0, button=LEFT, _pause=True):
    """

    Sends 3 click inputs as if you were triple clicking your mouse

    Args:
        x (int, optional): X coordinate to move to. Defaults to None.
        y (int, optional): Y coordinate to move to. Defaults to None.
        interval (float, optional): The sleep after the mouse button has been released. Defaults to 0.0.
        button (_type_, optional): The mouse button that you wish to click. Defaults to LEFT.
        _pause (bool, optional): Sleep after the function call has finished. Defaults to True.
    """
    click(x, y, interval, 3, button, _pause)


def scroll(scrollAmount=1, _pause=True):
    """

    Sends a scroll input

    Args:
        scrollAmount (int, optional): The amount you wish to scroll (negative numbers scroll up and positive scrolls down). Defaults to 1.
        _pause (bool, optional): Sleep after the function call has finished. Defaults to True.
    """
    
    ii_ = Input_I()
    ii_.mi = MouseInput(0,0, scrollAmount*120, MOUSEEVENTF_WHEEL, 0, ctypes.pointer(ctypes.c_ulong(0)))
    xx = Input(ctypes.c_ulong(0), ii_)
    _SendInput(1, ctypes.pointer(xx), ctypes.sizeof(xx))
    
    if _pause:
        time.sleep(PAUSE)


def press(key:str, interval=0.0, _pause=True):
    """
    Performs a keypress, also supports side mouse buttons (xbutton1 and xbutton2)

    pymousekey.KEYS for the dict of keys

    Args:
        key (str): The key/mouse button expected to be pressed.
        interval (float, optional): The sleep after the mouse button has been released. Defaults to 0.0.
        _pause (bool, optional): Sleep after the function call has finished. Defaults to True.
    """

    
    if not key.lower() in KEYS or KEYS[key.lower()] is None:
        return
    ii_ = Input_I()
    
    if key == ('xbutton1' or 'xbutton2'):
        ii_.mi = MouseInput(0, 0, KEYS[key], MOUSEEVENTF_XDOWN | MOUSEEVENTF_XUP, 0, None)
        xx = Input(ctypes.c_ulong(0), ii_)
        _SendInput(1, ctypes.pointer(xx), ctypes.sizeof(xx))
        return
    
    if str(key).isupper():
        ii_.ki = KeyBdInput(0, KEYS['shift'], KEYEVENTF_SCANCODE, 0, ctypes.pointer(ctypes.c_ulong(0)))
        x = Input(ctypes.c_ulong(1), ii_)
        _SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
    
    keyDown(key)
    time.sleep(interval)
    keyUp(key)
    
    if str(key).isupper():
        ii_.ki = KeyBdInput(0, KEYS['shift'], KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(ctypes.c_ulong(0)))
        x = Input(ctypes.c_ulong(1), ii_)
        _SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
    
    if _pause:
        time.sleep(PAUSE)


def keyDown(key:str):
    """

    Sends a keydown event

    Args:
        key (str): The key expected to me held down.
    """
    if not key.lower() in KEYS or KEYS[key.lower()] is None:
        return

    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, KEYS[key.lower()], KEYEVENTF_SCANCODE, 0, ctypes.pointer(ctypes.c_ulong(0)))
    x = Input(ctypes.c_ulong(1), ii_)
    _SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def keyUp(key:str):
    """

    Sends a keyup event

    Args:
        key (str): The key expected to be released.
    """
    if not key.lower() in KEYS or KEYS[key.lower()] is None:
        return

    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, KEYS[key.lower()], KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(ctypes.c_ulong(0)))
    x = Input(ctypes.c_ulong(1), ii_)
    _SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def add_hotkey(key:str, callback, args=(), suppress=True):
    """

    Registeres a system wide hotkey and starts it in a seperate daemon thread

    Args:
        key (str): The key you wish to register as the hotkey.
        callback (function): A function object that gets called when the specified key is pressed.
        args (tuple, optional): Args that should be sent to the specified callback function. Defaults to ().
        suppress (bool, optional): Whether to stop the input from being sent with the hotkey or not. Defaults to True.
    
    
    If the specified key is already a registered hotkey the function returns nothing
    
    pymousekey.VK_KEYS for a list of keys.

    Usage of how to add hotkeys:
    -
    add_hotkey("ctrl + shift + g")

    add_hotkey("shift + numpad 5") (shift + numpad keys dont actually work because of something to do with numlock and its secondary function i have no clue)

    add_hotkey("h")

    """
    
    def add_hotkey_thread():
        if 'shift' in key or 'ctrl' in key or 'alt' in key:
            registered_key = key.rsplit('+', 1)[1].strip()
            key_id = len(registered_hotkeys) + 1
            registered_hotkeys[key] = key_id, VK_KEYS[registered_key]
            hotkey_threads[key] = hotkey_thread.native_id
            if 'alt' in key and not 'ctrl' in key and not 'shift' in key:
                fsModifiers = 0x0001
            elif 'ctrl' in key and not 'alt' in key and not 'shift' in key:
                fsModifiers = 0x0002
            elif 'shift' in key and not 'ctrl' in key and not 'alt' in key:
                fsModifiers = 0x0004
            elif 'alt' in key and 'ctrl' in key:
                fsModifiers = 0x0001 | 0x0002
            elif 'alt' in key and 'shift' in key:
                fsModifiers = 0x0001 | 0x0004
            elif 'shift' in key and 'ctrl' in key:
                fsModifiers = 0x0004 | 0x0002
        else:
            registered_key = key
            key_id = len(registered_hotkeys) + 1
            registered_hotkeys[key] = key_id, VK_KEYS[registered_key]
            hotkey_threads[registered_key] = hotkey_thread.native_id
            fsModifiers = None

        _RegisterHotKey(None, key_id , fsModifiers, VK_KEYS[registered_key])
        
        msg = ctypes.wintypes.MSG()

        while _GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            if msg.message == WM_HOTKEY:
                if args:
                    callback(args)
                else:
                    callback()
                if not suppress:
                    _UnregisterHotKey(None, key_id , fsModifiers, VK_KEYS[registered_key])
                    press(key, 0, False)
                    _RegisterHotKey(None, key_id , fsModifiers, VK_KEYS[registered_key])
                _TranslateMessage(ctypes.byref(msg))
                _DispatchMessageW(ctypes.byref(msg))
        try:
            _UnregisterHotKey(None, registered_hotkeys[key][0])
        except(KeyError):
            pass
    try:
        if key in registered_hotkeys:
            return
    
        elif key in VK_KEYS:
            hotkey_thread = threading.Thread(target=add_hotkey_thread)
            hotkey_thread.daemon = True
            hotkey_thread.start()

        elif key.rsplit('+', 1)[1].strip() in VK_KEYS:
            hotkey_thread = threading.Thread(target=add_hotkey_thread)
            hotkey_thread.daemon = True
            hotkey_thread.start()
    except:
        pass

def remove_hotkey(key:str):
    """
    Unregisters and removed the specified hotkey if it was previously registered

    Args:
        key (str): The key you wish stop using as a hotkey.
    
    pymousekey.VK_KEYS for a list of keys.
    
    """

    if key in registered_hotkeys:
        _UnregisterHotKey(None, registered_hotkeys[key][0])
        _PostThreadMessageW(hotkey_threads[key], WM_QUIT, 0, 0)
        del registered_hotkeys[key]
        del hotkey_threads[key]

def remove_all_hotkeys():
    """
    Unregisters and removes all currently registered hotkeys
    
    """
    for key in registered_hotkeys.values():
        _UnregisterHotKey(None, key[0])
        
    for threads in hotkey_threads.values():
        _PostThreadMessageW(threads, WM_QUIT, 0, 0)

    registered_hotkeys.clear()
    hotkey_threads.clear()

def typeWrite(message:str, interval=0.0, _pause=True):
    """
    Writes a given message, supports lowercase and upercase characters

    Args:
        message (str): The message you wish to be typed out.
        interval (float, optional): The sleep after the mouse button has been held down. Defaults to 0.0.
        _pause (bool, optional): Sleep after the function call has finished. Defaults to True.
    """

    for i in message:
        press(i, interval, _pause)


def getPixelColor(x:int=None, y:int=None):
    """

    Gets the color from the specified coordinates, if no coordinates are specified grab the color from your mouse coordinates
    
    Args:
        x (int, optional): X coordinate to get pixel data from. Defaults to None.
        y (int, optional): Y coordinate to get pixel data from. Defaults to None.

    Returns:
        _type_: hexColor(str) & rgbColor(tuple)
    """

    hexColor & rgbColor
    
    
    dc = _GetDC(None)
    if not (x and y):
        x,y = getPos()
        color = _GetPixel(dc, x, y)
    else:
        color = _GetPixel(dc, x, y)

    _ReleaseDC(None, dc)
    red = color & 0xff
    green = (color >> 8) & 0xff
    blue = (color >> 16) & 0xff
    hexColor = '#{:02x}{:02x}{:02x}'.format(red,green,blue)
    rgbColor = red, green, blue
    return hexColor, rgbColor


def controlSend(key:str=None, className:str=None, windowTitle:str=None, lparam=None):
    """

    Sends software keyboard inputs to any inactive window/control by sending the WM_ACTIVATE msg and WA_ACTIVE wParam then sending the WH_CHAR message with the key you specified


    Args:
        key (str, optional): The key to be sent to the specified window. Defaults to None.
        className (str, optional): The target windows class name. Defaults to None.
        windowTitle (str, optional): The target windows title. Defaults to None.
        lparam (_type_, optional): Additional message-specific information. Defaults to None.
    
        
    Note:
        Some games/programs ignore these window messages and instead whenever they are sent they call their own internal functions to determine what key was pressed down/released
    
    """

    handle = _FindWindowW(className, windowTitle)

    _PostMessageW(handle, WM_ACTIVATE, WA_ACTIVE, 0)
    _PostMessageW(handle, WM_CHAR, ord(key), lparam)


def controlClick(x:int=None, y:int=None, className:str=None, windowTitle:str=None, button=LEFT):
    """

    Sends software mouse inputs to any inactive window/control by sending the WM_ACTIVATE msg and WA_ACTIVE wParam then sending WM_LBUTTONDOWN and WM_LBUTTONUP messages

    Args:
        x (int, optional): X coordinate to move to. Defaults to None.
        y (int, optional): y coordinate to move to. Defaults to None.
        className (str, optional): The target windows class name. Defaults to None.
        windowTitle (str, optional): The target windows title. Defaults to None.
        button (str, optional): The button . Defaults to LEFT.

    Note:
        Some games/programs ignore these window message and instead whenever they are sent call their own internal functions to get the position of your mouse and what mouse button was pressed

        For games built with unity this would be via the GetPhysicalCursorpos function which you can hook
    """

    

    handle = _FindWindowW(className, windowTitle)
    lparam = ctypes.c_long((y << 16) | (x & 0xFFFF)).value

    _PostMessageW(handle, WM_ACTIVATE, WA_ACTIVE, 0)
    
    if button == 'left':
        _PostMessageW(handle, WM_NCHITTEST, 0, lparam)
        _PostMessageW(handle, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        _PostMessageW(handle, WM_LBUTTONUP, MK_LBUTTON, lparam)

    elif button == 'right':
        _PostMessageW(handle, WM_NCHITTEST, 0, lparam)
        _PostMessageW(handle, WM_RBUTTONDOWN, MK_RBUTTON, lparam)
        _PostMessageW(handle, WM_RBUTTONUP, MK_RBUTTON, lparam)

    elif button == 'middle':
        _PostMessageW(handle, WM_NCHITTEST, 0, lparam)
        _PostMessageW(handle, WM_MBUTTONDOWN, MK_MBUTTON, lparam)
        _PostMessageW(handle, WM_MBUTTONUP, MK_MBUTTON, lparam)


class LowLevelKeyboardHook():
    """
    A class representing a low-level keyboard hook.

    Each parameter is optional so you can install whatever hook you intend to use.

    Example:
    -

    def example(key):
        print(f'{key} was pressed down')

    def example2(key):
        print(print(f'{key} was released'))

    # Create an instance of LowLevelKeyboardHook with a custom hook procedure

    keyboard_hook = LowLevelKeyboardHook(on_keydown=example, on_keyup=example2)
    
    # Install the hook

    keyboard_hook.start()

    # Uninstall the hook

    keyboard_hook.stop()
    """
    def __init__(self, on_keydown=None, on_keyup=None):
        self.running = False
        self.hook_id = None
        self.thread_id = None
        self.on_keydown = on_keydown
        self.on_keyup = on_keyup
    
    def callback(self, nCode, wParam, lParam):
        if nCode < 0:
            return _CallNextHookEx(0, nCode, wParam, lParam)

        keyboard_struct = KBDLLHOOKSTRUCT.from_address(lParam)
        reversed_VK_KEYS = {value: key for key, value in VK_KEYS.items()}
        
        if wParam == WM_KEYDOWN and self.on_keydown:
            self.on_keydown(reversed_VK_KEYS[keyboard_struct.vkCode])

        elif wParam == WM_KEYUP and self.on_keyup:
            self.on_keyup(reversed_VK_KEYS[keyboard_struct.vkCode])

        return _CallNextHookEx(0, nCode, wParam, lParam)

    @run_in_thread
    def start(self):
        """
        Starts the LowLevelKeyboardProc hook in a seperate daemon thread
        """
        if self.running:
            raise Exception('You cannot call this function twice you must stop the current hook before starting a new one')
        
        HOOKProc = ctypes.WINFUNCTYPE(ctypes.wintypes.LPVOID, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
        CBTProc = HOOKProc(self.callback)
        self.hook_id = _SetWindowsHookExW(13, CBTProc, 0, 0)


        self.running = True
        msg = ctypes.wintypes.MSG()
        while self.running:
            _GetMessageW(ctypes.byref(msg), 0, 0, 0)

    def stop(self):
        """
        Stops the currently running hook
        """
        if not self.running:
            raise Exception('You cannot stop something that has not been started yet')
        
        self.running = False
        _UnhookWindowsHookEx(self.hook_id)
        _PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)

class LowLevelMouseHook():
    """
    A class representing a low-level mouse hook.

    Each parameter is optional so you can install whatever hook you intend to use.

    Example:
    -

    def example(x, y, button, is_down):
        if is_down:
            print(x, y)
        
        elif not is_down:
            print(f'Mouse button released at: ({x,y})')

    def example2(x, y):
        if x > 500 and y > 100:
            print(x, y)

    def example3(x, y, scroll):
        if scroll < 0:
            print('You scrolled down')
        
        elif scroll > 0:
            print('You scrolled up')

    # Create an instance of LowLevelMouseHook with a custom hook procedure
    
    mouse_hook = LowLevelMouseHook(on_click=example, on_move=example2, on_scroll=example3)
    
    # Install the hook

    mouse_hook.start()

    # Uninstall the hook

    mouse_hook.stop()
    """
    def __init__(self, on_click=None, on_move=None, on_scroll=None):
        self.running = False
        self.hook_id = None
        self.thread_id = None
        self.on_click = on_click
        self.on_move = on_move
        self.on_scroll = on_scroll
        self.button = {WM_LBUTTONDOWN: 'left', WM_RBUTTONDOWN: 'right', WM_MBUTTONDOWN: 'middle', WM_LBUTTONUP: 'left', WM_RBUTTONUP: 'right', WM_MBUTTONUP: 'middle', 1: 'x1', 2: 'x2'}
    
    def callback(self, nCode, wParam, lParam):
        if nCode < 0:
            return _CallNextHookEx(0, nCode, wParam, lParam)

        mouse_struct = MSLLHOOKSTRUCT.from_address(lParam)
        if (wParam == WM_LBUTTONDOWN or wParam == WM_RBUTTONDOWN or wParam == WM_XBUTTONDOWN or wParam == WM_MBUTTONDOWN) and self.on_click:
            if wParam == WM_XBUTTONDOWN:
                wParam = (mouse_struct.mouseData >> 16) & 0xFF
            self.on_click(mouse_struct.pt.x, mouse_struct.pt.y, self.button[wParam], True)

        elif (wParam == WM_LBUTTONUP or wParam == WM_RBUTTONUP or wParam == WM_XBUTTONUP or wParam == WM_MBUTTONUP) and self.on_click:
            if wParam == WM_XBUTTONUP:
                wParam = (mouse_struct.mouseData >> 16) & 0xFF
            self.on_click(mouse_struct.pt.x, mouse_struct.pt.y, self.button[wParam], False)

        elif wParam == WM_MOUSEMOVE and self.on_move:
            self.on_move(mouse_struct.pt.x, mouse_struct.pt.y)

        elif wParam == WM_MOUSEWHEEL and self.on_scroll:
            wheel_delta = (mouse_struct.mouseData >> 16) & 0xFFFF
            if wheel_delta & 0x8000:
                wheel_delta = -(0x10000 - wheel_delta)
            self.on_scroll(mouse_struct.pt.x, mouse_struct.pt.y, wheel_delta)
        
        return _CallNextHookEx(0, nCode, wParam, lParam)

    @run_in_thread
    def start(self):
        """
        Starts the LowLevelMouseProc hook in a seperate daemon thread
        """
        if self.running:
            raise Exception('You cannot call this function twice you must stop the current hook before starting a new one')
        
        HOOKProc = ctypes.WINFUNCTYPE(ctypes.wintypes.LPVOID, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
        CBTProc = HOOKProc(self.callback)
        self.hook_id = _SetWindowsHookExW(14, CBTProc, 0, 0)


        self.running = True
        msg = ctypes.wintypes.MSG()
        while self.running:
            _GetMessageW(ctypes.byref(msg), 0, 0, 0)

    def stop(self):
        """
        Stops the currently running hook
        """
        if not self.running:
            raise Exception('You cannot stop something that has not been started yet')
        
        self.running = False
        _UnhookWindowsHookEx(self.hook_id)
        _PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)