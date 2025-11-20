import sys
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject, QEvent
from PyQt6.QtGui import QTransform, QColor
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QMainWindow
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem


class GraphicsClickFilter(QObject):
    clicked = pyqtSignal(object)   # emits the item that was clicked

    def __init__(self, target_item, parent=None):
        super().__init__(parent)
        self.target_item = target_item
    # ChatGPT magic because I couldn't figure out how to get this to work for the life of me

    def eventFilter(self, watched, event):
        # This filter is installed on the SCENE, so 'watched' is a QGraphicsScene
        if event.type() == QEvent.Type.GraphicsSceneMousePress and event.button() == Qt.MouseButton.LeftButton:
            # Which item is under the mouse?
            item = watched.itemAt(event.scenePos(), QTransform())
            if item is self.target_item:
                self.clicked.emit(self.target_item)
        return False  # allow normal handling to continue


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        screen_size = self.screen().availableGeometry()
        self.screen_height = screen_size.height() - 28
        self.screen_width = screen_size.width() - 50

        scene = QGraphicsScene()
        view = QGraphicsView(scene)
        view.setBackgroundBrush(QColor("#222222"))

        # background SVG
        path = "SVGs/Rocket_P&ID_GUI1.svg"  # loads the svg from the file path
        bg_rend = QSvgRenderer(path)
        bg_item = QGraphicsSvgItem()
        bg_item.setSharedRenderer(bg_rend)  # rendering the main svg to the background of the page

        # dimensioning
        svg_h = bg_item.boundingRect().height()  # gets the height in pixels from the background svg
        svg_w = bg_item.boundingRect().width()
        if svg_w < svg_h:
            scaling = self.screen_height / svg_h
            bg_item.setScale(scaling)
        elif svg_h < svg_w:
            scaling = self.screen_width / svg_w
            bg_item.setScale(scaling)

        scene.addItem(bg_item)
        self.setCentralWidget(view)

        # valve SVG
        valve_path = "SVGs/BallValveSchematic.svg" # load in valve SVG file
        self.valve_item1 = QGraphicsSvgItem(valve_path)
        self.valve_item2 = QGraphicsSvgItem(valve_path)
        self.valve_item3 = QGraphicsSvgItem(valve_path)
        self.valve_item4 = QGraphicsSvgItem(valve_path)
        self.valve_item5 = QGraphicsSvgItem(valve_path)
        self.valve_item6 = QGraphicsSvgItem(valve_path)
        self.valve_item7 = QGraphicsSvgItem(valve_path)

        scaling_valve = 1  # apparent size of the valve on screen

        self.valve_item1.setScale(scaling_valve)
        self.valve_item1.setElementId("OPEN")
        self.valve_item2.setScale(scaling_valve)
        self.valve_item2.setElementId("OPEN")
        self.valve_item3.setScale(scaling_valve)
        self.valve_item3.setElementId("OPEN")
        self.valve_item4.setScale(scaling_valve)
        self.valve_item4.setElementId("OPEN")
        self.valve_item5.setScale(scaling_valve)
        self.valve_item5.setElementId("OPEN")
        self.valve_item6.setScale(scaling_valve)
        self.valve_item6.setElementId("OPEN")
        self.valve_item7.setScale(scaling_valve)
        self.valve_item7.setElementId("OPEN")

        scene.addItem(self.valve_item1)  # adds the valve to the scene
        scene.addItem(self.valve_item2)
        scene.addItem(self.valve_item3)
        scene.addItem(self.valve_item4)
        scene.addItem(self.valve_item5)
        scene.addItem(self.valve_item6)
        scene.addItem(self.valve_item7)

        # valve 1 position
        self.valve_item1.setPos(215, 108)
        # valve 2 position
        self.valve_item2.setPos(460, 207)
        self.valve_item2.setRotation(90)
        # valve 3 position
        self.valve_item3.setPos(1099, 288)
        # valve 4 position
        self.valve_item4.setPos(370, 645)
        self.valve_item4.setRotation(90)
        # valve 5 position
        self.valve_item5.setPos(550, 645)
        self.valve_item5.setRotation(90)
        # valve 6 position
        self.valve_item6.setPos(822, 630)
        self.valve_item6.setRotation(90)
        # valve 7 position
        self.valve_item7.setPos(1099, 468)

        # click handling (install QObject filter on the SCENE, not the item)
        self.click_filter1 = GraphicsClickFilter(self.valve_item1, self)
        self.click_filter2 = GraphicsClickFilter(self.valve_item2, self)
        self.click_filter3 = GraphicsClickFilter(self.valve_item3, self)
        self.click_filter4 = GraphicsClickFilter(self.valve_item4, self)
        self.click_filter5 = GraphicsClickFilter(self.valve_item5, self)
        self.click_filter6 = GraphicsClickFilter(self.valve_item6, self)
        self.click_filter7 = GraphicsClickFilter(self.valve_item7, self)

        scene.installEventFilter(self.click_filter1)
        scene.installEventFilter(self.click_filter2)
        scene.installEventFilter(self.click_filter3)
        scene.installEventFilter(self.click_filter4)
        scene.installEventFilter(self.click_filter5)
        scene.installEventFilter(self.click_filter6)
        scene.installEventFilter(self.click_filter7)

        self.click_filter1.clicked.connect(self.toggle_valve)
        self.click_filter2.clicked.connect(self.toggle_valve)
        self.click_filter3.clicked.connect(self.toggle_valve)
        self.click_filter4.clicked.connect(self.toggle_valve)
        self.click_filter5.clicked.connect(self.toggle_valve)
        self.click_filter6.clicked.connect(self.toggle_valve)
        self.click_filter7.clicked.connect(self.toggle_valve)

        self.initUI()

    def initUI(self):
        screen_size = self.screen().availableGeometry()
        self.setFixedSize(screen_size.width(), screen_size.height() - 28)
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def toggle_valve(self, item: QGraphicsSvgItem):
        old_bounds = item.mapToScene(item.boundingRect()).boundingRect()  # get current center in scene coordinates
        old_center = old_bounds.center()
        # toggle the element
        if item.elementId() == "OPEN":
            item.setElementId("CLOSED")
        else:
            item.setElementId("OPEN")
        new_bounds = item.mapToScene(item.boundingRect()).boundingRect()  # get new bounds after switching
        new_center = new_bounds.center()
        delta = old_center - new_center
        item.setPos(item.pos() + delta)  # shift time back


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
