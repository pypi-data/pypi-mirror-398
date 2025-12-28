import sys
from PyQt6.QtWidgets import QApplication
from pyscreeps_arena.ui.qcreeplogic import QPSACreepLogic



def run_creeplogic_edit():
    app = QApplication(sys.argv)
    window = QPSACreepLogic()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    run_creeplogic_edit()
