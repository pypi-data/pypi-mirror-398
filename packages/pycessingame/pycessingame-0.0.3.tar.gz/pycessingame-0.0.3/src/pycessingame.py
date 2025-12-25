# -----------------------------------------------------------------------------
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or distribute
# this software, either in source code form or as a compiled binary, for any
# purpose, commercial or non-commercial, and by any means.
#
# In jurisdictions that recognize copyright laws, the author or authors of this
# software dedicate any and all copyright interest in the software to the
# public domain. We make this dedication for the benefit of the public at large
# and to the detriment of our heirs and successors. We intend this dedication
# to be an overt act of relinquishment in perpetuity of all present and future
# rights to this software under copyright law.
#
# OPTIONAL ATTRIBUTION:
# Credit to E. Luttmann is appreciated but not required.
#
# For more information, please refer to <https://unlicense.org>
# -----------------------------------------------------------------------------
"""
pycessingame.py

PROCESSING like API implemented for PYTHON only using pygame.

Features:
  - increasing most of the processing API (already)
  - camelCase/snake_case support for variables and functions
  - getPressed(<key>) function to query any <key> at any time

Prerequisites:
  - pygame must be installed ("pip install pygame")

Usage:
    import py_processing_game 

    def setup():
        size(640, 480)
        frameRate(60)

    def draw():
        background(30, 120, 200)
        fill(255, 200, 0)
        stroke(255)
        strokeWeight(4)
        ellipse(width/2, height/2, 150, 150)

    run()
"""

# -------------------------- Imports --------------------------

import sys
import colorsys
import time
import math
import __main__
import re
import datetime
import pygame
import random as _pyrandom

# -------------------------- Constants --------------------------

LEFT = 'LEFT'
RIGHT = 'RIGHT'
CENTER = 'CENTER'
TOP = 'TOP'
PI = math.pi
TWO_PI = 2*math.pi
HALF_PI = math.pi/2
QUARTER_PI = math.pi/4
DEGREES = 180.0 / math.pi
RADIANS = math.pi / 180.0
CORNER = 'CORNER'
RADIUS = 'RADIUS'
CORNERS = 'CORNERS'

ARROW = "ARROW"
CROSS = "CROSS"
HAND = "HAND"
MOVE = "MOVE"
WAIT = "WAIT"
CURSOR_CONSTANTS = {ARROW, CROSS, HAND, MOVE, WAIT}

RGB = 'RGB'
HSB = 'HSB'

# ------- Function Handle for overloaded function -----------

_python_map = map

# -------------------------- State --------------------------
class _State:
    def __init__(self):
        global LEFT
        self.width = 640
        self.height = 480
        self.surface = None

        # Looping
        self._looping = True
        self._draw_next_frame = True
        
        # Environment
        self._window_title = "pygame processing-Style"
        self._cursor_visible = True
        self._cursor_mode = ARROW
        self._cursor_image = None
        self._cursor_hotspot = (0, 0)
        self._smooth = True

        # Styles & Color mode
        self._color_mode = 'RGB'     # 'RGB' or 'HSB'
        self._color_max = [255, 255, 255, 255]  # r,g,b,a OR h,s,b,a
        self._fill_color = (255, 255, 255, 255)
        self._stroke_color = (0, 0, 0, 255)
        self._background_color = (0, 0, 0, 255)
        self._use_fill = True
        self._use_stroke = True
        self._stroke_weight = 1
        self._text_size = 16
        self._text_align_x = LEFT
        self._text_align_y = None
        self._text_font_cache = {}

        # Modes
        self.rect_mode = 'CORNER'
        self.ellipse_mode = 'CENTER'

        # Timing
        self._frame_rate = 60
        self.frameCount = 0
        self._clock = None
        self._running = True
        self._last_time_global = None

        # Input
        self.mouseX = 0
        self.mouseY = 0
        self.pmouseX = 0
        self.pmouseY = 0
        self.mousePressed = False
        self.mouseButton = None

        self.key = None
        self.keyCode = None
        self.keyPressed = False
        # Key state (continuous pressed state)
        self._keys_down = set()


        self._verbose = True

P = _State()

# -------------------------- Helpers --------------------------

_mouse_map = {1:'LEFT', 2:'CENTER', 3:'RIGHT'}

# -------------------------- Full Proxy System --------------------------
def _camel_to_snake(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

class BaseProxy:
    def __init__(self, state, attr):
        self._state = state
        self._attr = attr
        self._callback = None

    def get(self):
        return getattr(self._state, self._attr)

    def set(self, value):
        setattr(self._state, self._attr, value)

    def register_callback(self, fn):
        if callable(fn):
            self._callback = fn

    # Descriptor
    def __get__(self, instance=None, owner=None): return self.get()
    def __set__(self, instance, value): self.set(value)

    # Callable
    def __call__(self, *args, **kwargs):
        if self._callback:
            return self._callback(*args, **kwargs)
        raise TypeError(f"{self._attr} is not callable (no callback assigned)")

    # Representation
    def __repr__(self): return repr(self.get())
    def __str__(self): return str(self.get())

    # Bool / Comparison
    def __bool__(self): return bool(self.get())
    def __eq__(self, other): return self.get() == other
    def __ne__(self, other): return self.get() != other
    def __lt__(self, other): return self.get() < other
    def __le__(self, other): return self.get() <= other
    def __gt__(self, other): return self.get() > other
    def __ge__(self, other): return self.get() >= other

    # Numeric
    def __int__(self): return int(self.get())
    def __float__(self): return float(self.get())
    def __complex__(self): return complex(self.get())
    def __index__(self): return int(self.get())

    # Arithmetic
    def __add__(self, other): return self.get() + other
    def __radd__(self, other): return other + self.get()
    def __sub__(self, other): return self.get() - other
    def __rsub__(self, other): return other - self.get()
    def __mul__(self, other): return self.get() * other
    def __rmul__(self, other): return other * self.get()
    def __truediv__(self, other): return self.get() / other
    def __rtruediv__(self, other): return other / self.get()
    def __floordiv__(self, other): return self.get() // other
    def __rfloordiv__(self, other): return other // self.get()
    def __mod__(self, other): return self.get() % other
    def __rmod__(self, other): return other % self.get()
    def __pow__(self, other): return self.get() ** other
    def __rpow__(self, other): return other ** self.get()
    def __neg__(self): return -self.get()
    def __pos__(self): return +self.get()
    def __abs__(self): return abs(self.get())

class ProcessingVar(BaseProxy):
    pass

class DualProxy(BaseProxy):
    def get(self): return getattr(self._state, self._attr)
    def set(self, value): setattr(self._state, self._attr, value)
    def __call__(self, *args, **kwargs):
        if self._callback:
            return self._callback(*args, **kwargs)
        return None

def _inject_var(name, dual=False):
    proxy_class = DualProxy if dual else ProcessingVar
    proxy = proxy_class(P, name)
    snake = _camel_to_snake(name)

    # Callback falls schon vorhanden
    user_fn = getattr(__main__, name, None)
    if callable(user_fn) and dual:
        proxy.register_callback(user_fn)

    setattr(__main__, name, proxy)
    setattr(__main__, snake, proxy)
    return proxy

# -------------------------- Inject all variables --------------------------
def _inject_all():
    _inject_var("width")
    _inject_var("height")
    _inject_var("mouseX")
    _inject_var("mouseY")
    _inject_var("pmouseX")
    _inject_var("pmouseY")
    _inject_var("mousePressed", dual=True)
    _inject_var("mouseButton")
    _inject_var("key")
    _inject_var("keyCode")
    _inject_var("keyPressed", dual=True)
    _inject_var("frameCount", dual=True)

def _inject_key_constants_into_main():
    for name in PROCESSING_KEY_CONSTANTS:
        setattr(__main__, name, name)
    for name in CURSOR_CONSTANTS:
        setattr(__main__, name, name)
    
def _inject_return_alias():
    import __main__
    __main__.RETURN = "ENTER"

# -------------------------- Constants --------------------------
_keycode_map = {
    pygame.K_LEFT:      "LEFT",
    pygame.K_RIGHT:     "RIGHT",
    pygame.K_UP:        "UP",
    pygame.K_DOWN:      "DOWN",

    pygame.K_RETURN:    "ENTER",
    pygame.K_KP_ENTER:  "ENTER",
    pygame.K_BACKSPACE: "BACKSPACE",
    pygame.K_TAB:       "TAB",
    pygame.K_ESCAPE:    "ESC",
    pygame.K_DELETE:    "DELETE",
    pygame.K_HOME:      "HOME",
    pygame.K_END:       "END",
    pygame.K_PAGEUP:    "PAGE_UP",
    pygame.K_PAGEDOWN:  "PAGE_DOWN",
    pygame.K_CAPSLOCK: "CAPSLOCK",
    pygame.K_INSERT:   "INSERT",
    
    pygame.K_LSHIFT:    "SHIFT",
    pygame.K_RSHIFT:    "SHIFT",
    pygame.K_LCTRL:     "CONTROL",
    pygame.K_RCTRL:     "CONTROL",
    pygame.K_LALT:      "ALT",
    pygame.K_RALT:      "ALT",

    pygame.K_F1: "F1",  pygame.K_F2: "F2",  pygame.K_F3: "F3",
    pygame.K_F4: "F4",  pygame.K_F5: "F5",  pygame.K_F6: "F6",
    pygame.K_F7: "F7",  pygame.K_F8: "F8",  pygame.K_F9: "F9",
    pygame.K_F10:"F10", pygame.K_F11:"F11", pygame.K_F12:"F12",
}


PROCESSING_KEY_CONSTANTS = {
    "LEFT", "RIGHT", "UP", "DOWN",
    "ENTER", "RETURN", "BACKSPACE", "TAB", "ESC", "DELETE",
    "SHIFT", "CONTROL", "ALT",
    "HOME", "END", "PAGE_UP", "PAGE_DOWN",
    "F1","F2","F3","F4","F5","F6",
    "F7","F8","F9","F10","F11","F12"
}

for const_name in ['LEFT','RIGHT','CENTER','PI','TWO_PI','HALF_PI','QUARTER_PI','DEGREES','RADIANS','CORNER']:
    setattr(__main__, const_name, globals()[const_name])


def _get_font(size):
    """Return a pygame Font object from cache (None -> default font)."""
    key = int(size)
    font = P._text_font_cache.get(key)
    if font is None:
        # ensure pygame.font is initialized
        try:
            if not pygame.font.get_init():
                pygame.font.init()
        except Exception:
            pass
        font = pygame.font.Font(None, key)
        P._text_font_cache[key] = font
    return font


def _apply_fill(surf,func,*args,**kwargs):
    if P._use_fill and P._fill: func(surf,P._fill[:3],*args,**kwargs)

def _apply_stroke(surf,func,*args,**kwargs):
    if P._use_stroke and P._stroke: func(surf,P._stroke[:3],*args,width=P._stroke_weight,**kwargs)
# -------------------------- Input helpers --------------------------
def _update_mouse(event):
    # Handle movement
    if event.type == pygame.MOUSEMOTION:
        P.pmouseX, P.pmouseY = P.mouseX, P.mouseY
        P.mouseX, P.mouseY = event.pos

        if P.mousePressed:
            # Dragging
            P._mouse_dragged = True
            if callable(getattr(__main__, 'mouseDragged', None)):
                __main__.mouseDragged()
        else:
            # Moving without button
            if callable(getattr(__main__, 'mouseMoved', None)):
                __main__.mouseMoved()
        return

    # Handle mouse down
    if event.type == pygame.MOUSEBUTTONDOWN:
        # Wheel events should not trigger click logic
        if event.button in (4, 5):
            return

        P.pmouseX, P.pmouseY = P.mouseX, P.mouseY
        P.mouseX, P.mouseY = event.pos

        P.mousePressed = True
        P.mouseButton = _mouse_map.get(event.button)
        P._mouse_dragged = False
        P._mouse_down_pos = event.pos
        P._mouse_down_time = time.time()

        if callable(getattr(__main__, 'mousePressed', None)):
            __main__.mousePressed()
        return

    # Handle mouse up
    if event.type == pygame.MOUSEBUTTONUP:
        # Again: wheel events do not trigger click logic
        if event.button in (4, 5):
            return

        P.pmouseX, P.pmouseY = P.mouseX, P.mouseY
        P.mouseX, P.mouseY = event.pos

        was_dragged = P._mouse_dragged
        down_pos = P._mouse_down_pos
        down_time = P._mouse_down_time

        P.mousePressed = False
        P.mouseButton = None

        # Always trigger mouseReleased
        if callable(getattr(__main__, 'mouseReleased', None)):
            __main__.mouseReleased()

        # Click detection: small movement + fast release
        if not was_dragged:
            dx = P.mouseX - down_pos[0]
            dy = P.mouseY - down_pos[1]
            dist_sq = dx*dx + dy*dy
            time_diff = time.time() - down_time

            if dist_sq < 9 and time_diff < 0.3:
                if callable(getattr(__main__, 'mouseClicked', None)):
                    __main__.mouseClicked()
        return


def _update_mouse_wheel(event):
    """
    Processing-kompatibles mouseWheel():
    - event.delta > 0  = nach oben
    - event.delta < 0  = nach unten

    Processing ruft mouseWheel(event) auf,
    wobei event.count die Scroll-Richtung enthält.
    """

    # Pygame: button 4 (up), button 5 (down)
    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 4:  # wheel up
            wheel = -1
        elif event.button == 5:  # wheel down
            wheel = 1
        else:
            return
    else:
        return

    class WheelEvent:
        def __init__(self, count):
            self.count = count

    if callable(getattr(__main__, "mouseWheel", None)):
        __main__.mouseWheel(WheelEvent(wheel))

def _update_keyboard(event):
    if event.type==pygame.KEYDOWN:
        P.keyPressed=True
        P.keyCode=event.key
        # If not a special name, try unicode
        if event.key in _keycode_map:
#            P.key = _keycode_map.get(event.key, None)
            key_name = _keycode_map[event.key]
            P.key = key_name
            P._keys_down.add(key_name)
        else:
            try:
                P.key=event.unicode
                print(P.key)
                if P.key:
                    P._keys_down.add(P.key)
            except:
                P.key=None
        if callable(getattr(__main__,'keyPressed',None)):
            __main__.keyPressed()
        if callable(getattr(__main__,'keyTyped',None)) and P.key:
            __main__.keyTyped()
    elif event.type==pygame.KEYUP:
        P.keyPressed=False
        # Remove from pressed set
        if event.key in _keycode_map:
            P._keys_down.discard(_keycode_map[event.key])
        else:
            try:
                if event.unicode:
                    P._keys_down.discard(event.unicode)
            except:
                pass
        if callable(getattr(__main__,'keyReleased',None)):
            __main__.keyReleased()

# -------------------------- API Functions --------------------------

def map(*args):
    # Processing-Style map: 5 Parameter
    if len(args) == 5:
        """
        Re-maps a number from one range to another.
        Processing-compatible behavior.

        Example:
            map(5, 0, 10, 0, 100) -> 50.0
        """

        if start1 == stop1:
            raise ValueError("map() input range must not be zero")

        return start2 + (stop2 - start2) * ((value - start1) / (stop1 - start1))
    # Python-Style map: alles andere
    else:
        return _python_map(*args)

def getPressed(key=None):
    """
    Processing-style continuous key state check.

    Usage:
        getPressed()        -> True if ANY key is pressed
        getPressed('a')     -> True if 'a' is pressed
        getPressed(LEFT)    -> True if LEFT arrow is pressed
        getPressed(SHIFT)   -> True if any shift is pressed
    """

    # Any key?
    if key is None:
        return bool(P._keys_down)

    # Normalize
    if isinstance(key, str):
        key = key.upper() if len(key) > 1 else key

    return key in P._keys_down


def noLoop():
    """Stop automatic calling of draw() each frame."""
    P._looping = False

def loop():
    """Resume automatic calling of draw() each frame."""
    P._looping = True

def redraw():
    """Force draw() to execute once, even if noLoop() is active."""
    P._draw_next_frame = True
    
def random(*args):
    """
    Processing-compatible random():
    - random(high)
    - random(low, high)
    """

    if len(args) == 0:
        # Processing: random() without args → returns a float between 0 and 1
        return _pyrandom.random()

    if len(args) == 1:
        high = args[0]
        return _pyrandom.random() * high

    if len(args) == 2:
        low, high = args
        return low + _pyrandom.random() * (high - low)

    raise TypeError("random() takes 0, 1 or 2 arguments")

def randomSeed(v):
    _pyrandom.seed(v)
def randomGaussian():
    # Box-Muller transform
    u1 = 1.0 - _pyrandom.random()
    u2 = 1.0 - _pyrandom.random()
    return ( (-2 * math.log(u1)) ** 0.5 ) * math.cos(2 * math.pi * u2 )

def millis():
    """
    Returns milliseconds since sketch start.
    Processing: millis()
    """
    return int((time.time() - P._last_time_global) * 1000)

def second():
    """Return current second 0–59."""
    return datetime.datetime.now().second

def minute():
    """Return current minute 0–59."""
    return datetime.datetime.now().minute

def hour():
    """Return current hour 0–23."""
    return datetime.datetime.now().hour

def day():
    """Return day of month 1–31."""
    return datetime.datetime.now().day

def month():
    """Return month 1–12."""
    return datetime.datetime.now().month

def year():
    """Return full year (e.g. 2025)."""
    return datetime.datetime.now().year

def weekday():
    """
    Monday=1 ... Sunday=7
    (Processing hat das nicht, aber viele wollen es)
    """
    return datetime.datetime.now().isoweekday()

def timestamp():
    """
    Returns UNIX timestamp as int.
    (Zusatzfunktion – optional)
    """
    return int(time.time())

def textSize(size):
    P._text_size = size
    
def textAlign(align_x, align_y = None):
    P._text_align_x = align_x
    if align_y:
        P._text_align_y = align_y
        print("WARNING: Y alignment not implemented")

def textFont(which, size = None):
    print("WARNING: textFont not implemented")

def text(s, x, y):
    """
    Draw text onto the P.surface.
    - s: text (any -> str)
    - x, y: position (top-left by default, affected by align)
    - align: 'left'|'center'|'right'
    """
    if P.surface is None:
        return

    # coerce to str
    txt = str(s)

    # choose color from current fill (fallback white)
    color = P._fill[:3]
    font = _get_font(P._text_size)

    # render text surface (antialias = True)
    try:
        text_surf = font.render(txt, P._smooth, color)
    except Exception:
        # fallback if render fails
        text_surf = font.render(txt, False, color)

    tw, th = text_surf.get_size()

    # alignment handling
    ax = x
    if P._text_align_x == CENTER:
        ax = x - tw // 2
    elif P._text_align_x == RIGHT:
        ax = x - tw

    # blit to main surface
    P.surface.blit(text_surf, (int(ax), int(y)))

def size(w,h):
    P.width = int(w)
    P.height = int(h)
    if pygame.get_init():
        pygame.display.set_mode((P.width, P.height))
        P.surface = pygame.Surface((P.width,P.height), pygame.SRCALPHA).convert_alpha()

def windowTitle(title):
    P._window_title = str(title)
    try:
        pygame.display.set_caption(P._window_title)
    except Exception:
        pass

def smooth():
    """Enable anti-aliasing where supported."""
    P._smooth = True

def noSmooth():
    """Disable all anti-aliasing."""
    P._smooth = False


def noCursor():
    """
    Hide the mouse cursor (Processing-compatible).
    Works before and after run().
    """
    P._cursor_visible = False
    P._cursor_image = None
    P._cursor_mode = None
    try:
        pygame.mouse.set_visible(False)
    except Exception:
        pass

def cursor(mode_or_img=None, x=None, y=None):
    """
    Processing-compatible cursor() API.

    Supported calls:
        cursor()                   → default arrow
        cursor(MODE)               → ARROW, CROSS, HAND, MOVE, WAIT
        cursor(image, x, y)        → custom image cursor
    """

    # ------------------------------
    # CASE 1: cursor()  → default arrow
    # ------------------------------
    if mode_or_img is None:
        P._cursor_visible = True
        P._cursor_mode = ARROW
        P._cursor_image = None

        try:
            pygame.mouse.set_visible(True)
            pygame.mouse.set_cursor(pygame.Cursor(pygame.SYSTEM_CURSOR_ARROW))
        except Exception:
            pass

        return

    # ------------------------------
    # CASE 2: cursor(img, x, y) → custom image
    # (img = pygame.Surface)
    # ------------------------------
    if isinstance(mode_or_img, pygame.Surface):
        img = mode_or_img
        hx = int(x or 0)
        hy = int(y or 0)

        P._cursor_visible = True
        P._cursor_image = img
        P._cursor_hotspot = (hx, hy)
        P._cursor_mode = None  # disable system cursor modes

        try:
            pygame.mouse.set_visible(True)
            # Pygame cannot use ARGB images as real cursors → so fake minimal cursor
            pygame.mouse.set_cursor(
                pygame.Cursor(
                    (img.get_width(), img.get_height()),
                    (hx, hy),
                    pygame.cursors.compile(['X'], black='X')
                )
            )
        except Exception:
            pass

        return

    # ------------------------------
    # CASE 3: cursor(MODE)
    # mode is a string: ARROW, CROSS, HAND, MOVE, WAIT
    # ------------------------------
    if isinstance(mode_or_img, str):
        mode = mode_or_img.upper()

        if mode not in CURSOR_CONSTANTS:
            raise ValueError(f"cursor(): unknown mode '{mode}'")

        P._cursor_visible = True
        P._cursor_mode = mode
        P._cursor_image = None  # disable custom img cursor

        pygame_cursor_map = {
            ARROW: pygame.SYSTEM_CURSOR_ARROW,
            CROSS: pygame.SYSTEM_CURSOR_CROSSHAIR,
            HAND: pygame.SYSTEM_CURSOR_HAND,
            MOVE: pygame.SYSTEM_CURSOR_SIZEALL,
            WAIT: pygame.SYSTEM_CURSOR_WAIT,
        }

        try:
            pygame.mouse.set_visible(True)
            pygame.mouse.set_cursor(pygame.Cursor(pygame_cursor_map[mode]))
        except Exception:
            pass

        return

    # ------------------------------
    # Anything else is invalid
    # ------------------------------
    raise TypeError("cursor(): expected None, str mode, or pygame.Surface image")


def frameRate(f):
    P._frame_rate = float(f)

def _hsb_to_rgb(h, s, b):
    """
    h,s,b ∈ [0..1]
    returns r,g,b ∈ [0..255]
    """
    r, g, b = colorsys.hsv_to_rgb(h, s, b)
    return int(r * 255), int(g * 255), int(b * 255)

def _as_rgba(c):
    if not isinstance(c, (tuple, list)):
        raise TypeError("Expected color tuple")
    if len(c) == 3:
        return c[0], c[1], c[2], 255
    if len(c) == 4:
        return c
    raise ValueError("Invalid color format")

def _rgb_to_hsb(r, g, b):
    # normalize to 0..1
    r /= 255.0
    g /= 255.0
    b /= 255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return (
        int(h * 255),
        int(s * 255),
        int(v * 255),
    )

def colorMode(mode, *args):
    """
    Processing-kompatible colorMode() Funktion.
    Unterstützt RGB und HSB.
    """
    mode = mode.upper()
    if mode not in ('RGB', 'HSB'):
        raise ValueError("colorMode(): mode must be RGB or HSB")

    P._color_mode = mode

    if len(args) == 0:
        P._color_max = [255, 255, 255, 255]

    elif len(args) == 1:
        P._color_max = [args[0], args[0], args[0], args[0]]

    elif len(args) == 3:
        P._color_max = [args[0], args[1], args[2], 255]

    elif len(args) == 4:
        P._color_max = [args[0], args[1], args[2], args[3]]

    else:
        raise TypeError("colorMode() accepts 1, 2, 4 or 5 arguments")


'''
def color(*args):
    """
    Processing-kompatible color()-Funktion.
    Gibt immer ein (r,g,b,a)-Tuple zurück.
    Unterstützt int (0-255) und float (0.0-1.0).
    Akzeptiert Tupel oder Listen als einzelnes Argument.
    """
    # Flatten single tuple/list argument recursively
    while len(args) == 1 and isinstance(args[0], (tuple, list)):
        args = tuple(args[0])

    def fix(v):
        # float 0..1 -> 0..255, int clamp 0..255
        if isinstance(v, (int, float)):
            if isinstance(v, float) and 0 <= v <= 1:
                return int(v * 255)
            return int(max(0, min(255, v)))
        raise TypeError(f"color() received invalid component type: {type(v)}")

    n = len(args)
    if n == 1:
        r = g = b = args[0]
        a = 255
    elif n == 2:
        r = g = b = args[0]
        a = args[1]
    elif n == 3:
        r, g, b = args
        a = 255
    elif n == 4:
        r, g, b, a = args
    else:
        raise TypeError(f"color() accepts 1-4 arguments, got {n}")

    return (fix(r), fix(g), fix(b), fix(a))
'''
def color(*args):
    # Flatten tuple/list
    while len(args) == 1 and isinstance(args[0], (tuple, list)):
        args = tuple(args[0])

    n = len(args)
    if n == 1:
        v = args[0]
        comps = [v, v, v, P._color_max[3]]
    elif n == 2:
        v, a = args
        comps = [v, v, v, a]
    elif n == 3:
        comps = [args[0], args[1], args[2], P._color_max[3]]
    elif n == 4:
        comps = list(args)
    else:
        raise TypeError("color() accepts 1–4 arguments")

    # Normalize to 0..1
    norm = []
    for i, c in enumerate(comps):
        m = P._color_max[i]
        norm.append(c / m if m != 0 else 0)

    # Convert to RGBA
    if P._color_mode == 'RGB':
        r = int(norm[0] * 255)
        g = int(norm[1] * 255)
        b = int(norm[2] * 255)
    else:  # HSB
        r, g, b = _hsb_to_rgb(norm[0], norm[1], norm[2])

    a = int(norm[3] * 255)

    return (
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b)),
        max(0, min(255, a)),
    )

def alpha(c):
    return _as_rgba(c)[3]

def red(c):
    return _as_rgba(c)[0]

def green(c):
    return _as_rgba(c)[1]

def blue(c):
    return _as_rgba(c)[2]
def hue(c):
    r, g, b, _ = _as_rgba(c)
    h, _, _ = _rgb_to_hsb(r, g, b)
    return h
def saturation(c):
    r, g, b, _ = _as_rgba(c)
    _, s, _ = _rgb_to_hsb(r, g, b)
    return s
def brightness(c):
    r, g, b, _ = _as_rgba(c)
    _, _, v = _rgb_to_hsb(r, g, b)
    return v

def lerpColor(c1, c2, amt):
    """
    Linearly interpolates between two colors.
    Processing-compatible implementation.

    Parameters:
        c1, c2 : color tuples (r, g, b) or (r, g, b, a)
        amt    : interpolation amount (float)

    Returns:
        (r, g, b, a) tuple
    """

    if c1 is None or c2 is None:
        raise ValueError("lerpColor(): colors must not be None")

    # Normalize colors to RGBA
    if len(c1) == 3:
        r1, g1, b1 = c1
        a1 = 255
    elif len(c1) == 4:
        r1, g1, b1, a1 = c1
    else:
        raise ValueError("lerpColor(): invalid color c1")

    if len(c2) == 3:
        r2, g2, b2 = c2
        a2 = 255
    elif len(c2) == 4:
        r2, g2, b2, a2 = c2
    else:
        raise ValueError("lerpColor(): invalid color c2")

    def lerp(a, b, t):
        return a + (b - a) * t

    r = int(lerp(r1, r2, amt))
    g = int(lerp(g1, g2, amt))
    b = int(lerp(b1, b2, amt))
    a = int(lerp(a1, a2, amt))

    # Clamp like Processing's internal color storage
    def clamp(v):
        return max(0, min(255, v))

    return (clamp(r), clamp(g), clamp(b), clamp(a),)
'''
from math import fmod

def lerpColor(c1, c2, amt):
    """
    Processing-kompatible Farbliniearinterpolation.
    
    c1, c2 : RGBA-Tupel (0-255)
    amt : float (0..1 normal, >1 extrapolation erlaubt)
    
    Berücksichtigt colorMode() global:
      - RGB: lineare Interpolation der RGBA-Kanäle
      - HSB: lineare Interpolation von H, S, B, A mit Hue-Wrap
    """
    # globale Farb-Settings
    global P

    # Hilfsfunktion: clamp und round auf 0-255 int
    def clamp_byte(v):
        return max(0, min(255, int(round(v))))

    if P._color_mode == 'RGB':
        # Lineare Interpolation R,G,B,A
        r = c1[0] + (c2[0]-c1[0])*amt
        g = c1[1] + (c2[1]-c1[1])*amt
        b = c1[2] + (c2[2]-c1[2])*amt
        a = c1[3] + (c2[3]-c1[3])*amt
        return (clamp_byte(r), clamp_byte(g), clamp_byte(b), clamp_byte(a))

    elif P._color_mode == 'HSB':
        # Konvertiere RGB -> HSB
        h1,s1,b1 = rgb_to_hsb(*c1[:3])
        h2,s2,b2 = rgb_to_hsb(*c2[:3])
        a1,a2 = c1[3], c2[3]

        # Hue shortest path
        dh = h2 - h1
        if dh > 180:
            dh -= 360
        elif dh < -180:
            dh += 360

        h = h1 + dh*amt
        h = fmod(h,360)
        if h<0: h+=360

        s = s1 + (s2-s1)*amt
        b = b1 + (b2-b1)*amt
        a = a1 + (a2-a1)*amt

        r,g,b = hsb_to_rgb(h,s,b)
        return (clamp_byte(r), clamp_byte(g), clamp_byte(b), clamp_byte(a))

    else:
        raise ValueError(f"Unknown color mode: {P._color_mode}")

def rgb_to_hsb(r, g, b):
    """RGB 0-255 -> HSB H:0-360, S,B:0-100"""
    r_, g_, b_ = r/255.0, g/255.0, b/255.0
    max_c = max(r_, g_, b_)
    min_c = min(r_, g_, b_)
    delta = max_c - min_c

    # Hue
    if delta == 0:
        h = 0
    elif max_c == r_:
        h = 60 * (((g_ - b_) / delta) % 6)
    elif max_c == g_:
        h = 60 * (((b_ - r_) / delta) + 2)
    else:
        h = 60 * (((r_ - g_) / delta) + 4)

    # Saturation
    s = 0 if max_c==0 else (delta / max_c)*100

    # Brightness
    v = max_c*100

    return h, s, v
'''
def hsb_to_rgb(h, s, v):
    """HSB H:0-360, S,B:0-100 -> RGB 0-255"""
    s_ = s/100.0
    v_ = v/100.0
    c = v_ * s_
    x = c * (1 - abs(fmod(h/60.0,2) -1))
    m = v_ - c

    if 0 <= h < 60:
        r1,g1,b1 = c,x,0
    elif 60 <= h < 120:
        r1,g1,b1 = x,c,0
    elif 120 <= h < 180:
        r1,g1,b1 = 0,c,x
    elif 180 <= h < 240:
        r1,g1,b1 = 0,x,c
    elif 240 <= h < 300:
        r1,g1,b1 = x,0,c
    else: # 300<=h<360
        r1,g1,b1 = c,0,x

    r = (r1 + m) * 255
    g = (g1 + m) * 255
    b = (b1 + m) * 255
    return int(round(r)), int(round(g)), int(round(b))

def background(*args):
    col4 = color(args)
    if P.surface is None: return
    if col4[3]<255:
        tmp = pygame.Surface((P.width,P.height), pygame.SRCALPHA)
        tmp.fill(col4)
        P.surface.blit(tmp,(0,0))
    else:
        P.surface.fill(col4[:3])

def clear():
    if P.surface:
        P.surface.fill((0,0,0,0))
def fill(*args):
    if len(args)==0:
        return
    P._fill = color(args)
    P._use_fill = True

def noFill():
    P._use_fill = False
def stroke(*args):
    if len(args)==0:
        return
    P._stroke = color(args)
    P._use_stroke = True

def noStroke():
    P._use_stroke = False
def strokeWeight(w):
    P._stroke_weight = max(1,int(w))
def rectMode(mode):
    P.rect_mode = mode.upper()
def ellipseMode(mode):
    P.ellipse_mode = mode.upper()

def rect(x,y,w,h):
    rx,ry,rw,rh=float(x),float(y),float(w),float(h)
    if P.rect_mode=='CENTER':
        rx-=rw/2; ry-=rh/2
    r = pygame.Rect(int(rx),int(ry),int(rw),int(rh))
    _apply_fill(P.surface,pygame.draw.rect,r)
    _apply_stroke(P.surface,pygame.draw.rect,r)

def ellipse(x, y, w, h):
    x = float(x)
    y = float(y)
    w = float(w)
    h = float(h)

    if P.ellipse_mode == CENTER:
        rx = x - w / 2
        ry = y - h / 2
        rw = w
        rh = h

    elif P.ellipse_mode == RADIUS:
        rx = x - w
        ry = y - h
        rw = w * 2
        rh = h * 2

    elif P.ellipse_mode == CORNER:
        rx = x
        ry = y
        rw = w
        rh = h

    elif P.ellipse_mode == CORNERS:
        rx = min(x, w)
        ry = min(y, h)
        rw = abs(w - x)
        rh = abs(h - y)

    else:
        raise ValueError(f"Invalid ellipseMode: {P.ellipse_mode}")

    rect = pygame.Rect(int(rx), int(ry), int(rw), int(rh))
    _apply_fill(P.surface, pygame.draw.ellipse, rect)
    _apply_stroke(P.surface, pygame.draw.ellipse, rect)


def line(x1,y1,x2,y2):
    if P._smooth:
        if P._use_stroke:
            pygame.draw.aaline(P.surface,P._stroke[:3],(int(x1),int(y1)),(int(x2),int(y2)),P._stroke_weight)
    else:
        if P._use_stroke:
            pygame.draw.line(P.surface,P._stroke[:3],(int(x1),int(y1)),(int(x2),int(y2)),P._stroke_weight)
        

def point(x,y):
    if P._use_stroke: pygame.draw.circle(P.surface,P._stroke[:3],(int(x),int(y)),max(1,P._stroke_weight)//2)

def circle(cx,cy,r): ellipse(cx,cy,r*2,r*2)
def triangle(x1,y1,x2,y2,x3,y3):
    pts=[(int(x1),int(y1)),(int(x2),int(y2)),(int(x3),int(y3))]
    _apply_fill(P.surface,pygame.draw.polygon,pts)
    _apply_stroke(P.surface,pygame.draw.polygon,pts)


# -------------------------- Run loop --------------------------
def run():
    _inject_all()  # Camel/Snake, DualProxies + normale Variablen
    _inject_key_constants_into_main()
    _inject_return_alias()

    pygame.init()
    
    # Apply startup cursor state
    if not P._cursor_visible:
        pygame.mouse.set_visible(False)
    else:
        if P._cursor_image:
            cursor(P._cursor_image, *P._cursor_hotspot)
        elif P._cursor_mode:
            cursor(P._cursor_mode)
        else:
            cursor()

    size(P.width,P.height)
    pygame.display.set_caption(P._window_title)
    P._clock = pygame.time.Clock()

    P._running = True
    P._last_time = time.time()
    P._last_time_global = P._last_time

    setup_fn = getattr(__main__,'setup',None)
    draw_fn = getattr(__main__,'draw',None)
    if callable(setup_fn): setup_fn()

    while P._running:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                P._running=False
            elif event.type in (pygame.MOUSEMOTION,pygame.MOUSEBUTTONDOWN,pygame.MOUSEBUTTONUP):
                _update_mouse(event)
            elif event.type in (pygame.KEYDOWN,pygame.KEYUP):
                _update_keyboard(event)

        if callable(draw_fn):
            # Wenn looping aktiv oder redraw angefordert
            if P._looping or P._draw_next_frame:
                try:
                    draw_fn()
                except Exception:
                    import traceback; traceback.print_exc()
                    P._running=False
                    break
                P._draw_next_frame = False  # redraw zurücksetzen

        pygame.display.get_surface().blit(P.surface,(0,0))
        pygame.display.flip()
        P.frameCount+=1
        P._clock.tick(P._frame_rate)

    pygame.quit()

# -------------------------- Demo --------------------------
if __name__=='__main__':
    def setup():
        size(400,400)
        frameRate(60)        

    def draw():
        background(25,25,30)
        t = P.frameCount/60.0
        cx,cy = P.width/2,P.height/2
        c = color(255,180,0)
        fill(c)
        noStroke()
        circle(cx,cy,120)
        stroke(255)
        strokeWeight(2)
        for i in range(12):
            a = t + i*2*math.pi/12
            line(cx,cy,cx+math.cos(a)*140,cy+math.sin(a)*140)

        if getPressed(ESC):
            P._running = False

    run()
