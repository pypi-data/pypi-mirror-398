import sys, os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QCheckBox, QSpinBox, QProgressBar, QMenu, QMessageBox,
    QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal

from wincp.utils import build_tree_raw, save_archive, load_archive


# ---------------- Worker ----------------
class CompressWorker(QThread):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, folder, output, password=None, level=9, icon_path=None, icon_enable=True):
        super().__init__()
        self.folder = folder
        self.output = output
        self.password = password
        self.level = level
        self.icon_path = icon_path
        self.icon_enable = icon_enable

    def run(self):
        try:
            tree = build_tree_raw(self.folder)
            file_count = sum(1 for _ in self.iter_files(tree))
            processed = 0
            for node in self.iter_files(tree):
                processed += 1
                self.progress.emit(int(processed / file_count * 100))
            save_archive(tree, self.output, password=self.password,
                         compress_level=self.level, icon_path=self.icon_path,
                         icon_enable=self.icon_enable)
            self.finished.emit(self.output)
        except Exception as e:
            self.error.emit(str(e))

    def iter_files(self, node):
        if node["type"] == "file":
            yield node
        elif node["type"] == "dir":
            for c in node.get("children", []):
                yield from self.iter_files(c)


# ---------------- Main GUI ----------------
class CMPApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WinCP - Secure Compressor")
        self.resize(950, 650)

        self.icon_path = None
        self.icon_enable = True
        self.opened_tree = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab_compress = QWidget()
        self.tab_extract = QWidget()

        self.tabs.addTab(self.tab_compress, "Compress")
        self.tabs.addTab(self.tab_extract, "Extract")

        self.init_compress_tab()
        self.init_extract_tab()

        self.setAcceptDrops(True)

    # ---------------- Compress Tab ----------------
    def init_compress_tab(self):
        layout = QVBoxLayout()

        fg = QGroupBox("Folder")
        fl = QHBoxLayout()
        self.folder_entry = QLineEdit()
        fl.addWidget(self.folder_entry)
        btn = QPushButton("Browse")
        btn.clicked.connect(self.select_folder)
        fl.addWidget(btn)
        fg.setLayout(fl)
        layout.addWidget(fg)

        sg = QGroupBox("Settings")
        sl = QHBoxLayout()

        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 9)
        self.level_spin.setValue(9)

        self.pass_check = QCheckBox("Password")
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setEnabled(False)
        self.pass_check.stateChanged.connect(
            lambda _: self.pass_edit.setEnabled(self.pass_check.isChecked())
        )

        self.icon_btn = QPushButton("Select Icon")
        self.icon_btn.clicked.connect(self.select_icon)

        self.icon_enable_cb = QCheckBox("Enable Icon")
        self.icon_enable_cb.setChecked(True)
        self.icon_enable_cb.stateChanged.connect(
            lambda _: setattr(self, "icon_enable", self.icon_enable_cb.isChecked())
        )

        sl.addWidget(QLabel("Level"))
        sl.addWidget(self.level_spin)
        sl.addWidget(self.pass_check)
        sl.addWidget(self.pass_edit)
        sl.addWidget(self.icon_btn)
        sl.addWidget(self.icon_enable_cb)
        sg.setLayout(sl)
        layout.addWidget(sg)

        og = QGroupBox("Output")
        ol = QHBoxLayout()
        self.output_entry = QLineEdit()
        ol.addWidget(self.output_entry)
        ob = QPushButton("Browse")
        ob.clicked.connect(self.select_output)
        ol.addWidget(ob)
        og.setLayout(ol)
        layout.addWidget(og)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        run = QPushButton("Compress")
        run.clicked.connect(self.start_compress)
        layout.addWidget(run)

        self.tab_compress.setLayout(layout)

    # ---------------- Extract Tab ----------------
    def init_extract_tab(self):
        layout = QVBoxLayout()
        hl = QHBoxLayout()
        self.cmp_entry = QLineEdit()
        hl.addWidget(self.cmp_entry)
        b = QPushButton("Browse")
        b.clicked.connect(self.select_cmp_file)
        hl.addWidget(b)
        layout.addLayout(hl)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        layout.addWidget(self.tree)
        self.tab_extract.setLayout(layout)

    # ---------------- Actions ----------------
    def select_folder(self):
        p = QFileDialog.getExistingDirectory(self, "Select Folder")
        if p:
            self.folder_entry.setText(p)

    def select_output(self):
        p, _ = QFileDialog.getSaveFileName(self, "Output", "", "CMP (*.cmp)")
        if p:
            self.output_entry.setText(p)

    def select_icon(self):
        p, _ = QFileDialog.getOpenFileName(self, "Icon", "", "Icons (*.ico *.png)")
        if p:
            self.icon_path = p

    def start_compress(self):
        try:
            worker = CompressWorker(
                self.folder_entry.text(),
                self.output_entry.text(),
                self.pass_edit.text() if self.pass_check.isChecked() else None,
                self.level_spin.value(),
                self.icon_path,
                self.icon_enable
            )
            worker.progress.connect(self.progress.setValue)
            worker.finished.connect(lambda f: QMessageBox.information(self, "WinCP", f"Compressed to {f}"))
            worker.error.connect(lambda e: QMessageBox.critical(self, "WinCP Error", e))
            worker.start()
        except Exception as e:
            QMessageBox.critical(self, "WinCP Error", str(e))

    # ---------------- Extract ----------------
    def select_cmp_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CMP File", "", "CMP Archive (*.cmp)")
        if path:
            self.cmp_entry.setText(path)
            self.open_cmp(path)

    def open_cmp(self, path):
        try:
            archive = load_archive(path)
            self.opened_tree = archive["tree"]
            self.populate_tree(self.opened_tree)
        except Exception as e:
            QMessageBox.critical(self, "WinCP Error", f"Cannot open file: {e}")

    def populate_tree(self, tree):
        self.tree.clear()
        def add_items(parent, node):
            item = QTreeWidgetItem([node["name"]])
            if parent:
                parent.addChild(item)
            else:
                self.tree.addTopLevelItem(item)
            if node["type"] == "dir":
                for c in node.get("children", []):
                    add_items(item, c)
        add_items(None, tree)
        self.tree.expandAll()

    # ---------------- Context Menu ----------------
    def show_tree_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if item:
            menu = QMenu()
            extract_action = menu.addAction("Extract")
            extract_action.triggered.connect(lambda: self.extract_item(item))
            menu.exec(self.tree.viewport().mapToGlobal(pos))

    def extract_item(self, item):
        folder = QFileDialog.getExistingDirectory(self, "Select folder to extract")
        if not folder:
            return

        path_parts = []
        current = item
        while current:
            path_parts.insert(0, current.text(0))
            current = current.parent()

        node = self.find_node_by_path(self.opened_tree, path_parts)
        if not node:
            QMessageBox.critical(self, "WinCP Error", "Node not found")
            return

        try:
            self.extract_node(node, folder)
            QMessageBox.information(self, "WinCP", f"Extraction complete to {folder}")
        except Exception as e:
            QMessageBox.critical(self, "WinCP Error", str(e))

    def find_node_by_path(self, node, path_parts):
        if not path_parts or node["name"] != path_parts[0]:
            return None
        if len(path_parts) == 1:
            return node
        for c in node.get("children", []):
            result = self.find_node_by_path(c, path_parts[1:])
            if result:
                return result
        return None

    def extract_node(self, node, target_folder, rel_path=""):
        import os
        if node["type"] == "file":
            out_path = os.path.join(target_folder, rel_path, node["name"])
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(node["content"])
        elif node["type"] == "dir":
            folder_path = os.path.join(target_folder, rel_path, node["name"])
            os.makedirs(folder_path, exist_ok=True)
            for c in node.get("children", []):
                self.extract_node(c, target_folder, os.path.join(rel_path, node["name"]))

    # ---------------- Drag & Drop ----------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".cmp"):
                self.cmp_entry.setText(path)
                self.open_cmp(path)


# ---------------- Entry ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CMPApp()
    window.show()
    sys.exit(app.exec())
