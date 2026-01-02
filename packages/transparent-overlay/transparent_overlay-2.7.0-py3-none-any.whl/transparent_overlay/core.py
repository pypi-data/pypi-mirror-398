import sys
import time
from threading import Thread, Event, Lock
from ctypes import *
from ctypes.wintypes import POINT, SIZE, BYTE
import logging
from typing import Any, Dict, List, Optional, Tuple, DefaultDict, Literal, Sequence
from collections import defaultdict

# OS compatibility check
if sys.platform != 'win32':
    raise ImportError("This library works only on Windows")

try:
    from win32api import GetModuleHandle, GetSystemMetrics
    import win32con
    import win32gui
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    raise ImportError(f"Required dependencies not found: {e}")

# Module logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Optional Numba import with availability flag and fallback
try:
    from numba import jit  # type: ignore

    NUMBA_AVAILABLE = True
except Exception:
    NUMBA_AVAILABLE = False


    def jit(*a, **kw):  # type: ignore
        def wrapper(f):
            return f

        logger.warning("Numba not found. Falling back to NumPy implementation for blitting.")
        return wrapper


class BLENDFUNCTION(Structure):
    _fields_ = [
        ("BlendOp", BYTE),
        ("BlendFlags", BYTE),
        ("SourceConstantAlpha", BYTE),
        ("AlphaFormat", BYTE)
    ]


if NUMBA_AVAILABLE:
    @jit(nopython=True, fastmath=True, cache=True)
    def _blit_sprite_into_buf(buf, sprite, x, y):
        """Optimized blit with Numba"""
        sh, sw = sprite.shape[:2]
        bh, bw = buf.shape[:2]

        # Coordinate clipping
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(bw, x + sw), min(bh, y + sh)
        if x1 >= x2 or y1 >= y2:
            return

        # Source region offsets inside the sprite (ensure non-negative)
        sx1, sy1 = x1 - x, y1 - y
        if sx1 < 0:
            sx1 = 0
        if sy1 < 0:
            sy1 = 0
        sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)

        # Per-pixel processing
        for i in range(sy1, sy2):
            buf_y = y1 + (i - sy1)
            for j in range(sx1, sx2):
                buf_x = x1 + (j - sx1)

                # Read pixels as int to avoid overflow in fallback without Numba
                src_r = int(sprite[i, j, 0])
                src_g = int(sprite[i, j, 1])
                src_b = int(sprite[i, j, 2])
                src_a = int(sprite[i, j, 3])

                dst_r = int(buf[buf_y, buf_x, 0])
                dst_g = int(buf[buf_y, buf_x, 1])
                dst_b = int(buf[buf_y, buf_x, 2])
                dst_a = int(buf[buf_y, buf_x, 3])

                # Premultiplied alpha blending: out = src + dst * (1 - src_a)
                inv_alpha = 255 - src_a

                out_r = src_r + (dst_r * inv_alpha) // 255
                out_g = src_g + (dst_g * inv_alpha) // 255
                out_b = src_b + (dst_b * inv_alpha) // 255
                out_a = src_a + (dst_a * inv_alpha) // 255

                # Clamp and write
                if out_r < 0:
                    out_r = 0
                elif out_r > 255:
                    out_r = 255
                if out_g < 0:
                    out_g = 0
                elif out_g > 255:
                    out_g = 255
                if out_b < 0:
                    out_b = 0
                elif out_b > 255:
                    out_b = 255
                if out_a < 0:
                    out_a = 0
                elif out_a > 255:
                    out_a = 255

                buf[buf_y, buf_x, 0] = out_r
                buf[buf_y, buf_x, 1] = out_g
                buf[buf_y, buf_x, 2] = out_b
                buf[buf_y, buf_x, 3] = out_a
else:
    def _blit_sprite_into_buf(buf, sprite, x, y):
        """
        Draws sprite (BGRA, premultiplied alpha) into buf with correct alpha compositing.
        Compatible with the original logic, with careful shape handling.
        """
        sh, sw = sprite.shape[:2]
        bh, bw = buf.shape[:2]

        # Coordinate clipping
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(bw, x + sw), min(bh, y + sh)
        if x1 >= x2 or y1 >= y2:
            return

        sx1, sy1 = x1 - x, y1 - y
        sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)

        dst = buf[y1:y2, x1:x2]
        src = sprite[sy1:sy2, sx1:sx2].astype(np.uint16)  # src: (h, w, 4)
        dst_u = dst.astype(np.uint16)  # dst copy in uint16 for safe operations

        # Split channels
        src_rgb = src[..., :3]  # (h,w,3)
        src_a = src[..., 3]  # (h,w) (not (h,w,1))
        inv = 255 - src_a  # (h,w)

        # Compositing: out_rgb = src_rgb + dst_rgb * inv / 255
        # Expand inv to (h,w,1) for multiplication
        out_rgb = src_rgb + ((dst_u[..., :3] * inv[..., None] + 127) // 255)
        out_a = src_a + ((dst_u[..., 3] * inv + 127) // 255)  # (h,w)

        dst[..., :3] = out_rgb.astype(np.uint8)
        dst[..., 3] = out_a.astype(np.uint8)


class Overlay:
    """
    High-performance transparent overlay for Windows.

    Args:
        x (int, optional): X position of overlay. Defaults to 0 (full screen).
        y (int, optional): Y position of overlay. Defaults to 0 (full screen).
        width (int, optional): Overlay width. Defaults to screen width.
        height (int, optional): Overlay height. Defaults to screen height.
    """

    # ---------------- Initialization and window management ----------------
    def __init__(self, x: Optional[int] = None, y: Optional[int] = None, width: Optional[int] = None,
                 height: Optional[int] = None):
        """Initialize overlay: screen sizes, buffers, events and locks."""
        self.hInstance = GetModuleHandle()
        self.className = 'TransparentGraphicsWindow'
        self.hWindow = None

        self.stop_event = Event()
        self.lock = Lock()

        screen_width = GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = GetSystemMetrics(win32con.SM_CYSCREEN)
        self.x = x if x is not None else 0
        self.y = y if y is not None else 0
        self.width = width if width is not None else screen_width
        self.height = height if height is not None else screen_height
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Overlay area must have positive dimensions")

        self.hdc_mem = None
        self.bitmap_front = None
        self.bitmap_back = None
        self.old_bmp = None
        self.ppvBits_front = None
        self.ppvBits_back = None
        self.front_buf = None
        self.back_buf = None
        self.buf_lock = Lock()
        self.clear_back_buffer = False
        self.clear_front_buffer = False

        # Sprite cache: key -> np.ndarray (BGRA premultiplied)
        # Track last-used timestamps separately
        self.sprite_cache: Dict[Any, Any] = {}
        self.sprite_last_used: DefaultDict[Any, float] = defaultdict(float)
        self.sprite_lock = Lock()  # Dedicated lock for thread-safe cache access
        self.front_instances = []  # list of (sprite_key, x, y)
        self.back_instances = []  # list of (sprite_key, x, y)
        self.instances_lock = Lock()

        self.render_event = Event()  # Event to synchronize rendering
        self.thread = None

        self.render_frame_count = 0
        self.render_fps = 0
        self.render_fps_update_time = 0
        self.render_fps_lock = Lock()

        self.object_count = 0
        self.object_count_lock = Lock()

        # --- Cache cleanup settings (can be changed after creation) ---
        # Time (sec) to keep unused sprites before auto-removal
        self.sprite_ttl_seconds: float = 5.0
        # Period (sec) to check cache in render loop
        self.ttl_cleanup_period_seconds: float = 3.0
        # Enable/disable auto TTL cleanup in render loop
        self.enable_auto_ttl_cleanup: bool = True

        # Warn-once registry and throttling timers
        self._warned_once = set()
        self._warn_lock = Lock()
        self._last_signal_warn_time: float = 0.0

        self._register_window_class()

    def _register_window_class(self) -> None:
        """Register window class for the transparent overlay."""
        wndClass = win32gui.WNDCLASS()
        wndClass.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wndClass.lpfnWndProc = self._wnd_proc
        wndClass.hInstance = self.hInstance
        wndClass.hCursor = win32gui.LoadCursor(None, win32con.IDC_ARROW)
        wndClass.hbrBackground = win32gui.GetStockObject(win32con.BLACK_BRUSH)
        wndClass.lpszClassName = self.className
        try:
            win32gui.RegisterClass(wndClass)
        except win32gui.error:
            pass

    def _wnd_proc(self, hWnd: int, msg: int, wParam: int, lParam: int) -> int:
        """Window message procedure."""
        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hWnd, msg, wParam, lParam)

    def _init_buffers(self) -> None:
        """Initialize buffers for rendering."""
        if self.front_buf is not None:
            return  # Already initialized

        if not self.hdc_mem:
            raise RuntimeError("Memory DC is not initialized. Call after CreateCompatibleDC.")

        # Creation of BITMAPINFO and CreateDIBSection (extracted from _render_loop)
        screen_w, screen_h = self.width, self.height

        class BITMAPINFOHEADER(Structure):
            _fields_ = [
                ("biSize", c_uint), ("biWidth", c_int), ("biHeight", c_int),
                ("biPlanes", c_ushort), ("biBitCount", c_ushort),
                ("biCompression", c_uint), ("biSizeImage", c_uint),
                ("biXPelsPerMeter", c_int), ("biYPelsPerMeter", c_int),
                ("biClrUsed", c_uint), ("biClrImportant", c_uint)
            ]

        class BITMAPINFO(Structure):
            _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", c_uint * 3)]

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = screen_w
        bmi.bmiHeader.biHeight = -screen_h
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = win32con.BI_RGB

        # Create buffers...
        self.ppvBits_front = c_void_p()
        self.bitmap_front = windll.gdi32.CreateDIBSection(
            self.hdc_mem, byref(bmi), win32con.DIB_RGB_COLORS, byref(self.ppvBits_front), None, 0
        )
        if not self.bitmap_front or not self.ppvBits_front.value:
            raise RuntimeError("Failed to create front DIB section")

        self.front_buf = np.ctypeslib.as_array(
            (c_ubyte * (screen_w * screen_h * 4)).from_address(self.ppvBits_front.value))
        self.front_buf = self.front_buf.reshape((screen_h, screen_w, 4))

        self.ppvBits_back = c_void_p()
        self.bitmap_back = windll.gdi32.CreateDIBSection(
            self.hdc_mem, byref(bmi), win32con.DIB_RGB_COLORS, byref(self.ppvBits_back), None, 0
        )
        if not self.bitmap_back or not self.ppvBits_back.value:
            raise RuntimeError("Failed to create back DIB section")

        self.back_buf = np.ctypeslib.as_array(
            (c_ubyte * (screen_w * screen_h * 4)).from_address(self.ppvBits_back.value))
        self.back_buf = self.back_buf.reshape((screen_h, screen_w, 4))

    def _render_loop(self) -> None:
        """Main render loop with double buffering."""
        screen_x: int = self.x
        screen_y: int = self.y
        screen_w: int = self.width
        screen_h: int = self.height

        self.hWindow: int = win32gui.CreateWindowEx(
            win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT |
            win32con.WS_EX_TOPMOST | win32con.WS_EX_NOACTIVATE,
            self.className,
            "",
            win32con.WS_POPUP,
            screen_x, screen_y, screen_w, screen_h,
            None, None, self.hInstance, None
        )
        win32gui.ShowWindow(self.hWindow, win32con.SW_SHOW)

        hdc_screen = win32gui.GetDC(0)
        self.hdc_mem = win32gui.CreateCompatibleDC(hdc_screen)
        if not self.hdc_mem:
            raise RuntimeError("Failed to create memory DC")

        self._init_buffers()

        self.old_bmp = win32gui.SelectObject(self.hdc_mem, self.bitmap_front)

        try:
            last_cleanup = time.time()
            while not self.stop_event.is_set():
                if not self.render_event.wait():
                    continue
                self.render_event.clear()

                with self.buf_lock:
                    if self.clear_back_buffer:
                        self.back_buf[:, :, :] = 0
                        self.clear_back_buffer = False
                    if self.clear_front_buffer:
                        self.front_buf[:, :, :] = 0
                        self.clear_front_buffer = False

                # Render FPS tracking
                current_time = time.time()
                with self.render_fps_lock:
                    self.render_frame_count += 1
                    if current_time - self.render_fps_update_time >= 1.0:
                        self.render_fps = self.render_frame_count
                        self.render_frame_count = 0
                        self.render_fps_update_time = current_time

                # TTL cleanup (optional) — remove unused sprites on schedule
                if self.enable_auto_ttl_cleanup:
                    now = current_time
                    if now - last_cleanup >= self.ttl_cleanup_period_seconds:
                        removed = self.sprite_clear_expired(max_age=self.sprite_ttl_seconds)
                        if removed > 0:
                            logger.info("Sprite TTL cleanup removed %d entries", removed)
                        last_cleanup = now

                with self.instances_lock:
                    local_instances = list(self.front_instances)

                total_objects = 0

                for sprite_key, x, y in local_instances:
                    sprite = self._cache_get(sprite_key, update_ts=True)
                    if sprite is None:
                        self._warn_once(("missing_sprite", sprite_key),
                                        "Sprite key=%r not found in cache during render; skipping", sprite_key)
                        continue
                    total_objects += 1

                    # Skip and warn if sprite is fully outside the screen (no intersection)
                    sh, sw = sprite.shape[:2]
                    if x >= screen_w or y >= screen_h or (x + sw) <= 0 or (y + sh) <= 0:
                        self._warn_once(("sprite_offscreen", sprite_key),
                                        "Sprite key=%r fully outside the screen; skipping", sprite_key)
                        continue

                    _blit_sprite_into_buf(self.back_buf, sprite, x, y)

                with self.object_count_lock:
                    self.object_count = total_objects

                # Swap buffers
                with self.buf_lock:
                    self.front_buf, self.back_buf = self.back_buf, self.front_buf
                    self.ppvBits_front, self.ppvBits_back = self.ppvBits_back, self.ppvBits_front
                    self.bitmap_front, self.bitmap_back = self.bitmap_back, self.bitmap_front
                    win32gui.SelectObject(self.hdc_mem, self.bitmap_front)

                pt_src, pt_dst, size = POINT(0, 0), POINT(screen_x, screen_y), SIZE(screen_w, screen_h)
                blend = BLENDFUNCTION(0x00, 0, 255, 0x01)
                windll.user32.UpdateLayeredWindow(
                    self.hWindow, hdc_screen, byref(pt_dst), byref(size),
                    self.hdc_mem, byref(pt_src), 0, byref(blend), 0x02
                )
                windll.gdi32.GdiFlush()

        finally:
            try:
                win32gui.SelectObject(self.hdc_mem, self.old_bmp)
                win32gui.DeleteDC(self.hdc_mem)
                windll.gdi32.DeleteObject(self.bitmap_front)
                windll.gdi32.DeleteObject(self.bitmap_back)
                win32gui.ReleaseDC(0, hdc_screen)
                win32gui.DestroyWindow(self.hWindow)
                logger.info("Overlay window destroyed and resources released")
            except Exception:
                pass

    def start_layer(self) -> None:
        """Start the render thread."""
        if self.thread and self.thread.is_alive():
            logger.info("start_layer() ignored; render thread already running")
            return
        self.stop_event.clear()
        self.thread = Thread(target=self._render_loop, daemon=True)
        self.thread.start()
        logger.info("start_layer(): render thread started")

    def stop_layer(self) -> None:
        """Stop the overlay and render thread."""
        self.stop_event.set()
        self.signal_render()
        if self.hWindow:
            try:
                win32gui.PostMessage(self.hWindow, win32con.WM_DESTROY, 0, 0)
            except Exception:
                pass
        if self.thread:
            self.thread.join(timeout=3)
            if self.thread.is_alive():
                logger.warning("Render thread did not terminate cleanly")
            else:
                logger.info("stop_layer(): render thread stopped")

    # ----- Safe shutdown and context manager -----
    def close(self) -> None:
        """Gracefully release resources. Safe during interpreter shutdown."""
        try:
            self.stop_layer()
        except Exception:
            # During interpreter finalization, win32gui/windll/Event may already be destroyed
            pass

    def __enter__(self) -> "Overlay":
        self.start_layer()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        """Close the overlay. Return False to not suppress exceptions."""
        self.close()
        return False

    def __del__(self):  # as safe as possible destructor
        try:
            self.close()
        except Exception:
            pass

    # ---------------- Render and buffer management ----------------
    def _swap_instances(self) -> None:
        """Swap front and back instance lists for render synchronization."""
        with self.instances_lock:
            self.front_instances, self.back_instances = self.back_instances, self.front_instances

    def _warn_once(self, tag: Any, message: str, *args) -> None:
        """Log a warning only once per unique tag."""
        with self._warn_lock:
            if tag in self._warned_once:
                return
            self._warned_once.add(tag)
        logger.warning(message, *args)

    def frame_clear(self) -> None:
        """
        Full clear for a new frame
        - Clears render queue
        - Clears next frame buffer
        """
        self.frame_clear_queue()
        self.frame_clear_buffers('both')

    def frame_clear_queue(self) -> None:
        """
        Clear queued render objects.
        Removes all sprites scheduled for the next frame.
        """
        with self.instances_lock:
            self.back_instances.clear()

    def frame_clear_buffers(self, which: Literal['back', 'front', 'both'] = 'both') -> None:
        """Set clear flags to be processed in _render_loop().

        Args:
            which: What to clear:
                - 'back' — only the back buffer of the next frame
                - 'front' — only the current front buffer
                - 'both' — both buffers (default)
        """
        if which in ['back', 'both']:
            self.clear_back_buffer = True
        if which in ['front', 'both']:
            self.clear_front_buffer = True

    def add_sprite_instance(self, sprite_key: Any, x: int, y: int) -> None:
        """Add a sprite instance to the back buffer (in insertion order)."""
        with self.instances_lock:
            self.back_instances.append((sprite_key, int(x), int(y)))

    def signal_render(self) -> None:
        """Swap instance lists and signal the render loop."""
        # Perform swap and signal atomically relative to adding new instances
        with self.instances_lock:
            self.front_instances, self.back_instances = self.back_instances, self.front_instances
            self.render_event.set()
        # If render thread is not running, provide throttled debug info
        t = time.time()
        if not (self.thread and self.thread.is_alive()):
            if t - self._last_signal_warn_time > 5.0:
                logger.debug("signal_render() called while render thread is not running")
                self._last_signal_warn_time = t

    # ---------------- Sprite creation ----------------
    @staticmethod
    def _premultiply_arr(arr) -> Any:
        """
        Take array from PIL (usually RGBA) and return BGRA with premultiplied alpha.
        The returned array has dtype=uint8 and channel order BGRA.
        """
        if arr.size == 0:
            return arr

        if arr.shape[2] != 4:
            raise ValueError("_premultiply_arr expects an array with 4 channels (RGBA)")

        # Copy to avoid mutating the input array unexpectedly
        a = arr.copy().astype(np.uint8)

        # Reorder channels: RGBA -> BGRA (Win/GDI expects B,G,R,A)
        a = a[:, :, [2, 1, 0, 3]]

        # Premultiplication: RGB = round(RGB * A/255)
        alpha = a[..., 3:4].astype(np.float32) / 255.0
        rgb = a[..., :3].astype(np.float32) * alpha
        a[..., :3] = np.round(rgb).astype(np.uint8)

        return a

    # ---------------- Normalization utilities ----------------
    @staticmethod
    def _normalize_color(color: Any) -> Tuple[int, int, int, int]:
        """
        Normalize color to an RGBA tuple of 4 ints in 0..255.
        Accepts:
        - sequence of length 3 (RGB) or 4 (RGBA)
        - values outside range are clamped to 0..255
        """
        if color is None:
            return (0, 0, 0, 0)
        try:
            seq = list(color)
        except Exception:
            raise ValueError(f"Color must be a sequence, got: {type(color)}")

        if len(seq) == 3:
            seq.append(255)
        elif len(seq) != 4:
            raise ValueError(f"Color must have 3 or 4 components, got: {len(seq)}")

        # clamp and cast to int
        orig = tuple(int(v) for v in seq)
        r, g, b, a = (max(0, min(255, int(v))) for v in orig)
        clamped = (r, g, b, a)
        if clamped != orig:
            logger.debug("Color components clamped to 0..255: input=%r, normalized=%r", orig, clamped)
        return (r, g, b, a)

    def create_circle_sprite(
            self,
            radius: int,
            color: Tuple[int, int, int, int] = (255, 255, 255, 255),
            thickness: int = 0
    ) -> Any:
        """Create or return a cached circle sprite.

        Args:
            radius: Circle radius in pixels (must be >= 1)
            color: RGBA color tuple (default: white)
            thickness: Line thickness in pixels (0 = filled)

        Returns:
            A sprite key that can be used with add_sprite_instance()
        """
        if int(radius) < 1:
            raise ValueError("radius must be >= 1")
        if int(thickness) < 0:
            raise ValueError("thickness must be >= 0")
        color = self._normalize_color(color)
        key = ('circle', radius, color, thickness)
        with self.sprite_lock:
            if key in self.sprite_cache:
                self.sprite_last_used[key] = time.time()
                return key

        size = radius * 2 + 1
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        bbox = (0, 0, size - 1, size - 1)
        if thickness == 0:
            draw.ellipse(bbox, fill=color)
        else:
            draw.ellipse(bbox, outline=color, width=thickness)

        arr = np.array(img, dtype=np.uint8)
        arr = self._premultiply_arr(arr)
        self._cache_set(key, arr)
        return key

    def create_rect_sprite(
            self,
            width: int,
            height: int,
            color: Tuple[int, int, int, int] = (255, 255, 255, 255),
            thickness: int = 0
    ) -> Any:
        """Create or return a cached rectangle sprite.

        Args:
            width: Rectangle width in pixels (must be >= 1)
            height: Rectangle height in pixels (must be >= 1)
            color: RGBA color tuple (default: white)
            thickness: Line thickness in pixels (0 = filled)

        Returns:
            A sprite key that can be used with add_sprite_instance()
        """
        if int(width) < 1 or int(height) < 1:
            raise ValueError("width and height must be >= 1")
        if int(thickness) < 0:
            raise ValueError("thickness must be >= 0")
        color = self._normalize_color(color)
        key = ('rect', width, height, color, thickness)
        with self.sprite_lock:
            if key in self.sprite_cache:
                self.sprite_last_used[key] = time.time()
                return key

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        if thickness == 0:
            draw.rectangle((0, 0, width - 1, height - 1), fill=color)
        else:
            draw.rectangle((0, 0, width - 1, height - 1), outline=color, width=thickness)

        arr = np.array(img, dtype=np.uint8)
        arr = self._premultiply_arr(arr)
        self._cache_set(key, arr)
        return key

    def create_line_sprite(
            self,
            x1: int,
            y1: int,
            x2: int,
            y2: int,
            color: Tuple[int, int, int, int] = (255, 255, 255, 255),
            thickness: int = 1
    ) -> Any:
        """Create or return a cached line sprite.

        Args:
            x1, y1: Start point coordinates
            x2, y2: End point coordinates
            color: RGBA color tuple (default: white)
            thickness: Line thickness in pixels (must be >= 1)

        Returns:
            A sprite key that can be used with add_sprite_instance()
        """
        if int(thickness) < 1:
            raise ValueError("thickness must be >= 1 for line sprites")
        color = self._normalize_color(color)

        # Warn once for zero-length line (no span in both directions)
        if x1 == x2 and y1 == y2:
            self._warn_once(("zero_length_line", x1, y1, x2, y2, thickness),
                            "Zero-length line at (%d,%d)->(%d,%d); renders as a point with thickness=%d",
                            x1, y1, x2, y2, thickness)

        # Expand bounding box considering line thickness
        half_thickness = thickness // 2
        left = min(x1, x2) - half_thickness
        top = min(y1, y2) - half_thickness
        w = max(1, abs(x2 - x1) + thickness + 1)
        h = max(1, abs(y2 - y1) + thickness + 1)

        sx = x1 - left
        sy = y1 - top
        ex = x2 - left
        ey = y2 - top

        key = ('line', w, h, color, thickness, sx, sy, ex, ey)
        with self.sprite_lock:
            if key in self.sprite_cache:
                self.sprite_last_used[key] = time.time()
                return key

        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line((sx, sy, ex, ey), fill=color, width=thickness)

        arr = np.array(img, dtype=np.uint8)
        arr = self._premultiply_arr(arr)
        self._cache_set(key, arr)
        return key

    def create_text_sprite(
            self,
            text: str,
            font_size: float = 16.0,
            color: Tuple[int, int, int, int] = (255, 255, 255, 255),
            angle: int = 0,
            highlight: bool = False,
            bg_color: Tuple[int, int, int, int] = (0, 0, 0, 180),
            box_size: Optional[Tuple[int, int]] = None,
            fit_text: bool = False,
            align: Literal['left', 'center', 'right'] = 'center',
            valign: Literal['top', 'middle', 'bottom'] = 'middle',
            font_path: Optional[str] = None,
    ) -> Any:
        """
        Create (and cache) a text sprite. Returns the cache key.

        Args:
            text: Text string
            font_size: Font size (pt)
            color: Text color in RGBA (0..255)
            angle: Rotation angle in degrees
            highlight: Draw background under text
            bg_color: Background color RGBA
            box_size: Bounding box (width, height) if provided
            fit_text: Fit font size to fit inside box_size
            align: Horizontal alignment: left/center/right
            valign: Vertical alignment: top/middle/bottom
            font_path: Path to ttf font (if None — use Arial/fallback)
        """
        if float(font_size) < 1:
            raise ValueError("font_size must be >= 1")
        if box_size is not None:
            bw, bh = int(box_size[0]), int(box_size[1])
            if bw < 1 or bh < 1:
                # Graceful fallback with warning: ignore invalid box_size to avoid crashes
                self._warn_once(("invalid_box_size", box_size),
                                "Ignoring invalid box_size=%s; falling back to auto-sized text", box_size)
                box_size = None
        color = self._normalize_color(color)
        bg_color = self._normalize_color(bg_color)
        key = ("text", text, font_size, color, angle, highlight, bg_color, box_size, fit_text, align, valign, font_path)
        with self.sprite_lock:
            if key in self.sprite_cache:
                self.sprite_last_used[key] = time.time()
                return key

        try:
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        # --- compute font/size and create image ---
        tmp = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        dtmp = ImageDraw.Draw(tmp)
        bbox = dtmp.textbbox((0, 0), text, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

        if box_size is not None:
            box_w, box_h = box_size

            # If fit_text may change font
            final_font = font
            if fit_text and text_w > 0 and text_h > 0 and box_w > 0 and box_h > 0:
                scale = min(box_w / text_w, box_h / text_h)
                new_font_size = max(1, int(font_size * scale))
                try:
                    if font_path:
                        final_font = ImageFont.truetype(font_path, new_font_size)
                    else:
                        final_font = ImageFont.truetype("arial.ttf", new_font_size)
                except Exception:
                    final_font = ImageFont.load_default()
                bbox = dtmp.textbbox((0, 0), text, font=final_font)
                text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

            img_w, img_h = int(box_w), int(box_h)
            img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)

            if highlight:
                d.rectangle([(0, 0), (img_w, img_h)], fill=bg_color)

            # position
            if align == "left":
                tx = 0
            elif align == "center":
                tx = (box_w - text_w) / 2
            elif align == "right":
                tx = box_w - text_w
            else:
                tx = 0

            if valign == "top":
                ty = 0
            elif valign == "middle":
                ty = (box_h - text_h) / 2
            elif valign == "bottom":
                ty = box_h - text_h
            else:
                ty = 0

            d.text((int(tx - bbox[0]), int(ty - bbox[1])), text, font=final_font, fill=color)
        else:
            img_w, img_h = int(text_w), int(text_h)
            img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            if highlight:
                d.rectangle([(0, 0), (img_w, img_h)], fill=bg_color)
            d.text((int(-bbox[0]), int(-bbox[1])), text, font=font, fill=color)

        # Rotation if needed (Pillow 10+ compatible)
        if angle != 0:
            resample_base = getattr(Image, "Resampling", Image)
            img = img.rotate(angle, expand=True, resample=resample_base.BICUBIC)

        arr = np.array(img, dtype=np.uint8)
        arr = self._premultiply_arr(arr)
        self._cache_set(key, arr)
        return key

    def create_sprite_from_numpy(self, array, sprite_key) -> Optional[Any]:
        """
        Create a sprite directly from a numpy array.
        Useful for custom graphics, screenshots, generative images.

        Args:
            array: numpy array in RGBA format (height, width, 4)
            sprite_key: Unique key for the sprite

        Returns:
            sprite_key or None on error

        Example:
            # Create a gradient
            gradient = np.zeros((100, 100, 4), dtype=np.uint8)
            gradient[:, :, 0] = 255  # Blue channel
            gradient[:, :, 3] = 128  # Semi-transparency
            key = overlay.create_sprite_from_numpy(gradient, ('gradient', 'blue_fade'))
        """
        try:
            if not hasattr(array, 'ndim') or not hasattr(array, 'shape'):
                logger.error("Error creating sprite from array: input is not a numpy-like array")
                return None
            if array.ndim != 3 or array.shape[2] != 4:
                logger.error(
                    "Error creating sprite from array: expected (H,W,4) RGBA, got shape=%s",
                    getattr(array, 'shape', None),
                )
                return None

            processed_array = self._premultiply_arr(array.copy())
            self._cache_set(sprite_key, processed_array)
            return sprite_key

        except Exception as e:
            # Unexpected error: concise log without full traceback to avoid noise
            logger.error("Unexpected error creating sprite from array: %s", e)
            return None

    # ---------------- Sprite Cache Management ----------------

    def sprite_clear_cache(self) -> None:
        """
        Full sprite cache cleanup.
        Removes all created sprites to free memory.

        Example:
            overlay.clear_cache()  # Fully clears cache
        """
        with self.sprite_lock:
            self.sprite_cache.clear()
            self.sprite_last_used.clear()

    def sprite_clear_expired(self, max_age: float = 5.0) -> int:
        """Remove sprites older than max_age seconds (by last-used time). Returns number removed."""
        now = time.time()
        removed = 0
        with self.sprite_lock:
            for key, ts in list(self.sprite_last_used.items()):
                if now - ts > max_age:
                    self.sprite_last_used.pop(key, None)
                    self.sprite_cache.pop(key, None)
                    removed += 1
        return removed

    def sprite_remove(self, sprite_key: Any) -> bool:
        """
        Remove a specific sprite from the cache.

        Args:
            sprite_key: The sprite key to remove

        Returns:
            bool: True if the sprite was removed, False if not found

        Example:
            success = overlay.remove_sprite(circle_key)
            if success:
                print("Sprite removed")
        """
        with self.sprite_lock:
            if sprite_key in self.sprite_cache:
                del self.sprite_cache[sprite_key]
                self.sprite_last_used.pop(sprite_key, None)
                return True
            logger.debug("sprite_remove: key=%r not found", sprite_key)
            return False

    # ---------------- High-Level Drawing ----------------
    def draw_circle(
        self,
        x: int,
        y: int,
        radius: int,
        color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        thickness: int = 0
    ) -> None:
        """Draw a circle on the overlay.

        Args:
            x: Center X coordinate
            y: Center Y coordinate
            radius: Circle radius in pixels (must be >= 1)
            color: RGBA color tuple (default: white, fully opaque)
            thickness: Line thickness in pixels (0 = filled)

        Raises:
            ValueError: If coordinates are invalid, radius < 1, or thickness is negative
        """
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("x and y coordinates must be integers")
        if not isinstance(radius, int) or radius < 1:
            raise ValueError("radius must be a positive integer")
        if not isinstance(thickness, int) or thickness < 0:
            raise ValueError("thickness must be a non-negative integer")

        color = self._normalize_color(color)
        key = self.create_circle_sprite(radius, color, thickness)
        self.add_sprite_instance(key, x - radius, y - radius)

    def draw_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        thickness: int = 0
    ) -> None:
        """Draw a rectangle on the overlay.

        Args:
            x: Left X coordinate
            y: Top Y coordinate
            width: Rectangle width in pixels (must be >= 1)
            height: Rectangle height in pixels (must be >= 1)
            color: RGBA color tuple (default: white, fully opaque)
            thickness: Line thickness in pixels (0 = filled)

        Raises:
            ValueError: If coordinates are invalid, width/height < 1, or thickness is negative
        """
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("x and y coordinates must be integers")
        if not isinstance(width, int) or width < 1 or not isinstance(height, int) or height < 1:
            raise ValueError("width and height must be positive integers")
        if not isinstance(thickness, int) or thickness < 0:
            raise ValueError("thickness must be a non-negative integer")

        color = self._normalize_color(color)
        key = self.create_rect_sprite(width, height, color, thickness)
        self.add_sprite_instance(key, x, y)

    def draw_line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        thickness: int = 1
    ) -> None:
        """Draw a line on the overlay.

        Args:
            x1: Start X coordinate
            y1: Start Y coordinate
            x2: End X coordinate
            y2: End Y coordinate
            color: RGBA color tuple (default: white, fully opaque)
            thickness: Line thickness in pixels (must be >= 1)

        Raises:
            ValueError: If coordinates are invalid or thickness < 1
        """
        if not all(isinstance(coord, int) for coord in (x1, y1, x2, y2)):
            raise ValueError("All coordinates must be integers")
        if not isinstance(thickness, int) or thickness < 1:
            raise ValueError("thickness must be a positive integer")

        color = self._normalize_color(color)
        key = self.create_line_sprite(x1, y1, x2, y2, color, thickness)
        half_thickness = thickness // 2
        left = min(x1, x2) - half_thickness
        top = min(y1, y2) - half_thickness
        self.add_sprite_instance(key, left, top)

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        font_size: float = 16.0,
        anchor: Literal['lt', 'mt', 'rt', 'lm', 'mm', 'rm', 'lb', 'mb', 'rb'] = 'lt',
        angle: int = 0,
        highlight: bool = False,
        bg_color: Tuple[int, int, int, int] = (0, 0, 0, 180),
        box_size: Optional[Tuple[int, int]] = None,
        fit_text: bool = False,
        align: Literal['left', 'center', 'right'] = 'center',
        valign: Literal['top', 'middle', 'bottom'] = 'middle',
        font_path: Optional[str] = None,
    ) -> None:
        """Draw text with positioning and optional bounding box.

        Args:
            x: Base X coordinate (see anchor parameter)
            y: Base Y coordinate (see anchor parameter)
            text: Text string to draw
            color: Text color as RGBA tuple (default: white, fully opaque)
            font_size: Font size in points (must be > 0)
            anchor: Text anchor point relative to (x,y):
                - 'lt': left-top, 'mt': middle-top, 'rt': right-top
                - 'lm': left-middle, 'mm': middle-middle, 'rm': right-middle
                - 'lb': left-bottom, 'mb': middle-bottom, 'rb': right-bottom
            angle: Text rotation angle in degrees (0-360)
            highlight: If True, draw background behind text
            bg_color: Background color as RGBA tuple when highlight is True
            box_size: Optional (width, height) tuple to constrain text within a box
            fit_text: If True, automatically adjust font size to fit within box_size
            align: Horizontal text alignment when box_size is specified:
                'left', 'center', or 'right'
            valign: Vertical text alignment when box_size is specified:
                'top', 'middle', or 'bottom'
            font_path: Optional path to .ttf font file

        Raises:
            ValueError: If font_size is not positive or invalid parameters are provided
        """
        if not isinstance(text, str):
            text = str(text)
        if not isinstance(font_size, (int, float)) or font_size <= 0:
            raise ValueError("font_size must be a positive number")
        if box_size is not None and (not isinstance(box_size, tuple) or len(box_size) != 2 or
                                   not all(isinstance(v, int) and v > 0 for v in box_size)):
            raise ValueError("box_size must be a tuple of two positive integers")

        color = self._normalize_color(color)
        if highlight:
            bg_color = self._normalize_color(bg_color)

        key = self.create_text_sprite(
            text, font_size, color, angle, highlight, bg_color, box_size, fit_text, align, valign, font_path
        )
        sprite = self._cache_get(key, update_ts=True)
        if sprite is None:
            # In case of a rare sprite creation failure — silently skip drawing
            return
        h, w = sprite.shape[:2]

        # bx, by - base position (if box is set, x,y are bx,by; otherwise same)
        bx, by = x, y

        # --- Offset depending on anchor ---
        anchor_map = {
            "lt": (0, 0),
            "mt": (-w / 2, 0),
            "rt": (-w, 0),
            "lm": (0, -h / 2),
            "mm": (-w / 2, -h / 2),
            "rm": (-w, -h / 2),
            "lb": (0, -h),
            "mb": (-w / 2, -h),
            "rb": (-w, -h),
        }
        if anchor not in anchor_map:
            self._warn_once(("invalid_anchor", anchor), "Invalid anchor=%r; using default 'lt'", anchor)
        dx, dy = anchor_map.get(anchor, (0, 0))
        final_x = int(bx + dx)
        final_y = int(by + dy)

        self.add_sprite_instance(key, final_x, final_y)

    # ---------------- Diagnostics and statistics ----------------

    def get_render_fps(self) -> int:
        """Return current render FPS."""
        with self.render_fps_lock:
            return self.render_fps

    def get_object_count(self) -> int:
        with self.object_count_lock:
            return self.object_count

    def get_render_statistics(self) -> Tuple[str, List[Tuple[Any, Tuple[int, int, int, int]]]]:
        """
        Return (stats_text, detailed_items)
        detailed_items: [(sprite_key, (x1,y1,x2,y2)), ...]
        """
        with self.instances_lock:
            detailed_items = []
            stats_summary = {}
            total_instances = 0

            with self.sprite_lock:
                cache_copy = self.sprite_cache.copy()

            for item in self.front_instances:
                sprite_key, x, y = item
                sprite_arr = cache_copy.get(sprite_key)
                if sprite_arr is not None:
                    h, w = sprite_arr.shape[:2]
                    x1, y1 = x, y
                    x2, y2 = x + w, y + h
                else:
                    # fallback — if sprite is missing
                    x1, y1 = x, y
                    x2, y2 = x + 1, y + 1  # minimal valid bbox

                detailed_items.append((sprite_key, (x1, y1, x2, y2)))

                obj_type = sprite_key[0] if isinstance(sprite_key, tuple) else 'unknown'
                stats_summary.setdefault(obj_type, {'instances': 0})
                stats_summary[obj_type]['instances'] += 1
                total_instances += 1

            stats_text = f"Total instances: {total_instances}\n"
            for obj_type, data in stats_summary.items():
                stats_text += f"{obj_type}: {data['instances']} instances\n"

            return stats_text, detailed_items

    def get_sprite_cache_info(self, sprite_key: Any) -> Optional[Dict[str, Any]]:
        """
        Return information about a specific sprite.

        Args:
            sprite_key: Sprite key

        Returns:
            dict or None if the sprite is not found

        Example:
            info = overlay.get_sprite_info(text_key)
            if info:
                print(f"Size: {info['width']}x{info['height']}")
        """
        sprite = self._cache_get(sprite_key, update_ts=False)
        if sprite is None:
            return None
        return {
            'key': sprite_key,
            'width': sprite.shape[1],
            'height': sprite.shape[0],
            'memory_bytes': sprite.nbytes,
            'type': sprite_key[0] if isinstance(sprite_key, tuple) else 'unknown'
        }

    # ---------------- Internal cache utilities ----------------
    def _cache_get(self, key: Any, update_ts: bool = True):
        with self.sprite_lock:
            arr = self.sprite_cache.get(key)
            if arr is None:
                return None
            if update_ts:
                self.sprite_last_used[key] = time.time()
            return arr

    def _cache_set(self, key: Any, arr) -> None:
        with self.sprite_lock:
            self.sprite_cache[key] = arr
            self.sprite_last_used[key] = time.time()
