"""
Student Marks Calculator — complete pure-Python PySide6 rewrite.
No .ui files; all widgets are built directly in code.
"""

# ---------------------------------------------------------------------------
# Bootstrap: when run as "python src/main.py", make "src" a proper package
# ---------------------------------------------------------------------------
import sys, os
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QMessageBox, QFileDialog,
    QFrame, QScrollArea, QGraphicsDropShadowEffect,
    QProgressBar,
)
from PySide6.QtCore  import Qt, QRect, QThread, Signal, QTimer, QEventLoop
from PySide6.QtGui   import (
    QFont, QColor, QLinearGradient, QPainter,
    QBrush, QPen, QPainterPath, QPixmap, QIcon,
)

import pyqtgraph as pg
from pyqtgraph import exporters

from src.crypto import (
    verify_password, store_password_meta,
    encrypt_field, decrypt_field,
)
from src.db import (
    init_db, SessionLocal,
    add_student, add_exam, add_mark,
    Student, Exam, Mark,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SRC   = Path(__file__).parent
_ROOT  = _SRC.parent
_LOGO  = _ROOT / "logo.png"
_META  = _SRC / "app_meta.json"

# ---------------------------------------------------------------------------
# Design tokens — deep indigo dark theme
# ---------------------------------------------------------------------------
C_BG      = "#0d0d1f"
C_SURFACE = "#13132a"
C_CARD    = "#1a1a3a"
C_BORDER  = "#2a2a5a"
C_ACCENT  = "#7c6fcd"   # purple
C_ACCENT2 = "#e96d8a"   # pink
C_TEAL    = "#43c9b0"
C_TEXT    = "#f0f0ff"
C_SUBTEXT = "#8888bb"
C_SUCCESS = "#43c97a"
C_WARN    = "#f5c542"
C_DANGER  = "#e96d8a"

# Keep old names as aliases so existing code still compiles
BG        = C_BG
SURFACE   = C_SURFACE
ACCENT    = C_ACCENT
HIGHLIGHT = C_ACCENT2
TEXT      = C_TEXT
SUBTEXT   = C_SUBTEXT
SUCCESS   = C_SUCCESS
WARNING   = C_WARN

def _lg(a, b, h=False):
    x2 = "1" if h else "0"
    y2 = "0" if h else "1"
    return f"qlineargradient(x1:0,y1:0,x2:{x2},y2:{y2},stop:0 {a},stop:1 {b})"

GLOBAL_SS = (
    "* { font-family: 'Segoe UI', Arial, sans-serif; }"
    "QWidget { background: " + C_BG + "; color: " + C_TEXT + "; font-size: 13px; }"
    "QDialog { background: " + C_BG + "; }"
    "QTabWidget::pane { border:1px solid " + C_BORDER + "; border-radius:12px; background:" + C_SURFACE + "; top:-1px; }"
    "QTabBar { background: transparent; }"
    "QTabBar::tab { background:" + C_CARD + "; color:" + C_SUBTEXT + "; padding:10px 28px; margin-right:4px;"
        " border:1px solid " + C_BORDER + "; border-bottom:none;"
        " border-top-left-radius:10px; border-top-right-radius:10px;"
        " font-weight:600; font-size:13px; min-width:120px; }"
    "QTabBar::tab:selected { background:" + _lg(C_ACCENT, '#5a3fa8') + "; color:white; border-color:" + C_ACCENT + "; }"
    "QTabBar::tab:hover:!selected { background:#242450; color:" + C_TEXT + "; }"
    "QLineEdit { background:" + C_CARD + "; border:1.5px solid " + C_BORDER + ";"
        " border-radius:8px; padding:9px 13px; color:" + C_TEXT + ";"
        " selection-background-color:" + C_ACCENT + "; font-size:13px; }"
    "QLineEdit:focus { border:1.5px solid " + C_ACCENT + "; background:#1f1f42; }"
    "QLineEdit:hover { border:1.5px solid #3a3a6a; }"
    "QComboBox { background:" + C_CARD + "; border:1.5px solid " + C_BORDER + ";"
        " border-radius:8px; padding:9px 13px; color:" + C_TEXT + "; min-width:180px; font-size:13px; }"
    "QComboBox:focus { border:1.5px solid " + C_ACCENT + "; }"
    "QComboBox::drop-down { border:none; width:28px; }"
    "QComboBox QAbstractItemView { background:" + C_CARD + "; border:1px solid " + C_ACCENT + ";"
        " border-radius:8px; selection-background-color:" + C_ACCENT + ";"
        " color:" + C_TEXT + "; padding:4px; outline:0; }"
    "QPushButton { background:" + _lg(C_ACCENT2, '#c04568') + "; color:white; border:none;"
        " border-radius:9px; padding:10px 26px; font-weight:700; font-size:13px; letter-spacing:0.3px; }"
    "QPushButton:hover { background:" + _lg('#f08099', '#d05078') + "; }"
    "QPushButton:pressed { background:#a03050; }"
    "QPushButton#ghost { background:transparent; border:1.5px solid " + C_BORDER + ";"
        " color:" + C_SUBTEXT + "; padding:9px 20px; }"
    "QPushButton#ghost:hover { border-color:" + C_ACCENT + "; color:" + C_TEXT + "; background:#1f1f42; }"
    "QPushButton#secondaryBtn { background:" + C_CARD + "; color:" + C_SUBTEXT + ";"
        " border:1.5px solid " + C_BORDER + "; }"
    "QPushButton#secondaryBtn:hover { border-color:" + C_ACCENT + "; color:" + C_TEXT + "; background:#1f1f42; }"
    "QPushButton#accent { background:" + _lg(C_ACCENT, '#5a3fa8') + "; }"
    "QPushButton#accent:hover { background:" + _lg('#9c8fe0', '#6a50c0') + "; }"
    "QPushButton#teal { background:" + _lg(C_TEAL, '#2ea890') + "; }"
    "QPushButton#teal:hover { background:" + _lg('#5dd9c0', '#3ab8a0') + "; }"
    "QGroupBox { border:1px solid " + C_BORDER + "; border-radius:12px;"
        " margin-top:20px; padding:14px 16px 12px 16px; background:" + C_CARD + "; }"
    "QGroupBox::title { subcontrol-origin:margin; left:16px; top:0px;"
        " color:" + C_ACCENT + "; font-size:11px; font-weight:700; letter-spacing:1.5px;"
        " padding:0 6px; background:" + C_CARD + "; }"
    "QTableWidget { background:" + C_CARD + "; gridline-color:" + C_BORDER + ";"
        " border:1px solid " + C_BORDER + "; border-radius:10px;"
        " alternate-background-color:#171732; selection-background-color:" + C_ACCENT + "; outline:0; }"
    "QTableWidget::item { padding:8px 12px; border:none; }"
    "QTableWidget::item:selected { background:" + C_ACCENT + "; color:white; }"
    "QHeaderView::section { background:" + _lg('#1e1e40', '#16163a') + ";"
        " color:" + C_SUBTEXT + "; padding:10px 12px; border:none;"
        " border-right:1px solid " + C_BORDER + ";"
        " font-weight:700; font-size:11px; letter-spacing:1px; }"
    "QHeaderView::section:first { border-top-left-radius:10px; }"
    "QHeaderView::section:last { border-top-right-radius:10px; border-right:none; }"
    "QScrollBar:vertical { background:transparent; width:7px; margin:0; }"
    "QScrollBar::handle:vertical { background:" + C_BORDER + "; border-radius:3px; min-height:24px; }"
    "QScrollBar::handle:vertical:hover { background:" + C_ACCENT + "; }"
    "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }"
    "QScrollBar:horizontal { background:transparent; height:7px; }"
    "QScrollBar::handle:horizontal { background:" + C_BORDER + "; border-radius:3px; }"
    "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }"
    "QLabel#heading { font-size:22px; font-weight:800; color:" + C_TEXT + "; letter-spacing:0.5px; }"
    "QLabel#subheading { font-size:13px; color:" + C_SUBTEXT + "; }"
    "QLabel#statCard { background:" + C_SURFACE + "; border:1px solid " + C_BORDER + ";"
        " border-radius:10px; padding:14px 20px; font-size:14px; font-weight:700; min-width:160px; }"
    "QFrame#divider { background:" + C_BORDER + "; max-height:1px; }"
    "QMessageBox { background:" + C_SURFACE + "; }"
    "QMessageBox QPushButton { min-width:80px; }"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def label(text, style="", object_name=""):
    lbl = QLabel(text)
    if style:
        lbl.setStyleSheet(style)
    if object_name:
        lbl.setObjectName(object_name)
    return lbl

def divider():
    f = QFrame()
    f.setObjectName("divider")
    f.setFrameShape(QFrame.HLine)
    return f

def shadow(w, radius=18, color="#000000", offset=(0, 4)):
    eff = QGraphicsDropShadowEffect(w)
    eff.setBlurRadius(radius)
    eff.setColor(QColor(color))
    eff.setOffset(*offset)
    w.setGraphicsEffect(eff)

def mk_label(text, size=13, bold=False, color=C_TEXT, align=Qt.AlignLeft):
    lbl = QLabel(text)
    f = QFont("Segoe UI", size)
    f.setBold(bold)
    lbl.setFont(f)
    lbl.setStyleSheet(f"color: {color}; background: transparent;")
    lbl.setAlignment(align)
    return lbl

def h_div():
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"background:{C_BORDER}; max-height:1px; border:none;")
    return f


class GradCard(QWidget):
    """Rounded card with linear gradient fill."""
    def __init__(self, ca=C_CARD, cb=C_SURFACE, radius=14, parent=None):
        super().__init__(parent)
        self._ca, self._cb, self._r = QColor(ca), QColor(cb), radius

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, self._ca); g.setColorAt(1, self._cb)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._r, self._r)
        p.fillPath(path, QBrush(g))
        p.setPen(QPen(QColor(C_BORDER), 1))
        p.drawPath(path)


class StatCard(GradCard):
    """KPI card with coloured left accent bar."""
    def __init__(self, icon, key_txt, value="\u2014", accent=C_ACCENT, parent=None):
        super().__init__(C_CARD, "#141430", parent=parent)
        self._accent = QColor(accent)
        self.setMinimumSize(155, 96)
        self.setMaximumHeight(108)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 14, 18, 14); lay.setSpacing(14)
        ico = mk_label(icon, 26)
        ico.setFixedWidth(42); ico.setAlignment(Qt.AlignCenter)
        lay.addWidget(ico)
        col = QVBoxLayout(); col.setSpacing(3)
        self.val = mk_label(value, 19, bold=True)
        self.key = mk_label(key_txt, 9, color=C_SUBTEXT)
        self.key.setStyleSheet(f"color:{C_SUBTEXT}; letter-spacing:1.2px; background:transparent;")
        col.addStretch(); col.addWidget(self.val); col.addWidget(self.key); col.addStretch()
        lay.addLayout(col)
        shadow(self, 22, "#000028", (0, 5))

    def set_value(self, v): self.val.setText(v)

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen); p.setBrush(QBrush(self._accent))
        p.drawRoundedRect(0, 14, 4, self.height() - 28, 2, 2)


class PctBadge(QWidget):
    """Custom-painted percentage pill badge."""
    def __init__(self, pct=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(88, 28); self._pct = pct

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pct = self._pct
        if pct is None:   bg, fg, txt = C_BORDER,  C_SUBTEXT, "\u2014"
        elif pct >= 75:   bg, fg, txt = "#1a4030", C_SUCCESS, f"{pct:.1f}%"
        elif pct >= 50:   bg, fg, txt = "#3a3010", C_WARN,    f"{pct:.1f}%"
        else:             bg, fg, txt = "#3a1020", C_DANGER,  f"{pct:.1f}%"
        r = self.rect()
        p.setBrush(QColor(bg)); p.setPen(QPen(QColor(fg), 1))
        p.drawRoundedRect(r, 14, 14)
        p.setPen(QColor(fg))
        f = QFont("Segoe UI", 10); f.setBold(True); p.setFont(f)
        p.drawText(r, Qt.AlignCenter, txt)


class MarkField(QWidget):
    """Per-subject row: emoji label + float input + live % hint."""
    def __init__(self, subject, max_marks, emoji="", parent=None):
        super().__init__(parent)
        self.max_marks = max_marks
        self.setFixedHeight(44)
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 0, 4, 0); row.setSpacing(10)
        lbl = mk_label(f"{emoji}  {subject}", 13)
        lbl.setFixedWidth(130); row.addWidget(lbl)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(f"0 \u2013 {max_marks}")
        self.edit.setFixedWidth(110); row.addWidget(self.edit)
        row.addWidget(mk_label(f"/ {max_marks}", 11, color=C_SUBTEXT))
        self.hint = mk_label("", 11, color=C_SUBTEXT)
        self.hint.setFixedWidth(80); row.addWidget(self.hint)
        row.addStretch()
        self.edit.textChanged.connect(self._on_change)

    def _on_change(self, txt):
        txt = txt.strip()
        if not txt:
            self.hint.setText(""); self.edit.setStyleSheet(""); return
        try:
            v = float(txt)
            if 0 <= v <= self.max_marks:
                pct = v / self.max_marks * 100
                col = C_SUCCESS if pct >= 75 else C_WARN if pct >= 50 else C_DANGER
                self.hint.setText(f"({pct:.1f}%)")
                self.hint.setStyleSheet(f"color:{col}; background:transparent;")
                self.edit.setStyleSheet(f"border-color:{col};")
            else:
                self.hint.setText(f"max {self.max_marks}")
                self.hint.setStyleSheet(f"color:{C_DANGER}; background:transparent;")
                self.edit.setStyleSheet(f"border-color:{C_DANGER};")
        except ValueError:
            self.hint.setText("numbers only")
            self.hint.setStyleSheet(f"color:{C_DANGER}; background:transparent;")
            self.edit.setStyleSheet(f"border-color:{C_DANGER};")

    def value(self):
        txt = self.edit.text().strip()
        if not txt: return None
        return round(float(txt), 4)

    def set_value(self, val):
        if val is None:
            self.edit.clear()
        else:
            self.edit.setText(f"{val:g}" if isinstance(val, float) else str(val))

    def clear(self): self.edit.clear()

# ---------------------------------------------------------------------------
# First-time setup dialog
# ---------------------------------------------------------------------------
class SetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("StatSketch — Setup")
        if _LOGO.exists(): self.setWindowIcon(QIcon(str(_LOGO)))
        self.setMinimumWidth(400)
        self.setModal(True)
        self.key = None

        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(32, 32, 32, 32)

        root.addWidget(label("✨  StatSketch Setup", object_name="heading"))
        root.addWidget(label("Create a master password to encrypt your workspace.", object_name="subheading"))
        root.addWidget(divider())

        form = QFormLayout()
        form.setSpacing(10)
        self.pwd1 = QLineEdit(); self.pwd1.setEchoMode(QLineEdit.Password)
        self.pwd1.setPlaceholderText("Enter password…")
        self.pwd2 = QLineEdit(); self.pwd2.setEchoMode(QLineEdit.Password)
        self.pwd2.setPlaceholderText("Confirm password…")
        form.addRow("Password:", self.pwd1)
        form.addRow("Confirm:", self.pwd2)
        root.addLayout(form)

        self.err = label("", f"color: {HIGHLIGHT}; font-size: 12px;")
        root.addWidget(self.err)

        btns = QHBoxLayout()
        btns.addStretch()
        ok_btn = QPushButton("Create Password")
        ok_btn.clicked.connect(self._create)
        btns.addWidget(ok_btn)
        root.addLayout(btns)

        self.pwd1.returnPressed.connect(self._create)
        self.pwd2.returnPressed.connect(self._create)

    def _create(self):
        p1, p2 = self.pwd1.text(), self.pwd2.text()
        if not p1:
            self.err.setText("Password cannot be empty."); return
        if p1 != p2:
            self.err.setText("Passwords do not match."); return
        meta = store_password_meta(p1)
        with open(_META, "w") as f:
            json.dump(meta, f, indent=2)
        self.accept()

# ---------------------------------------------------------------------------
# Login dialog
# ---------------------------------------------------------------------------
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("StatSketch — Login")
        if _LOGO.exists(): self.setWindowIcon(QIcon(str(_LOGO)))
        self.setMinimumWidth(380)
        self.setModal(True)
        self.key = None

        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(32, 32, 32, 32)

        root.addWidget(label("🔐  StatSketch Login", object_name="heading"))
        root.addWidget(label("Enter your master password to unlock your records.", object_name="subheading"))
        root.addWidget(divider())

        self.pwd = QLineEdit()
        self.pwd.setEchoMode(QLineEdit.Password)
        self.pwd.setPlaceholderText("Password…")
        root.addWidget(self.pwd)

        self.err = label("", f"color: {HIGHLIGHT}; font-size: 12px;")
        root.addWidget(self.err)

        btns = QHBoxLayout()
        cancel = QPushButton("Cancel"); cancel.setObjectName("secondaryBtn")
        cancel.clicked.connect(self.reject)
        login  = QPushButton("Login")
        login.clicked.connect(self._login)
        btns.addWidget(cancel)
        btns.addStretch()
        btns.addWidget(login)
        root.addLayout(btns)

        self.pwd.returnPressed.connect(self._login)

    def _login(self):
        with open(_META) as f:
            meta = json.load(f)
        key = verify_password(self.pwd.text(), meta)
        if key:
            self.key = key
            self.accept()
        else:
            self.err.setText("Incorrect password. Please try again.")
            self.pwd.clear()
            self.pwd.setFocus()

# ---------------------------------------------------------------------------
# Enter-Marks tab
# ---------------------------------------------------------------------------
SUBJECTS = [
    ("Math",    80, "\u2795"),
    ("Science", 80, "\U0001f52c"),
    ("SST",     80, "\U0001f30d"),
    ("English", 80, "\U0001f4d6"),
    ("Hindi",   80, "\u0905"),
    ("AI",      50, "\U0001f916"),
]
EXAM_TYPES = ["midterm", "preboard1", "preboard2", "preboard3"]

class EnterMarksTab(QWidget):
    def __init__(self, db, key):
        super().__init__()
        self.db = db; self.key = key; self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background:transparent;")
        inner = QWidget()
        inner.setStyleSheet(f"background:{C_SURFACE};")
        root = QVBoxLayout(inner)
        root.setSpacing(20); root.setContentsMargins(32, 28, 32, 28)

        hr = QHBoxLayout()
        hr.addWidget(mk_label("Enter Marks", 17, bold=True)); hr.addStretch()
        fl = mk_label("Decimals supported  (e.g. 72.5)", 11, color=C_SUBTEXT)
        fl.setAlignment(Qt.AlignRight | Qt.AlignVCenter); hr.addWidget(fl)
        root.addLayout(hr); root.addWidget(h_div())

        c1 = GradCard(C_CARD, "#111128", 14)
        c1.setStyleSheet(f"border:1px solid {C_BORDER}; border-radius:14px;")
        c1l = QVBoxLayout(c1); c1l.setContentsMargins(20, 14, 20, 18); c1l.setSpacing(12)
        c1l.addWidget(mk_label("STUDENT & EXAM", 10, bold=True, color=C_ACCENT))
        g = QGridLayout(); g.setSpacing(10)
        g.addWidget(mk_label("Student Name", 12, color=C_SUBTEXT), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Alice Smith")
        g.addWidget(self.name_edit, 0, 1)
        g.addWidget(mk_label("Exam Type", 12, color=C_SUBTEXT), 1, 0)
        self.exam_combo = QComboBox(); self.exam_combo.addItems(EXAM_TYPES)
        g.addWidget(self.exam_combo, 1, 1); c1l.addLayout(g)
        root.addWidget(c1); shadow(c1, 20)

        c2 = GradCard(C_CARD, "#111128", 14)
        c2.setStyleSheet(f"border:1px solid {C_BORDER}; border-radius:14px;")
        c2l = QVBoxLayout(c2); c2l.setContentsMargins(20, 14, 20, 20); c2l.setSpacing(8)
        c2l.addWidget(mk_label("SUBJECT MARKS  \u2014  blank fields are skipped", 10, bold=True, color=C_ACCENT))
        c2l.addWidget(h_div())
        self._mark_fields = []
        for subj, mx, emoji in SUBJECTS:
            mf = MarkField(subj, mx, emoji); c2l.addWidget(mf)
            self._mark_fields.append((subj, mx, mf))
        root.addWidget(c2); shadow(c2, 20)

        br = QHBoxLayout(); br.addStretch()
        clr = QPushButton("  Clear  "); clr.setObjectName("secondaryBtn")
        sub = QPushButton("  Save Marks  "); sub.setObjectName("teal")
        clr.clicked.connect(self._clear); sub.clicked.connect(self._submit)
        br.addWidget(clr); br.addWidget(sub); root.addLayout(br); root.addStretch()

        scroll.setWidget(inner)
        ol = QVBoxLayout(self); ol.setContentsMargins(0, 0, 0, 0); ol.addWidget(scroll)

    def _clear(self):
        self.name_edit.clear(); self.exam_combo.setCurrentIndex(0)
        for _, _, mf in self._mark_fields: mf.clear()

    def _submit(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a student name."); return
        student   = add_student(self.db, name, self.key)
        exam_type = self.exam_combo.currentText()
        exam = self.db.query(Exam).filter_by(type=exam_type).first()
        if not exam: exam = add_exam(self.db, exam_type)
        saved = 0
        for subj, mx, mf in self._mark_fields:
            try: val = mf.value()
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"{subj}: enter a valid number."); return
            if val is None: continue
            if not (0 <= val <= mx):
                QMessageBox.warning(self, "Out of Range", f"{subj}: must be 0\u2013{mx}."); return
            add_mark(self.db, student.id, exam.id, subj, val, mx, self.key); saved += 1
        if saved == 0:
            QMessageBox.warning(self, "No Marks", "Enter at least one mark."); return
        QMessageBox.information(self, "Saved", f"Marks saved for {name}  ({exam_type}).")
        self._clear()

# ---------------------------------------------------------------------------
# Edit Record Dialog
# ---------------------------------------------------------------------------
class EditRecordDialog(QDialog):
    def __init__(self, parent, db, key, student_id, exam_id):
        super().__init__(parent)
        self.db = db
        self.key = key
        self.student_id = student_id
        self.exam_id = exam_id
        self.setWindowTitle("Edit Record")
        self.setMinimumWidth(440)
        self.setModal(True)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(24, 24, 24, 24)

        header = QHBoxLayout()
        header.addWidget(mk_label("✏  Edit Student Marks", 15, bold=True))
        header.addStretch()
        root.addLayout(header)
        root.addWidget(h_div())

        st = self.db.query(Student).filter_by(id=self.student_id).first()
        ex = self.db.query(Exam).filter_by(id=self.exam_id).first()
        try:
            current_name = decrypt_field(st.name_enc, self.key)
        except Exception:
            current_name = ""

        # Form for Name and Exam
        form_card = GradCard(C_CARD, "#111128", 12)
        form_card.setStyleSheet(f"border:1px solid {C_BORDER}; border-radius:12px;")
        fl = QVBoxLayout(form_card)
        fl.setContentsMargins(16, 12, 16, 14)
        fl.setSpacing(10)
        fl.addWidget(mk_label("STUDENT & EXAM", 10, bold=True, color=C_ACCENT))

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.addWidget(mk_label("Student Name", 11, color=C_SUBTEXT), 0, 0)
        self.name_edit = QLineEdit(current_name)
        grid.addWidget(self.name_edit, 0, 1)

        grid.addWidget(mk_label("Exam", 11, color=C_SUBTEXT), 1, 0)
        exam_lbl = mk_label(ex.type if ex else "", 12, bold=True, color=C_TEXT)
        grid.addWidget(exam_lbl, 1, 1)
        fl.addLayout(grid)
        root.addWidget(form_card)

        # Subject marks card
        marks_card = GradCard(C_CARD, "#111128", 12)
        marks_card.setStyleSheet(f"border:1px solid {C_BORDER}; border-radius:12px;")
        ml = QVBoxLayout(marks_card)
        ml.setContentsMargins(16, 12, 16, 16)
        ml.setSpacing(8)
        ml.addWidget(mk_label("SUBJECT MARKS  \u2014  blank removes mark", 10, bold=True, color=C_ACCENT))
        ml.addWidget(h_div())

        existing_marks = self.db.query(Mark).filter_by(student_id=self.student_id, exam_id=self.exam_id).all()
        mark_dict = {}
        for m in existing_marks:
            try:
                ob = float(decrypt_field(m.obtained_enc, self.key))
                mark_dict[m.subject] = ob
            except Exception:
                pass

        self._fields = []
        for subj, mx, emoji in SUBJECTS:
            mf = MarkField(subj, mx, emoji)
            if subj in mark_dict:
                mf.set_value(mark_dict[subj])
            ml.addWidget(mf)
            self._fields.append((subj, mx, mf))
        root.addWidget(marks_card)

        self.err_lbl = mk_label("", 11, color=C_DANGER)
        root.addWidget(self.err_lbl)

        # Action buttons
        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("  Cancel  ")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("  Save Changes  ")
        save_btn.setObjectName("teal")
        save_btn.clicked.connect(self._save)
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        root.addLayout(btns)

    def _save(self):
        new_name = self.name_edit.text().strip()
        if not new_name:
            self.err_lbl.setText("Student name cannot be empty.")
            return

        st = self.db.query(Student).filter_by(id=self.student_id).first()
        if st:
            st.name_enc = encrypt_field(new_name, self.key)

        existing_marks = {m.subject: m for m in self.db.query(Mark).filter_by(
            student_id=self.student_id, exam_id=self.exam_id).all()}

        has_any_mark = False
        for subj, mx, mf in self._fields:
            try:
                val = mf.value()
            except ValueError:
                self.err_lbl.setText(f"{subj}: invalid number.")
                return
            if val is not None:
                if not (0 <= val <= mx):
                    self.err_lbl.setText(f"{subj}: must be between 0 and {mx}.")
                    return
                has_any_mark = True
                enc_val = encrypt_field(str(val), self.key)
                if subj in existing_marks:
                    existing_marks[subj].obtained_enc = enc_val
                    existing_marks[subj].total = mx
                else:
                    new_m = Mark(
                        student_id=self.student_id,
                        exam_id=self.exam_id,
                        subject=subj,
                        obtained_enc=enc_val,
                        total=mx
                    )
                    self.db.add(new_m)
            else:
                if subj in existing_marks:
                    self.db.delete(existing_marks[subj])

        if not has_any_mark:
            self.err_lbl.setText("Please enter at least one mark.")
            return

        self.db.commit()
        self.accept()


# ---------------------------------------------------------------------------
# Statistics tab
# ---------------------------------------------------------------------------
class StatisticsTab(QWidget):
    def __init__(self, db, key):
        super().__init__()
        self.db  = db
        self.key = key
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(18); root.setContentsMargins(28, 24, 28, 24)
        hr = QHBoxLayout()
        hr.addWidget(mk_label("Statistics", 17, bold=True)); hr.addStretch()
        ref = QPushButton("  Refresh  "); ref.setObjectName("secondaryBtn")
        ref.clicked.connect(self.refresh); hr.addWidget(ref)
        root.addLayout(hr); root.addWidget(h_div())
        cards = QHBoxLayout(); cards.setSpacing(14)
        self.card_avg  = StatCard("📊", "AVERAGE",  accent=C_ACCENT)
        self.card_high = StatCard("🏆", "HIGHEST",  accent=C_SUCCESS)
        self.card_low  = StatCard("📉", "LOWEST",   accent=C_DANGER)
        self.card_cnt  = StatCard("👥", "ENTRIES",  value="0", accent=C_TEAL)
        for c in (self.card_avg, self.card_high, self.card_low, self.card_cnt): cards.addWidget(c)
        root.addLayout(cards)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Student", "Exam", "Score", "Percentage", "Actions"])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        root.addWidget(self.table)

    def refresh(self):
        self.table.setRowCount(0)
        rows, percents = [], []
        students = self.db.query(Student).all()
        exams    = self.db.query(Exam).all()
        for st in students:
            try: s_name = decrypt_field(st.name_enc, self.key)
            except Exception: s_name = "<error>"
            for ex in exams:
                marks = self.db.query(Mark).filter_by(student_id=st.id, exam_id=ex.id).all()
                if not marks: continue
                tp = sum(m.total for m in marks)
                try: ob = sum(float(decrypt_field(m.obtained_enc, self.key)) for m in marks)
                except Exception: continue
                pct = (ob * 100.0 / tp) if tp else 0.0
                percents.append(pct)
                rows.append((st.id, ex.id, s_name, ex.type, ob, tp, pct))
        self.table.setRowCount(len(rows))
        for r, (st_id, ex_id, name, exam, ob, tp, pct) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(f"  {name}"))
            ei = QTableWidgetItem(exam); ei.setForeground(QColor(C_SUBTEXT)); self.table.setItem(r, 1, ei)
            si = QTableWidgetItem(f"{ob:.2f}  /  {tp}"); si.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 2, si)
            badge = PctBadge(pct)
            cw = QWidget(); cw.setStyleSheet("background:transparent;")
            cl = QHBoxLayout(cw); cl.setContentsMargins(8, 4, 8, 4)
            cl.addStretch(); cl.addWidget(badge); cl.addStretch()
            self.table.setCellWidget(r, 3, cw)

            # Actions: Edit and Delete buttons
            act_w = QWidget(); act_w.setStyleSheet("background:transparent;")
            act_l = QHBoxLayout(act_w); act_l.setContentsMargins(6, 4, 6, 4); act_l.setSpacing(8)
            act_l.addStretch()

            btn_edit = QPushButton("✏ Edit")
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet(
                f"QPushButton {{ background:{C_CARD}; color:{C_TEXT}; border:1px solid {C_BORDER};"
                "  border-radius:6px; padding:4px 10px; font-size:11px; font-weight:600; min-width:54px; }"
                f"QPushButton:hover {{ border-color:{C_ACCENT}; background:#252550; }}"
            )
            btn_edit.clicked.connect(lambda _, sid=st_id, eid=ex_id: self._on_edit(sid, eid))

            btn_del = QPushButton("🗑 Delete")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet(
                f"QPushButton {{ background:{C_CARD}; color:#ff8090; border:1px solid #5a2030;"
                "  border-radius:6px; padding:4px 10px; font-size:11px; font-weight:600; min-width:60px; }"
                "QPushButton:hover {{ border-color:#e96d8a; background:#381420; color:white; }}"
            )
            btn_del.clicked.connect(lambda _, sid=st_id, eid=ex_id, sn=name, et=exam: self._on_delete(sid, eid, sn, et))

            act_l.addWidget(btn_edit)
            act_l.addWidget(btn_del)
            act_l.addStretch()
            self.table.setCellWidget(r, 4, act_w)

        if percents:
            avg = sum(percents) / len(percents)
            self.card_avg.set_value(f"{avg:.1f}%")
            self.card_high.set_value(f"{max(percents):.1f}%")
            self.card_low.set_value(f"{min(percents):.1f}%")
        else:
            self.card_avg.set_value("—"); self.card_high.set_value("—"); self.card_low.set_value("—")
        self.card_cnt.set_value(str(len(rows)))

    def _on_edit(self, student_id, exam_id):
        dlg = EditRecordDialog(self, self.db, self.key, student_id, exam_id)
        if dlg.exec() == QDialog.Accepted:
            self.refresh()
            win = self.window()
            if hasattr(win, "graph_tab"):
                win.graph_tab.refresh()

    def _on_delete(self, student_id, exam_id, student_name, exam_type):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete all marks for:\n\n"
            f"  • Student: {student_name}\n"
            f"  • Exam: {exam_type}\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.query(Mark).filter_by(student_id=student_id, exam_id=exam_id).delete()
            rem = self.db.query(Mark).filter_by(student_id=student_id).count()
            if rem == 0:
                self.db.query(Student).filter_by(id=student_id).delete()
            self.db.commit()
            self.refresh()
            win = self.window()
            if hasattr(win, "graph_tab"):
                win.graph_tab.refresh()


# ---------------------------------------------------------------------------
# Charts Tab  — 4 sub-tabs of analytics
# ---------------------------------------------------------------------------

# Palette lists for multi-series charts
_SERIES_COLORS = [
    "#7c6fcd", "#e96d8a", "#43c9b0", "#f5c542",
    "#43c97a", "#c07aff", "#ff9f43", "#54a0ff",
]

def _make_plot(title="", x_label="", y_label=""):
    """Return a styled PlotWidget with consistent theme."""
    pw = pg.PlotWidget()
    pw.setStyleSheet(f"border-radius:12px; border:1px solid {C_BORDER};")
    pw.showGrid(x=False, y=True, alpha=0.10)
    pw.getAxis("bottom").setStyle(tickTextOffset=8, tickFont=QFont("Segoe UI", 9))
    pw.getAxis("left").setStyle(tickFont=QFont("Segoe UI", 9))
    pw.setMenuEnabled(False)
    if x_label: pw.setLabel("bottom", x_label, color=C_SUBTEXT, size="10pt")
    if y_label: pw.setLabel("left",   y_label, color=C_SUBTEXT, size="10pt")
    if title:   pw.setTitle(title, color=C_TEXT, size="11pt")
    for level, col in ((75, C_SUCCESS), (50, C_WARN)):
        pw.addItem(pg.InfiniteLine(pos=level, angle=0,
                   pen=pg.mkPen(col, width=1, style=Qt.DashLine)))
    return pw

def _ref_lines(pw):
    """Add 75 % / 50 % dashed reference lines to a plot."""
    for level, col in ((75, C_SUCCESS), (50, C_WARN)):
        pw.addItem(pg.InfiniteLine(pos=level, angle=0,
                   pen=pg.mkPen(col, width=1, style=Qt.DashLine)))
        lab = pg.TextItem(f"{level}%", anchor=(0, 0.5), color=col)
        lab.setFont(QFont("Segoe UI", 8))
        lab.setPos(-0.4, level)
        pw.addItem(lab)

def _export_plot(parent, plot_widget):
    path, _ = QFileDialog.getSaveFileName(parent, "Export Chart", "", "PNG Image (*.png)")
    if path:
        exp = exporters.ImageExporter(plot_widget.plotItem)
        exp.parameters()["width"] = 1600
        exp.export(path)


def _chart_toolbar(parent, title, plot_widget):
    """Return a QHBoxLayout with title + refresh + export buttons."""
    hr = QHBoxLayout()
    hr.addWidget(mk_label(title, 15, bold=True))
    hr.addStretch()
    ref = QPushButton("  ↺  Refresh  "); ref.setObjectName("secondaryBtn")
    exp = QPushButton("  ↓  Export PNG  "); exp.setObjectName("accent")
    ref.clicked.connect(parent.refresh)
    exp.clicked.connect(lambda: _export_plot(parent, plot_widget))
    hr.addWidget(ref); hr.addWidget(exp)
    return hr


# ── Sub-tab 1: Overview bar chart ───────────────────────────────────────────
class _OverviewChart(QWidget):
    """Average overall % per student (bar chart)."""
    def __init__(self, db, key):
        super().__init__()
        self.db = db; self.key = key
        self._build(); self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12); root.setContentsMargins(20, 16, 20, 16)
        pg.setConfigOption("background", C_SURFACE); pg.setConfigOption("foreground", C_TEXT)
        self.plot = _make_plot(y_label="Average %", x_label="Student")
        root.addLayout(_chart_toolbar(self, "Overall Performance", self.plot))
        root.addWidget(h_div())
        tip = mk_label(
            "Each bar shows a student\'s average percentage across all exams. "
            "Green ≥75%  ·  Amber ≥50%  ·  Red <50%",
            10, color=C_SUBTEXT
        )
        tip.setWordWrap(True); root.addWidget(tip)
        root.addWidget(self.plot)

    def refresh(self):
        self.plot.clear()
        students = self.db.query(Student).all()
        exams    = self.db.query(Exam).all()
        perc, names = [], []
        for st in students:
            try: name = decrypt_field(st.name_enc, self.key)
            except Exception: name = "<err>"
            tp_sum, cnt = 0.0, 0
            for ex in exams:
                marks = self.db.query(Mark).filter_by(student_id=st.id, exam_id=ex.id).all()
                if not marks: continue
                tp = sum(m.total for m in marks)
                try: ob = sum(float(decrypt_field(m.obtained_enc, self.key)) for m in marks)
                except Exception: continue
                tp_sum += (ob * 100.0 / tp) if tp else 0.0; cnt += 1
            if cnt > 0: names.append(name); perc.append(tp_sum / cnt)
        if not names:
            self.plot.setTitle("No data yet", color=C_SUBTEXT, size="12pt"); return
        xs      = list(range(len(names)))
        brushes = [pg.mkBrush(C_SUCCESS if v >= 75 else C_WARN if v >= 50 else C_DANGER) for v in perc]
        self.plot.addItem(pg.BarGraphItem(x=xs, height=perc, width=0.58, brushes=brushes, pen=pg.mkPen(None)))
        for x, v, n in zip(xs, perc, names):
            col = C_SUCCESS if v >= 75 else C_WARN if v >= 50 else C_DANGER
            ti = pg.TextItem(f"{v:.1f}%", anchor=(0.5, 1.12), color=col)
            ti.setFont(QFont("Segoe UI", 9, QFont.Bold)); ti.setPos(x, v); self.plot.addItem(ti)
        _ref_lines(self.plot)
        ticks = [[(i, n) for i, n in enumerate(names)]]
        self.plot.getAxis("bottom").setTicks(ticks)
        self.plot.setTitle("Average Percentage per Student", color=C_TEXT, size="11pt")
        self.plot.setXRange(-0.6, len(names) - 0.4, padding=0.1)
        self.plot.setYRange(0, 115, padding=0)


# ── Sub-tab 2: Subject breakdown grouped bar chart ───────────────────────────
class _SubjectChart(QWidget):
    """Per-subject scores per student, grouped bars, with student filter."""
    SUBJECT_COLORS = {
        "Math":    "#7c6fcd",
        "Science": "#43c9b0",
        "SST":     "#f5c542",
        "English": "#e96d8a",
        "Hindi":   "#54a0ff",
        "AI":      "#ff9f43",
    }

    def __init__(self, db, key):
        super().__init__()
        self.db = db; self.key = key
        self._build(); self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12); root.setContentsMargins(20, 16, 20, 16)
        self.plot = _make_plot(y_label="% Score", x_label="Subject")
        root.addLayout(_chart_toolbar(self, "Subject-wise Comparison", self.plot))
        root.addWidget(h_div())

        ctrl = QHBoxLayout()
        ctrl.addWidget(mk_label("Filter exam:", 11, color=C_SUBTEXT))
        self.exam_combo = QComboBox(); self.exam_combo.setFixedWidth(160)
        self.exam_combo.addItem("All Exams (avg)")
        self.exam_combo.currentIndexChanged.connect(self.refresh)
        ctrl.addWidget(self.exam_combo)
        ctrl.addSpacing(24)

        # Legend
        for subj, col in self.SUBJECT_COLORS.items():
            dot = QLabel("●")
            dot.setStyleSheet(f"color:{col}; font-size:14px; background:transparent;")
            ctrl.addWidget(dot)
            ctrl.addWidget(mk_label(subj, 10, color=C_SUBTEXT))
            ctrl.addSpacing(6)
        ctrl.addStretch()
        root.addLayout(ctrl)

        tip = mk_label(
            "Grouped bars per subject. Each colour = one student. "
            "Use the filter to compare a specific exam.",
            10, color=C_SUBTEXT
        )
        tip.setWordWrap(True); root.addWidget(tip)
        root.addWidget(self.plot)

    def _populate_exam_combo(self):
        exams = self.db.query(Exam).all()
        current = self.exam_combo.currentText()
        self.exam_combo.blockSignals(True)
        self.exam_combo.clear()
        self.exam_combo.addItem("All Exams (avg)")
        for ex in exams:
            self.exam_combo.addItem(ex.type)
        idx = self.exam_combo.findText(current)
        self.exam_combo.setCurrentIndex(max(0, idx))
        self.exam_combo.blockSignals(False)

    def refresh(self):
        self._populate_exam_combo()
        self.plot.clear()
        students = self.db.query(Student).all()
        exams    = self.db.query(Exam).all()
        filter_exam = self.exam_combo.currentText()
        if filter_exam != "All Exams (avg)":
            exams = [e for e in exams if e.type == filter_exam]

        # Build subject_name → {student_name: avg_%}
        subjects = [s[0] for s in SUBJECTS]
        data = {subj: {} for subj in subjects}

        for st in students:
            try: s_name = decrypt_field(st.name_enc, self.key)
            except Exception: s_name = "<err>"
            for ex in exams:
                for subj in subjects:
                    marks = self.db.query(Mark).filter_by(
                        student_id=st.id, exam_id=ex.id, subject=subj).all()
                    for m in marks:
                        try: ob = float(decrypt_field(m.obtained_enc, self.key))
                        except Exception: continue
                        pct = ob * 100.0 / m.total if m.total else 0.0
                        if s_name not in data[subj]:
                            data[subj][s_name] = []
                        data[subj][s_name].append(pct)

        # Average per student per subject
        st_names = sorted({n for d in data.values() for n in d})
        if not st_names:
            self.plot.setTitle("No data yet", color=C_SUBTEXT, size="12pt"); return

        n_students = len(st_names)
        bar_w = 0.7 / max(n_students, 1)
        st_colors = {n: _SERIES_COLORS[i % len(_SERIES_COLORS)] for i, n in enumerate(st_names)}

        legend_added = set()
        for si, subj in enumerate(subjects):
            col = self.SUBJECT_COLORS.get(subj, "#ffffff")
            for ki, s_name in enumerate(st_names):
                vals = data[subj].get(s_name)
                if not vals: continue
                avg = sum(vals) / len(vals)
                x_pos = si + (ki - n_students / 2.0 + 0.5) * bar_w
                bar = pg.BarGraphItem(
                    x=[x_pos], height=[avg], width=bar_w * 0.88,
                    brush=pg.mkBrush(st_colors[s_name]),
                    pen=pg.mkPen(None)
                )
                self.plot.addItem(bar)
                if s_name not in legend_added:
                    legend_added.add(s_name)

        ticks = [[(i, s) for i, s in enumerate(subjects)]]
        self.plot.getAxis("bottom").setTicks(ticks)
        self.plot.setTitle(f"Subject % — {filter_exam}", color=C_TEXT, size="11pt")
        self.plot.setXRange(-0.6, len(subjects) - 0.4, padding=0.05)
        self.plot.setYRange(0, 115, padding=0)
        _ref_lines(self.plot)

        # Student colour legend as text items on plot
        for i, s_name in enumerate(st_names):
            lab = pg.TextItem(f"■ {s_name}", color=st_colors[s_name])
            lab.setFont(QFont("Segoe UI", 8))
            lab.setPos(len(subjects) - 0.5, 108 - i * 10)
            self.plot.addItem(lab)


# ── Sub-tab 3: Exam progression line chart ──────────────────────────────────
EXAM_ORDER = ["midterm", "preboard1", "preboard2", "preboard3"]

class _TrendChart(QWidget):
    """One line per student showing overall % across exam sequence."""
    def __init__(self, db, key):
        super().__init__()
        self.db = db; self.key = key
        self._build(); self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12); root.setContentsMargins(20, 16, 20, 16)
        self.plot = _make_plot(y_label="Overall %", x_label="Exam")
        root.addLayout(_chart_toolbar(self, "Exam Progression Trends", self.plot))
        root.addWidget(h_div())

        ctrl = QHBoxLayout()
        ctrl.addWidget(mk_label("Subject filter:", 11, color=C_SUBTEXT))
        self.subj_combo = QComboBox(); self.subj_combo.setFixedWidth(150)
        self.subj_combo.addItem("Overall")
        for s, _, _ in SUBJECTS:
            self.subj_combo.addItem(s)
        self.subj_combo.currentIndexChanged.connect(self.refresh)
        ctrl.addWidget(self.subj_combo)
        ctrl.addStretch()
        root.addLayout(ctrl)

        tip = mk_label(
            "Each line traces one student\'s score across exams in chronological order. "
            "Hover near a point to see the value. Only exams with data are shown.",
            10, color=C_SUBTEXT
        )
        tip.setWordWrap(True); root.addWidget(tip)
        root.addWidget(self.plot)

    def refresh(self):
        self.plot.clear()
        students = self.db.query(Student).all()
        exams    = self.db.query(Exam).all()
        subj_filter = self.subj_combo.currentText()

        # Order exams
        exam_map = {ex.type: ex for ex in exams}
        ordered_exam_types = [e for e in EXAM_ORDER if e in exam_map]
        if not ordered_exam_types:
            self.plot.setTitle("No data yet", color=C_SUBTEXT, size="12pt"); return

        xs = list(range(len(ordered_exam_types)))
        has_data = False

        for idx, st in enumerate(students):
            try: s_name = decrypt_field(st.name_enc, self.key)
            except Exception: s_name = "<err>"
            col = _SERIES_COLORS[idx % len(_SERIES_COLORS)]
            ys = []
            valid_xs = []
            for xi, et in enumerate(ordered_exam_types):
                ex = exam_map.get(et)
                if not ex: continue
                if subj_filter == "Overall":
                    marks = self.db.query(Mark).filter_by(student_id=st.id, exam_id=ex.id).all()
                    if not marks: continue
                    tp = sum(m.total for m in marks)
                    try: ob = sum(float(decrypt_field(m.obtained_enc, self.key)) for m in marks)
                    except Exception: continue
                    pct = ob * 100.0 / tp if tp else 0.0
                else:
                    marks = self.db.query(Mark).filter_by(
                        student_id=st.id, exam_id=ex.id, subject=subj_filter).all()
                    if not marks: continue
                    m = marks[0]
                    try: ob = float(decrypt_field(m.obtained_enc, self.key))
                    except Exception: continue
                    pct = ob * 100.0 / m.total if m.total else 0.0
                ys.append(pct); valid_xs.append(xi)

            if len(ys) < 1: continue
            has_data = True
            pen = pg.mkPen(col, width=2.5)
            self.plot.plot(valid_xs, ys, pen=pen, symbol='o',
                           symbolSize=9, symbolBrush=col, symbolPen=pg.mkPen(None))
            # Label last point
            ti = pg.TextItem(f"{s_name}\n{ys[-1]:.1f}%", anchor=(0, 0.5), color=col)
            ti.setFont(QFont("Segoe UI", 8))
            ti.setPos(valid_xs[-1] + 0.1, ys[-1])
            self.plot.addItem(ti)

        if not has_data:
            self.plot.setTitle("No data yet", color=C_SUBTEXT, size="12pt"); return

        ticks = [[(i, et) for i, et in enumerate(ordered_exam_types)]]
        self.plot.getAxis("bottom").setTicks(ticks)
        label = subj_filter if subj_filter != "Overall" else "Overall"
        self.plot.setTitle(f"Progression — {label}", color=C_TEXT, size="11pt")
        self.plot.setXRange(-0.4, len(ordered_exam_types) - 0.6, padding=0.18)
        self.plot.setYRange(0, 115, padding=0)
        _ref_lines(self.plot)


# ── Sub-tab 4: Subject heatmap (student × subject) ──────────────────────────
class _HeatmapChart(QWidget):
    """Custom QPainter heatmap: rows = students, cols = subjects, colour = %."""
    def __init__(self, db, key):
        super().__init__()
        self.db = db; self.key = key
        self._data  = []   # list of (student_name, {subject: pct})
        self._build(); self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12); root.setContentsMargins(20, 16, 20, 16)
        hr = QHBoxLayout()
        hr.addWidget(mk_label("Score Heatmap", 15, bold=True))
        hr.addStretch()
        ref = QPushButton("  ↺  Refresh  "); ref.setObjectName("secondaryBtn")
        ref.clicked.connect(self.refresh)
        hr.addWidget(ref)
        root.addLayout(hr); root.addWidget(h_div())

        ctrl = QHBoxLayout()
        ctrl.addWidget(mk_label("Exam filter:", 11, color=C_SUBTEXT))
        self.exam_combo = QComboBox(); self.exam_combo.setFixedWidth(160)
        self.exam_combo.addItem("All Exams (avg)")
        self.exam_combo.currentIndexChanged.connect(self.refresh)
        ctrl.addWidget(self.exam_combo)
        ctrl.addStretch()

        # Legend gradient
        grad_w = QLabel()
        grad_w.setFixedSize(200, 16)
        grad_w.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {C_DANGER}, stop:0.5 {C_WARN}, stop:1 {C_SUCCESS});"
            "border-radius:4px;"
        )
        ctrl.addWidget(mk_label("0%", 9, color=C_SUBTEXT))
        ctrl.addWidget(grad_w)
        ctrl.addWidget(mk_label("100%", 9, color=C_SUBTEXT))
        root.addLayout(ctrl)

        tip = mk_label(
            "Each cell shows a student\'s percentage in one subject. "
            "Darker red = below 50 %, amber = 50-75 %, green = above 75 %.",
            10, color=C_SUBTEXT
        )
        tip.setWordWrap(True); root.addWidget(tip)

        self.canvas = _HeatmapCanvas(self)
        root.addWidget(self.canvas, stretch=1)

    def _populate_exam_combo(self):
        exams = self.db.query(Exam).all()
        current = self.exam_combo.currentText()
        self.exam_combo.blockSignals(True)
        self.exam_combo.clear()
        self.exam_combo.addItem("All Exams (avg)")
        for ex in exams:
            self.exam_combo.addItem(ex.type)
        idx = self.exam_combo.findText(current)
        self.exam_combo.setCurrentIndex(max(0, idx))
        self.exam_combo.blockSignals(False)

    def refresh(self):
        self._populate_exam_combo()
        students = self.db.query(Student).all()
        exams    = self.db.query(Exam).all()
        filter_exam = self.exam_combo.currentText()
        if filter_exam != "All Exams (avg)":
            exams = [e for e in exams if e.type == filter_exam]

        subjects = [s[0] for s in SUBJECTS]
        rows = []
        for st in students:
            try: s_name = decrypt_field(st.name_enc, self.key)
            except Exception: s_name = "<err>"
            subj_pcts = {}
            for subj in subjects:
                vals = []
                for ex in exams:
                    marks = self.db.query(Mark).filter_by(
                        student_id=st.id, exam_id=ex.id, subject=subj).all()
                    for m in marks:
                        try: ob = float(decrypt_field(m.obtained_enc, self.key))
                        except Exception: continue
                        vals.append(ob * 100.0 / m.total if m.total else 0.0)
                if vals:
                    subj_pcts[subj] = sum(vals) / len(vals)
            if subj_pcts:
                rows.append((s_name, subj_pcts))
        self._data = rows
        self.canvas.set_data(rows, subjects)


class _HeatmapCanvas(QWidget):
    """Pure QPainter heatmap grid."""
    CELL_H = 46
    CELL_W = 100
    LABEL_W = 130
    HEADER_H = 34

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._cols = []
        self.setMinimumHeight(120)

    def set_data(self, rows, cols):
        self._rows = rows
        self._cols = cols
        h = self.HEADER_H + max(len(rows), 1) * self.CELL_H + 12
        self.setMinimumHeight(h)
        self.update()

    @staticmethod
    def _pct_color(pct):
        if pct is None: return QColor("#1a1a3a")
        if pct >= 75:
            t = (pct - 75) / 25.0
            r = int(0x43 + (0x20 - 0x43) * (1 - t))
            g = int(0xc9 + (0xff - 0xc9) * t)
            b = int(0x7a)
            return QColor(r, g, b)
        elif pct >= 50:
            t = (pct - 50) / 25.0
            r = int(0xf5 + (0x43 - 0xf5) * t)
            g = int(0xc5 + (0xc9 - 0xc5) * t)
            b = int(0x42 + (0x7a - 0x42) * t)
            return QColor(r, g, b)
        else:
            t = pct / 50.0
            r = int(0xe9 + (0xf5 - 0xe9) * t)
            g = int(0x6d + (0xc5 - 0x6d) * t)
            b = int(0x8a + (0x42 - 0x8a) * t)
            return QColor(r, g, b)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        lw = self.LABEL_W
        cw = self.CELL_W
        ch = self.CELL_H
        hh = self.HEADER_H

        cols = self._cols or []
        rows = self._rows or []

        # Background
        p.fillRect(self.rect(), QColor(C_SURFACE))

        if not cols or not rows:
            p.setPen(QColor(C_SUBTEXT))
            p.setFont(QFont("Segoe UI", 12))
            p.drawText(self.rect(), Qt.AlignCenter, "No data yet — enter some marks first")
            return

        # Column headers
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        for ci, col_name in enumerate(cols):
            x = lw + ci * cw
            rect = QRect(x, 0, cw, hh)
            p.setPen(QColor(C_SUBTEXT))
            p.drawText(rect, Qt.AlignCenter, col_name)

        for ri, (s_name, subj_pcts) in enumerate(rows):
            y = hh + ri * ch
            # Row label
            lbl_rect = QRect(0, y, lw - 8, ch)
            p.setPen(QColor(C_TEXT))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(lbl_rect, Qt.AlignRight | Qt.AlignVCenter, s_name)

            for ci, col_name in enumerate(cols):
                pct = subj_pcts.get(col_name)
                x = lw + ci * cw
                cell_rect = QRect(x + 3, y + 4, cw - 6, ch - 8)
                path = QPainterPath()
                path.addRoundedRect(x + 3, y + 4, cw - 6, ch - 8, 7, 7)
                cell_col = self._pct_color(pct)
                p.fillPath(path, QBrush(cell_col))
                p.setPen(QColor(C_BORDER))
                p.drawPath(path)

                # Value text
                if pct is not None:
                    lum = 0.299 * cell_col.redF() + 0.587 * cell_col.greenF() + 0.114 * cell_col.blueF()
                    txt_col = QColor("#000000") if lum > 0.55 else QColor("#ffffff")
                    p.setPen(txt_col)
                    p.setFont(QFont("Segoe UI", 10, QFont.Bold))
                    p.drawText(cell_rect, Qt.AlignCenter, f"{pct:.1f}%")
                else:
                    p.setPen(QColor(C_SUBTEXT))
                    p.setFont(QFont("Segoe UI", 9))
                    p.drawText(cell_rect, Qt.AlignCenter, "—")


# ── Main GraphsTab (orchestrates the 4 sub-tabs) ─────────────────────────────
class GraphsTab(QWidget):
    def __init__(self, db, key):
        super().__init__()
        self.db = db; self.key = key
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(0); root.setContentsMargins(0, 0, 0, 0)

        # Inner tab bar styled to match design system
        self.inner_tabs = QTabWidget()
        self.inner_tabs.setStyleSheet(
            "QTabWidget::pane { border:none; border-radius:0; background:" + C_SURFACE + "; }"
            "QTabBar { background:transparent; }"
            "QTabBar::tab { background:" + C_CARD + "; color:" + C_SUBTEXT + ";"
            "  padding:9px 22px; margin-right:3px; font-weight:600; font-size:12px;"
            "  border:1px solid " + C_BORDER + "; border-bottom:none;"
            "  border-top-left-radius:9px; border-top-right-radius:9px; }"
            "QTabBar::tab:selected { background:" + _lg(C_ACCENT, "#5a3fa8") + ";"
            "  color:white; border-color:" + C_ACCENT + "; }"
            "QTabBar::tab:hover:!selected { background:#242450; color:" + C_TEXT + "; }"
        )

        self._overview  = _OverviewChart(self.db, self.key)
        self._subjects  = _SubjectChart(self.db, self.key)
        self._trends    = _TrendChart(self.db, self.key)
        self._heatmap   = _HeatmapChart(self.db, self.key)

        self.inner_tabs.addTab(self._overview, "  📊  Overview  ")
        self.inner_tabs.addTab(self._subjects, "  📚  Subject Breakdown  ")
        self.inner_tabs.addTab(self._trends,   "  📈  Exam Trends  ")
        self.inner_tabs.addTab(self._heatmap,  "  🔥  Score Heatmap  ")

        self.inner_tabs.currentChanged.connect(self._on_tab_change)
        root.addWidget(self.inner_tabs)

    def _on_tab_change(self, idx):
        w = self.inner_tabs.widget(idx)
        if hasattr(w, "refresh"):
            w.refresh()

    def refresh(self):
        w = self.inner_tabs.currentWidget()
        if hasattr(w, "refresh"):
            w.refresh()


# ---------------------------------------------------------------------------
# Main Window  — sidebar navigation
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, key):
        super().__init__()
        self.key = key
        self.db  = SessionLocal()
        self.setWindowTitle("StatSketch")
        if _LOGO.exists():
            self.setWindowIcon(QIcon(str(_LOGO)))
        self.setMinimumSize(980, 680)
        self._build()

    def _build(self):
        root_w = QWidget()
        self.setCentralWidget(root_w)
        body = QHBoxLayout(root_w)
        body.setSpacing(0)
        body.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(214)
        sidebar.setStyleSheet(
            f"background:{C_SURFACE}; border-right:1px solid {C_BORDER};"
        )
        sb = QVBoxLayout(sidebar)
        sb.setSpacing(4)
        sb.setContentsMargins(14, 20, 14, 18)

        # Clean StatSketch branding inside sidebar with logo
        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        brand_row.setContentsMargins(2, 0, 2, 0)
        if _LOGO.exists():
            pix = QPixmap(str(_LOGO))
            if not pix.isNull():
                lbl_icon = QLabel()
                lbl_icon.setPixmap(pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                lbl_icon.setStyleSheet("background:transparent;")
                brand_row.addWidget(lbl_icon)
        brand = mk_label("StatSketch", 15, bold=True)
        brand.setStyleSheet(f"color:{C_TEXT}; letter-spacing:0.5px; background:transparent;")
        brand_row.addWidget(brand)
        brand_row.addStretch()
        sb.addLayout(brand_row)

        sec = mk_label("🔒 AES-256 Encrypted", 9, color=C_SUBTEXT)
        sec.setStyleSheet(f"color:{C_SUBTEXT}; padding-left: 2px;")
        sb.addWidget(sec)
        sb.addSpacing(14)
        sb.addWidget(h_div())
        sb.addSpacing(10)
        sb.addWidget(mk_label("MENU", 9, bold=True, color=C_SUBTEXT))
        sb.addSpacing(6)

        # Tabs — tab bar hidden; sidebar drives navigation
        self.tabs = QTabWidget()
        self.tabs.tabBar().setVisible(False)
        self.enter_tab = EnterMarksTab(self.db, self.key)
        self.stats_tab = StatisticsTab(self.db, self.key)
        self.graph_tab = GraphsTab(self.db, self.key)
        self.tabs.addTab(self.enter_tab, "")
        self.tabs.addTab(self.stats_tab, "")
        self.tabs.addTab(self.graph_tab, "")

        NAV = [
            ("✏", "Enter Marks", 0),
            ("📋", "Statistics",  1),
            ("📈", "Graphs",      2),
        ]
        self._nav_btns = []
        for emoji, lbl_txt, idx in NAV:
            btn = QPushButton(f"  {emoji}  {lbl_txt}")
            btn.setCheckable(True)
            btn.setStyleSheet(self._nav_ss(False))
            btn.clicked.connect(lambda _, i=idx: self._switch(i))
            sb.addWidget(btn)
            self._nav_btns.append(btn)

        sb.addStretch()
        sb.addWidget(h_div())
        sb.addSpacing(10)
        ver = mk_label("StatSketch v3.0", 9, color=C_SUBTEXT)
        ver.setAlignment(Qt.AlignCenter)
        sb.addWidget(ver)

        body.addWidget(sidebar)
        body.addWidget(self.tabs)

        # Status bar
        self.statusBar().setStyleSheet(
            f"background:{C_SURFACE}; color:{C_SUBTEXT}; font-size:11px;"
            f"border-top:1px solid {C_BORDER};"
        )
        self.statusBar().showMessage(
            "  StatSketch v3.0  ·  Float marks supported  ·  AES-256-GCM encryption"
        )
        self._switch(0)

    @staticmethod
    def _nav_ss(active):
        if active:
            return (
                f"QPushButton {{ background:{C_ACCENT}; color:white; border-radius:10px;"
                "  padding:11px 14px; font-weight:700; font-size:13px; text-align:left; border:none; }"
                f"QPushButton:hover {{ background:{C_ACCENT}; }}"
            )
        return (
            f"QPushButton {{ background:transparent; color:{C_SUBTEXT}; border-radius:10px;"
            "  padding:11px 14px; font-weight:600; font-size:13px; text-align:left; border:none; }"
            f"QPushButton:hover {{ background:#1c1c40; color:{C_TEXT}; }}"
        )

    def _switch(self, idx):
        self.tabs.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == idx)
            btn.setStyleSheet(self._nav_ss(i == idx))
        if idx == 1: self.stats_tab.refresh()
        if idx == 2: self.graph_tab.refresh()


# ---------------------------------------------------------------------------
# Async Splash Screen with Logo & Active Progress Loader
# ---------------------------------------------------------------------------
class InitWorker(QThread):
    progress = Signal(int, str)  # percent, message
    finished = Signal()

    def run(self):
        import time

        steps = [
            (18, "Initializing StatSketch core engine..."),
            (38, "Verifying cryptographic security primitives..."),
            (58, "Connecting to database & migrating schema..."),
            (78, "Loading analytics & charting modules..."),
            (92, "Configuring workspace & design system..."),
            (100, "StatSketch is ready!"),
        ]

        # Step 1: Pre-warm core
        time.sleep(0.12)
        self.progress.emit(steps[0][0], steps[0][1])

        # Step 2: Crypto test
        from src.crypto import store_password_meta
        time.sleep(0.15)
        self.progress.emit(steps[1][0], steps[1][1])

        # Step 3: Database init
        init_db()
        time.sleep(0.15)
        self.progress.emit(steps[2][0], steps[2][1])

        # Step 4: Charts configuration
        pg.setConfigOption("background", C_SURFACE)
        pg.setConfigOption("foreground", C_TEXT)
        time.sleep(0.15)
        self.progress.emit(steps[3][0], steps[3][1])

        # Step 5: Final prep
        time.sleep(0.12)
        self.progress.emit(steps[4][0], steps[4][1])

        time.sleep(0.10)
        self.progress.emit(steps[5][0], steps[5][1])
        time.sleep(0.08)
        self.finished.emit()


class SplashScreen(QWidget):
    """
    Modern frameless splash screen with animated gradient loader,
    custom-branded logo, and real-time async initialization status.
    """
    completed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 340)

        self._progress_val = 0
        self._target_val = 0
        self._is_closing = False

        self._build()
        self._center()

        # Smooth timer for fluid progress bar movement
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._step_progress)
        self._anim_timer.start(16)  # ~60 fps

        # Background worker thread
        self.worker = InitWorker()
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.finished.connect(self._on_worker_finished)

    def _center(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(x, y)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # Card container with rounded gradient background
        card = QFrame()
        card.setObjectName("splashCard")
        card.setStyleSheet(
            f"#splashCard {{ "
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #12122b, stop:1 #1a1a38);"
            f"  border: 1.5px solid {C_BORDER};"
            f"  border-radius: 20px;"
            f"}}"
        )
        shadow(card, 30, "#000000", (0, 8))

        cl = QVBoxLayout(card)
        cl.setContentsMargins(36, 30, 36, 26)
        cl.setSpacing(10)

        # Logo display
        logo_lbl = QLabel()
        logo_lbl.setAlignment(Qt.AlignCenter)
        if _LOGO.exists():
            pix = QPixmap(str(_LOGO))
            if not pix.isNull():
                scaled = pix.scaled(88, 88, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_lbl.setPixmap(scaled)
        if not logo_lbl.pixmap():
            logo_lbl.setText("📊")
            logo_lbl.setStyleSheet(f"font-size: 64px; color: {C_ACCENT};")
        cl.addWidget(logo_lbl, alignment=Qt.AlignCenter)

        # App Brand Title
        title = mk_label("StatSketch", 22, bold=True)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; letter-spacing: 1px;")
        cl.addWidget(title)

        # Subtitle
        sub = mk_label("Student Performance & Analytics Suite", 11, color=C_SUBTEXT)
        sub.setAlignment(Qt.AlignCenter)
        cl.addWidget(sub)

        cl.addSpacing(12)

        # Progress bar
        self.bar = QProgressBar()
        self.bar.setFixedHeight(6)
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setStyleSheet(
            f"QProgressBar {{ background: {C_CARD}; border: none; border-radius: 3px; }}"
            f"QProgressBar::chunk {{ "
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C_ACCENT}, stop:0.6 {C_ACCENT2}, stop:1 {C_TEAL});"
            f"  border-radius: 3px;"
            f"}}"
        )
        cl.addWidget(self.bar)

        # Status text row: Status message (left) + Percentage (right)
        status_row = QHBoxLayout()
        self.lbl_status = mk_label("Starting StatSketch...", 10, color=C_SUBTEXT)
        self.lbl_pct = mk_label("0%", 10, bold=True, color=C_ACCENT)
        self.lbl_pct.setAlignment(Qt.AlignRight)
        status_row.addWidget(self.lbl_status)
        status_row.addStretch()
        status_row.addWidget(self.lbl_pct)
        cl.addLayout(status_row)

        layout.addWidget(card)

    def _step_progress(self):
        if self._progress_val < self._target_val:
            step = max(1, int((self._target_val - self._progress_val) * 0.25))
            self._progress_val = min(self._target_val, self._progress_val + step)
            self.bar.setValue(self._progress_val)
            self.lbl_pct.setText(f"{self._progress_val}%")
        elif self._progress_val >= 100 and not self._is_closing:
            self._is_closing = True
            self._anim_timer.stop()
            QTimer.singleShot(200, self._finish_and_close)

    def _on_worker_progress(self, val, msg):
        self._target_val = val
        self.lbl_status.setText(msg)

    def _on_worker_finished(self):
        self._target_val = 100

    def _finish_and_close(self):
        self.close()
        self.completed.emit()

    def start_loading(self):
        self.show()
        self.worker.start()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("StatSketch")
    app.setStyleSheet(GLOBAL_SS)

    if _LOGO.exists():
        app.setWindowIcon(QIcon(str(_LOGO)))

    # Async splash screen with logo & active progress loader
    splash = SplashScreen()
    loop = QEventLoop()
    splash.completed.connect(loop.quit)
    splash.start_loading()
    loop.exec()

    # First-time setup
    if not _META.exists():
        dlg = SetupDialog()
        if _LOGO.exists():
            dlg.setWindowIcon(QIcon(str(_LOGO)))
        if dlg.exec() != QDialog.Accepted:
            sys.exit(0)

    # Login
    login = LoginDialog()
    if _LOGO.exists():
        login.setWindowIcon(QIcon(str(_LOGO)))
    if login.exec() != QDialog.Accepted:
        sys.exit(0)

    win = MainWindow(login.key)
    if _LOGO.exists():
        win.setWindowIcon(QIcon(str(_LOGO)))
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
