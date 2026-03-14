from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
)

from app.infrastructure.db.repositories.template_repo import TemplateRepository


class PartDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        selected_template_id: int | None = None,
        name: str = "",
        serial_number: str | None = None,
        installation_place: str | None = None,
        notes: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Деталь")

        self.template_repo = TemplateRepository()
        self._templates = list(self.template_repo.list())

        layout = QFormLayout(self)

        self.template_combo = QComboBox()
        for t in self._templates:
            self.template_combo.addItem(t.name, userData=t.id)

        if selected_template_id is not None:
            idx = self._index_of_template(selected_template_id)
            if idx >= 0:
                self.template_combo.setCurrentIndex(idx)

        self.name_edit = QLineEdit(name)
        self.serial_edit = QLineEdit(serial_number or "")
        self.place_edit = QLineEdit(installation_place or "")
        self.notes_edit = QTextEdit(notes or "")

        layout.addRow("Шаблон:", self.template_combo)
        layout.addRow("Название детали:", self.name_edit)
        layout.addRow("Серийный номер:", self.serial_edit)
        layout.addRow("Место установки:", self.place_edit)
        layout.addRow("Примечание:", self.notes_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _index_of_template(self, template_id: int) -> int:
        for i in range(self.template_combo.count()):
            if self.template_combo.itemData(i) == template_id:
                return i
        return -1

    def has_templates(self) -> bool:
        return len(self._templates) > 0

    def get_data(self) -> tuple[int, str, str | None, str | None, str | None]:
        template_id = int(self.template_combo.currentData())
        name = self.name_edit.text().strip()
        serial = self.serial_edit.text().strip() or None
        place = self.place_edit.text().strip() or None
        notes = self.notes_edit.toPlainText().strip() or None
        return template_id, name, serial, place, notes