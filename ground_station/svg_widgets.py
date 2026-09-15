"""Procedurally-drawn gauge/valve SVGs and a clickable SVG widget.

Ported from the GUI_SVG_BUILT_IN_PYTHON.py prototype (which already worked
end-to-end against fake data) -- generalized off that file's hardcoded
'Industrial Process Control' naming so the same drawing code serves this
project's real sensor set (sensors.SENSOR_META) and valve set.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QByteArray, QSize, pyqtSignal
from PyQt6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout
from PyQt6.QtSvgWidgets import QSvgWidget


def gauge_svg_for(name: str, value: float, max_value: float) -> str:
    """Dispatches to the right gauge drawing by channel-name prefix (P/T/L),
    the same convention sensors.SENSOR_KEYS already uses."""
    if name.startswith("P"):
        return _pressure_svg(value, max_value)
    if name.startswith("T"):
        return _thermo_svg(value, max_value)
    return _load_cell_svg(value, max_value)


def _pressure_svg(value: float, max_value: float) -> str:
    angle = (value / max_value) * 180 - 90
    return f"""
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <title>{value:.1f} PSI</title>
      <circle cx="50" cy="50" r="45" fill="#111c17" stroke="#3a4a3f" stroke-width="4" />
      <text x="50" y="20" text-anchor="middle" fill="#8fffb0" font-size="9" font-weight="bold">{max_value/2:.0f}</text>
      <text x="18" y="54" text-anchor="middle" fill="#8fffb0" font-size="9" font-weight="bold">0</text>
      <text x="82" y="54" text-anchor="middle" fill="#8fffb0" font-size="9" font-weight="bold">{max_value:.0f}</text>
      <line x1="50" y1="50" x2="50" y2="15" stroke="#f5c518" stroke-width="3"
            stroke-linecap="round" transform="rotate({angle} 50 50)"/>
      <circle cx="50" cy="50" r="5" fill="#f5c518" />
    </svg>
    """


def _thermo_svg(value: float, max_value: float) -> str:
    max_fill_height = 55
    min_y = 25
    fill_height = max(0.0, min(1.0, value / max_value)) * max_fill_height
    fill_y = min_y + (max_fill_height - fill_height)
    return f"""
    <svg viewBox="0 0 60 100" xmlns="http://www.w3.org/2000/svg">
      <title>{value:.1f} °C</title>
      <rect x="25" y="10" width="10" height="65" rx="5" fill="#111c17" stroke="#3a4a3f" stroke-width="1" />
      <rect x="25" y="{fill_y}" width="10" height="{fill_height}" rx="5" fill="#8fffb0" />
      <circle cx="30" cy="75" r="10" fill="#8fffb0" stroke="#3a4a3f" stroke-width="2" />
      <rect x="25" y="65" width="10" height="10" fill="#8fffb0" />
      <text x="15" y="75" fill="#c3c2b7" font-size="8">0</text>
      <text x="12" y="25" fill="#c3c2b7" font-size="8">{max_value:.0f}</text>
    </svg>
    """


def _load_cell_svg(value: float, max_value: float) -> str:
    compression = max(0.0, min(1.0, value / max_value)) * 10
    return f"""
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <title>{value:.1f} kg</title>
      <rect x="10" y="80" width="80" height="10" fill="#3a4a3f" rx="3"/>
      <rect x="40" y="{30 + compression}" width="20" height="{50 - compression}" fill="#f5c518" rx="5"/>
      <rect x="30" y="25" width="40" height="10" fill="#8fffb0" rx="3"/>
      <line x1="45" y1="50" x2="55" y2="50" stroke="#0a0c0a" stroke-width="2" stroke-dasharray="2,2"/>
      <line x1="45" y1="60" x2="55" y2="60" stroke="#0a0c0a" stroke-width="2" stroke-dasharray="2,2"/>
      <line x1="45" y1="70" x2="55" y2="70" stroke="#0a0c0a" stroke-width="2" stroke-dasharray="2,2"/>
    </svg>
    """


def valve_svg(is_open: bool) -> str:
    body_color = "#8fffb0" if is_open else "#ff4d4d"
    handle_rotation = 0 if is_open else 90
    return f"""
    <svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
      <title>Valve ({'OPEN' if is_open else 'CLOSED'})</title>
      <rect x="5" y="37" width="70" height="6" fill="#3a4a3f" />
      <circle cx="40" cy="40" r="12" fill="{body_color}" />
      <rect x="5" y="28" width="50" height="4" rx="2" fill="#f5c518"
            transform="rotate({handle_rotation} 10 30)"/>
    </svg>
    """


class ClickableSvgWidget(QFrame):
    """A clickable panel-instrument widget: an SVG face plus a hazard-yellow
    stenciled placard label riveted underneath (the direction's borrowed raise
    from the aerospace placard/stencil world -- see PRODUCT.md)."""

    clicked = pyqtSignal(str)

    def __init__(self, component_id: str, parent=None):
        super().__init__(parent)
        self._component_id = component_id
        self.svg_widget = QSvgWidget(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.svg_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(6, 6, 6, 6)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame { border: 1px solid #2c3a30; border-radius: 4px; background: #0f1512; }
            QFrame:hover { border: 1px solid #f5c518; }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def load_svg(self, svg_data: str) -> None:
        self.svg_widget.load(QByteArray(svg_data.encode("utf-8")))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._component_id)
        super().mousePressEvent(event)

    def sizeHint(self) -> QSize:
        return QSize(96, 96)
