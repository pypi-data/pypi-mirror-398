import sys
from PyQt6.QtWidgets import QApplication
from pyscreeps_arena.ui.qmapker.qmapmarker import QPSAMapMarker


def run_mapviewer():
    app = QApplication(sys.argv)
    window = QPSAMapMarker()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run_mapviewer()
