import enum

import ExtendMode
import numpy
from numpy.typing import NDArray


def version() -> str: ...

class CompOp(enum.Enum):
    SRC_COPY = 1

    SRC_OVER = 0

SRC_COPY: CompOp = CompOp.SRC_COPY

SRC_OVER: CompOp = CompOp.SRC_OVER

class ExtendMode(enum.Enum):
    PAD = 0

    REPEAT = 1

    REFLECT = 2

PAD: ExtendMode = ExtendMode.PAD

REPEAT: ExtendMode = ExtendMode.REPEAT

REFLECT: ExtendMode = ExtendMode.REFLECT

class GradientType(enum.Enum):
    LINEAR = 0

    RADIAL = 1

    CONIC = 2

LINEAR: GradientType = GradientType.LINEAR

RADIAL: GradientType = GradientType.RADIAL

CONIC: GradientType = GradientType.CONIC

class StrokeCap(enum.Enum):
    BUTT = 0

    SQUARE = 1

    ROUND = 2

    ROUND_REV = 3

    TRIANGLE = 4

    TRIANGLE_REV = 5

BUTT: StrokeCap = StrokeCap.BUTT

SQUARE: StrokeCap = StrokeCap.SQUARE

ROUND: StrokeJoin = StrokeJoin.ROUND

ROUND_REV: StrokeCap = StrokeCap.ROUND_REV

TRIANGLE: StrokeCap = StrokeCap.TRIANGLE

TRIANGLE_REV: StrokeCap = StrokeCap.TRIANGLE_REV

class StrokeJoin(enum.Enum):
    MITER_CLIP = 0

    MITER_BEVEL = 1

    MITER_ROUND = 2

    BEVEL = 3

    ROUND = 4

MITER_CLIP: StrokeJoin = StrokeJoin.MITER_CLIP

MITER_BEVEL: StrokeJoin = StrokeJoin.MITER_BEVEL

MITER_ROUND: StrokeJoin = StrokeJoin.MITER_ROUND

BEVEL: StrokeJoin = StrokeJoin.BEVEL

class Image:
    def __init__(self, width: int, height: int) -> None: ...

    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...

    def memoryview(self) -> memoryview:
        """PEP 3118 memoryview (1D, size=stride*height)"""

    def asarray(self) -> NDArray[numpy.uint8]:
        """NumPy ndarray view (H, W, 4) uint8; zero-copy"""

class Path:
    def __init__(self) -> None: ...

    def move_to(self, x: float, y: float) -> None: ...

    def line_to(self, x: float, y: float) -> None: ...

    def quad_to(self, x1: float, y1: float, x2: float, y2: float) -> None: ...

    def cubic_to(self, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> None: ...

    def smooth_quad_to(self, x2: float, y2: float) -> None: ...

    def smooth_cubic_to(self, x2: float, y2: float, x3: float, y3: float) -> None: ...

    def arc_to(self, cx: float, cy: float, rx: float, ry: float, start: float, sweep: float, force_move_to: bool = False) -> None: ...

    def elliptic_arc_to(self, rx: float, ry: float, x_axis_rotation: float, large_arc_flag: bool, sweep_flag: bool, x: float, y: float) -> None: ...

    def close(self) -> None: ...

class FontFace:
    def __init__(self) -> None: ...

    def create_from_file(self, filename: str) -> None: ...

    @property
    def family_name(self) -> str: ...

    @property
    def weight(self) -> int: ...

class Font:
    def __init__(self, face: FontFace, size: float) -> None: ...

    @property
    def size(self) -> float: ...

class Gradient:
    def __init__(self) -> None: ...

    def create_linear(self, x0: float, y0: float, x1: float, y1: float, extend_mode: ExtendMode = ExtendMode.PAD) -> None: ...

    def create_radial(self, x0: float, y0: float, x1: float, y1: float, r0: float, extend_mode: ExtendMode = ExtendMode.PAD, r1: float = 0.0) -> None: ...

    def create_conic(self, x0: float, y0: float, angle: float, extend_mode: ExtendMode = ExtendMode.PAD, repeat: float = 1.0) -> None: ...

    def add_stop(self, offset: float, r: int, g: int, b: int, a: int = 255) -> None: ...

    def reset_stops(self) -> None: ...

    @property
    def stop_count(self) -> int: ...

    @property
    def gradient_type(self) -> GradientType: ...

    @property
    def extend_mode(self) -> ExtendMode: ...

class Pattern:
    def __init__(self) -> None: ...

    def create(self, image: Image, extend_mode: ExtendMode = ExtendMode.REPEAT) -> None: ...

    def set_area(self, x: int, y: int, w: int, h: int) -> None: ...

    def reset_area(self) -> None: ...

    def set_extend_mode(self, extend_mode: ExtendMode) -> None: ...

    @property
    def extend_mode(self) -> ExtendMode: ...

class Context:
    def __init__(self, image: Image, thread_count: int = 0) -> None: ...

    def end(self) -> None: ...

    def save(self) -> None: ...

    def restore(self) -> None: ...

    def set_comp_op(self, op: CompOp) -> None: ...

    def set_fill_style_rgba(self, r: int, g: int, b: int, a: int = 255) -> None: ...

    def set_fill_style_gradient(self, gradient: Gradient) -> None: ...

    def set_fill_style_pattern(self, pattern: Pattern) -> None: ...

    def set_stroke_style_rgba(self, r: int, g: int, b: int, a: int = 255) -> None: ...

    def set_stroke_style_gradient(self, gradient: Gradient) -> None: ...

    def set_stroke_style_pattern(self, pattern: Pattern) -> None: ...

    def set_stroke_width(self, width: float) -> None: ...

    def set_stroke_miter_limit(self, miter_limit: float) -> None: ...

    def set_stroke_join(self, stroke_join: StrokeJoin) -> None: ...

    def set_stroke_caps(self, stroke_cap: StrokeCap) -> None: ...

    def translate(self, x: float, y: float) -> None: ...

    def rotate(self, rad: float) -> None: ...

    def fill_all(self) -> None: ...

    def fill_rect(self, x: float, y: float, w: float, h: float) -> None: ...

    def fill_circle(self, cx: float, cy: float, r: float) -> None: ...

    def fill_pie(self, cx: float, cy: float, r: float, start: float, sweep: float) -> None: ...

    def fill_path(self, path: Path) -> None: ...

    def fill_utf8_text(self, x: float, y: float, font: Font, text: str) -> None: ...

    def stroke_rect(self, x: float, y: float, w: float, h: float) -> None: ...

    def stroke_circle(self, cx: float, cy: float, r: float) -> None: ...

    def stroke_path(self, path: Path) -> None: ...

    def __enter__(self) -> Context: ...

    def __exit__(self, exc_type: object | None, exc_val: object | None, exc_tb: object | None) -> None: ...
