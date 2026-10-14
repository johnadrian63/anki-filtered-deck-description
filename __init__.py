from aqt import mw, gui_hooks
from aqt.filtered_deck import FilteredDeckConfigDialog
from aqt.qt import (QLabel, QPlainTextEdit, QBoxLayout, QTimer,
                    QPushButton, QHBoxLayout, QWidget)
from aqt.utils import tooltip
import html

CONFIG_KEY = "filtered_deck_descriptions"


def _notes():
    return mw.col.get_config(CONFIG_KEY, {})


def _store(deck_id, text):
    notes = _notes()
    if text.strip():
        notes[str(deck_id)] = text
    else:
        notes.pop(str(deck_id), None)
    mw.col.set_config(CONFIG_KEY, notes)


def _dialog_deck_id(dlg):
    deck = getattr(dlg, "_deck", None)
    did = getattr(deck, "id", 0) if deck else 0
    if not did:
        did = getattr(dlg, "deck_id", 0) or 0
    if not did:
        current = mw.col.decks.current()
        if current.get("dyn"):
            did = current["id"]
    return did


def _save_now(dlg):
    did = getattr(dlg, "_desc_deck_id", 0)
    if not did:
        tooltip("Build this deck once first, then you can save its description.",
                parent=dlg)
        return
    _store(did, dlg._desc_box.toPlainText())
    tooltip("Description saved", parent=dlg)
    try:
        mw.overview.refresh()
    except Exception:
        pass


def _add_box(dlg):
    layout = dlg.layout()
    if not isinstance(layout, QBoxLayout):
        return
    did = _dialog_deck_id(dlg)
    dlg._desc_deck_id = did

    label = QLabel("<b>Description</b>")
    box = QPlainTextEdit()
    box.setMinimumHeight(110)
    box.setPlaceholderText("Notes, card IDs, questions...")
    if did:
        box.setPlainText(_notes().get(str(did), ""))
    dlg._desc_box = box

    save_btn = QPushButton("Save description")
    save_btn.setAutoDefault(False)
    save_btn.setDefault(False)
    save_btn.clicked.connect(lambda: _save_now(dlg))
    row = QWidget()
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.addStretch()
    row_layout.addWidget(save_btn)

    # insert just above the bottom button row
    index = max(layout.count() - 1, 0)
    layout.insertWidget(index, label)
    layout.insertWidget(index + 1, box)
    layout.insertWidget(index + 2, row)


_orig_init = FilteredDeckConfigDialog.__init__


def _new_init(self, *args, **kwargs):
    _orig_init(self, *args, **kwargs)
    try:
        _add_box(self)
    except Exception as e:
        print("Filtered deck description add-on:", e)


FilteredDeckConfigDialog.__init__ = _new_init

_orig_accept = FilteredDeckConfigDialog.accept


def _new_accept(self):
    box = getattr(self, "_desc_box", None)
    text = box.toPlainText() if box else None
    did = getattr(self, "_desc_deck_id", 0)
    name = self.form.name.text() if hasattr(self.form, "name") else ""
    _orig_accept(self)
    if text is None:
        return

    def save():
        key_id = did or mw.col.decks.id_for_name(name)
        if key_id:
            _store(key_id, text)

    # the dialog saves asynchronously, so wait briefly for new decks to exist
    QTimer.singleShot(800, save)


FilteredDeckConfigDialog.accept = _new_accept


def add_to_overview(overview, content):
    deck = mw.col.decks.current()
    if not deck.get("dyn"):
        return
    text = _notes().get(str(deck["id"]), "")
    if text:
        content.table += (
            "<div style='margin-top:1em; text-align:left; white-space:pre-wrap; overflow-wrap: break-word; word-wrap: break-word;'>"
            + html.escape(text) + "</div>"
        )


gui_hooks.overview_will_render_content.append(add_to_overview)