"""Compliance checks for brand and legal content."""

from typing import List, Tuple, Optional

from PIL import Image


class ComplianceChecker:
    """Checks compliance of creatives against brand and legal guidelines."""

    def __init__(
        self,
        brand_colors: Optional[List[str]] = None,
        prohibited_words: Optional[List[str]] = None,
    ):
        """Initialize compliance checker.

        Args:
            brand_colors: List of brand hex colors, defaults to standard palette
            prohibited_words: List of prohibited words for content compliance
        """
        self.brand_colors = brand_colors or ["#0066CC", "#FFFFFF"]
        self.prohibited_words = prohibited_words or [
            "free",
            "guaranteed",
            "cure",
            "miracle",
            "100% effective",
            "clinically proven",
        ]

    def check_message_compliance(self, message: str) -> Tuple[bool, List[str]]:
        """Check campaign message for prohibited words.

        Args:
            message: Campaign message text

        Returns:
            Tuple of (passed: bool, warnings: List[str])
        """
        warnings = []
        message_lower = message.lower()

        for word in self.prohibited_words:
            if word.lower() in message_lower:
                warnings.append(f"Prohibited word found: '{word}'")

        passed = len(warnings) == 0
        return passed, warnings

    def check_image_dimensions(self, width: int, height: int, aspect_ratio: str) -> Tuple[bool, List[str]]:
        """Check if image dimensions match expected aspect ratio.

        Args:
            width: Image width in pixels
            height: Image height in pixels
            aspect_ratio: Expected aspect ratio (e.g., '1:1')

        Returns:
            Tuple of (passed: bool, warnings: List[str])
        """
        warnings = []

        try:
            expected_w, expected_h = map(float, aspect_ratio.split(":"))
            actual_ratio = width / height
            expected_ratio = expected_w / expected_h
            tolerance = 0.05

            if abs(actual_ratio - expected_ratio) > tolerance:
                warnings.append(
                    f"Dimension mismatch: got {width}x{height} "
                    f"({actual_ratio:.2f}), expected ratio {aspect_ratio} ({expected_ratio:.2f})"
                )
        except (ValueError, ZeroDivisionError):
            # Invalid aspect ratio format (missing ':' or division by zero)
            warnings.append(f"Invalid aspect ratio format: {aspect_ratio}")

        passed = len(warnings) == 0
        return passed, warnings

    def check_text_overlay_presence(self, image_text: str) -> Tuple[bool, List[str]]:
        """Check if text overlay contains expected content.

        Args:
            image_text: Text extracted or expected in image

        Returns:
            Tuple of (passed: bool, warnings: List[str])
        """
        warnings = []

        if not image_text or image_text.strip() == "":
            warnings.append("No text overlay detected on image")

        passed = len(warnings) == 0
        return passed, warnings

    def check_brand_colors(
        self, image_path: str, brand_colors: List[str], tolerance: int = 80, min_coverage: float = 0.05
    ) -> Tuple[bool, List[str]]:
        """Check if an image contains sufficient brand color coverage.

        Samples a pixel grid and measures what fraction of pixels fall within
        ``tolerance`` (Euclidean RGB distance) of at least one brand color.
        Warns when coverage is below ``min_coverage``.

        Args:
            image_path: Path to the saved image file
            brand_colors: List of brand hex colors (e.g. ['#2D5016', '#FFFFFF'])
            tolerance: Max Euclidean RGB distance to consider a pixel a color match (0-441)
            min_coverage: Minimum fraction of sampled pixels that must match (0.0-1.0)

        Returns:
            Tuple of (passed: bool, warnings: List[str])
        """
        warnings = []

        if not brand_colors:
            return True, []

        # Parse hex colors into (R, G, B) tuples
        parsed_colors: List[Tuple[int, int, int]] = []
        for hex_color in brand_colors:
            try:
                h = hex_color.lstrip("#")
                parsed_colors.append((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)))
            except (ValueError, IndexError):
                warnings.append(f"Invalid brand color format: '{hex_color}'")

        if not parsed_colors:
            return len(warnings) == 0, warnings

        try:
            img = Image.open(image_path).convert("RGB")
        except Exception as e:
            warnings.append(f"Could not open image for color check: {e}")
            return False, warnings

        width, height = img.size
        # Sample a ~50×50 grid of pixels regardless of image size
        step_x = max(1, width // 50)
        step_y = max(1, height // 50)

        total = 0
        matched = 0
        for y in range(0, height, step_y):
            for x in range(0, width, step_x):
                pixel = img.getpixel((x, y))
                total += 1
                for brand_rgb in parsed_colors:
                    dist = (
                        (pixel[0] - brand_rgb[0]) ** 2
                        + (pixel[1] - brand_rgb[1]) ** 2
                        + (pixel[2] - brand_rgb[2]) ** 2
                    ) ** 0.5
                    if dist <= tolerance:
                        matched += 1
                        break

        if total == 0:
            return True, []

        coverage = matched / total
        if coverage < min_coverage:
            color_list = ", ".join(brand_colors)
            warnings.append(
                f"Brand color coverage too low: {coverage:.1%} of sampled pixels match "
                f"brand colors ({color_list}) — expected at least {min_coverage:.0%}"
            )

        return len(warnings) == 0, warnings

    def run_full_check(
        self,
        message: str,
        width: int,
        height: int,
        aspect_ratio: str,
        overlay_text: str = "",
        image_path: Optional[str] = None,
        brand_colors: Optional[List[str]] = None,
    ) -> Tuple[bool, List[str]]:
        """Run all compliance checks.

        Args:
            message: Campaign message
            width: Image width
            height: Image height
            aspect_ratio: Target aspect ratio
            overlay_text: Text overlaid on image
            image_path: Path to saved image file (required for brand color check)
            brand_colors: Brand hex colors to verify in the image

        Returns:
            Tuple of (passed: bool, warnings: List[str])
        """
        all_warnings = []

        _, msg_warnings = self.check_message_compliance(message)
        all_warnings.extend(msg_warnings)

        _, dim_warnings = self.check_image_dimensions(width, height, aspect_ratio)
        all_warnings.extend(dim_warnings)

        _, text_warnings = self.check_text_overlay_presence(overlay_text or message)
        all_warnings.extend(text_warnings)

        if image_path and brand_colors:
            _, color_warnings = self.check_brand_colors(image_path, brand_colors)
            all_warnings.extend(color_warnings)

        passed = len(all_warnings) == 0
        return passed, all_warnings
