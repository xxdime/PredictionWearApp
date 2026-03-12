from app.ui.windows.start_window import StartWindow


def test_start_window_title(qtbot) -> None:
    window = StartWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "Turbine Wear Forecast"
