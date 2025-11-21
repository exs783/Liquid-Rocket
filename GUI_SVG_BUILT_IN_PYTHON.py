import sys
import random
import time
from typing import Dict, Any, List

# PyQt6 Core and Widgets
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QGridLayout, QVBoxLayout,
    QGroupBox, QMainWindow, QPushButton, QHBoxLayout, QFrame, QSizePolicy
)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtCore import Qt, QTimer, QByteArray, pyqtSignal, QSize, QUrl

# PyQtGraph for plotting
import pyqtgraph as pg

# Configure pyqtgraph defaults to match the dark theme
pg.setConfigOption('background', '#111827')
pg.setConfigOption('foreground', '#F3F4F6')


# --- Utility Functions (SVG Definitions) ---

def get_valve_svg(is_open: bool) -> str:
    """Generates the SVG string for a ball valve based on its state."""
    handle_color = "#3B82F6"
    body_color = "#10B981" if is_open else "#EF4444"
    handle_rotation = 0 if is_open else 90

    return f"""
    <svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
      <title>Ball Valve (State: {'Open' if is_open else 'Closed'})</title>
      <!-- Pipe Section -->
      <rect x="5" y="37" width="70" height="6" fill="#4B5563" /> 
      <!-- Valve Body and Connection Area -->
      <circle cx="40" cy="40" r="12" fill="{body_color}" /> 
      <!-- Handle -->
      <rect x="5" y="28" width="50" height="4" rx="2" fill="{handle_color}" 
            transform="rotate({handle_rotation} 10 30)"/>
    </svg>
    """


def get_servo_svg(is_on: bool, angle: int) -> str:
    """Generates the SVG string for a servo motor."""
    body_color = "#3B82F6" if is_on else "#6B7280"

    return f"""
    <svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
      <title>Servo (State: {'On' if is_on else 'Off'}, Angle: {angle}°)</title>
      <!-- Servo Body -->
      <rect fill="{body_color}" x="10" y="10" width="40" height="40" rx="5" />
      <!-- Servo Hub -->
      <circle fill="#9CA3AF" cx="30" cy="30" r="8" />
      <!-- Servo Arm (0 deg is vertical, 90 deg is right) -->
      <rect fill="{body_color}" x="28" y="5" width="4" height="25" rx="2" 
            transform="rotate({angle} 30 30)"/>
    </svg>
    """


def get_pressure_svg(value: float, max_value: int = 200) -> str:
    """Generates the SVG for a pressure gauge."""
    angle = (value / max_value) * 180 - 90

    return f"""
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <title>Pressure Gauge ({value:.1f} PSI)</title>
      <!-- Gauge Face -->
      <circle cx="50" cy="50" r="45" fill="#374151" stroke="#9CA3AF" stroke-width="4" />
      <!-- Markings (0, 100, 200) -->
      <text x="50" y="20" text-anchor="middle" fill="white" font-size="10" font-weight="bold">100</text>
      <text x="18" y="54" text-anchor="middle" fill="white" font-size="10" font-weight="bold">0</text>
      <text x="82" y="54" text-anchor="middle" fill="white" font-size="10" font-weight="bold">200</text>
      <!-- Needle -->
      <line x1="50" y1="50" x2="50" y2="15" stroke="#F87171" stroke-width="3" 
            stroke-linecap="round" transform="rotate({angle} 50 50)"/>
      <!-- Hub -->
      <circle cx="50" cy="50" r="5" fill="#F87171" />
    </svg>
    """


def get_thermo_svg(value: float, max_value: int = 100) -> str:
    """Generates the SVG for a thermometer."""
    max_fill_height = 55
    min_y = 25
    fill_height = (value / max_value) * max_fill_height
    fill_y = min_y + (max_fill_height - fill_height)

    return f"""
    <svg viewBox="0 0 60 100" xmlns="http://www.w3.org/2000/svg">
      <title>Thermometer ({value:.1f} °C)</title>
      <!-- Background tube -->
      <rect x="25" y="10" width="10" height="65" rx="5" fill="#1F2937" stroke="#9CA3AF" stroke-width="1" />
      <!-- Mercury Fill -->
      <rect x="25" y="{fill_y}" width="10" height="{fill_height}" rx="5" fill="#DC2626" />
      <!-- Bulb -->
      <circle cx="30" cy="75" r="10" fill="#DC2626" stroke="#9CA3AF" stroke-width="2" />
      <!-- Stem covering bulb connection -->
      <rect x="25" y="65" width="10" height="10" fill="#DC2626" />
      <!-- Markings -->
      <text x="15" y="75" fill="white" font-size="8">0</text>
      <text x="15" y="25" fill="white" font-size="8">100</text>
    </svg>
    """


def get_load_cell_svg(value: float, max_value: int = 1000) -> str:
    """Generates the SVG for a simple load cell or scale."""
    compression = (value / max_value) * 10

    return f"""
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <title>Load Cell ({value:.1f} kg)</title>
      <!-- Base Plate -->
      <rect x="10" y="80" width="80" height="10" fill="#4B5563" rx="3"/>
      <!-- Body of Load Cell (Compressed) -->
      <rect x="40" y="{30 + compression}" width="20" height="{50 - compression}" fill="#3B82F6" rx="5"/>
      <!-- Top Plate (The item being weighed rests here) -->
      <rect x="30" y="25" width="40" height="10" fill="#9CA3AF" rx="3"/>

      <!-- Compression indicator (Spring/Force lines) -->
      <line x1="45" y1="50" x2="55" y2="50" stroke="white" stroke-width="2" stroke-dasharray="2,2"/>
      <line x1="45" y1="60" x2="55" y2="60" stroke="white" stroke-width="2" stroke-dasharray="2,2"/>
      <line x1="45" y1="70" x2="55" y2="70" stroke="white" stroke-width="2" stroke-dasharray="2,2"/>

      <!-- Connection points -->
      <circle cx="35" cy="85" r="3" fill="#10B981" />
      <circle cx="65" cy="85" r="3" fill="#10B981" />
    </svg>
    """


def get_igniter_svg(is_active: bool) -> str:
    """Generates the SVG string for an igniter/heater."""
    # Amber (Active) or Gray (Inactive)
    flame_color = "#F59E0B" if is_active else "#6B7280"

    return f"""
    <svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
      <title>Igniter (State: {'Active' if is_active else 'Inactive'})</title>
      <!-- Base Coil/Element -->
      <rect x="15" y="35" width="50" height="10" rx="3" fill="#374151" stroke="#9CA3AF" stroke-width="2"/>
      <!-- Glowing Effect / Flame -->
      <path d="M 40 10 L 30 40 L 50 40 Z" fill="{flame_color}" opacity="{1.0 if is_active else 0.3}" stroke="none"/>
      <circle cx="40" cy="40" r="5" fill="{flame_color}" opacity="{0.5 if is_active else 0.1}"/>
    </svg>
    """


# -------------------------------------------------------------------------------
# Custom Clickable SVG Widget (Outputs)
# -------------------------------------------------------------------------------

class OutputSvgWidget(QFrame):
    """
    A clickable widget to display an SVG for an output component.
    It communicates a click event via a signal.
    """
    clicked = pyqtSignal(str)

    def __init__(self, component_id: str, parent=None):
        super().__init__(parent)
        self._component_id = component_id
        self.svg_widget = QSvgWidget(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.svg_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setStyleSheet(f"""
            QFrame {{ 
                border: 2px solid #1F2937;
                border-radius: 8px;
            }}
            QFrame:hover {{ 
                border: 2px solid #3B82F6;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def load_svg(self, svg_data: str):
        """Loads new SVG data into the internal QSvgWidget."""
        self.svg_widget.load(QByteArray(svg_data.encode('utf-8')))

    def mousePressEvent(self, event):
        """Emit the signal when the mouse is pressed on the widget."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._component_id)
            super().mousePressEvent(event)

    def sizeHint(self) -> QSize:
        """Provide a default size hint for layout management."""
        return QSize(80, 80)  # Adjusted size for denser layout


# -------------------------------------------------------------------------------
# Main Application Window
# -------------------------------------------------------------------------------

class DashboardWindow(QMainWindow):
    """
    Industrial monitoring dashboard with multiple sensors and actuators.
    """
    # Define control setpoints
    PRESSURE_MAX = 150.0  # PSI (If exceeded, V-101 closes)
    TEMP_MAX = 80.0  # °C (If exceeded, SRV-A activates)
    LOAD_TARGET = 500.0  # kg (SRV-B aims for this)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Industrial Process Control & Monitoring")
        self.setGeometry(100, 100, 1400, 800)

        # --- Sensor and Output Mappings ---
        self.sensor_keys = ['P_101', 'P_102', 'P_103', 'P_104', 'P_105', 'P_106', 'P_107', 'T_202', 'L_301']
        self.output_keys = ['V_101', 'IGN_E', 'SRV_A', 'SRV_B', 'SRV_C', 'SRV_D']

        # Mapping sensor keys to their display names and units
        self.sensor_map = {
            'P_101': ("P-101 Pressure", "PSI", 200, get_pressure_svg),
            'P_102': ("P-102 Pressure", "PSI", 200, get_pressure_svg),
            'P_103': ("P-103 Pressure", "PSI", 200, get_pressure_svg),
            'P_104': ("P-104 Pressure", "PSI", 200, get_pressure_svg),
            'P_105': ("P-105 Pressure", "PSI", 200, get_pressure_svg),
            'P_106': ("P-106 Pressure", "PSI", 200, get_pressure_svg),
            'P_107': ("P-107 Pressure", "PSI", 200, get_pressure_svg),
            'T_202': ("T-202 Temp", "°C", 100, get_thermo_svg),
            'L_301': ("L-301 Load", "kg", 1000, get_load_cell_svg),
        }

        # --- Application State (Initial Values) ---
        initial_state = {
            'V_101_open': True,
            'IGN_E_active': False,  # IGNITER STARTS OFF (As requested)

            # Note: Keys use 'servo_A_on', 'servo_B_on', etc.
            'servo_A_on': False, 'servo_A_angle': 0,
            'servo_B_on': False, 'servo_B_angle': 0,
            'servo_C_on': False, 'servo_C_angle': 0,
            'servo_D_on': False, 'servo_D_angle': 0,

            'P_101': 50.0, 'P_102': 48.0, 'P_103': 52.0, 'P_104': 50.5,
            'P_105': 51.0, 'P_106': 49.5, 'P_107': 53.0,
            'T_202': 20.0,
            'L_301': 100.0,
        }
        self.state: Dict[str, Any] = initial_state
        self.sensor_widgets: Dict[str, QLabel] = {}
        self.output_widgets: Dict[str, Any] = {}
        self.gauge_widgets: Dict[str, Any] = {}

        # --- Initialize UI and Components ---
        self._set_dark_stylesheet()
        self._setup_ui()

        # --- Initialize All Visuals based on initial state ---
        self.update_output_visuals()
        self.update_sensor_visuals()

        # --- Start Polling Timer (Simulates continuous data feed) ---
        self.polling_timer = QTimer(self)
        self.polling_timer.timeout.connect(self.poll_and_update_system)
        self.polling_timer.start(2000)

    def _set_dark_stylesheet(self):
        """Applies a consistent dark theme using CSS."""
        self.setStyleSheet("""
            QWidget {
                background-color: #111827; /* gray-900 */
                color: #F3F4F6; /* gray-100 */
                font-family: 'Segoe UI', 'System-ui', sans-serif; 
            }
            QTabWidget::pane {
                border: 1px solid #374151;
                background-color: #111827;
                margin: 0;
                padding: 10px;
            }
            QTabBar::tab {
                background: #1F2937; /* gray-800 */
                color: #F3F4F6;
                padding: 10px 20px;
                border: 1px solid #374151;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #111827;
                border-bottom: 2px solid #2563EB;
                font-weight: bold;
            }
            QGroupBox {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
                padding-top: 20px;
                margin-top: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px 0 5px;
                left: 10px;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                background-color: transparent;
            }
            QPushButton {
                background-color: #2563EB;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
            QLineEdit {
                background-color: #374151; 
                border: 1px solid #4B5563; 
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
        """)

    def _setup_ui(self):
        """Sets up the main layout using a QTabWidget."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        from PyQt6.QtWidgets import QTabWidget  # Ensure QTabWidget is imported

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self._create_main_pid_view(), "Main")
        self.tab_widget.addTab(self._create_graph_view(), "Graph")
        self.tab_widget.addTab(self._create_data_view(), "Data")

        self.tab_widget.setCurrentIndex(0)

        main_layout.addWidget(self.tab_widget)

        self.status_light = QFrame()
        self.status_light.setFixedSize(20, 20)
        self.status_light.setToolTip("Control System Status")
        self.status_light.setStyleSheet("background-color: #10B981; border-radius: 10px;")
        self.status_label = QLabel("System Control Active")

        status_bar = QHBoxLayout()
        status_bar.addWidget(self.status_label)
        status_bar.addWidget(self.status_light)
        status_bar.addStretch(1)

        main_layout.addLayout(status_bar)

    # --- Tab Content Views ---

    def _create_display_field(self, label: str, component_id: str, initial_value: str) -> QHBoxLayout:
        """Helper to create a label + display value row, storing the value widget."""
        row = QHBoxLayout()
        label_widget = QLabel(label)

        value_widget = QLabel(initial_value)
        value_widget.setStyleSheet(
            "font-size: 18px; color: #FBBF24; padding: 5px; border: 1px solid #374151; border-radius: 4px; min-width: 100px;")
        value_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.sensor_widgets[component_id] = value_widget  # Store reference

        row.addWidget(label_widget)
        row.addStretch()
        row.addWidget(value_widget)
        return row

    def _create_main_pid_view(self) -> QWidget:
        """Creates the primary 'Main' view with current sensor values, setpoints, and all outputs."""
        main_page = QWidget()
        layout = QHBoxLayout(main_page)

        # --- 1. Sensor Status and Setpoints (Left Side) ---
        left_column = QVBoxLayout()

        # A. Live Sensor Data
        sensor_group = QGroupBox("Live Sensor Data")
        sensor_grid = QGridLayout(sensor_group)

        for i, key in enumerate(self.sensor_keys):
            name, unit, _, _ = self.sensor_map[key]
            value = self.state[key]
            row = self._create_display_field(f"{name} ({unit}):", key, f"{value:.1f}")
            sensor_grid.addLayout(row, i, 0)

        # B. Setpoints Display
        setpoint_group = QGroupBox("Control Setpoints")
        setpoint_layout = QVBoxLayout(setpoint_group)
        setpoint_layout.addLayout(
            self._create_display_field("V-101 Trip (PSI):", "sp_pressure", f"{self.PRESSURE_MAX:.1f}"))
        setpoint_layout.addLayout(self._create_display_field("SRV-A Vent (°C):", "sp_temp", f"{self.TEMP_MAX:.1f}"))
        setpoint_layout.addLayout(
            self._create_display_field("SRV-B Load Target (kg):", "sp_load", f"{self.LOAD_TARGET:.1f}"))
        setpoint_layout.addStretch()

        left_column.addWidget(sensor_group, 2)
        left_column.addWidget(setpoint_group, 1)
        layout.addLayout(left_column, 1)

        # --- 2. Actuators and Outputs (Right Side) ---
        output_container = QGroupBox("Outputs & Actuators (Click to Override)")
        output_layout = QVBoxLayout(output_container)

        # P&ID Placeholder (Top Area)
        pid_placeholder = QLabel("P&ID Visualization Area [Image of Process and Instrumentation Diagram]")
        pid_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pid_placeholder.setStyleSheet(
            "background-color: #374151; border: 2px dashed #4B5563; padding: 50px; min-height: 200px;")
        output_layout.addWidget(pid_placeholder)

        # Actuator Controls Grid (Bottom Area)
        actuator_grid = QGridLayout()

        # Define output components and their associated SVG function
        output_components = {
            'V-101': (get_valve_svg, 'V_101_open', "Main Valve"),
            'IGN-E': (get_igniter_svg, 'IGN_E_active', "Igniter"),
            'SRV-A': (get_servo_svg, 'servo_A_on', "Vent Servo"),
            'SRV-B': (get_servo_svg, 'servo_B_on', "Load Servo"),
            'SRV-C': (get_servo_svg, 'servo_C_on', "Servo C"),
            'SRV-D': (get_servo_svg, 'servo_D_on', "Servo D"),
        }

        for i, (comp_id, (svg_func, state_key_prefix, title)) in enumerate(output_components.items()):
            box = QGroupBox(f"{comp_id} - {title}")
            vbox = QVBoxLayout(box)

            # 1. Clickable SVG Widget
            widget = OutputSvgWidget(component_id=comp_id)
            widget.clicked.connect(self.handle_output_toggle)
            vbox.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)
            self.output_widgets[comp_id] = {'widget': widget, 'status': QLabel(), 'svg_func': svg_func,
                                            'key_prefix': state_key_prefix}

            # 2. Status Label
            status_label = self.output_widgets[comp_id]['status']
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(status_label)

            # Add to grid
            row = i // 3
            col = i % 3
            actuator_grid.addWidget(box, row, col)

        output_layout.addLayout(actuator_grid)
        layout.addWidget(output_container, 2)
        return main_page

    def _create_sensor_gauge(self, title: str, component_id: str, svg_func: callable, initial_value: float,
                             fixed_width: int, fixed_height: int) -> QGroupBox:
        """Dynamically creates a sensor display group for the Data tab."""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # SVG Widget
        svg_widget = QSvgWidget()
        svg_widget.setFixedSize(fixed_width, fixed_height)
        svg_widget.load(QByteArray(svg_func(initial_value).encode('utf-8')))

        # Label Widget
        label = QLabel(f"{initial_value:.1f}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 20px; font-weight: bold; margin-top: 5px;")

        # Store references in the class dictionary
        self.gauge_widgets[component_id] = {'svg': svg_widget, 'label': label, 'svg_func': svg_func}

        layout.addWidget(svg_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addStretch()

        return group

    def _create_data_view(self) -> QWidget:
        """Creates the 'Data' view with detailed sensor information using all 9 gauges."""
        data_page = QWidget()
        main_layout = QVBoxLayout(data_page)

        sensor_grid_layout = QGridLayout()

        # Display 7 pressure transducers, 1 temp, 1 load (9 total) in a 3x3 or similar grid
        i = 0
        for key in self.sensor_keys:
            name, unit, max_val, svg_func = self.sensor_map[key]
            initial_value = self.state[key]

            # Adjust dimensions based on sensor type for best visualization
            width = 100 if key == 'T_202' else 150
            height = 150 if key == 'T_202' else 150

            group = self._create_sensor_gauge(
                f"{name}",
                key,
                svg_func,
                initial_value,
                width,
                height
            )

            # Arrange in a 3-column layout
            row = i // 3
            col = i % 3
            sensor_grid_layout.addWidget(group, row, col)
            i += 1

        main_layout.addLayout(sensor_grid_layout)
        main_layout.addStretch()

        return data_page

    def _create_graph_view(self) -> QWidget:
        """
        Creates the 'Graph' view for custom plotting integration.
        """
        graph_page = QWidget()
        col_layout = QVBoxLayout(graph_page)

        graph_group = QGroupBox("Custom Data Trend")
        graph_layout = QVBoxLayout()

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1F2937')

        self.plot_widget.setLabel('left', "Y-Axis Value", units='Units')
        self.plot_widget.setLabel('bottom', "Time / Index")

        axis_pen = pg.mkPen(color='#9CA3AF')
        text_pen = pg.mkPen(color='#F3F4F6')
        self.plot_widget.getAxis('left').setPen(axis_pen)
        self.plot_widget.getAxis('left').setTextPen(text_pen)
        self.plot_widget.getAxis('bottom').setPen(axis_pen)
        self.plot_widget.getAxis('bottom').setTextPen(text_pen)

        # Initialize plot line with empty data
        self.data_line = self.plot_widget.plot(
            [],
            [],
            pen=pg.mkPen(color='#3B82F6', width=2)
        )

        graph_layout.addWidget(self.plot_widget)
        graph_group.setLayout(graph_layout)
        col_layout.addWidget(graph_group)
        col_layout.setStretchFactor(graph_group, 1)

        return graph_page

    # --- Core Integration Function ---

    def read_microcontroller_data(self) -> Dict[str, float]:
        """
        *** INTEGRATION POINT FOR YOUR SCRIPTS ***

        Replace the logic inside this function with your actual code
        to read from the microcontroller (e.g., Serial, TCP/IP, Bluetooth).

        The function must return a dictionary with keys matching the sensor_keys list:
        P_101 to P_107, T_202, and L_301.
        """
        new_data: Dict[str, float] = {}

        # Simulate Pressure changes (7 sensors)
        for i in range(1, 8):
            key = f'P_{100 + i}'
            old_val = self.state.get(key, 50.0)
            new_val = old_val + random.uniform(-1.5, 1.5)
            # Enforce boundary: 0 to 200 PSI
            new_data[key] = max(0.0, min(200.0, new_val))

        # Simulate Temperature change
        t_key = 'T_202'
        old_temp = self.state.get(t_key, 20.0)
        # IGNITER EFFECT: If igniter is ON, temperature increases slightly faster
        temp_change_rate = 0.5 if self.state.get('IGN_E_active', False) else 0.2
        new_temp = old_temp + random.uniform(-temp_change_rate, temp_change_rate)
        new_data[t_key] = max(0.0, min(100.0, new_temp))

        # Simulate Load change
        l_key = 'L_301'
        old_load = self.state.get(l_key, 100.0)
        new_load = old_load + random.uniform(-3.0, 3.0)
        new_data[l_key] = max(0.0, min(1000.0, new_load))

        return new_data

    # --- Manual Override Handler (Generic) ---

    def handle_output_toggle(self, component_id: str):
        """Toggles the state of a valve, igniter, or servo."""

        if component_id == 'V-101':
            key = 'V_101_open'
            new_state = not self.state[key]
            self.state[key] = new_state
            status = 'OPEN' if new_state else 'CLOSED'
            print(f"!!! MANUAL OVERRIDE !!! Valve V-101 set to {status}")

        elif component_id == 'IGN-E':
            # --- IGNITER LATCHING TOGGLE LOGIC (As requested) ---
            key = 'IGN_E_active'
            new_state = not self.state[key]
            self.state[key] = new_state
            status = 'ACTIVE' if new_state else 'INACTIVE'
            print(f"!!! MANUAL OVERRIDE !!! Igniter IGN-E set to {status}")

        elif component_id.startswith('SRV'):
            # Servo Toggle Logic
            key_letter = component_id.split('-')[1]  # Extracts 'A', 'B', etc.
            key_on = f'servo_{key_letter}_on'
            key_angle = f'servo_{key_letter}_angle'

            new_state = not self.state[key_on]
            self.state[key_on] = new_state
            self.state[key_angle] = 45 if new_state else 0  # Set default angle if ON
            status = 'ON' if new_state else 'OFF'
            print(f"!!! MANUAL OVERRIDE !!! Servo {component_id} set to {status}")

        self.update_output_visuals()

    # --- Control & Update Logic ---

    def run_control_logic(self, sensor_data: Dict[str, float]):
        """Runs the control logic based on the latest sensor values."""
        new_state = {}

        p_101 = sensor_data['P_101']
        t_202 = sensor_data['T_202']
        l_301 = sensor_data['L_301']

        # 1. Valve V-101 Control Logic (P-101 Safety Trip)
        if p_101 > self.PRESSURE_MAX:
            new_state['V_101_open'] = False
            self.status_label.setText(f"P-101 ALERT! V-101 Closed ({p_101:.1f} PSI).")
            self.status_light.setStyleSheet("background-color: #EF4444; border-radius: 10px;")
        else:
            new_state['V_101_open'] = self.state.get('V_101_open', True)  # Keep existing state if not over-pressure
            if self.status_light.styleSheet().find("#EF4444") == -1:  # Only change if not already an alert
                self.status_label.setText("System Control Active")
                self.status_light.setStyleSheet("background-color: #10B981; border-radius: 10px;")

        # 2. Igniter IGN-E Control Logic (REMOVED: Retained for manual control only)
        # The state for IGN_E_active is retained from the manual toggle (self.state)

        # 3. Servo SRV-A Control Logic (Temperature Venting)
        if t_202 > self.TEMP_MAX:
            new_state['servo_A_on'] = True
            new_state['servo_A_angle'] = 90
        else:
            new_state['servo_A_on'] = False
            new_state['servo_A_angle'] = 0

        # 4. Servo SRV-B Control Logic (Load Management)
        if l_301 > self.LOAD_TARGET:
            new_state['servo_B_on'] = True
            # Simple proportional error: (Current - Target) / 200 * 90 degrees max
            angle = int(min(90, max(0, ((l_301 - self.LOAD_TARGET) / 200.0) * 90)))
            new_state['servo_B_angle'] = angle
        else:
            new_state['servo_B_on'] = False
            new_state['servo_B_angle'] = 0

        # Servos C and D are left for manual override/custom logic

        self.state.update(new_state)

    def poll_and_update_system(self):
        """Reads new data, runs control logic, and updates the UI."""

        # 1. READ DATA (Your script goes here)
        try:
            new_sensor_data = self.read_microcontroller_data()
            self.state.update(new_sensor_data)
        except Exception as e:
            print(f"Failed to read data from script: {e}")
            return

        # 2. RUN CONTROL LOGIC
        self.run_control_logic(new_sensor_data)

        # 3. UPDATE VISUALS
        self.update_sensor_visuals()
        self.update_output_visuals()
        self.update_graph()

    def update_sensor_visuals(self):
        """Updates all sensor values and gauges across the 'Main' and 'Data' tabs."""

        for key in self.sensor_keys:
            p = self.state[key]
            name, unit, max_val, svg_func = self.sensor_map[key]

            # Update Main View Display Labels
            if key in self.sensor_widgets:
                self.sensor_widgets[key].setText(f"{p:.1f} {unit}")

            # Update Data View Gauges
            if key in self.gauge_widgets:
                svg_data = svg_func(p, max_val)
                self.gauge_widgets[key]['svg'].load(QByteArray(svg_data.encode('utf-8')))
                self.gauge_widgets[key]['label'].setText(f"{p:.1f} {unit}")

    def update_output_visuals(self):
        """Updates all actuator SVGs and status labels."""

        for comp_id, item in self.output_widgets.items():
            widget = item['widget']
            status_label = item['status']
            svg_func = item['svg_func']

            if comp_id == 'V-101':
                is_open = self.state['V_101_open']
                svg_data = svg_func(is_open)
                status = "OPEN (NORMAL)" if is_open else "CLOSED (SAFETY)"
                color = "#10B981" if is_open else "#EF4444"
                widget.setLineWidth(4) if not is_open else widget.setLineWidth(2)

            elif comp_id == 'IGN-E':
                is_active = self.state['IGN_E_active']
                svg_data = svg_func(is_active)
                status = "ACTIVE" if is_active else "INACTIVE"
                color = "#F59E0B" if is_active else "#9CA3AF"

            elif comp_id.startswith('SRV'):
                # Servo Logic for SRV-A, SRV-B, SRV-C, SRV-D
                key_letter = comp_id.split('-')[1]  # Extracts 'A', 'B', etc.
                key_on = f'servo_{key_letter}_on'
                key_angle = f'servo_{key_letter}_angle'

                is_on = self.state[key_on]
                angle = self.state[key_angle]
                svg_data = svg_func(is_on, angle)
                status = f"ACTIVE ({angle}°)" if is_on else f"INACTIVE ({angle}°)"
                color = "#3B82F6" if is_on else "#9CA3AF"

            widget.load_svg(svg_data)
            status_label.setText(status)
            status_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")

    def update_graph(self):
        """
        Updates the graph using the pyqtgraph object. This is called every 2 seconds.
        """
        ###################################################################################
        ###                                                                             ###
        ###                    <--- GRAPH PLOTTING INTEGRATION POINT --->               ###
        ###                                                                             ###
        ###################################################################################

        # Example: Plotting P-101 over time. In a real app, you would manage a history buffer.
        # For simplicity, let's plot a few simulated points relative to current state.

        if not hasattr(self, '_graph_history_x'):
            self._graph_history_x = [0]
            self._graph_history_y = [self.state['P_101']]

        # Add new point (X: time index, Y: P-101 value)
        current_index = self._graph_history_x[-1] + 1
        self._graph_history_x.append(current_index)
        self._graph_history_y.append(self.state['P_101'])

        # Keep only the last 50 points
        if len(self._graph_history_x) > 50:
            self._graph_history_x = self._graph_history_x[-50:]
            self._graph_history_y = self._graph_history_y[-50:]
            # Recalculate X values to start from 0 for the visual range
            base_x = self._graph_history_x[0]
            display_x = [x - base_x for x in self._graph_history_x]
        else:
            display_x = self._graph_history_x

        self.data_line.setData(display_x, self._graph_history_y)
        self.plot_widget.setTitle(f"P-101 Trend (Current: {self.state['P_101']:.1f} PSI)")


# -------------------------------------------------------------------------------
# Main Execution
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    # Ensure correct scaling for high-DPI screens
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    window = DashboardWindow()
    window.show()
    sys.exit(app.exec())