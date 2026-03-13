from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox


class TemplateDialog(QDialog):
    def __init__(self, parent=None, name: str = "", description: str | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Шаблон")

        layout = QFormLayout(self)

        self.name_edit = QLineEdit(name)
        self.desc_edit = QTextEdit(description or "")

        layout.addRow("Название:", self.name_edit)
        layout.addRow("Описание:", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> tuple[str, str | None]:
        name = self.name_edit.text().strip()
        desc = self.desc_edit.toPlainText().strip() or None
        return name, desc