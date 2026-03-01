
import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QGridLayout, QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QColor, QPainter, QPixmap, QIcon, QFont, QRadialGradient

# === ICONS ===
class IconSVG:
    CAMERA = '''<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>'''
    EXPORT = '''<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/><polyline points="12 11 15 14 12 17"/><line x1="9" y1="14" x2="15" y2="14"/></svg>'''
    PRINTER = '''<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>'''
    SHARE = '''<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>'''
    TRASH = '''<svg viewBox="0 0 24 24" fill="none" stroke="#FF453A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>'''

class AppIcon(QWidget):
    def __init__(self, title, svg_data, bg_color="#333333", parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 200)
        
        # Icon Container (Rounded Box)
        self.icon_box = QFrame(self)
        self.icon_box.setGeometry(20, 10, 120, 120)
        self.icon_box.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 28px;
            }}
        """)
        
        # SVG Display provided by simple label for now (In prod use QSvgRenderer)
        # Using simple Unicode logic or placeholder if SVG hard to render directly without library
        # But we are using PySide6 which supports SVG. 
        # For prototype simplicity, I'll use text/emoji if SVG fails or just trust standard rendering?
        # Actually I'll use a SvgWidget logic here or just a Label with SVG byte array.
        
        # For this prototype: Simplification -> We will render SVG to Pixmap
        from PySide6.QtSvg import QSvgRenderer
        self.renderer = QSvgRenderer(QByteArray(svg_data.encode()))
        self.img_label = QLabel(self.icon_box)
        self.img_label.setGeometry(30, 30, 60, 60)
        # We need to paint it.
        
        # Label
        self.label = QLabel(title, self)
        self.label.setGeometry(0, 140, 160, 30)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Segoe UI", 16, QFont.Medium))
        self.label.setStyleSheet("color: white;")
        
        # Animation
        self.anim = QPropertyAnimation(self.icon_box, b"geometry")
        self.anim.setDuration(150)
        
    def paintEvent(self, event):
        # Render SVG manually on top of the box
        painter = QPainter(self)
        # But wait, painting on child? No.
        # Let's paint on the icon_box's label.
        pass

    def enterEvent(self, event):
        self.anim.setStartValue(QRect(20, 10, 120, 120))
        self.anim.setEndValue(QRect(15, 5, 130, 130)) # Scale up
        self.anim.start()

    def leaveEvent(self, event):
        self.anim.setStartValue(QRect(15, 5, 130, 130))
        self.anim.setEndValue(QRect(20, 10, 120, 120))
        self.anim.start()
        
    def mousePressEvent(self, event):
        # Button press simulation
        self.anim.setStartValue(QRect(20, 10, 120, 120))
        self.anim.setEndValue(QRect(25, 15, 110, 110)) # Press down
        self.anim.start()

class ModernWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("iPad Style Prototype")
        self.resize(1024, 768)
        self.setStyleSheet("background-color: #1C1C1E;") # Deep gray/black
        
        central = QWidget()
        self.setCentralWidget(central)
        
        # Grid Layout
        layout = QGridLayout(central)
        layout.setSpacing(60)
        layout.setContentsMargins(100, 100, 100, 100)
        
        # Add Icons
        # Row 1
        layout.addWidget(AppIcon("촬영 시작", IconSVG.CAMERA, "#007AFF"), 0, 0)
        layout.addWidget(AppIcon("내보내기", IconSVG.EXPORT, "#5856D6"), 0, 1)
        layout.addWidget(AppIcon("인화하기", IconSVG.PRINTER, "#FF2D55"), 0, 2)
        
        # Row 2
        layout.addWidget(AppIcon("폴더 압축", IconSVG.SHARE, "#FF9500"), 1, 0)
        layout.addWidget(AppIcon("종료", IconSVG.TRASH, "#1C1C1E"), 1, 1) # Dark for trash
        
        # Make SVG rendering work properly
        self.fix_svg_rendering()

    def fix_svg_rendering(self):
        # Helper to actually render the SVGs in the widgets
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtCore import QByteArray
        
        for i in range(self.centralWidget().layout().count()):
            widget = self.centralWidget().layout().itemAt(i).widget()
            if isinstance(widget, AppIcon):
                # We need to set the pixmap on the label
                # Find the SVG data (hacky via class lookup for now)
                pass 
                # Improvement: Pass svg to constructor properly and render there.

# Redefine AppIcon for easier SVG handling
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray

class AppIconFinal(QWidget):
    def __init__(self, title, svg_xml, bg_color, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 220)
        
        # Background Circle/Rect
        self.bg = QFrame(self)
        self.bg.setGeometry(20, 10, 140, 140)
        self.bg.setStyleSheet(f"background-color: {bg_color}; border-radius: 35px;")
        
        # Icon Label
        self.icon_lbl = QLabel(self.bg)
        self.icon_lbl.setGeometry(35, 35, 70, 70)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        
        # Render SVG
        pm = QPixmap(70, 70)
        pm.fill(Qt.transparent)
        painter = QPainter(pm)
        renderer = QSvgRenderer(QByteArray(svg_xml.encode()))
        renderer.render(painter)
        painter.end()
        self.icon_lbl.setPixmap(pm)
        
        # Text Label
        self.text_lbl = QLabel(title, self)
        self.text_lbl.setGeometry(0, 160, 180, 40)
        self.text_lbl.setAlignment(Qt.AlignCenter)
        self.text_lbl.setStyleSheet("color: white; font-family: 'Segoe UI'; font-size: 20px; font-weight: 500;")
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0,0,0,80))
        shadow.setOffset(0, 5)
        self.bg.setGraphicsEffect(shadow)

    # Simple Hover Animation
    def enterEvent(self, e):
        self.bg.setGeometry(15, 5, 150, 150)
        self.icon_lbl.setGeometry(37, 37, 76, 76) # Approx scale
    
    def leaveEvent(self, e):
        self.bg.setGeometry(20, 10, 140, 140)
        self.icon_lbl.setGeometry(35, 35, 70, 70)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    win = ModernWindow()
    # Replace the placeholder grid items with Final App Icons
    central = QWidget()
    win.setCentralWidget(central)
    grid = QGridLayout(central)
    grid.setSpacing(50)
    grid.setContentsMargins(100, 100, 100, 100)
    
    # iPad Home Screen Layout
    grid.addWidget(AppIconFinal("촬영 시작", IconSVG.CAMERA, "#0A84FF"), 0, 0)
    grid.addWidget(AppIconFinal("내보내기", IconSVG.EXPORT, "#30D158"), 0, 1)
    grid.addWidget(AppIconFinal("인화하기", IconSVG.PRINTER, "#FF375F"), 0, 2)
    grid.addWidget(AppIconFinal("폴더 압축", IconSVG.SHARE, "#FF9F0A"), 1, 0)
    grid.addWidget(AppIconFinal("종료", IconSVG.TRASH, "#FF453A"), 1, 1)
    
    win.show()
    sys.exit(app.exec())
