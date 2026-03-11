from app.ui.windows.start_window import StartWindow


def test_start_window_title() -> None:
    window = StartWindow()
    assert window.windowTitle() == "Turbine Wear Forecast"
