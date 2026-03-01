import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QFileDialog, QGraphicsView, QGraphicsScene, 
                             QGraphicsRectItem, QGraphicsPixmapItem, QMessageBox,
                             QHBoxLayout, QLabel)
from PySide6.QtGui import QPixmap, QColor, QPen, QBrush, QImage, QPainter
from PySide6.QtCore import Qt, QRectF, QPointF, QSize
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

class CropOverlay(QGraphicsRectItem):
    """5:7 비율 고정 4개 모서리 조절 + 선명한 3분할 그리드"""
    def __init__(self, rect, parent=None):
        super().__init__(rect, parent)
        self.setPen(QPen(QColor(255, 255, 255), 2)) # 더 굵고 진한 선
        self.setBrush(QBrush(QColor(0, 0, 0, 80)))
        self.setFlags(QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        self.handle_size = 18
        self.resizing = None # None, 'TL', 'TR', 'BL', 'BR'
        self.aspect_ratio = 5 / 7
        
    def paint(self, painter, option, widget):
        rect = self.rect()
        
        # 1. 3분할 그리드 (매우 선명하게)
        grid_pen = QPen(QColor(255, 255, 255, 200), 1.5, Qt.SolidLine)
        painter.setPen(grid_pen)
        
        # 세로선
        w3 = rect.width() / 3
        painter.drawLine(rect.left() + w3, rect.top(), rect.left() + w3, rect.bottom())
        painter.drawLine(rect.left() + w3 * 2, rect.top(), rect.left() + w3 * 2, rect.bottom())
        
        # 가로선
        h3 = rect.height() / 3
        painter.drawLine(rect.left(), rect.top() + h3, rect.right(), rect.top() + h3)
        painter.drawLine(rect.left(), rect.top() + h3 * 2, rect.right(), rect.top() + h3 * 2)

        # 2. 메인 테두리
        painter.setPen(QPen(QColor(255, 255, 255), 3)) # 테두리는 더 진하게
        painter.drawRect(rect)
        
        # 3. 4개 모서리 핸들
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(Qt.black, 1))
        h = self.handle_size
        painter.drawRect(rect.left(), rect.top(), h, h) # TL
        painter.drawRect(rect.right() - h, rect.top(), h, h) # TR
        painter.drawRect(rect.left(), rect.bottom() - h, h, h) # BL
        painter.drawRect(rect.right() - h, rect.bottom() - h, h, h) # BR

    def _get_handle_at(self, pos):
        rect = self.rect()
        h = self.handle_size
        if QRectF(rect.left(), rect.top(), h, h).contains(pos): return 'TL'
        if QRectF(rect.right() - h, rect.top(), h, h).contains(pos): return 'TR'
        if QRectF(rect.left(), rect.bottom() - h, h, h).contains(pos): return 'BL'
        if QRectF(rect.right() - h, rect.bottom() - h, h, h).contains(pos): return 'BR'
        return None

    def mousePressEvent(self, event):
        self.resizing = self._get_handle_at(event.pos())
        if self.resizing:
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            curr_rect = self.rect()
            pos = event.pos()
            
            if self.resizing == 'BR':
                new_w = max(50, pos.x() - curr_rect.left())
                new_h = new_w / self.aspect_ratio
                self.setRect(QRectF(curr_rect.left(), curr_rect.top(), new_w, new_h))
            elif self.resizing == 'TL':
                new_w = max(50, curr_rect.right() - pos.x())
                new_h = new_w / self.aspect_ratio
                self.setRect(QRectF(curr_rect.right() - new_w, curr_rect.bottom() - new_h, new_w, new_h))
            elif self.resizing == 'TR':
                new_w = max(50, pos.x() - curr_rect.left())
                new_h = new_w / self.aspect_ratio
                self.setRect(QRectF(curr_rect.left(), curr_rect.bottom() - new_h, new_w, new_h))
            elif self.resizing == 'BL':
                new_w = max(50, curr_rect.right() - pos.x())
                new_h = new_w / self.aspect_ratio
                self.setRect(QRectF(curr_rect.right() - new_w, curr_rect.top(), new_w, new_h))
                
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.resizing = None
        super().mouseReleaseEvent(event)

    def hoverMoveEvent(self, event):
        handle = self._get_handle_at(event.pos())
        if handle in ['TL', 'BR']: self.setCursor(Qt.SizeFDiagCursor)
        elif handle in ['TR', 'BL']: self.setCursor(Qt.SizeBDiagCursor)
        else: self.setCursor(Qt.SizeAllCursor)
        super().hoverMoveEvent(event)

class CropView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.pixmap_item = None
        self.crop_item = None
        self.setBackgroundBrush(QBrush(QColor(20, 20, 20)))

    def load_image(self, path):
        self.scene.clear()
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return False
            
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        
        img_rect = pixmap.rect()
        w = img_rect.width() * 0.7
        h = w * (7 / 5)
        
        if h > img_rect.height():
            h = img_rect.height() * 0.7
            w = h * (5 / 7)
            
        self.crop_item = CropOverlay(QRectF(0, 0, w, h))
        self.crop_item.setPos((img_rect.width()-w)/2, (img_rect.height()-h)/2)
        self.scene.addItem(self.crop_item)
        
        self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        return True

class PrototypeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Studio Birthday - 5:7 Crop & Print Prototype")
        self.setMinimumSize(1000, 800)
        self.setAcceptDrops(True) # Drag & Drop 허용
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        info_label = QLabel("📸 사진을 여기로 끌어다 놓거나(Drag&Drop) 버튼을 눌러주세요. 모든 모서리에서 비율 고정 조절이 가능합니다.")
        info_label.setStyleSheet("color: #eee; font-size: 15px; font-weight: bold; margin: 10px; background: #333; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)
        
        self.crop_view = CropView()
        layout.addWidget(self.crop_view)
        
        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("사진 불러오기")
        self.btn_load.clicked.connect(self.on_load_clicked)
        self.btn_load.setMinimumHeight(50)
        
        self.btn_print = QPushButton("5:7 사이즈 즉시 인화")
        self.btn_print.clicked.connect(self.on_print_clicked)
        self.btn_print.setMinimumHeight(60)
        self.btn_print.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; font-size: 18px; border-radius: 5px;")
        self.btn_print.setEnabled(False)
        
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_print)
        layout.addLayout(btn_layout)
        
        self.current_image_path = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            path = files[0]
            if path.lower().endswith(('.png', '.jpg', '.jpeg')):
                if self.crop_view.load_image(path):
                    self.current_image_path = path
                    self.btn_print.setEnabled(True)
                    self.statusBar().showMessage(f"로드됨: {os.path.basename(path)}")

    def on_load_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "사진 선택", "", "Images (*.jpg *.jpeg *.png)")
        if file_path:
            if self.crop_view.load_image(file_path):
                self.current_image_path = file_path
                self.btn_print.setEnabled(True)
                self.statusBar().showMessage(f"로드됨: {os.path.basename(file_path)}")

    def get_cropped_image(self):
        if not self.crop_view.pixmap_item or not self.crop_view.crop_item:
            return None
            
        source_pixmap = self.crop_view.pixmap_item.pixmap()
        crop_rect = self.crop_view.crop_item.rect()
        crop_pos = self.crop_view.crop_item.pos()
        
        # 실제 픽셀 좌표로 변환하여 잘라내기
        target_rect = QRectF(crop_pos.x() + crop_rect.left(), crop_pos.y() + crop_rect.top(), 
                             crop_rect.width(), crop_rect.height())
        cropped = source_pixmap.copy(target_rect.toRect())
        return cropped.toImage()

    def on_print_clicked(self):
        cropped_image = self.get_cropped_image()
        if not cropped_image:
            return

        printer = QPrinter(QPrinter.HighResolution)
        printer.setFullPage(True)
        
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.Accepted:
            painter = QPainter(printer)
            rect = printer.pageRect(QPrinter.DevicePixel)
            painter.drawImage(rect, cropped_image)
            painter.end()
            QMessageBox.information(self, "인화 완료", "파일을 프린터로 성공적으로 전송했습니다.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.crop_view.pixmap_item:
            self.crop_view.fitInView(self.crop_view.pixmap_item, Qt.KeepAspectRatio)

if __name__ == "__main__":
    print("프로그램을 시작합니다... 창이 뜰 때까지 잠시만 기다려 주세요.")
    try:
        app = QApplication(sys.argv)
        # 폰트 깨짐 방지 (Windows 최적화)
        app.setStyle('Fusion')
        window = PrototypeWindow()
        window.show()
        print("창이 표시되었습니다. 터미널을 종료하지 마세요.")
        sys.exit(app.exec())
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        input("엔터를 누르면 종료합니다...")
