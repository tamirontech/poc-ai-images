"""Tests for image processor module."""

from PIL import Image, ImageDraw
from pathlib import Path



class TestImageProcessor:
    """Test ImageProcessor class."""

    def test_init_creates_temp_dir(self, image_processor, temp_dir):
        """ImageProcessor should create temp directory."""
        assert image_processor.temp_dir.exists()

    def test_aspect_ratios_defined(self, image_processor):
        """All expected aspect ratios should be defined."""
        expected_ratios = {"1:1", "9:16", "16:9", "4:3", "3:2", "16:10"}
        assert set(image_processor.ASPECT_RATIOS.keys()) == expected_ratios

    def test_target_sizes_defined(self, image_processor):
        """All expected target sizes should be defined."""
        expected_sizes = {"1:1", "9:16", "16:9", "4:3", "3:2", "16:10"}
        assert set(image_processor.TARGET_SIZES.keys()) == expected_sizes

    def test_process_image_basic(self, image_processor, sample_image):
        """Process image with default settings."""
        img = image_processor.process_image(
            str(sample_image),
            aspect_ratio="1:1",
        )
        assert isinstance(img, Image.Image)
        assert img.width == 1024
        assert img.height == 1024

    def test_process_image_9_16_ratio(self, image_processor, sample_image):
        """Process image to 9:16 aspect ratio."""
        img = image_processor.process_image(
            str(sample_image),
            aspect_ratio="9:16",
        )
        assert img.width == 576
        assert img.height == 1024

    def test_process_image_16_9_ratio(self, image_processor, sample_image):
        """Process image to 16:9 aspect ratio."""
        img = image_processor.process_image(
            str(sample_image),
            aspect_ratio="16:9",
        )
        assert img.width == 1024
        assert img.height == 576

    def test_process_image_with_text_overlay(self, image_processor, sample_image):
        """Process image with text overlay."""
        overlay_text = "Modern eco-friendly beauty products"
        img = image_processor.process_image(
            str(sample_image),
            aspect_ratio="1:1",
            overlay_text=overlay_text,
        )
        assert isinstance(img, Image.Image)

    def test_process_image_with_language(self, image_processor, sample_image):
        """Process image with specific language."""
        img = image_processor.process_image(
            str(sample_image),
            aspect_ratio="1:1",
            overlay_text="Test",
            language="ja",
        )
        assert isinstance(img, Image.Image)


class TestImageProcessorResizing:
    """Test image resizing logic."""

    def test_resize_to_aspect_ratio_square(self, image_processor, sample_image):
        """Resize to 1:1 (square) aspect ratio."""
        img = Image.open(sample_image).convert("RGB")
        target_size = (1024, 1024)
        result = image_processor._resize_to_aspect_ratio(img, "1:1", target_size)

        assert result.width == 1024
        assert result.height == 1024

    def test_resize_to_aspect_ratio_portrait(self, image_processor, sample_image):
        """Resize to 9:16 (portrait) aspect ratio."""
        img = Image.open(sample_image).convert("RGB")
        target_size = (576, 1024)
        result = image_processor._resize_to_aspect_ratio(img, "9:16", target_size)

        assert result.width == 576
        assert result.height == 1024

    def test_resize_to_aspect_ratio_landscape(self, image_processor, sample_image):
        """Resize to 16:9 (landscape) aspect ratio."""
        img = Image.open(sample_image).convert("RGB")
        target_size = (1024, 576)
        result = image_processor._resize_to_aspect_ratio(img, "16:9", target_size)

        assert result.width == 1024
        assert result.height == 576


class TestImageProcessorTextOverlay:
    """Test text overlay functionality."""

    def test_add_text_overlay_basic(self, image_processor, sample_image):
        """Add basic text overlay to image."""
        img = Image.open(sample_image).convert("RGB")
        text = "Sample overlay text"
        result = image_processor._add_text_overlay(img, text)

        assert isinstance(result, Image.Image)
        assert result.width == img.width
        assert result.height == img.height

    def test_add_text_overlay_long_text(self, image_processor, sample_image):
        """Add long text that should wrap."""
        img = Image.open(sample_image).convert("RGB")
        text = "This is a very long text that should wrap across multiple lines"
        result = image_processor._add_text_overlay(img, text)

        assert isinstance(result, Image.Image)

    def test_add_text_overlay_empty_text(self, image_processor, sample_image):
        """Add empty text overlay."""
        img = Image.open(sample_image).convert("RGB")
        result = image_processor._add_text_overlay(img, "")

        assert isinstance(result, Image.Image)


class TestImageProcessorTextWrapping:
    """Test text wrapping functionality."""

    def test_wrap_text_basic(self, image_processor, sample_image):
        """Wrap simple text."""
        img = Image.open(sample_image).convert("RGB")
        draw = ImageDraw.Draw(img)
        from PIL import ImageFont

        font = ImageFont.load_default()
        text = "Hello world"
        lines = image_processor._wrap_text(text, 200, draw, font)

        assert isinstance(lines, list)

    def test_wrap_text_long_string(self, image_processor, sample_image):
        """Wrap long text string."""
        img = Image.open(sample_image).convert("RGB")
        draw = ImageDraw.Draw(img)
        from PIL import ImageFont

        font = ImageFont.load_default()
        text = (
            "This is a very long text that should be wrapped "
            "into multiple lines for readability"
        )
        lines = image_processor._wrap_text(text, 100, draw, font)

        assert isinstance(lines, list)
        assert len(lines) >= 1

    def test_wrap_text_empty_string(self, image_processor, sample_image):
        """Wrap empty string."""
        img = Image.open(sample_image).convert("RGB")
        draw = ImageDraw.Draw(img)
        from PIL import ImageFont

        font = ImageFont.load_default()
        lines = image_processor._wrap_text("", 200, draw, font)

        assert isinstance(lines, list)


class TestImageProcessorFontLoading:
    """Test font loading logic."""

    def test_load_font_with_height(self, image_processor):
        """Load font with specific image height."""
        font = image_processor._load_font(1024)

        assert font is not None

    def test_load_font_small_height(self, image_processor):
        """Load font with small image height."""
        font = image_processor._load_font(100)

        assert font is not None

    def test_font_constants_defined(self, image_processor):
        """Font path constants should be defined."""
        assert hasattr(image_processor, "MACOS_FONT_PATH")
        assert hasattr(image_processor, "WINDOWS_FONT_PATH")
        assert isinstance(image_processor.MACOS_FONT_PATH, str)
        assert isinstance(image_processor.WINDOWS_FONT_PATH, str)


class TestImageProcessorSaveImage:
    """Test image saving functionality."""

    def test_save_image(self, image_processor, sample_image, temp_dir):
        """Save image to disk."""
        img = Image.open(sample_image).convert("RGB")
        output_path = temp_dir / "output.jpg"

        result_path = image_processor.save_image(img, str(output_path))

        assert Path(result_path).exists()

    def test_save_image_creates_directories(self, image_processor, sample_image, temp_dir):
        """Save image creates necessary directories."""
        img = Image.open(sample_image).convert("RGB")
        nested_output = temp_dir / "nested" / "dir" / "output.jpg"

        result_path = image_processor.save_image(img, str(nested_output))

        assert Path(result_path).exists()
        assert Path(result_path).parent.exists()
