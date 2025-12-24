"""Animation utilities for Cilow CLI"""

from typing import List, Tuple, Callable
from enum import Enum


# Triquetra gradient colors
COLORS = {
    "blue": "#00BFFF",
    "cyan": "#00CED1",
    "green": "#32CD32",
    "yellow": "#FFD700",
    "dim": "#6e7681",
    "bright": "#ffffff",
}


class AnimationType(Enum):
    """Types of animations available."""
    WAVE = "wave"
    PULSE = "pulse"
    FLASH = "flash"
    DOTS = "dots"


# ASCII-safe spinner frames (no Unicode issues)
SPINNER_FRAMES = [
    ".",
    "..",
    "...",
    "   ",
]

# Thinking dots animation
THINKING_DOTS = ["   ", ".  ", ".. ", "..."]

# Wave animation - which letter to highlight (0-4 for cilow)
WAVE_FRAMES = [0, 1, 2, 3, 4, 4, 3, 2, 1, 0]

# Pulse animation - brightness levels (0=dim, 1=normal, 2=bright)
PULSE_FRAMES = [1, 2, 2, 1, 0, 0]

# Flash animation - all on/off
FLASH_FRAMES = [True, True, True, False, False, False]


def get_wave_highlight(frame: int) -> int:
    """Get which letter index should be highlighted for wave animation."""
    return WAVE_FRAMES[frame % len(WAVE_FRAMES)]


def get_pulse_level(frame: int) -> int:
    """Get pulse brightness level (0-2)."""
    return PULSE_FRAMES[frame % len(PULSE_FRAMES)]


def get_flash_state(frame: int) -> bool:
    """Get flash on/off state."""
    return FLASH_FRAMES[frame % len(FLASH_FRAMES)]


def get_thinking_dots(frame: int) -> str:
    """Get thinking dots string for current frame."""
    return THINKING_DOTS[frame % len(THINKING_DOTS)]


def get_spinner_char(frame: int) -> str:
    """Get spinner character for current frame."""
    return SPINNER_FRAMES[frame % len(SPINNER_FRAMES)]


def interpolate_color(color1: str, color2: str, t: float) -> str:
    """
    Interpolate between two hex colors.

    Args:
        color1: Starting color (hex)
        color2: Ending color (hex)
        t: Interpolation factor (0.0 to 1.0)

    Returns:
        Interpolated hex color
    """
    # Parse hex colors
    r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
    r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

    # Interpolate
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)

    return f"#{r:02x}{g:02x}{b:02x}"


def ease_in_out(t: float) -> float:
    """Smooth ease-in-out function."""
    if t < 0.5:
        return 2 * t * t
    return 1 - pow(-2 * t + 2, 2) / 2


def ease_out(t: float) -> float:
    """Smooth ease-out function."""
    return 1 - pow(1 - t, 3)


class AnimationController:
    """
    Controller for managing animation state.

    Usage:
        controller = AnimationController(frame_count=10, fps=10)
        controller.start()
        # On each tick
        frame = controller.tick()
        # Get animation values
        highlight = get_wave_highlight(frame)
    """

    def __init__(self, frame_count: int = 10, fps: int = 10):
        self.frame_count = frame_count
        self.fps = fps
        self.frame = 0
        self.running = False
        self._callbacks: List[Callable[[int], None]] = []

    def start(self) -> None:
        """Start the animation."""
        self.running = True
        self.frame = 0

    def stop(self) -> None:
        """Stop the animation."""
        self.running = False

    def reset(self) -> None:
        """Reset to first frame."""
        self.frame = 0

    def tick(self) -> int:
        """Advance to next frame and return current frame."""
        if self.running:
            self.frame = (self.frame + 1) % self.frame_count
            for callback in self._callbacks:
                callback(self.frame)
        return self.frame

    def on_frame(self, callback: Callable[[int], None]) -> None:
        """Register a callback for frame updates."""
        self._callbacks.append(callback)

    @property
    def progress(self) -> float:
        """Get animation progress (0.0 to 1.0)."""
        return self.frame / self.frame_count


# Predefined animation sequences for common effects

def create_wave_sequence(letter_count: int = 5, cycles: int = 2) -> List[int]:
    """Create a wave animation sequence."""
    frames = []
    for _ in range(cycles):
        frames.extend(range(letter_count))
        frames.extend(range(letter_count - 2, 0, -1))
    return frames


def create_pulse_sequence(on_frames: int = 3, off_frames: int = 3) -> List[bool]:
    """Create a pulse on/off sequence."""
    return [True] * on_frames + [False] * off_frames


def create_fade_sequence(steps: int = 5) -> List[float]:
    """Create a fade sequence with easing."""
    return [ease_out(i / steps) for i in range(steps + 1)]
