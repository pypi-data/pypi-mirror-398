import ctypes
from ctypes import windll, wintypes
from .structures import COORD, CONSOLE_CURSOR_INFO, CONSOLE_SCREEN_BUFFER_INFO, ACCENTPOLICY, WINDOWCOMPOSITIONATTRIBDATA
from .enums import AccentState, AccentFlags, AnimationId, GradientColors

class Console:
    STD_OUTPUT_HANDLE = -11
    STD_INPUT_HANDLE = -10
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    ENABLE_PROCESSED_OUTPUT = 0x0001

    def __init__(self):
        self._initialized = False
        self._hwnd = None
        self._h_output = None
        self._h_input = None

    def init(self):
        self._h_output = windll.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE)
        self._h_input = windll.kernel32.GetStdHandle(self.STD_INPUT_HANDLE)
        self._hwnd = windll.kernel32.GetConsoleWindow()
        self._initialized = True
        return self

    def enable_vt(self):
        mode = wintypes.DWORD()
        windll.kernel32.GetConsoleMode(self._h_output, ctypes.byref(mode))
        windll.kernel32.SetConsoleMode(self._h_output, mode.value | self.ENABLE_VIRTUAL_TERMINAL_PROCESSING | self.ENABLE_PROCESSED_OUTPUT)
        return self

    def disable_vt(self):
        mode = wintypes.DWORD()
        windll.kernel32.GetConsoleMode(self._h_output, ctypes.byref(mode))
        windll.kernel32.SetConsoleMode(self._h_output, mode.value & ~self.ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        return self

    def set_thin_cursor(self, size: int = 25, visible: bool = True):
        windll.kernel32.SetConsoleCursorInfo(self._h_output, ctypes.byref(CONSOLE_CURSOR_INFO(bVisible=visible, dwSize=size)))
        return self

    def set_block_cursor(self):
        windll.kernel32.SetConsoleCursorInfo(self._h_output, ctypes.byref(CONSOLE_CURSOR_INFO(bVisible=True, dwSize=100)))
        return self

    def hide_cursor(self):
        windll.kernel32.SetConsoleCursorInfo(self._h_output, ctypes.byref(CONSOLE_CURSOR_INFO(bVisible=False, dwSize=1)))
        return self

    def show_cursor(self):
        windll.kernel32.SetConsoleCursorInfo(self._h_output, ctypes.byref(CONSOLE_CURSOR_INFO(bVisible=True, dwSize=25)))
        return self

    def disable_mouse_interaction(self):
        mode = wintypes.DWORD()
        windll.kernel32.GetConsoleMode(self._h_input, ctypes.byref(mode))
        windll.kernel32.SetConsoleMode(self._h_input, mode.value & ~(0x0001 | 0x0080 | 0x0020 | 0x0004 | 0x0002))
        if self._hwnd:
            windll.user32.SetWindowLongW(self._hwnd, -16, windll.user32.GetWindowLongW(self._hwnd, -16) & ~(0x00020000 | 0x00010000 | 0x00080000))
        return self

    def enable_mouse_interaction(self):
        mode = wintypes.DWORD()
        windll.kernel32.GetConsoleMode(self._h_input, ctypes.byref(mode))
        windll.kernel32.SetConsoleMode(self._h_input, mode.value | 0x0001 | 0x0080 | 0x0020 | 0x0004 | 0x0002)
        return self

    def lock_console_resize(self):
        if self._hwnd:
            windll.user32.SetWindowLongW(self._hwnd, -16, windll.user32.GetWindowLongW(self._hwnd, -16) & ~(0x00020000 | 0x00040000))
            windll.user32.SetWindowPos(self._hwnd, None, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0020)
        return self

    def unlock_console_resize(self):
        if self._hwnd:
            windll.user32.SetWindowLongW(self._hwnd, -16, windll.user32.GetWindowLongW(self._hwnd, -16) | 0x00020000 | 0x00040000)
            windll.user32.SetWindowPos(self._hwnd, None, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0020)
        return self

    def hide_console_scrollbar(self):
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        windll.kernel32.GetConsoleScreenBufferInfo(self._h_output, ctypes.byref(csbi))
        windll.kernel32.SetConsoleScreenBufferSize(self._h_output, COORD(X=csbi.srWindow.Right - csbi.srWindow.Left + 1, Y=csbi.srWindow.Bottom - csbi.srWindow.Top + 1))
        return self

    def enable_blur_behind(self, accent_state: int = AccentState.ACCENT_ENABLE_BLURBEHIND, accent_flags: int = AccentFlags.NONE, gradient_color: int = GradientColors.SEMI_BLACK, animation_id: int = AnimationId.NONE):
        if self._hwnd:
            policy = ACCENTPOLICY(AccentState=accent_state, AccentFlags=accent_flags, GradientColor=gradient_color, AnimationId=animation_id)
            data = WINDOWCOMPOSITIONATTRIBDATA(Attribute=19, Data=ctypes.addressof(policy), SizeOfData=ctypes.sizeof(policy))
            windll.user32.SetWindowCompositionAttribute(self._hwnd, ctypes.byref(data))
        return self

    def disable_blur_behind(self):
        if self._hwnd:
            policy = ACCENTPOLICY(AccentState=0, AccentFlags=0, GradientColor=0, AnimationId=0)
            data = WINDOWCOMPOSITIONATTRIBDATA(Attribute=19, Data=ctypes.addressof(policy), SizeOfData=ctypes.sizeof(policy))
            windll.user32.SetWindowCompositionAttribute(self._hwnd, ctypes.byref(data))
        return self

    def set_title(self, title: str):
        windll.kernel32.SetConsoleTitleW(title)
        return self

    def clear(self):
        print("\033[2J\033[H", end="", flush=True)
        return self

    def reset(self):
        print("\033[0m\033[2J\033[H", end="", flush=True)
        mode = wintypes.DWORD()
        windll.kernel32.GetConsoleMode(self._h_output, ctypes.byref(mode))
        windll.kernel32.SetConsoleMode(self._h_output, mode.value | self.ENABLE_VIRTUAL_TERMINAL_PROCESSING | self.ENABLE_PROCESSED_OUTPUT)
        windll.kernel32.SetConsoleCursorInfo(self._h_output, ctypes.byref(CONSOLE_CURSOR_INFO(bVisible=True, dwSize=25)))
        if self._hwnd:
            windll.user32.SetWindowLongW(self._hwnd, -16, windll.user32.GetWindowLongW(self._hwnd, -16) | 0x00020000 | 0x00040000)
        return self

    def set_size(self, width: int, height: int):
        windll.kernel32.SetConsoleScreenBufferSize(self._h_output, COORD(X=width, Y=height))
        return self

    def move_cursor(self, x: int, y: int):
        print(f"\033[{y};{x}H", end="", flush=True)
        return self

    def get_hwnd(self):
        return self._hwnd

    def get_output_handle(self):
        return self._h_output

    def get_input_handle(self):
        return self._h_input

    @property
    def initialized(self):
        return self._initialized
