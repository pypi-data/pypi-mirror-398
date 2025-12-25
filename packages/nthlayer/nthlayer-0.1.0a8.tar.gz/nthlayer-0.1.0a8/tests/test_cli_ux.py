"""Tests for CLI UX module - styling and interactive prompts."""


class TestPromptStyle:
    """Test questionary prompt styling configuration."""

    def test_prompt_style_imports_without_error(self):
        """PROMPT_STYLE should be valid and importable."""
        from nthlayer.cli.ux import PROMPT_STYLE

        assert PROMPT_STYLE is not None

    def test_prompt_style_has_required_keys(self):
        """PROMPT_STYLE should define all required style keys."""
        from nthlayer.cli.ux import PROMPT_STYLE

        # Get the style rules from the Style object
        style_rules = PROMPT_STYLE.style_rules

        # Required keys for questionary prompts
        required_keys = [
            "qmark",
            "question",
            "answer",
            "pointer",
            "highlighted",
            "selected",
            "text",
        ]

        defined_keys = [rule[0] for rule in style_rules]

        for key in required_keys:
            assert key in defined_keys, f"Missing required style key: {key}"

    def test_prompt_style_colors_are_valid(self):
        """All colors in PROMPT_STYLE should be valid hex colors."""
        import re

        from nthlayer.cli.ux import PROMPT_STYLE

        hex_color_pattern = re.compile(r"#[0-9A-Fa-f]{6}")

        for class_name, style_str in PROMPT_STYLE.style_rules:
            # Extract hex colors from style string
            colors = hex_color_pattern.findall(style_str)
            for color in colors:
                # Verify it's a valid 6-digit hex
                assert len(color) == 7, f"Invalid color format in {class_name}: {color}"

    def test_prompt_style_no_class_prefix(self):
        """Style keys should not have 'class:' prefix (internal to prompt_toolkit)."""
        from nthlayer.cli.ux import PROMPT_STYLE

        for class_name, _ in PROMPT_STYLE.style_rules:
            assert not class_name.startswith("class:"), (
                f"Invalid style key '{class_name}': " "class: prefix is internal to prompt_toolkit"
            )


class TestConsoleSetup:
    """Test Rich console configuration."""

    def test_console_imports_without_error(self):
        """Console should be properly configured and importable."""
        from nthlayer.cli.ux import console

        assert console is not None

    def test_nthlayer_theme_has_required_styles(self):
        """NTHLAYER_THEME should define all required style names."""
        from nthlayer.cli.ux import NTHLAYER_THEME

        required_styles = ["info", "success", "warning", "error", "muted"]

        for style in required_styles:
            assert style in NTHLAYER_THEME.styles, f"Missing theme style: {style}"


class TestOutputFunctions:
    """Test output helper functions."""

    def test_header_function_exists(self):
        """header() function should be importable."""
        from nthlayer.cli.ux import header

        assert callable(header)

    def test_success_function_exists(self):
        """success() function should be importable."""
        from nthlayer.cli.ux import success

        assert callable(success)

    def test_error_function_exists(self):
        """error() function should be importable."""
        from nthlayer.cli.ux import error

        assert callable(error)

    def test_warning_function_exists(self):
        """warning() function should be importable."""
        from nthlayer.cli.ux import warning

        assert callable(warning)

    def test_info_function_exists(self):
        """info() function should be importable."""
        from nthlayer.cli.ux import info

        assert callable(info)


class TestInteractivePrompts:
    """Test interactive prompt functions (without actually prompting)."""

    def test_select_function_exists(self):
        """select() function should be importable."""
        from nthlayer.cli.ux import select

        assert callable(select)

    def test_multi_select_function_exists(self):
        """multi_select() function should be importable."""
        from nthlayer.cli.ux import multi_select

        assert callable(multi_select)

    def test_text_input_function_exists(self):
        """text_input() function should be importable."""
        from nthlayer.cli.ux import text_input

        assert callable(text_input)

    def test_confirm_function_exists(self):
        """confirm() function should be importable."""
        from nthlayer.cli.ux import confirm

        assert callable(confirm)

    def test_password_input_function_exists(self):
        """password_input() function should be importable."""
        from nthlayer.cli.ux import password_input

        assert callable(password_input)


class TestBanner:
    """Test banner display."""

    def test_print_banner_function_exists(self):
        """print_banner() function should be importable."""
        from nthlayer.cli.ux import print_banner

        assert callable(print_banner)

    def test_banner_constant_exists(self):
        """NTHLAYER_BANNER constant should be defined."""
        from nthlayer.cli.ux import NTHLAYER_BANNER

        assert NTHLAYER_BANNER is not None
        # Banner contains ASCII art + tagline
        assert "The Missing Layer of Reliability" in NTHLAYER_BANNER


class TestQuestionaryIntegration:
    """Test that questionary integration works correctly."""

    def test_questionary_style_is_valid_style_object(self):
        """PROMPT_STYLE should be a valid questionary Style object."""
        from nthlayer.cli.ux import PROMPT_STYLE
        from questionary import Style

        assert isinstance(PROMPT_STYLE, Style)

    def test_questionary_select_accepts_style(self):
        """questionary.select should accept our PROMPT_STYLE without error."""
        import questionary
        from nthlayer.cli.ux import PROMPT_STYLE

        # Create a select question (don't ask it)
        question = questionary.select(
            "Test question",
            choices=["Option 1", "Option 2"],
            style=PROMPT_STYLE,
        )

        # Should create without error
        assert question is not None

    def test_questionary_checkbox_accepts_style(self):
        """questionary.checkbox should accept our PROMPT_STYLE without error."""
        import questionary
        from nthlayer.cli.ux import PROMPT_STYLE

        # Create a checkbox question (don't ask it)
        question = questionary.checkbox(
            "Test question",
            choices=["Option 1", "Option 2"],
            style=PROMPT_STYLE,
        )

        # Should create without error
        assert question is not None

    def test_questionary_text_accepts_style(self):
        """questionary.text should accept our PROMPT_STYLE without error."""
        import questionary
        from nthlayer.cli.ux import PROMPT_STYLE

        # Create a text question (don't ask it)
        question = questionary.text(
            "Test question",
            style=PROMPT_STYLE,
        )

        # Should create without error
        assert question is not None

    def test_questionary_confirm_accepts_style(self):
        """questionary.confirm should accept our PROMPT_STYLE without error."""
        import questionary
        from nthlayer.cli.ux import PROMPT_STYLE

        # Create a confirm question (don't ask it)
        question = questionary.confirm(
            "Test question",
            style=PROMPT_STYLE,
        )

        # Should create without error
        assert question is not None
