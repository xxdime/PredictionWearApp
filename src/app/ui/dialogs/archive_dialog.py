from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)


class ArchiveDialog(QDialog):
    """Dialog for specifying the archive destination directory and name."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Создать архив")
        self.setMinimumWidth(420)

        layout = QFormLayout(self)

        # Directory row
        dir_row = QHBoxLayout()
        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText("Выберите папку…")
        btn_browse = QPushButton("Обзор…")
        btn_browse.clicked.connect(self._browse_directory)
        dir_row.addWidget(self._dir_edit)
        dir_row.addWidget(btn_browse)
        layout.addRow("Папка сохранения:", dir_row)

        # Archive name row
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("название_архива")
        layout.addRow("Название архива:", self._name_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _browse_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if path:
            self._dir_edit.setText(path)

    def _on_accept(self) -> None:
        if not self._dir_edit.text().strip():
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Архив", "Укажите папку для сохранения.")
            return
        if not self._name_edit.text().strip():
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Архив", "Укажите название архива.")
            return
        self.accept()

    def get_data(self) -> tuple[str, str]:
        """Return (directory, archive_name)."""
        return self._dir_edit.text().strip(), self._name_edit.text().strip()
