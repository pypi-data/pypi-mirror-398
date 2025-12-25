from wincp.cli import cli_main
from wincp.app import CMPApp

def main():
    import sys
    if len(sys.argv) > 1:
        cli_main()
    else:
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = CMPApp()
        window.show()
        sys.exit(app.exec())
