"""Color calibration app for the NERV theme."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Static

from textual_nerv import nerv


class CalibrateApp(App):
    """Color calibration app to test NERV theme colors."""

    TITLE = "NERV COLOR CALIBRATION"

    CSS = """
    Screen {
        layout: vertical;
    }

    #custom-header {
        dock: top;
        height: 1;
        background: $primary;
        color: #000000;  /* $primary-foreground */
    }

    #header-left {
        dock: left;
        width: auto;
        padding: 0 1;
    }

    #header-right {
        dock: right;
        width: auto;
        padding: 0 1;
    }

    .section {
        height: auto;
        padding: 1;
        margin: 1;
        border: solid $primary;
    }

    .section-title {
        text-style: bold;
        color: $secondary;
        margin-bottom: 1;
    }

    .swatch-row {
        height: auto;
        margin-bottom: 1;
    }

    .swatch {
        width: auto;
        min-width: 20;
        height: 1;
        padding: 0 2;
        margin-right: 1;
    }

    #text-samples Static {
        height: auto;
    }

    #primary-combos .swatch-row {
        height: 3;
    }

    #primary-combos .swatch {
        height: 3;
        content-align: center middle;
    }

    /* Text color samples */
    .text-muted {
        color: $text-muted;
    }

    .foreground-sample {
        color: $foreground;
    }

    .primary-sample {
        color: $primary;
    }

    .secondary-sample {
        color: $secondary;
    }

    /* Primary background combinations */
    .primary-text {
        background: $primary;
        color: $text;
    }

    .primary-fg {
        background: $primary;
        color: #000000;  /* $primary-foreground */
    }

    .primary-black {
        background: $primary;
        color: #000000;
    }

    .primary-white {
        background: $primary;
        color: #ffffff;
    }

    /* Surface/panel combinations */
    .surface-primary {
        background: $surface;
        color: $primary;
    }

    .surface-text {
        background: $surface;
        color: $text;
    }

    .panel-primary {
        background: $panel;
        color: $primary;
    }

    .panel-text {
        background: $panel;
        color: $text;
    }

    /* Palette swatches */
    .color-primary {
        background: $primary;
        color: #000000;
    }

    .color-secondary {
        background: $secondary;
        color: #000000;
    }

    .color-accent {
        background: $accent;
        color: #000000;
    }

    .color-success {
        background: $success;
        color: #000000;
    }

    .color-warning {
        background: $warning;
        color: #000000;
    }

    .color-error {
        background: $error;
        color: #000000;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        # Custom header like ghtui
        with Horizontal(id="custom-header"):
            yield Static("NERV CALIBRATION - Primary Header", id="header-left")
            yield Static("$primary bg / $primary-foreground", id="header-right")

        # Text color samples
        yield Container(
            Static("TEXT COLORS", classes="section-title"),
            Static("$text: Main text color - should be readable on dark backgrounds"),
            Static("$text-muted: Muted text for secondary information", classes="text-muted"),
            Static("$foreground: Widget foreground color", classes="foreground-sample"),
            Static("$primary: Primary accent color - used for highlights", classes="primary-sample"),
            Static("$secondary: Secondary color - for less prominent accents", classes="secondary-sample"),
            id="text-samples",
            classes="section",
        )

        # Primary color combinations
        yield Container(
            Static("PRIMARY COLOR COMBINATIONS", classes="section-title"),
            Horizontal(
                Static("$primary bg\n$text fg", classes="swatch primary-text"),
                Static("$primary bg\n$primary-foreground", classes="swatch primary-fg"),
                Static("$primary bg\n#000 fg", classes="swatch primary-black"),
                Static("$primary bg\n#fff fg", classes="swatch primary-white"),
                classes="swatch-row",
            ),
            Horizontal(
                Static("$surface bg\n$primary fg", classes="swatch surface-primary"),
                Static("$surface bg\n$text fg", classes="swatch surface-text"),
                Static("$panel bg\n$primary fg", classes="swatch panel-primary"),
                Static("$panel bg\n$text fg", classes="swatch panel-text"),
                classes="swatch-row",
            ),
            id="primary-combos",
            classes="section",
        )

        # All theme colors
        yield Container(
            Static("THEME COLOR PALETTE", classes="section-title"),
            Horizontal(
                Static("primary", classes="swatch color-primary"),
                Static("secondary", classes="swatch color-secondary"),
                Static("accent", classes="swatch color-accent"),
                Static("success", classes="swatch color-success"),
                Static("warning", classes="swatch color-warning"),
                Static("error", classes="swatch color-error"),
                classes="swatch-row",
            ),
            id="palette",
            classes="section",
        )

        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(nerv)
        self.theme = "nerv"


if __name__ == "__main__":
    app = CalibrateApp()
    app.run()
