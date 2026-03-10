"""Image processing and text overlay utilities."""

from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.sanitization import sanitize_text_input

try:
    from bidi.algorithm import get_display as bidi_get_display
    _BIDI_AVAILABLE = True
except ImportError:
    _BIDI_AVAILABLE = False

try:
    import arabic_reshaper
    _ARABIC_RESHAPER_AVAILABLE = True
except ImportError:
    _ARABIC_RESHAPER_AVAILABLE = False


class ImageProcessor:
    """Processes images: resizing, cropping, and text overlay."""

    # System font paths for text overlay — Latin
    MACOS_FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"
    WINDOWS_FONT_PATH = "arial.ttf"

    # CJK fonts (Japanese, Chinese, Korean)
    MACOS_CJK_FONT_PATHS = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ]
    WINDOWS_CJK_FONT_PATHS = ["msyh.ttc", "simsun.ttc"]
    LINUX_CJK_FONT_PATHS = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    # Arabic / Persian / Urdu fonts
    MACOS_ARABIC_FONT_PATHS = [
        "/System/Library/Fonts/GeezaPro.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    WINDOWS_ARABIC_FONT_PATHS = ["arial.ttf", "tahoma.ttf"]
    LINUX_ARABIC_FONT_PATHS = [
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/arabic/DejaVuSans.ttf",
    ]

    # Hebrew fonts
    MACOS_HEBREW_FONT_PATHS = [
        "/System/Library/Fonts/Arial Hebrew.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    WINDOWS_HEBREW_FONT_PATHS = ["arial.ttf"]
    LINUX_HEBREW_FONT_PATHS = [
        "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf",
    ]

    # Language families
    _RTL_LANGUAGES = {"ar", "he", "fa", "ur"}
    _CJK_LANGUAGES = {"ja", "zh", "zh-cn", "zh-tw", "zh-hk", "ko"}
    _ARABIC_LANGUAGES = {"ar", "fa", "ur"}
    _HEBREW_LANGUAGES = {"he"}

    ASPECT_RATIOS = {
        "1:1": (1, 1),
        "9:16": (9, 16),
        "16:9": (16, 9),
        "4:3": (4, 3),
        "3:2": (3, 2),
        "16:10": (16, 10),
    }

    TARGET_SIZES = {
        "1:1": (1024, 1024),
        "9:16": (576, 1024),
        "16:9": (1024, 576),
        "4:3": (1024, 768),
        "3:2": (1024, 682),
        "16:10": (1024, 640),
    }

    def __init__(self):
        """Initialize image processor."""
        self.temp_dir = Path(settings.temp_dir)
        self.temp_dir.mkdir(exist_ok=True)

    def process_image(
        self,
        source_image_path: str,
        aspect_ratio: str,
        overlay_text: str = "",
        language: str = "en",
        logo_path: Optional[str] = None,
        logo_position: str = "bottom-right",
        logo_scale: float = 0.15,
    ) -> Image.Image:
        """Process image for target aspect ratio and add text overlay and logo.

        Args:
            source_image_path: Path to source image
            aspect_ratio: Target aspect ratio (e.g., '1:1')
            overlay_text: Text to overlay on image
            language: Language code for text
            logo_path: Path to logo image file (PNG with transparency preferred)
            logo_position: Position for logo ('top-left', 'top-right', 'bottom-left', 'bottom-right', 'center')
            logo_scale: Logo scale as fraction of image width (0.1-0.5)

        Returns:
            Processed PIL Image object
        """
        # Load source image
        img = Image.open(source_image_path).convert("RGB")

        # Resize to target aspect ratio
        target_size = self.TARGET_SIZES.get(aspect_ratio, (1024, 1024))
        img = self._resize_to_aspect_ratio(img, aspect_ratio, target_size)

        # Add text overlay if provided
        if overlay_text:
            img = self._add_text_overlay(img, overlay_text, language)

        # Add logo if provided
        if logo_path:
            img = self._add_logo_overlay(img, logo_path, logo_position, logo_scale)

        return img

    def _resize_to_aspect_ratio(
        self, img: Image.Image, aspect_ratio: str, target_size: Tuple[int, int]
    ) -> Image.Image:
        """Resize and crop image to target aspect ratio.

        Args:
            img: PIL Image object
            aspect_ratio: Target aspect ratio
            target_size: Target dimensions (width, height)

        Returns:
            Resized PIL Image object
        """
        aspect_w, aspect_h = self.ASPECT_RATIOS.get(aspect_ratio, (1, 1))
        target_w, target_h = target_size

        # Calculate scaling to fit within target dimensions
        source_ratio = img.width / img.height
        target_ratio = target_w / target_h

        if source_ratio > target_ratio:
            # Source is wider, scale by height
            new_h = target_h
            new_w = int(new_h * source_ratio)
        else:
            # Source is taller, scale by width
            new_w = target_w
            new_h = int(new_w / source_ratio)

        # Resize
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Crop to exact size (center)
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        right = left + target_w
        bottom = top + target_h
        img = img.crop((left, top, right, bottom))

        return img

    def _prepare_rtl_text(self, text: str) -> str:
        """Reshape and apply bidi algorithm for RTL scripts (Arabic/Hebrew).

        Uses arabic_reshaper for Arabic glyph joining and python-bidi for
        right-to-left visual reordering. Falls back to the original text if
        neither library is installed.

        Args:
            text: Text in an RTL script

        Returns:
            Visually reordered text ready for Pillow rendering
        """
        if _ARABIC_RESHAPER_AVAILABLE:
            text = arabic_reshaper.reshape(text)
        if _BIDI_AVAILABLE:
            text = bidi_get_display(text)
        return text

    def _add_text_overlay(
        self, img: Image.Image, text: str, language: str = "en"
    ) -> Image.Image:
        """Add text overlay with drop shadow to image.

        Args:
            img: PIL Image object
            text: Text to overlay on image
            language: BCP-47 language code (e.g. 'en', 'ar', 'ja')

        Returns:
            Image with text overlay (white text with drop shadow)
        """
        # Return unchanged image if no text provided
        if not text or not text.strip():
            return img

        # Sanitize text input to prevent injection attacks
        try:
            text = sanitize_text_input(text, max_length=200)
        except ValueError as e:
            raise ValueError(f"Invalid text overlay: {e}")

        lang = language.lower().strip()
        is_rtl = lang in self._RTL_LANGUAGES

        # Reshape + reorder RTL text for correct Pillow rendering
        if is_rtl:
            text = self._prepare_rtl_text(text)

        draw = ImageDraw.Draw(img)
        font = self._load_font(img.height, lang)

        # Wrap text for optimal readability
        max_width = img.width - 40
        lines = self._wrap_text(text, max_width, draw, font)

        # Position text in lower portion of image
        line_height = font.getbbox("A")[3] - font.getbbox("A")[1] + 10
        total_text_height = len(lines) * line_height
        text_y = img.height - total_text_height - 30

        # Render each text line with drop shadow effect
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (img.width - text_width) // 2

            # Draw shadow (dark offset)
            draw.text(
                (text_x + 2, text_y + 2), line, fill=(0, 0, 0, 128), font=font
            )
            # Draw main text (white)
            draw.text((text_x, text_y), line, fill=(255, 255, 255), font=font)

            text_y += line_height

        return img

    def _add_logo_overlay(
        self, img: Image.Image, logo_path: str, position: str = "bottom-right", scale: float = 0.15
    ) -> Image.Image:
        """Add logo to image with transparency support.

        Args:
            img: PIL Image object
            logo_path: Path to logo file (PNG with transparency preferred)
            position: Logo position ('top-left', 'top-right', 'bottom-left', 'bottom-right', 'center')
            scale: Logo scale as fraction of image width (0.1-0.5)

        Returns:
            Image with logo overlay

        Raises:
            FileNotFoundError: If logo file does not exist
            ValueError: If logo path is invalid or scale is out of range
        """
        logo_file = Path(logo_path)
        if not logo_file.exists():
            raise FileNotFoundError(f"Logo file not found: {logo_path}")

        if not 0.1 <= scale <= 0.5:
            raise ValueError(f"Logo scale must be between 0.1 and 0.5, got {scale}")

        # Load and convert logo (preserve transparency if available)
        try:
            logo = Image.open(logo_file)
            # If logo has transparency, keep RGBA; otherwise convert to RGB
            if logo.mode in ("RGBA", "LA", "P"):
                logo = logo.convert("RGBA")
            else:
                logo = logo.convert("RGB")
        except Exception as e:
            raise ValueError(f"Failed to load logo image: {e}")

        # Calculate logo size based on image width
        logo_width = int(img.width * scale)
        aspect_ratio = logo.width / logo.height
        logo_height = int(logo_width / aspect_ratio)
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

        # Calculate position
        padding = 20
        positions = {
            "top-left": (padding, padding),
            "top-right": (img.width - logo_width - padding, padding),
            "bottom-left": (padding, img.height - logo_height - padding),
            "bottom-right": (img.width - logo_width - padding, img.height - logo_height - padding),
            "center": ((img.width - logo_width) // 2, (img.height - logo_height) // 2),
        }

        if position not in positions:
            position = "bottom-right"

        x, y = positions[position]

        # Composite logo onto image
        if logo.mode == "RGBA":
            img.paste(logo, (x, y), logo)
        else:
            img.paste(logo, (x, y))

        return img

    def _load_font(self, image_height: int, language: str = "en"):
        """Load appropriate font for the given language and image height.

        Selects a font family that supports the target script (Latin, CJK,
        Arabic, Hebrew), trying platform-specific paths in priority order and
        falling back to Pillow's built-in default if none are found.

        Args:
            image_height: Height of image for font size calculation
            language: BCP-47 language code used to pick the right script font

        Returns:
            PIL Font object for text rendering
        """
        font_size = max(int(image_height / 10), 20)
        lang = language.lower().strip()

        if lang in self._CJK_LANGUAGES:
            font_paths = (
                self.MACOS_CJK_FONT_PATHS
                + self.WINDOWS_CJK_FONT_PATHS
                + self.LINUX_CJK_FONT_PATHS
            )
        elif lang in self._ARABIC_LANGUAGES:
            font_paths = (
                self.MACOS_ARABIC_FONT_PATHS
                + self.WINDOWS_ARABIC_FONT_PATHS
                + self.LINUX_ARABIC_FONT_PATHS
            )
        elif lang in self._HEBREW_LANGUAGES:
            font_paths = (
                self.MACOS_HEBREW_FONT_PATHS
                + self.WINDOWS_HEBREW_FONT_PATHS
                + self.LINUX_HEBREW_FONT_PATHS
            )
        else:
            font_paths = [self.MACOS_FONT_PATH, self.WINDOWS_FONT_PATH]

        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, font_size)
            except (OSError, AttributeError):
                continue

        # Fallback to default font if no system fonts available
        return ImageFont.load_default()

    def _wrap_text(self, text: str, max_width: int, draw, font) -> List[str]:
        """Wrap text to fit within max width.

        Args:
            text: Text to wrap
            max_width: Maximum width in pixels
            draw: PIL ImageDraw object
            font: PIL Font object

        Returns:
            List of wrapped text lines
        """
        lines = []
        words = text.split()

        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]

            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def save_image(self, img: Image.Image, output_path: str) -> str:
        """Save processed image to file.

        Args:
            img: PIL Image object
            output_path: Path to save image

        Returns:
            Path to saved image
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", quality=95)
        return output_path
