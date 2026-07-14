import os
import sys
import time
from pathlib import Path
import webbrowser
import winreg

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QFileDialog, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import (
    QPainter, QColor, QPixmap, QPainterPath,
    QLinearGradient, QFont, QFontDatabase,
    QPen, QBrush, QIcon, QCursor
)

MOD_NOMI         = "O'ZBEK TILIDA"
MOD_VERSIYA      = "v1.0.0"
MOD_MUALLIF      = "Muhammadsaid Nizomiy"
TELEGRAM_USER   = "@Muhammadsaid_nizomiy_Official"
YOUTUBE_LINK    = "https://www.youtube.com/@Muhammadsaid_Nizomiy"
PHONE_NUMBER    = "+998997707506"
NISBI_YOL       = ""  
FAYL_D30        = "BigFile_PC.d30"
FAYL_IDX        = "BigFile_PC.idx"
DETROIT_APPID   = "1247740"  

OYNA_W = 540
OYNA_H = 720

C_BG        = "#0B1116"  
C_BLUE      = "#00A2FF"  
C_BLUE_L    = "#66C2FF"  
C_TEXT      = "#E6F4FF"  
C_MUTED     = "#5F7585"  
C_GREEN     = "#00E676"  
C_GREEN_BG  = "#082B1B"
C_RED       = "#FF3D00"  
C_LINE      = "#1F3545"  
C_WHITE     = "#FFFFFF"


def res(name: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, name)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


def steam_topish() -> str | None:
    steam_paths = []
    try:
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for sub in (r"SOFTWARE\Valve\Steam", r"SOFTWARE\WOW6432Node\Valve\Steam"):
                try:
                    key = winreg.OpenKey(hive, sub)
                    path, _ = winreg.QueryValueEx(key, "InstallPath")
                    winreg.CloseKey(key)
                    if path and os.path.exists(path):
                        steam_paths.append(path)
                except Exception:
                    pass
    except Exception:
        pass

    library_dirs = []
    for sp in steam_paths:
        vdf = os.path.join(sp, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf):
            library_dirs.append(os.path.join(sp, "steamapps"))
            try:
                with open(vdf, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if '"path"' in line.lower():
                            parts = line.split('"')
                            if len(parts) >= 4:
                                lib = parts[3].replace("\\\\", "\\")
                                apps = os.path.join(lib, "steamapps")
                                if os.path.exists(apps):
                                    library_dirs.append(apps)
            except Exception:
                pass

    for apps_dir in library_dirs:
        manifest = os.path.join(apps_dir, f"appmanifest_{DETROIT_APPID}.acf")
        if os.path.exists(manifest):
            try:
                with open(manifest, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if '"installdir"' in line.lower():
                            parts = line.split('"')
                            if len(parts) >= 4:
                                full = os.path.join(apps_dir, "common", parts[3])
                                if os.path.exists(full):
                                    return full
            except Exception:
                pass
        direct = os.path.join(apps_dir, "common", "Detroit Become Human")
        if os.path.exists(direct):
            return direct
    return None


class InstallWorker(QThread):
    progress   = Signal(int, str)
    finished   = Signal(bool, str)
    log_signal = Signal(str)

    def __init__(self, game_path: str, restore: bool = False):
        super().__init__()
        self.game_path = game_path
        self.restore   = restore

    def run(self):
        try:
            root = Path(self.game_path)
            dest_d30 = root / FAYL_D30
            dest_idx = root / FAYL_IDX
            bak_d30  = dest_d30.with_suffix(".d30.bak")
            bak_idx  = dest_idx.with_suffix(".idx.bak")

            if self.restore:
                self._restore(dest_d30, dest_idx, bak_d30, bak_idx)
            else:
                self._install(dest_d30, dest_idx, bak_d30, bak_idx)
        except Exception as e:
            self.log_signal.emit(f"Xatolik: {e}")
            self.finished.emit(False, str(e))

    def _copy_with_progress(self, src: Path, dest: Path, start_pct: int, end_pct: int, status_text: str):
        total_size = src.stat().st_size
        copied = 0
        chunk_size = 1024 * 1024

        with open(src, "rb") as fsrc, open(dest, "wb") as fdest:
            while True:
                chunk = fsrc.read(chunk_size)
                if not chunk:
                    break
                fdest.write(chunk)
                copied += len(chunk)

                ratio = copied / total_size
                current_pct = int(start_pct + (end_pct - start_pct) * ratio)
                
                mb_copied = copied // (1024 * 1024)
                mb_total = total_size // (1024 * 1024)
                
                self.progress.emit(current_pct, f"{status_text} ({mb_copied}/{mb_total} MB)")

    def _install(self, dest_d30, dest_idx, bak_d30, bak_idx):
        mod_d30 = Path(sys.argv[0]).parent / FAYL_D30
        if not mod_d30.exists(): mod_d30 = Path(res(FAYL_D30))
        
        mod_idx = Path(sys.argv[0]).parent / FAYL_IDX
        if not mod_idx.exists(): mod_idx = Path(res(FAYL_IDX))

        if not mod_d30.exists() or not mod_idx.exists():
            raise FileNotFoundError("Mod fayllari (d30 yoki idx) topilmadi!")

        self.progress.emit(5, "Tizim tekshirilmoqda...")
        time.sleep(0.4)

        if dest_idx.exists() and not bak_idx.exists():
            self.log_signal.emit("Original idx fayl zaxirlanmoqda...")
            self._copy_with_progress(dest_idx, bak_idx, start_pct=10, end_pct=25, status_text="Indeks zaxiralanyapti...")
            self.log_signal.emit("Original indeks zaxiralandi (.idx.bak)")
            time.sleep(0.2)

        if dest_d30.exists() and not bak_d30.exists():
            self.log_signal.emit("Eski d30 fayl zaxirlanmoqda...")
            self._copy_with_progress(dest_d30, bak_d30, start_pct=25, end_pct=40, status_text="Arxiv zaxiralanyapti...")
            self.log_signal.emit("Eski arxiv zaxiralandi (.d30.bak)")
            time.sleep(0.2)

        self.log_signal.emit("O'zbek tili mod arxiv fayli yozilmoqda...")
        self._copy_with_progress(mod_d30, dest_d30, start_pct=40, end_pct=75, status_text="Arxiv o'rnatilmoqda...")

        self.log_signal.emit("Yangi indeks fayli yozilmoqda...")
        self._copy_with_progress(mod_idx, dest_idx, start_pct=75, end_pct=90, status_text="Indeks o'rnatilmoqda...")

        self.progress.emit(95, "Fayllar tekshirilmoqda...")
        time.sleep(0.4)

        self.progress.emit(100, "Muvaffaqiyatli o'rnatildi!")
        self.log_signal.emit("Detroit: Become Human O'zbek tili muvaffaqiyatli o'rnatildi!")
        self.finished.emit(True, "")

    def _restore(self, dest_d30, dest_idx, bak_d30, bak_idx):
        if not bak_idx.exists():
            raise FileNotFoundError("Zaxira indeks (.idx.bak) fayli topilmadi!")

        self.progress.emit(10, "Zaxira tekshirilmoqda...")
        time.sleep(0.4)

        self.log_signal.emit("Original indeks tiklanmoqda...")
        self._copy_with_progress(bak_idx, dest_idx, start_pct=20, end_pct=60, status_text="Indeks tiklanmoqda...")

        if bak_d30.exists():
            self.log_signal.emit("Original d30 arxiv tiklanmoqda...")
            self._copy_with_progress(bak_d30, dest_d30, start_pct=60, end_pct=90, status_text="Arxiv tiklanmoqda...")
        else:
            if dest_d30.exists():
                os.remove(dest_d30)
                self.log_signal.emit("Mod d30 fayli muvaffaqiyatli o'chirildi.")

        self.progress.emit(95, "Tekshirilmoqda...")
        time.sleep(0.3)

        self.progress.emit(100, "Asl holat tiklandi!")
        self.log_signal.emit("Original o'yin tili muvaffaqiyatli tiklandi")
        self.finished.emit(True, "restored")


class CircularAvatar(QWidget):
    def __init__(self, image_path: str, size: int = 86,
                 border_color: str = C_BLUE_L, border_width: int = 3, parent=None):
        super().__init__(parent)
        self._image_path  = image_path  
        self._size        = size + border_width * 2
        self._bw          = border_width
        self._border_color = QColor(border_color)
        self._pixmap      = None

        self.setFixedSize(self._size, self._size)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        if os.path.exists(image_path):
            src = QPixmap(image_path).scaled(
                size, size,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation)

            masked = QPixmap(size, size)
            masked.fill(Qt.transparent)
            p = QPainter(masked)
            p.setRenderHint(QPainter.Antialiasing, True)
            p.setRenderHint(QPainter.SmoothPixmapTransform, True)
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            p.setClipPath(path)
            p.drawPixmap(0, 0, src)
            p.end()
            self._pixmap = masked

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and os.path.exists(self._image_path):
            try:
                os.startfile(self._image_path)
            except Exception:
                pass
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        total = self._size
        bw    = self._bw
        inner = total - bw * 2

        pen = QPen(self._border_color, bw)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        offset = bw / 2
        p.drawEllipse(int(offset), int(offset), int(total - bw), int(total - bw))

        if self._pixmap:
            p.drawPixmap(bw, bw, self._pixmap)
        else:
            p.setBrush(QBrush(QColor("#101B24")))
            p.setPen(Qt.NoPen)
            p.drawEllipse(bw, bw, inner, inner)
            p.setPen(QColor(C_BLUE_L))
            fnt = QFont("Montserrat", inner // 3, QFont.Bold)
            p.setFont(fnt)
            p.drawText(bw, bw, inner, inner, Qt.AlignCenter, "M")
        p.end()


class GoldProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._color = QColor(C_BLUE)
        self.setFixedHeight(5)

    def setValue(self, v: int):
        self._value = max(0, min(100, v))
        self.update()

    def setColor(self, c: str):
        self._color = QColor(c)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = h // 2

        p.setBrush(QBrush(QColor("#111A21")))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, w, h, r, r)

        if self._value > 0:
            fill_w = int(w * self._value / 100)
            if fill_w > 0:
                p.setBrush(QBrush(self._color))
                p.drawRoundedRect(0, 0, fill_w, h, r, r)
        p.end()


class SocialBtn(QWidget):
    def __init__(self, icon_path: str, label: str, url: str, parent=None):
        super().__init__(parent)
        self._url = url
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 4, 12, 4)

        if os.path.exists(icon_path):
            px = QLabel()
            pm = QPixmap(icon_path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            px.setPixmap(pm)
            px.setAlignment(Qt.AlignCenter)
            layout.addWidget(px)

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignCenter)
        
        if "Telegram" in label:
            lbl.setStyleSheet("color: #3AA1E0; font-size: 11px; font-family: Montserrat; border: none; background: transparent;")
        elif "YouTube" in label:
            lbl.setStyleSheet("color: #E64A41; font-size: 11px; font-family: Montserrat; border: none; background: transparent;")
        else:
            lbl.setStyleSheet(f"color: {C_BLUE_L}; font-size: 11px; font-family: Montserrat; border: none; background: transparent;")
            
        layout.addWidget(lbl)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        webbrowser.open(self._url)


class ShaffofKarta(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg_color = QColor(11, 20, 28, 215)  
        p.setBrush(QBrush(bg_color))
        p.setPen(QPen(QColor(C_LINE), 1))
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 6, 6)
        p.end()


class InstallerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Detroit: Become Human — {MOD_NOMI}")
        self.setFixedSize(OYNA_W, OYNA_H)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        self._drag_pos = None
        self._game_path = ""
        self._worker = None

        self._setup_fonts()
        self._build_ui()
        self._set_icon()

        QTimer.singleShot(200, self._auto_detect)

    def _set_icon(self):
        icon_path = res("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _setup_fonts(self):
        for name in ["Montserrat-Regular.ttf", "Montserrat-Bold.ttf", "Consolas.ttf"]:
            p = res(name)
            if os.path.exists(p):
                QFontDatabase.addApplicationFont(p)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setBrush(QBrush(QColor(C_BG)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect(), 14, 14)

        bg_path = res("background.png")
        if os.path.exists(bg_path):
            pm = QPixmap(bg_path).scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            p.setOpacity(0.35) 
            p.drawPixmap(0, 0, pm)
            p.setOpacity(1.0)

        grad = QLinearGradient(0, self.height() * 0.3, 0, self.height())
        grad.setColorAt(0, QColor("#00000000"))
        grad.setColorAt(1, QColor("#0B1116E5"))
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(self.rect(), 14, 14)

        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(C_LINE), 1))
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 14, 14)
        p.end()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_title_bar())

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(24, 10, 24, 24)
        lay.setSpacing(14)

        lay.addWidget(self._make_header())
        lay.addWidget(self._make_path_block())
        lay.addWidget(self._make_author_block_layered()) 
        lay.addWidget(self._make_progress_block())
        lay.addLayout(self._make_buttons())

        root.addWidget(content)

    def _make_title_bar(self):
        bar = QWidget()
        bar.setFixedHeight(34)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 0, 6, 0)

        title = QLabel("")
        lay.addWidget(title)
        lay.addStretch()

        for sym, cmd in [("─", self.showMinimized), ("✕", self.close)]:
            btn = QPushButton(sym)
            btn.setFixedSize(28, 28)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {C_MUTED};
                    font-size: 12px;
                    border: none;
                }}
                QPushButton:hover {{
                    color: {C_TEXT};
                }}
            """)
            btn.clicked.connect(cmd)
            lay.addWidget(btn)
        return bar

    def _make_header(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 4)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignCenter)

        badge = QLabel("R A S M I Y  M O D")
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"color: {C_BLUE}; font-size: 11px; font-family: Montserrat; font-weight: bold; letter-spacing: 3px; border: none; background: transparent;")

        main_title = QLabel("DETROIT: BECOME HUMAN")
        main_title.setAlignment(Qt.AlignCenter)
        main_title.setStyleSheet(f"color: {C_TEXT}; font-size: 26px; font-family: Montserrat; font-weight: bold; letter-spacing: 1px; border: none; background: transparent;")

        sub = QLabel("Muhammadsaid Nizomiy  |  +998997707506")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color: {C_BLUE_L}; font-size: 13px; font-family: Montserrat; font-weight: bold; letter-spacing: 0.5px; border: none; background: transparent;")

        lay.addWidget(badge)
        lay.addWidget(main_title)
        lay.addWidget(sub)
        return w

    def _make_path_block(self):
        card = ShaffofKarta()
        lay  = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        title = QLabel("📁  O'YIN PAPKASINI TANLANG")
        title.setStyleSheet(f"color: {C_TEXT}; font-size: 12px; font-family: Montserrat; font-weight: bold; border: none; background: transparent;")
        lay.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(8)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("O'yin papkasi yo'li...")
        self.entry.setStyleSheet(f"""
            QLineEdit {{
                background: #080D12;
                border: 1px solid {C_LINE};
                border-radius: 4px;
                color: #A4B9C7;
                font-size: 11px;
                font-family: Montserrat;
                padding: 0 10px;
                height: 32px;
            }}
        """)
        self.entry.textChanged.connect(self._check_path)
        row.addWidget(self.entry)

        btn_steam = QPushButton("⚡  Steam")
        btn_steam.setFixedSize(85, 32)
        btn_steam.setCursor(QCursor(Qt.PointingHandCursor))
        btn_steam.setStyleSheet(f"""
            QPushButton {{
                background: {C_GREEN_BG};
                border: 1px solid {C_GREEN};
                border-radius: 4px;
                color: #74E39B;
                font-size: 12px;
                font-family: Montserrat;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #13422A; }}
        """)
        btn_steam.clicked.connect(self._steam_search)
        row.addWidget(btn_steam)

        btn_browse = QPushButton("📁  Tanlash")
        btn_browse.setFixedSize(95, 32)
        btn_browse.setCursor(QCursor(Qt.PointingHandCursor))
        btn_browse.setStyleSheet(f"""
            QPushButton {{
                background: #15222E;
                border: 1px solid {C_LINE};
                border-radius: 4px;
                color: #D2E4F0;
                font-size: 12px;
                font-family: Montserrat;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #223547; }}
        """)
        btn_browse.clicked.connect(self._browse)
        row.addWidget(btn_browse)

        lay.addLayout(row)

        self.lbl_indicator = QLabel("● O'yin papkasini tanlang")
        self.lbl_indicator.setStyleSheet(f"color: {C_MUTED}; font-size: 11px; font-family: Montserrat; border: none; background: transparent;")
        lay.addWidget(self.lbl_indicator)

        return card

    def _make_author_block_layered(self):
        baza_karta = ShaffofKarta()
        baza_karta.setStyleSheet(f"""
            ShaffofKarta {{
                border-left: 4px solid {C_BLUE};
                border-top-left-radius: 2px;
                border-bottom-left-radius: 2px;
            }}
        """)
        baza_lay = QVBoxLayout(baza_karta)
        baza_lay.setContentsMargins(0, 0, 0, 0)
        baza_lay.setSpacing(0)

        info_konteyner = QWidget()
        info_konteyner.setAttribute(Qt.WA_TranslucentBackground)
        info_konteyner.setStyleSheet("""
            QWidget { border: none; background: transparent; }
            QLabel { border: none; background: transparent; }
        """)

        lay = QVBoxLayout(info_konteyner)
        lay.setContentsMargins(18, 14, 16, 12)
        lay.setSpacing(10)

        section_title = QLabel("LOYIHA MUALLIFI")
        section_title.setStyleSheet(f"color: {C_BLUE_L}; font-size: 10px; font-family: Montserrat; font-weight: bold; letter-spacing: 3px; margin-left: 165px;")
        lay.addWidget(section_title)

        avatar_row = QHBoxLayout()
        avatar_row.setSpacing(0) 
        avatar_row.setContentsMargins(0, 0, 0, 0) 
        avatar_row.setAlignment(Qt.AlignCenter) 

        avatar = CircularAvatar(res("Muhammadsaid.png"), size=76, border_color=C_BLUE, border_width=2)
        avatar_row.addWidget(avatar)

        info = QVBoxLayout()
        info.setSpacing(2)
        info.setContentsMargins(22, 0, 0, 0) 
        info.setAlignment(Qt.AlignVCenter)

        name_lbl = QLabel(MOD_MUALLIF.upper())
        name_lbl.setStyleSheet(f"color: {C_WHITE}; font-size: 16px; font-family: Montserrat; font-weight: bold; letter-spacing: 0.5px;")

        role_lbl = QLabel("Lead Developer & Localization Specialist")
        role_lbl.setStyleSheet("color: #7A93A6; font-size: 11px; font-family: Montserrat; font-weight: 500;")

        ver_lbl = QLabel(f"Loyiha versiyasi: {MOD_VERSIYA}  •  2026")
        ver_lbl.setStyleSheet("color: #4B5E6D; font-size: 11px; font-family: Montserrat;")

        info.addWidget(name_lbl)
        info.addWidget(role_lbl)
        info.addWidget(ver_lbl)
        
        avatar_row.addLayout(info)
        lay.addLayout(avatar_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: #1A2B38; border: none; max-height: 1px;")
        lay.addWidget(sep)

        social_row = QHBoxLayout()
        social_row.setAlignment(Qt.AlignCenter)  
        social_row.setSpacing(24)

        tg_url = f"https://t.me/{TELEGRAM_USER[1:]}"
        social_row.addWidget(SocialBtn(res("telegram.png"), "Telegram", tg_url))
        social_row.addWidget(SocialBtn(res("youtube.png"),  "YouTube",  YOUTUBE_LINK))
        social_row.addWidget(SocialBtn(res("phone.png"), PHONE_NUMBER, f"tel:{PHONE_NUMBER}"))
        lay.addLayout(social_row)

        baza_lay.addWidget(info_konteyner)
        return baza_karta

    def _make_progress_block(self):
        card = ShaffofKarta()
        lay  = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(6)

        title = QLabel("⚡  O'RNATISH HOLATI")
        title.setStyleSheet(f"color: {C_TEXT}; font-size: 12px; font-family: Montserrat; font-weight: bold; border: none; background: transparent;")
        lay.addWidget(title)

        status_row = QHBoxLayout()
        self.lbl_status = QLabel("Kutish...")
        self.lbl_status.setStyleSheet("color: #6A8294; font-size: 11px; font-family: Montserrat; border: none; background: transparent;")
        self.lbl_pct = QLabel("0%")
        self.lbl_pct.setStyleSheet(f"color: {C_BLUE_L}; font-size: 12px; font-family: Montserrat; font-weight: bold; border: none; background: transparent;")
        status_row.addWidget(self.lbl_status)
        status_row.addStretch()
        status_row.addWidget(self.lbl_pct)
        lay.addLayout(status_row)

        self.progress_bar = GoldProgressBar()
        lay.addWidget(self.progress_bar)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFixedHeight(50)
        self.txt_log.setStyleSheet(f"""
            QTextEdit {{
                background: #060A0E;
                border: 1px solid #14232F;
                border-radius: 4px;
                color: #587285;
                font-size: 11px;
                font-family: Consolas, monospace;
                padding: 4px;
            }}
        """)
        lay.addWidget(self.txt_log)

        return card

    def _make_buttons(self):
        row = QHBoxLayout()
        row.setSpacing(10)

        self.btn_readme = QPushButton("  QO'LLANMA")
        self.btn_readme.setFixedHeight(46)
        self.btn_readme.setFixedWidth(120)
        self.btn_readme.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_readme.setStyleSheet(f"""
            QPushButton {{
                background: #080D12;
                border: 1px solid #1C3245;
                border-radius: 4px;
                color: #83A1B8;
                font-size: 11px;
                font-family: Montserrat;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: #14222E;
                color: {C_TEXT};
                border-color: {C_BLUE};
            }}
        """)
        self.btn_readme.clicked.connect(self._open_readme)
        row.addWidget(self.btn_readme)

        self.btn_install = QPushButton("  O'RNATISH")
        self.btn_install.setFixedHeight(46)
        self.btn_install.setCursor(QCursor(Qt.PointingHandCursor))
        
        ic_install = res("install.png")
        if os.path.exists(ic_install):
            self.btn_install.setIcon(QIcon(ic_install))
            self.btn_install.setIconSize(QSize(18, 18))

        self.btn_install.setStyleSheet(f"""
            QPushButton {{
                background: #0D2233;
                border: 1px solid {C_BLUE};
                border-radius: 4px;
                color: {C_BLUE_L};
                font-size: 12px;
                font-family: Montserrat;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: #14354F;
                border-color: {C_BLUE_L};
            }}
            QPushButton:disabled {{
                background: #0A1117;
                color: #374B59;
                border-color: #162430;
            }}
        """)
        self.btn_install.clicked.connect(self._start_install)
        row.addWidget(self.btn_install, 2)

        self.btn_restore = QPushButton("  TIKLASH")
        self.btn_restore.setFixedHeight(46)
        self.btn_restore.setFixedWidth(100)
        self.btn_restore.setCursor(QCursor(Qt.PointingHandCursor))
        
        ic_restore = res("restore.png")
        if os.path.exists(ic_restore):
            self.btn_restore.setIcon(QIcon(ic_restore))
            self.btn_restore.setIconSize(QSize(16, 16))

        self.btn_restore.setStyleSheet(f"""
            QPushButton {{
                background: #080D12;
                border: 1px solid #162633;
                border-radius: 4px;
                color: #6C8699;
                font-size: 12px;
                font-family: Montserrat;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #14222E;
                color: {C_TEXT};
            }}
        """)
        self.btn_restore.clicked.connect(self._start_restore)
        row.addWidget(self.btn_restore)

        return row

    def _open_readme(self):
        readme_path = Path(sys.argv[0]).parent / "README(Majburiy).txt"
        if not readme_path.exists():
            readme_path = Path(res("README(Majburiy).txt"))

        if readme_path.exists():
            try:
                os.startfile(readme_path)
                self._log("Qo'llanma ochildi.")
            except Exception as e:
                self._log(f"Qo'llanmani ochishda xatolik: {e}")
        else:
            self._log("README(Majburiy).txt topilmadi!")
            QMessageBox.warning(self, "Topilmadi", "Qo'llanma fayli topilmadi!")

    def _log(self, text: str):
        self.txt_log.append(f">> {text}")
        self.txt_log.verticalScrollBar().setValue(self.txt_log.verticalScrollBar().maximum())

    def _check_path(self, path: str):
        self._game_path = path.strip()
        if not path:
            self._set_indicator("● O'yin papkasini tanlang", C_MUTED)
            return
            
        exe = Path(path) / "DetroitBecomeHuman.exe"
        idx = Path(path) / FAYL_IDX
        
        if exe.exists() and idx.exists():
            self._set_indicator("✓ O'yin topildi — o'rnatishga tayyor", C_GREEN)
        elif exe.exists():
            self._set_indicator("⚠ O'yin exe topildi, lekin original BigFile_PC.idx yo'q", C_BLUE)
        elif Path(path).exists():
            self._set_indicator("⚠ Katalog topildi, DetroitBecomeHuman.exe aniqlanmadi", C_BLUE)
        else:
            self._set_indicator("✗ Noto'g'ri katalog", C_RED)

    def _set_indicator(self, text, color):
        self.lbl_indicator.setText(text)
        self.lbl_indicator.setStyleSheet(f"color: {color}; font-size: 11px; font-family: Montserrat; border: none; background: transparent;")

    def _auto_detect(self):
        found = steam_topish()
        if found:
            self.entry.setText(found)
            self._log("O'yin katalogi aniqlandi")
            self._log("Steam orqali avtomatik topildi")

    def _steam_search(self):
        self._log("Steam orqali qidirilmoqda...")
        found = steam_topish()
        if found:
            self.entry.setText(found)
            self._log("Steam papkasi topildi!")
        else:
            self._log("Steam'da Detroit topilmadi — qo'lda tanlang")
            QMessageBox.warning(self, "Topilmadi", "Steam orqali 'Detroit: Become Human' topilmadi.")

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "Detroit: Become Human papkasini tanlang")
        if path:
            self.entry.setText(path)

    def _set_progress(self, val: int, text: str, color: str = C_BLUE):
        self.progress_bar.setValue(val)
        self.progress_bar.setColor(color)
        self.lbl_status.setText(text)
        self.lbl_pct.setText(f"{val}%")

    def _start_install(self):
        path = self.entry.text().strip()
        if not path or not Path(path).exists():
            QMessageBox.critical(self, "Xato", "O'yin papkasi to'g'ri ko'rsatilmadi!")
            return
        self._run_worker(path, restore=False)

    def _start_restore(self):
        path = self.entry.text().strip()
        if not path or not Path(path).exists():
            QMessageBox.critical(self, "Xato", "Katalog aniqlanmadi!")
            return
            
        bak = Path(path) / f"{FAYL_IDX}.bak"
        if not bak.exists():
            QMessageBox.warning(self, "Zaxira yo'q", "Zaxira (idx.bak) fayli topilmadi!")
            return
            
        reply = QMessageBox.question(self, "Tiklash", "Original tilni tiklashni xohlaysizmi?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._run_worker(path, restore=True)

    def _run_worker(self, path: str, restore: bool):
        self.btn_install.setEnabled(False)
        self.btn_restore.setEnabled(False)
        self._set_progress(0, "Boshlanmoqda...", C_BLUE)

        self._worker = InstallWorker(path, restore)
        self._worker.progress.connect(lambda v, t: self._set_progress(v, t))
        self._worker.log_signal.connect(self._log)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, ok: bool, msg: str):
        self.btn_restore.setEnabled(True)
        self.btn_install.setEnabled(True)
        if ok:
            if msg == "restored":
                self._set_progress(100, "Asl holat tiklandi!", C_GREEN)
                QMessageBox.information(self, "Tiklandi", "O'yin tili asl holatiga qaytarildi!")
            else:
                self._set_progress(100, "Muvaffaqiyatli o'rnatildi!", C_GREEN)
                QMessageBox.information(self, "Tayyor!", "O'zbek tili muvaffaqiyatli o'rnatildi!")
        else:
            self._set_progress(0, "Xatolik yuz berdi!", C_RED)


if __name__ == "__main__":
    try:
        from PySide6.QtGui import QGuiApplication
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Detroit Uzbek Mod Installer")

    win = InstallerWindow()
    win.show()
    sys.exit(app.exec())