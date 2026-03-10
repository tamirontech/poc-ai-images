"""Tests for compliance checking module."""


from app.compliance import ComplianceChecker


class TestComplianceChecker:
    """Test ComplianceChecker class."""

    def test_init_with_defaults(self):
        """Initialize with default brand colors and prohibited words."""
        checker = ComplianceChecker()

        assert isinstance(checker.brand_colors, list)
        assert isinstance(checker.prohibited_words, list)

    def test_init_with_custom_values(self, compliance_checker):
        """Initialize with custom brand colors and prohibited words."""
        assert compliance_checker.brand_colors == ["#00AA00", "#FFFFFF"]
        assert "banned" in compliance_checker.prohibited_words

    def test_check_message_compliance_valid(self, compliance_checker):
        """Valid brand message should return no warnings."""
        message = "Discover eco-friendly beauty solutions"
        passed, warnings = compliance_checker.check_message_compliance(message)

        assert passed is True
        assert len(warnings) == 0

    def test_check_message_compliance_with_prohibited_word(self, compliance_checker):
        """Message with prohibited word should return warning."""
        message = "This product is banned in some countries"
        passed, warnings = compliance_checker.check_message_compliance(message)

        assert passed is False
        assert len(warnings) > 0

    def test_check_image_dimensions_valid(self, compliance_checker):
        """Valid dimensions should return no warnings."""
        passed, warnings = compliance_checker.check_image_dimensions(1024, 1024, "1:1")

        assert passed is True
        assert len(warnings) == 0

    def test_check_image_dimensions_9_16(self, compliance_checker):
        """Valid 9:16 dimensions should return no warnings."""
        passed, warnings = compliance_checker.check_image_dimensions(576, 1024, "9:16")

        assert passed is True
        assert len(warnings) == 0

    def test_check_image_dimensions_16_9(self, compliance_checker):
        """Valid 16:9 dimensions should return no warnings."""
        passed, warnings = compliance_checker.check_image_dimensions(1024, 576, "16:9")

        assert passed is True
        assert len(warnings) == 0

    def test_check_image_dimensions_invalid_ratio(self, compliance_checker):
        """Invalid dimensions for ratio should return warning."""
        passed, warnings = compliance_checker.check_image_dimensions(800, 600, "1:1")

        assert passed is False
        assert len(warnings) > 0

    def test_check_image_dimensions_invalid_format(self, compliance_checker):
        """Invalid aspect ratio format should return warning."""
        passed, warnings = compliance_checker.check_image_dimensions(
            1024, 1024, "invalid:format"
        )

        assert passed is False
        assert len(warnings) > 0

    def test_check_text_overlay_presence_with_text(self, compliance_checker):
        """Text overlay presence with valid text."""
        passed, warnings = compliance_checker.check_text_overlay_presence("Great product")

        assert passed is True
        assert len(warnings) == 0

    def test_check_text_overlay_presence_empty(self, compliance_checker):
        """Text overlay presence with empty text."""
        passed, warnings = compliance_checker.check_text_overlay_presence("")

        assert passed is False
        assert len(warnings) > 0


class TestComplianceCheckerIntegration:
    """Test ComplianceChecker integration scenarios."""

    def test_run_full_check_valid(self, compliance_checker):
        """Full compliance check with valid inputs."""
        passed, warnings = compliance_checker.run_full_check(
            message="Great eco-friendly products",
            width=1024,
            height=1024,
            aspect_ratio="1:1",
            overlay_text="Great products",
        )

        assert passed is True
        assert len(warnings) == 0

    def test_run_full_check_messaging_issue(self, compliance_checker):
        """Full check should detect messaging issues."""
        passed, warnings = compliance_checker.run_full_check(
            message="This banned product contains cure claims",
            width=1024,
            height=1024,
            aspect_ratio="1:1",
            overlay_text="Product",
        )

        assert passed is False
        assert len(warnings) > 0

    def test_run_full_check_dimension_issue(self, compliance_checker):
        """Full check should detect dimension issues."""
        passed, warnings = compliance_checker.run_full_check(
            message="Great products",
            width=800,
            height=600,
            aspect_ratio="1:1",
            overlay_text="Product",
        )

        assert passed is False
        assert len(warnings) > 0

    def test_run_full_check_multiple_issues(self, compliance_checker):
        """Full check should detect multiple issues."""
        passed, warnings = compliance_checker.run_full_check(
            message="This banned product uses guaranteed cure claims",
            width=800,
            height=600,
            aspect_ratio="1:1",
            overlay_text="",
        )

        assert passed is False
        assert len(warnings) >= 2


class TestComplianceCheckerEdgeCases:
    """Test ComplianceChecker edge cases."""

    def test_check_message_compliance_case_insensitive(self, compliance_checker):
        """Prohibited word check should be case-insensitive."""
        message = "This product is BANNED"
        passed, warnings = compliance_checker.check_message_compliance(message)

        assert passed is False

    def test_check_image_dimensions_zero_height(self, compliance_checker):
        """Zero height should be handled gracefully."""
        # Should not raise exception
        passed, warnings = compliance_checker.check_image_dimensions(1024, 0, "1:1")

        assert isinstance(passed, bool)
        assert isinstance(warnings, list)
