class PackageSelectDialog(QDialog):
    """패키지 선택 다이얼로그"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_minutes = None
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle("패키지 선택")
        self.setFixedSize(450, 280)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        theme = CURRENT_THEME
        
        # 메인 컨테이너
        container = QFrame(self)
        container.setGeometry(0, 0, 450, 280)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme['dialog_bg']};
                border-radius: 20px;
                border: 2px solid {theme['glass_border']};
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 타이틀
        title = QLabel("촬영 패키지를 선택해주세요")
        title.setStyleSheet(f"color: {theme['text_main']}; font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        # 베이직 버튼
        btn_basic = QPushButton("35분 촬영 - 베이직")
        btn_basic.setFixedHeight(60)
        btn_basic.setCursor(Qt.PointingHandCursor)
        btn_basic.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['glass_bg']};
                border: 2px solid {theme['glass_border']};
                border-radius: 15px;
                color: {theme['text_main']};
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme['glass_hover']};
                border-color: {theme['text_accent']};
            }}
        """)
        btn_basic.clicked.connect(lambda: self._select_package(35))
        layout.addWidget(btn_basic)
        
        # 프리미엄 버튼
        btn_premium = QPushButton("⭐ 55분 촬영 - 프리미엄 ⭐")
        btn_premium.setFixedHeight(60)
        btn_premium.setCursor(Qt.PointingHandCursor)
        btn_premium.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(218, 165, 32, 0.3), stop:1 rgba(184, 134, 11, 0.3));
                border: 2px solid rgba(218, 165, 32, 0.8);
                border-radius: 15px;
                color: #B8860B;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(218, 165, 32, 0.5), stop:1 rgba(184, 134, 11, 0.5));
                border-color: #DAA520;
            }}
        """)
        btn_premium.clicked.connect(lambda: self._select_package(55))
        layout.addWidget(btn_premium)
        
    def _select_package(self, minutes):
        self.selected_minutes = minutes
        self.accept()
        
    def get_selected_minutes(self):
        return self.selected_minutes


