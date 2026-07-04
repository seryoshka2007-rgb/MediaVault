"""Add/edit dialog for a single library entry. Talks only in DTOs (core.schemas)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from core.enums import ENTRY_TYPE_LABELS_RU, STATUS_LABELS_RU, EntryType, Status
from core.schemas import EntryCreate, EntryRead, EntryUpdate
from core.validators.url_validator import is_valid_url

_NO_VALUE = -1  # spinbox sentinel meaning "not set" -> None


def _spin_no_value(minimum: int, maximum: int) -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(_NO_VALUE, maximum)
    spin.setSpecialValueText("—")
    spin.setValue(_NO_VALUE)
    return spin


class EntryDialog(QDialog):
    """Form for creating a new entry or editing an existing one."""

    def __init__(self, parent: object = None, *, entry: EntryRead | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._entry = entry
        self.setWindowTitle("Изменить запись" if entry else "Добавить запись")
        self._build_ui()
        if entry is not None:
            self._prefill(entry)
        else:
            self._on_type_changed()

    def _build_ui(self) -> None:
        form = QFormLayout()

        self._title = QLineEdit()
        form.addRow("Название*", self._title)

        self._original_title = QLineEdit()
        form.addRow("Оригинальное название", self._original_title)

        self._type = QComboBox()
        for entry_type in EntryType:
            self._type.addItem(ENTRY_TYPE_LABELS_RU[entry_type], entry_type)
        self._type.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Тип", self._type)

        self._url = QLineEdit()
        form.addRow("Ссылка", self._url)

        self._status = QComboBox()
        for status in Status:
            self._status.addItem(STATUS_LABELS_RU[status], status)
        form.addRow("Статус", self._status)

        self._year = _spin_no_value(1870, 2100)
        form.addRow("Год выпуска", self._year)

        self._rating = _spin_no_value(0, 10)
        form.addRow("Моя оценка", self._rating)

        self._rating_other = _spin_no_value(0, 10)
        form.addRow("Оценка (др. ПК)", self._rating_other)

        self._season = _spin_no_value(0, 9999)
        form.addRow("Сезон", self._season)

        self._episode = _spin_no_value(0, 9999)
        form.addRow("Серия", self._episode)

        self._is_favorite = QCheckBox("Избранное")
        form.addRow(self._is_favorite)

        self._description = QLineEdit()
        form.addRow("Описание", self._description)

        self._comment = QLineEdit()
        form.addRow("Комментарий", self._comment)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(buttons)

    def _on_type_changed(self) -> None:
        episodic = self._type.currentData().is_episodic
        self._season.setEnabled(episodic)
        self._episode.setEnabled(episodic)

    def _prefill(self, entry: EntryRead) -> None:
        self._title.setText(entry.title)
        self._original_title.setText(entry.original_title or "")
        self._type.setCurrentIndex(self._type.findData(entry.type))
        self._type.setEnabled(False)  # type is immutable after creation (EntryUpdate has no `type`)
        self._url.setText(entry.url or "")
        self._status.setCurrentIndex(self._status.findData(entry.status))
        self._year.setValue(entry.year if entry.year is not None else _NO_VALUE)
        self._rating.setValue(entry.rating if entry.rating is not None else _NO_VALUE)
        self._rating_other.setValue(
            entry.rating_other if entry.rating_other is not None else _NO_VALUE
        )
        self._season.setValue(entry.season if entry.season is not None else _NO_VALUE)
        self._episode.setValue(entry.episode if entry.episode is not None else _NO_VALUE)
        self._is_favorite.setChecked(entry.is_favorite)
        self._description.setText(entry.description or "")
        self._comment.setText(entry.comment or "")
        self._on_type_changed()

    def _on_accept(self) -> None:
        if not self._title.text().strip():
            QMessageBox.warning(self, "Проверка", "Название не может быть пустым.")
            return
        url = self._url.text().strip() or None
        if url and not is_valid_url(url):
            QMessageBox.warning(self, "Проверка", "Ссылка выглядит некорректно.")
            return
        self.accept()

    @staticmethod
    def _none_if_unset(value: int) -> int | None:
        return None if value == _NO_VALUE else value

    def to_create(self) -> EntryCreate:
        return EntryCreate(
            type=self._type.currentData(),
            title=self._title.text().strip(),
            original_title=self._original_title.text().strip() or None,
            status=self._status.currentData(),
            rating=self._none_if_unset(self._rating.value()),
            rating_other=self._none_if_unset(self._rating_other.value()),
            year=self._none_if_unset(self._year.value()),
            url=self._url.text().strip() or None,
            description=self._description.text().strip() or None,
            comment=self._comment.text().strip() or None,
            is_favorite=self._is_favorite.isChecked(),
            season=self._none_if_unset(self._season.value()),
            episode=self._none_if_unset(self._episode.value()),
        )

    def to_update(self) -> EntryUpdate:
        return EntryUpdate(
            title=self._title.text().strip(),
            original_title=self._original_title.text().strip() or None,
            status=self._status.currentData(),
            rating=self._none_if_unset(self._rating.value()),
            rating_other=self._none_if_unset(self._rating_other.value()),
            year=self._none_if_unset(self._year.value()),
            url=self._url.text().strip() or None,
            description=self._description.text().strip() or None,
            comment=self._comment.text().strip() or None,
            is_favorite=self._is_favorite.isChecked(),
            season=self._none_if_unset(self._season.value()),
            episode=self._none_if_unset(self._episode.value()),
        )
