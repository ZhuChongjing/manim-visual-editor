import sys
import os
import uuid
import copy
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any, Callable
from decimal import Decimal
from io import BytesIO
from manim import Text, MathTex, config
from manim.utils.tex_file_writing import tex_to_svg_file, TexTemplate
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QListWidgetItem, QPushButton, QLabel, QLineEdit, 
    QComboBox, QTextEdit, QDialog, QSplitter, QToolBar,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QFormLayout, 
    QMessageBox, QAbstractItemView, QSizePolicy, QFontComboBox, 
    QProgressBar, QGraphicsRectItem, QSlider, QToolButton,
    QScrollArea, QColorDialog, QGraphicsLineItem, QStyleOptionGraphicsItem,
    QGraphicsSceneMouseEvent
)
from PyQt6.QtCore import Qt, QSize, QProcess, pyqtSignal, QRectF, QByteArray, QPointF
from PyQt6.QtGui import (
    QAction, QColor, QBrush, QPainter, QPixmap, QFont, QIcon, QMovie, 
    QPen, QFontMetrics, QKeySequence, QImage, QWheelEvent, QMouseEvent
)
import qtawesome as qta
import matplotlib.pyplot as plt

# === 配置与环境初始化 ===
os.environ["QT_API"] = "pyqt6"
config.tex_dir = os.path.join(os.path.dirname(__file__), "tex_cache")

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "Consolas",
    "mathtext.fontset": "cm",
    "figure.dpi": 150,
})

QUALITY_MAP = {
    "480p (854*480)": "854,480",
    "720p (1280*720)": "1280,720",
    "1080p (1920*1080)": "1920,1080",
    "4K (3840*2160)": "3840,2160"
}

MANIM_COLORS_DICT = {
    "WHITE": "#FFFFFF",
    "GRAY_A": "#DDDDDD",
    "GREY_A": "#DDDDDD",
    "GRAY_B": "#BBBBBB",
    "GREY_B": "#BBBBBB",
    "GRAY_C": "#888888",
    "GREY_C": "#888888",
    "GRAY_D": "#444444",
    "GREY_D": "#444444",
    "GRAY_E": "#222222",
    "GREY_E": "#222222",
    "BLACK": "#000000",
    "LIGHTER_GRAY": "#DDDDDD",
    "LIGHTER_GREY": "#DDDDDD",
    "LIGHT_GRAY": "#BBBBBB",
    "LIGHT_GREY": "#BBBBBB",
    "GRAY": "#888888",
    "GREY": "#888888",
    "DARK_GRAY": "#444444",
    "DARK_GREY": "#444444",
    "DARKER_GRAY": "#222222",
    "DARKER_GREY": "#222222",
    "BLUE_A": "#C7E9F1",
    "BLUE_B": "#9CDCEB",
    "BLUE_C": "#58C4DD",
    "BLUE_D": "#29ABCA",
    "BLUE_E": "#236B8E",
    "PURE_BLUE": "#0000FF",
    "BLUE": "#58C4DD",
    "DARK_BLUE": "#236B8E",
    "TEAL_A": "#ACEAD7",
    "TEAL_B": "#76DDC0",
    "TEAL_C": "#5CD0B3",
    "TEAL_D": "#55C1A7",
    "TEAL_E": "#49A88F",
    "TEAL": "#5CD0B3",
    "GREEN_A": "#C9E2AE",
    "GREEN_B": "#A6CF8C",
    "GREEN_C": "#83C167",
    "GREEN_D": "#77B05D",
    "GREEN_E": "#699C52",
    "PURE_GREEN": "#00FF00",
    "GREEN": "#83C167",
    "YELLOW_A": "#FFF1B6",
    "YELLOW_B": "#FFEA94",
    "YELLOW_C": "#FFFF00",
    "YELLOW_D": "#F4D345",
    "YELLOW_E": "#E8C11C",
    "YELLOW": "#FFFF00",
    "GOLD_A": "#F7C797",
    "GOLD_B": "#F9B775",
    "GOLD_C": "#F0AC5F",
    "GOLD_D": "#E1A158",
    "GOLD_E": "#C78D46",
    "GOLD": "#F0AC5F",
    "RED_A": "#F7A1A3",
    "RED_B": "#FF8080",
    "RED_C": "#FC6255",
    "RED_D": "#E65A4C",
    "RED_E": "#CF5044",
    "PURE_RED": "#FF0000",
    "RED": "#FC6255",
    "MAROON_A": "#ECABC1",
    "MAROON_B": "#EC92AB",
    "MAROON_C": "#C55F73",
    "MAROON_D": "#A24D61",
    "MAROON_E": "#94424F",
    "MAROON": "#C55F73",
    "PURPLE_A": "#CAA3E8",
    "PURPLE_B": "#B189C6",
    "PURPLE_C": "#9A72AC",
    "PURPLE_D": "#715582",
    "PURPLE_E": "#644172",
    "PURPLE": "#9A72AC",
    "PINK": "#D147BD",
    "LIGHT_PINK": "#DC75CD",
    "ORANGE": "#FF862F",
    "LIGHT_BROWN": "#CD853F",
    "DARK_BROWN": "#8B4513",
    "GRAY_BROWN": "#736357",
    "GREY_BROWN": "#736357",

    # Colors used for Manim Community's logo and banner

    "LOGO_WHITE": "#ECE7E2",
    "LOGO_GREEN": "#87C2A5",
    "LOGO_BLUE": "#525893",
    "LOGO_RED": "#E07A5F",
    "LOGO_BLACK": "#343434",
}

MANIM_COLORS_LIST = list(MANIM_COLORS_DICT.keys())

CANVAS_WIDTH: int = 960
CANVAS_HEIGHT: int = 540
BASE_TEXT_SIZE: int = 32
MANIM_UNIT_PER_PIXEL: Decimal = Decimal(str(MathTex("x").height)) / Decimal(str(QSvgRenderer(str(tex_to_svg_file("$x$", tex_template=TexTemplate()))).viewBoxF().height()))
SNAP_THRESHOLD_PIXELS: float = 10.0

# === 辅助函数 ===
def findfile(file_name: str, search_dir: str = ".") -> Optional[str]:
    for root, dirs, files in os.walk(search_dir):
        if file_name in files:
            return os.path.abspath(os.path.join(root, file_name))
    return None

def get_qt_color(color_name: str) -> QColor:
    if color_name in MANIM_COLORS_LIST:
        return QColor(MANIM_COLORS_DICT[color_name])
    qt_c = QColor(color_name)
    return qt_c if qt_c.isValid() else QColor("#FFFFFF")

def render_latex_to_pixmap_mpl(latex_text: str, color_str: str = "#000000") -> Tuple[QPixmap, Optional[str]]:
    if not latex_text.strip():
        return QPixmap(), None
    fig = None
    try:
        fig = plt.figure(figsize=(2, 2), dpi=100) 
        fig.patch.set_alpha(0)
        c = get_qt_color(color_str)
        mpl_color = c.name()
        fig.text(0.5, 0.5, f"${latex_text}$", ha='center', va='center', fontsize=20, color=mpl_color)
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, facecolor='none', dpi=100)
        buf.seek(0)
        image = QImage()
        image.loadFromData(buf.getvalue())
        plt.close(fig)
        buf.close()
        if image.isNull(): return QPixmap(), "Render Error"
        return QPixmap.fromImage(image), None
    except Exception as e:
        if fig: plt.close(fig)
        return QPixmap(), str(e)

def create_manim_svg_renderer(latex_text: str, color_str: str) -> Tuple[Optional[QSvgRenderer], Optional[str]]:
    if not latex_text.strip(): return None, None
    try:
        tex_template = TexTemplate()
        svg_file = tex_to_svg_file(f"${latex_text}$", tex_template=tex_template)
        if not os.path.exists(svg_file): return None, "LaTeX Compile Failed"
        with open(svg_file, 'r', encoding='utf-8') as f:
            svg_data = f.read()
        qt_color = get_qt_color(color_str)
        hex_color = qt_color.name()
        if "<svg " in svg_data:
            svg_data = svg_data.replace("<svg ", f'<svg fill="{hex_color}" stroke="none" ')
        renderer = QSvgRenderer(QByteArray(svg_data.encode('utf-8')))
        if not renderer.isValid(): return None, "Invalid SVG Data"
        return renderer, None
    except Exception as e:
        return None, str(e)

# === 数据类 ===
@dataclass
class MobjectData:
    id: str
    name: str
    mob_type: str 
    color: str
    content: str = "" 
    font: str = "Arial" 
    x: float = 0.0
    y: float = 0.0
    scale: float = 1.0
    visible: bool = True 

@dataclass
class AnimationData:
    id: str
    anim_type: str 
    target_id: str
    target_name_snapshot: str 
    replacement_id: Optional[str] = None 
    replacement_name_snapshot: Optional[str] = None
    duration: float = 1.0 

# === UI 组件 ===
class GifItemWidget(QWidget):
    def __init__(self, text: str, gif_path: Optional[str] = None, icon_fallback: Optional[str] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setStyleSheet("border: 1px solid #ccc; background: #eee; border-radius: 4px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if gif_path and os.path.exists(gif_path):
            movie = QMovie(gif_path)
            movie.setScaledSize(QSize(38, 38))
            self.icon_label.setMovie(movie)
            movie.start()
        elif icon_fallback:
             self.icon_label.setPixmap(qta.icon(icon_fallback, color='#555').pixmap(24, 24))
        else:
            self.icon_label.setText("GIF")
        layout.addWidget(self.icon_label)
        self.text_label = QLabel(text)
        self.text_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(self.text_label)
        layout.addStretch()

class JumpSlider(QSlider):
    """支持点击跳转的滑块"""
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self.orientation() == Qt.Orientation.Horizontal:
                ratio = event.position().x() / self.width()
                new_val = self.minimum() + (self.maximum() - self.minimum()) * ratio
            else:
                ratio = (self.height() - event.position().y()) / self.height()
                new_val = self.minimum() + (self.maximum() - self.minimum()) * ratio
            self.setValue(int(new_val))
        super().mousePressEvent(event)

class TypeSelectorDialog(QDialog):
    def __init__(self, title: str, items: List[Tuple[str, Optional[str], Optional[str]]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(350, 450)
        self.selected_item: Optional[str] = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("请选择类型:"))
        self.list_widget = QListWidget()
        for item_data in items:
            display_text, gif_path, icon_fallback = item_data
            lw_item = QListWidgetItem()
            lw_item.setSizeHint(QSize(0, 55))
            lw_item.setData(Qt.ItemDataRole.UserRole, display_text)
            self.list_widget.addItem(lw_item)
            widget = GifItemWidget(display_text, gif_path, icon_fallback)
            self.list_widget.setItemWidget(lw_item, widget)
        self.list_widget.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.list_widget)
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("确定")
        btn_ok.setStyleSheet("background-color: #0078d4; color: white; border: none;")
        btn_ok.clicked.connect(self.accept_selection)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def accept_selection(self) -> None:
        current = self.list_widget.currentItem()
        if current:
            self.selected_item = current.data(Qt.ItemDataRole.UserRole)
            self.accept()

class MobjectEditDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, mobject: Optional[MobjectData] = None, existing_names: Optional[List[MobjectData]] = None, default_type: str = "Square") -> None:
        super().__init__(parent)
        self.setWindowTitle("对象属性设置")
        self.resize(450, 0) 
        self.layout: QFormLayout = QFormLayout(self)
        self.layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # --- 1. 初始化所有控件 (先创建，后赋值/连接信号) ---

        # 名称
        self.name_edit = QLineEdit()
        if mobject: self.name_edit.setText(mobject.name)
        elif existing_names is not None: self.name_edit.setText(f"{default_type}_{len(existing_names) + 1}")
        
        self.type_label = QLabel(mobject.mob_type if mobject else default_type)
        
        # 颜色相关控件
        self.color_row_container = QWidget()
        self.color_row_layout = QHBoxLayout(self.color_row_container)
        self.color_row_layout.setContentsMargins(0, 0, 0, 0)
        self.color_row_layout.setSpacing(5)

        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(["Manim内置", "自定义"])
        self.color_mode_combo.setFixedWidth(90)
        
        self.builtin_color_combo = QComboBox()
        self.builtin_color_combo.addItems(MANIM_COLORS_LIST)
        self.builtin_color_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.custom_color_container = QWidget()
        self.custom_color_layout = QHBoxLayout(self.custom_color_container)
        self.custom_color_layout.setContentsMargins(0, 0, 0, 0)
        self.custom_color_layout.setSpacing(5)
        
        self.custom_color_edit = QLineEdit()
        self.custom_color_edit.setPlaceholderText("#RRGGBB")
        
        self.pick_color_btn = QToolButton()
        self.pick_color_btn.setIcon(qta.icon('fa5s.eye-dropper', color='#333'))
        self.pick_color_btn.setFixedSize(26, 26) 
        self.pick_color_btn.clicked.connect(self.open_color_picker)
        
        # 组装颜色布局
        self.custom_color_layout.addWidget(self.custom_color_edit)
        self.custom_color_layout.addWidget(self.pick_color_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.color_row_layout.addWidget(self.color_mode_combo, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.color_row_layout.addWidget(self.builtin_color_combo, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.color_row_layout.addWidget(self.custom_color_container, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 内容与字体
        self.content_edit = QLineEdit("E=mc^2") # <--- 确保在连接信号前创建
        if mobject: self.content_edit.setText(mobject.content)
        
        self.font_combo = QFontComboBox()
        self.font_combo.clear()
        self.font_combo.addItems(Text.font_list())
        if mobject and mobject.font: self.font_combo.setCurrentFont(QFont(mobject.font))
        
        self.content_label = QLabel("内容:")
        self.font_label = QLabel("字体:")
        
        # 预览区域
        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        self.preview_area.setFixedHeight(140)
        self.preview_area.setVisible(False)
        
        self.preview_label = QLabel("公式预览")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setWordWrap(True)
        self.base_preview_style = "background-color: black; border: 1px solid #444;"
        self.preview_label.setStyleSheet(self.base_preview_style + "color: #888;")
        self.preview_area.setWidget(self.preview_label)

        # 确定按钮
        btn_ok = QPushButton("应用")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet("background-color: #0078d4; color: white; border: none; padding: 6px; font-weight: bold;")
        btn_ok.clicked.connect(self.validate_and_accept)

        # --- 2. 添加到主布局 ---
        self.layout.addRow("类型:", self.type_label)
        self.layout.addRow("名称:", self.name_edit)
        self.layout.addRow("颜色:", self.color_row_container)
        self.layout.addRow(self.content_label, self.content_edit)
        self.layout.addRow(self.font_label, self.font_combo)
        self.layout.addRow(self.preview_area)
        self.layout.addRow(btn_ok)

        # --- 3. 连接信号 (此时所有控件已存在，触发信号不会报错) ---
        self.color_mode_combo.currentIndexChanged.connect(self.toggle_color_ui)
        self.builtin_color_combo.currentTextChanged.connect(self.refresh_preview)
        self.custom_color_edit.textChanged.connect(self.refresh_preview)
        self.content_edit.textChanged.connect(self.refresh_preview)

        # --- 4. 初始化状态 (这会触发一次信号，但现在安全了) ---
        initial_color = mobject.color if mobject else "WHITE"
        self.init_color_state(initial_color)
        
        self.update_fields(self.type_label.text())
        self.toggle_color_ui()

    def init_color_state(self, color_str: str) -> None:
        upper_color = color_str.upper()
        if upper_color in MANIM_COLORS_LIST:
            self.color_mode_combo.setCurrentIndex(0) 
            index = self.builtin_color_combo.findText(upper_color)
            if index >= 0: self.builtin_color_combo.setCurrentIndex(index)
        else:
            self.color_mode_combo.setCurrentIndex(1) 
            self.custom_color_edit.setText(color_str)

    def toggle_color_ui(self) -> None:
        is_builtin = (self.color_mode_combo.currentIndex() == 0)
        self.builtin_color_combo.setVisible(is_builtin)
        self.custom_color_container.setVisible(not is_builtin)
        self.refresh_preview()

    def open_color_picker(self) -> None:
        current_text = self.custom_color_edit.text().strip()
        initial_color = QColor(current_text)
        if not initial_color.isValid(): initial_color = QColor("white")
        color = QColorDialog.getColor(initial_color, self, "选择颜色")
        if color.isValid(): self.custom_color_edit.setText(color.name().upper())

    def update_fields(self, text: str) -> None:
        is_text = (text == "Text")
        is_math = (text == "MathTex")
        self.content_label.setVisible(is_text or is_math)
        self.content_edit.setVisible(is_text or is_math)
        self.font_label.setVisible(is_text)
        self.font_combo.setVisible(is_text)
        self.preview_area.setVisible(is_math)
        if is_math:
            self.content_label.setText("LaTeX:")
            self.refresh_preview()
        else:
            self.content_label.setText("文本:")

    def refresh_preview(self, _: Optional[Any] = None) -> None:
        # 安全检查：防止未初始化时调用 (虽然调整顺序后基本不会发生，但加个保险)
        if not hasattr(self, 'content_edit'): return

        if self.type_label.text() == "MathTex":
            self.update_preview(self.content_edit.text())

    def update_preview(self, latex_text: str) -> None:
        current_color = self.get_current_color_str()
        pixmap, error = render_latex_to_pixmap_mpl(latex_text, current_color)
        if error:
            self.preview_label.setText(str(error).strip())
            self.preview_label.setStyleSheet(self.base_preview_style + "color: #FF5555; padding: 5px;")
        elif not pixmap.isNull():
            current_width = self.preview_area.width()
            max_width = 360 if (current_width < 100 or current_width > 600) else current_width - 25
            if pixmap.width() > max_width:
                pixmap = pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setStyleSheet(self.base_preview_style)
            self.preview_label.setPixmap(pixmap)
        else:
            self.preview_label.setText("输入 LaTeX 以预览")
            self.preview_label.setStyleSheet(self.base_preview_style + "color: #888;")

    def validate_and_accept(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "提示", "名称不能为空！")
            return
        if self.color_mode_combo.currentIndex() == 1:
            c = QColor(self.custom_color_edit.text())
            if not c.isValid(): self.custom_color_edit.setText("#FFFFFF")
        self.accept()

    def get_current_color_str(self) -> str:
        if self.color_mode_combo.currentIndex() == 0: return self.builtin_color_combo.currentText()
        else: return self.custom_color_edit.text().strip()

    def get_data(self) -> Dict[str, str]:
        return {
            "name": self.name_edit.text().strip(),
            "type": self.type_label.text(),
            "color": self.get_current_color_str(),
            "content": self.content_edit.text(),
            "font": self.font_combo.currentFont().family()
        }
  
class AnimationEditDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, mobjects: List[MobjectData] = [], animation: Optional[AnimationData] = None, default_type: str = "Create") -> None:
        super().__init__(parent)
        self.setWindowTitle("动画属性设置")
        self.resize(350, 0)
        self.mobjects = mobjects
        self.layout: QFormLayout = QFormLayout(self)
        self.layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.type_label = QLabel(animation.anim_type if animation else default_type)
        self.target_combo = QComboBox()
        for m in mobjects: self.target_combo.addItem(m.name, m.id)
        if animation: 
            idx = self.target_combo.findData(animation.target_id)
            if idx >= 0: self.target_combo.setCurrentIndex(idx)
        self.replacement_label = QLabel("变换至:")
        self.replacement_combo = QComboBox()
        for m in mobjects: self.replacement_combo.addItem(m.name, m.id)
        if animation and animation.replacement_id:
            idx = self.replacement_combo.findData(animation.replacement_id)
            if idx >= 0: self.replacement_combo.setCurrentIndex(idx)
        self.dur_edit = QLineEdit("1.0")
        if animation: self.dur_edit.setText(str(animation.duration))
        self.layout.addRow("动画效果:", self.type_label)
        self.layout.addRow("作用对象:", self.target_combo)
        if self.type_label.text() == "Transform":
            self.layout.addRow(self.replacement_label, self.replacement_combo)
        self.layout.addRow("时长(秒):", self.dur_edit)
        btn_ok = QPushButton("应用")
        btn_ok.setStyleSheet("background-color: #0078d4; color: white; border: none; padding: 6px; font-weight: bold;")
        btn_ok.clicked.connect(self.accept)
        self.layout.addRow(btn_ok)

    def get_data(self) -> Dict[str, Any]:
        try: dur = float(self.dur_edit.text())
        except: dur = 1.0
        rep_id = None
        rep_name = None
        if self.type_label.text() == "Transform":
            rep_id = self.replacement_combo.currentData()
            rep_name = self.replacement_combo.currentText()
        return {
            "type": self.type_label.text(),
            "target_id": self.target_combo.currentData(),
            "target_name": self.target_combo.currentText(),
            "replacement_id": rep_id,
            "replacement_name": rep_name,
            "duration": dur
        }

# === 核心画布组件 ===

class ResizeHandle(QGraphicsRectItem):
    def __init__(self, parent: QGraphicsItem, cursor_shape: Qt.CursorShape) -> None:
        super().__init__(-5, -5, 10, 10, parent)
        self.setBrush(QBrush(QColor("white")))
        self.setPen(QPen(QColor("#0078d4"), 1))
        self.setCursor(cursor_shape)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIgnoresParentOpacity)
        self.setZValue(99) 

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        parent: VisualMobjectItem = self.parentItem()
        if hasattr(parent, "on_manipulation_start"):
            parent.on_manipulation_start()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        parent: VisualMobjectItem = self.parentItem()
        if hasattr(parent, 'handle_resize_event'):
            parent.handle_resize_event(self, event.scenePos())

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        parent: VisualMobjectItem = self.parentItem()
        if hasattr(parent, "on_manipulation_end"):
            parent.on_manipulation_end()

class VisualMobjectItem(QGraphicsItem):
    def __init__(self, mobject_data: MobjectData, scene_scale: float, on_move_callback: Optional[Callable[[str], None]] = None, change_callback: Optional[Callable[[str], None]] = None) -> None:
        super().__init__()
        self.mob_data = mobject_data
        self.scene_scale = Decimal(str(scene_scale)) 
        self.on_move_callback = on_move_callback
        self.change_callback = change_callback 
        
        self.setZValue(1)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable | 
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        self.svg_renderer: Optional[QSvgRenderer] = None
        self.last_content_signature: Optional[Tuple[str, str, str, str]] = None 
        self.has_render_error = False
        self.render_error_msg = ""
        self.update_content()
        self.setScale(self.mob_data.scale)
        self.update_position_from_data()
        self.update_tooltip()
        self.handles: List[ResizeHandle] = []
        self.is_resizing = False
        self.is_manipulating = False

    def update_content(self) -> None:
        sig = (self.mob_data.content, self.mob_data.color, self.mob_data.font, self.mob_data.mob_type)
        if sig == self.last_content_signature: return
        self.last_content_signature = sig
        self.prepareGeometryChange()
        self.has_render_error = False
        self.svg_renderer = None
        if self.mob_data.mob_type == "MathTex":
            renderer, error = create_manim_svg_renderer(self.mob_data.content, self.mob_data.color)
            if error:
                self.has_render_error = True
                self.render_error_msg = error
            else:
                self.svg_renderer = renderer
        self._bounding_rect = self._calculate_bounding_rect()

    def _calculate_bounding_rect(self) -> QRectF:
        factor = Decimal("1.0") / self.scene_scale
        if self.mob_data.mob_type == "Square":
            s = Decimal("2.0") * factor
            return QRectF(-s/2, -s/2, s, s)
        elif self.mob_data.mob_type == "Circle":
            d = Decimal("2.0") * factor 
            return QRectF(-d/2, -d/2, d, d)
        elif self.mob_data.mob_type == "Text":
            font = QFont(self.mob_data.font, BASE_TEXT_SIZE)
            fm = QFontMetrics(font)
            rect = fm.boundingRect(self.mob_data.content)
            return QRectF(-rect.width()/2, -rect.height()/2, rect.width(), rect.height())
        elif self.mob_data.mob_type == "MathTex":
            if self.svg_renderer and self.svg_renderer.isValid():
                vbox = self.svg_renderer.viewBoxF()
                width_in_units = Decimal(str(vbox.width())) * MANIM_UNIT_PER_PIXEL
                height_in_units = Decimal(str(vbox.height())) * MANIM_UNIT_PER_PIXEL
                display_w = width_in_units * factor
                display_h = height_in_units * factor
                return QRectF(-display_w/2, -display_h/2, display_w, display_h)
            else:
                return QRectF(-50, -25, 100, 50)
        return QRectF(-50, -50, 100, 100)

    def boundingRect(self) -> QRectF:
        base_rect = self._bounding_rect
        padding = 5.0 
        if self.mob_data.mob_type == "Text": padding = 10.0
        return base_rect.adjusted(-padding, -padding, padding, padding)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget]) -> None:
        color = get_qt_color(self.mob_data.color)
        
        # 错误处理显示
        if self.has_render_error and self.mob_data.mob_type == "MathTex":
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            painter.drawRect(self._bounding_rect)
            painter.drawText(self._bounding_rect, Qt.AlignmentFlag.AlignCenter, "LaTeX Error")
            return
            
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        rect = self._bounding_rect
        
        # 创建一个 "Cosmetic" 画笔
        # setCosmetic(True) 意味着画笔宽度是基于屏幕像素的，不受 Item 缩放影响
        shape_pen = QPen(color, 2)
        shape_pen.setCosmetic(True) 
        
        if self.mob_data.mob_type == "Square":
            painter.setPen(shape_pen)
            # 设置半透明填充
            c = QColor(color)
            c.setAlphaF(0.5)
            painter.setBrush(QBrush(c))
            painter.drawRect(rect)
            
        elif self.mob_data.mob_type == "Circle":
            painter.setPen(shape_pen)
            c = QColor(color)
            c.setAlphaF(0.5)
            painter.setBrush(QBrush(c))
            painter.drawEllipse(rect)
            
        elif self.mob_data.mob_type == "Text":
            # 文本通常不需要边框，只需要颜色
            painter.setPen(QPen(color))
            font = QFont(self.mob_data.font, BASE_TEXT_SIZE)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextDontClip, self.mob_data.content)
            
        elif self.mob_data.mob_type == "MathTex":
            if self.svg_renderer and self.svg_renderer.isValid():
                self.svg_renderer.render(painter, rect)

        # 选中状态的边框
        if self.isSelected():
            # 选中框也应该是 Cosmetic 的，防止缩放后虚线变得极粗
            sel_pen = QPen(Qt.GlobalColor.white, 1, Qt.PenStyle.SolidLine)
            sel_pen.setCosmetic(True)
            
            painter.setPen(sel_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())

    def update_position_from_data(self) -> None:
        self.setPos(Decimal(str(self.mob_data.x)) / self.scene_scale, -Decimal(str(self.mob_data.y)) / self.scene_scale)
        
    def update_tooltip(self) -> None:
        self.setToolTip(f"{self.mob_data.name}\nPos: ({self.mob_data.x:.2f}, {self.mob_data.y:.2f})\nScale: {self.mob_data.scale:.2f}")
        
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and not self.is_resizing:
            # 智能吸附逻辑：只有当用户拖动时（我是Grabber）才触发
            views = self.scene().views()
            if views and isinstance(views[0], ManimCanvas) and self.scene().mouseGrabberItem() == self:
                canvas = views[0]
                new_pos = canvas.get_snapped_position(self, value)
                
                self.mob_data.x = round(Decimal(str(new_pos.x())) * self.scene_scale, 2)
                self.mob_data.y = round(-Decimal(str(new_pos.y())) * self.scene_scale, 2)
                self.update_tooltip()
                if self.on_move_callback: self.on_move_callback(self.mob_data.id)
                return new_pos

            # 默认逻辑
            new_pos = value
            self.mob_data.x = round(Decimal(str(new_pos.x())) * self.scene_scale, 2)
            self.mob_data.y = round(-Decimal(str(new_pos.y())) * self.scene_scale, 2)
            self.update_tooltip()
            if self.on_move_callback: self.on_move_callback(self.mob_data.id)
            
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value: self.create_handles()
            else: self.remove_handles()
        return super().itemChange(change, value)

    def create_handles(self) -> None:
        self.remove_handles()
        b = self.boundingRect() 
        w, h = b.width() / 2, b.height() / 2
        corners = [
            (-w, -h, Qt.CursorShape.SizeFDiagCursor),
            ( w, -h, Qt.CursorShape.SizeBDiagCursor),
            ( w,  h, Qt.CursorShape.SizeFDiagCursor),
            (-w,  h, Qt.CursorShape.SizeBDiagCursor),
        ]
        current_scale = self.scale()
        for x, y, cursor in corners:
            handle = ResizeHandle(self, cursor)
            handle.setPos(x, y)
            handle.setScale(1.0 / current_scale if current_scale != 0 else 1.0)
            self.handles.append(handle)

    def remove_handles(self) -> None:
        for h in self.handles: self.scene().removeItem(h)
        self.handles.clear()

    # --- 交互事件处理 (撤销/重做支持) ---
    def on_manipulation_start(self) -> None:
        if not self.is_manipulating:
            self.is_manipulating = True
            if self.change_callback: self.change_callback("start")

    def on_manipulation_end(self) -> None:
        if self.is_manipulating:
            self.is_manipulating = False
            if self.change_callback: self.change_callback("end")

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.on_manipulation_start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.on_manipulation_end()
        # 拖动结束清除辅助线
        views = self.scene().views()
        if views and isinstance(views[0], ManimCanvas):
            views[0].clear_guides()

    def handle_resize_event(self, handle: ResizeHandle, mouse_scene_pos: QPointF) -> None:
        self.is_resizing = True
        center_scene = self.scenePos()
        diff = mouse_scene_pos - center_scene
        current_dist = (diff.x()**2 + diff.y()**2) ** 0.5
        b = self._bounding_rect 
        original_radius = (b.width()**2 + b.height()**2)**0.5 / 2
        if original_radius == 0: 
            self.is_resizing = False
            return
        new_scale = current_dist / original_radius
        if new_scale < 0.1: new_scale = 0.1
        self.setScale(new_scale)
        self.mob_data.scale = round(new_scale, 3)
        self.update_tooltip()
        inv_scale = 1.0 / new_scale
        for h in self.handles: h.setScale(inv_scale)
        self.is_resizing = False

class ManimCanvas(QGraphicsView):
    scale_changed = pyqtSignal(int) 

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scene_width = CANVAS_WIDTH
        self.scene_height = CANVAS_HEIGHT
        self.units_to_pixels = CANVAS_HEIGHT / 8.0
        self.pixels_to_units = 1.0 / self.units_to_pixels
        self.scene: QGraphicsScene = QGraphicsScene(-2000, -2000, 4000, 4000)
        self.setScene(self.scene)
        self.setBackgroundBrush(QBrush(QColor("#555555"))) 
        
        self.black_board = QGraphicsRectItem(-self.scene_width/2, -self.scene_height/2, self.scene_width, self.scene_height)
        self.black_board.setBrush(QBrush(Qt.GlobalColor.black))
        self.black_board.setZValue(-100) 
        self.scene.addItem(self.black_board)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.items_map: Dict[str, VisualMobjectItem] = {}
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.current_zoom_percent = 100

        # --- 智能对齐线 ---
        self.guide_lines: List[QGraphicsLineItem] = [] 
        self.snap_threshold = SNAP_THRESHOLD_PIXELS

    def clear_guides(self) -> None:
        for line in self.guide_lines:
            self.scene.removeItem(line)
        self.guide_lines.clear()

    def draw_guide_line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        line = QGraphicsLineItem(x1, y1, x2, y2)
        # 设置对齐线颜色为 #FF8800 (橙色)
        pen = QPen(QColor("#FF8800"), 1, Qt.PenStyle.DashLine) 
        line.setPen(pen)
        line.setZValue(1000) # 最上层
        self.scene.addItem(line)
        self.guide_lines.append(line)

    def get_snapped_position(self, moving_item: VisualMobjectItem, proposed_pos: QPointF) -> QPointF:
        """
        计算吸附后的位置，并绘制辅助线。
        修正：直接使用 _bounding_rect (真实几何) 而非 boundingRect() (含Padding)，解决对齐缝隙问题。
        """
        self.clear_guides()
        
        # 1. 获取移动物体在预测位置的 *真实* 几何边界 (无 Padding)
        # VisualMobjectItem 的 _bounding_rect 是局部未缩放坐标
        local_rect = moving_item._bounding_rect
        scale = moving_item.scale()
        
        # 计算预测的场景坐标边界
        # 假设局部原点 (0,0) 是物体中心
        cx = proposed_pos.x()
        cy = proposed_pos.y()
        
        my_left = cx + local_rect.left() * scale
        my_right = cx + local_rect.right() * scale
        my_top = cy + local_rect.top() * scale
        my_bottom = cy + local_rect.bottom() * scale
        
        # 待检测的关键点 [左, 中, 右]
        x_candidates = [my_left, cx, my_right]
        y_candidates = [my_top, cy, my_bottom]

        # 2. 收集所有对齐目标 (也必须是 无Padding 的真实边界)
        targets = []
        
        # (A) 画布背景 (BlackBoard)
        # 使用 rect() 而非 boundingRect() 来排除边框笔触宽度
        targets.append(self.black_board.mapRectToScene(self.black_board.rect()))
        
        # (B) 其他可见物体
        for other_id, other_item in self.items_map.items():
            if other_item == moving_item: continue
            if not other_item.isVisible(): continue
            
            # 关键修正：使用 other_item._bounding_rect 并映射到场景
            # 这会自动处理其他物体的当前位置、缩放，且不包含 Padding
            real_rect = other_item.mapRectToScene(other_item._bounding_rect)
            targets.append(real_rect)

        # 3. 初始化计算变量
        final_dx = 0.0
        final_dy = 0.0
        min_dist_x = self.snap_threshold
        min_dist_y = self.snap_threshold
        
        snap_x_draw_params = None 
        snap_y_draw_params = None

        # --- X轴扫描 (左右对齐) ---
        target: QRectF
        for target in targets:
            t_pts = [target.left(), target.center().x(), target.right()]
            
            for my_val in x_candidates:
                for target_val in t_pts:
                    dist = abs(my_val - target_val)
                    if dist < min_dist_x:
                        min_dist_x = dist
                        final_dx = target_val - my_val
                        
                        # 计算辅助线绘制范围 (取Y轴并集)
                        union_top = min(my_top, target.top())
                        union_bottom = max(my_bottom, target.bottom())
                        snap_x_draw_params = (target_val, union_top, union_bottom)

        # --- Y轴扫描 (上下对齐) ---
        for target in targets:
            t_pts = [target.top(), target.center().y(), target.bottom()]
            
            for my_val in y_candidates:
                for target_val in t_pts:
                    dist = abs(my_val - target_val)
                    if dist < min_dist_y:
                        min_dist_y = dist
                        final_dy = target_val - my_val
                        
                        # 计算辅助线绘制范围 (取X轴并集)
                        # 这里加上 final_dx 预测值，让横线跟随吸附后的X位置
                        pred_left = my_left + final_dx
                        pred_right = my_right + final_dx
                        union_left = min(pred_left, target.left())
                        union_right = max(pred_right, target.right())
                        snap_y_draw_params = (target_val, union_left, union_right)

        # 4. 应用吸附结果
        new_x = cx + final_dx
        new_y = cy + final_dy

        # 绘制辅助线
        if snap_x_draw_params:
            x, y1, y2 = snap_x_draw_params
            self.draw_guide_line(x, y1 - 20, x, y2 + 20)
            
        if snap_y_draw_params:
            y, x1, x2 = snap_y_draw_params
            self.draw_guide_line(x1 - 20, y, x2 + 20, y)

        return QPointF(new_x, new_y)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0: self.set_zoom(self.current_zoom_percent + 10)
            else: self.set_zoom(self.current_zoom_percent - 10)
        else: super().wheelEvent(event)

    def set_zoom(self, percent: int) -> None:
        if percent < 10: percent = 10
        if percent > 400: percent = 400
        self.current_zoom_percent = percent
        scale_factor = percent / 100.0
        self.resetTransform()
        self.scale(scale_factor, scale_factor)
        if percent > 100:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.centerOn(0, 0)
        self.scale_changed.emit(percent)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            # 中键：平移画布
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            # 生成一个新的事件传递给父类，确保平移立即生效
            dummy_event = QMouseEvent(event.type(), event.position(), event.globalPosition(), 
                                      event.button(), event.buttons(), event.modifiers())
            super().mousePressEvent(dummy_event)
            
        elif event.button() == Qt.MouseButton.LeftButton:
            # 左键：判断是点到了物体还是空白处
            
            # 获取点击位置下的所有物体
            scene_pos = self.mapToScene(event.pos())
            items = self.scene.items(scene_pos)
            
            clicked_on_item = False
            for item in items:
                # 如果点击了可视物体或缩放手柄 (排除背景板)
                if isinstance(item, (VisualMobjectItem, ResizeHandle)):
                    clicked_on_item = True
                    break
                # 注意：self.black_board 也是一个 Item，但我们需要忽略它
            
            # 只有当点击的是背景板（即没有点到任何可操作物体）时，才开启框选
            if clicked_on_item:
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
            else:
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
                
            super().mousePressEvent(event)
            
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        super().mouseReleaseEvent(event)

    def add_visual_item(self, mobject: MobjectData, on_move_cb: Callable[[str], None], change_cb: Optional[Callable[[str], None]] = None) -> None:
        if mobject.id in self.items_map: self.remove_visual_item(mobject.id)
        item = VisualMobjectItem(mobject, self.pixels_to_units, on_move_cb, change_cb)
        self.scene.addItem(item)
        self.items_map[mobject.id] = item

    def update_item_content(self, mob_id: str) -> None:
        if mob_id in self.items_map:
            item = self.items_map[mob_id]
            item.update_content()
            item.update()

    def remove_visual_item(self, mob_id: str) -> None:
        if mob_id in self.items_map:
            self.scene.removeItem(self.items_map[mob_id])
            del self.items_map[mob_id]
            
    def set_item_visible(self, mob_id: str, visible: bool) -> None:
        if mob_id in self.items_map:
            self.items_map[mob_id].setVisible(visible)

# === 主窗口 ===

class ManimEditor(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Manim Visual Editor")
        self.setWindowIcon(QIcon(findfile("icon.png")))
        self.mobjects: List[MobjectData] = []
        self.animations: List[AnimationData] = []
        
        self.is_syncing_selection = False

        # --- Undo/Redo Stacks ---
        self.undo_stack: List[Tuple[List[MobjectData], List[AnimationData]]] = []
        self.redo_stack: List[Tuple[List[MobjectData], List[AnimationData]]] = []
        self.max_history = 50
        self.temp_state_snapshot: Optional[Tuple[List[MobjectData], List[AnimationData]]] = None 

        self.setStyleSheet(
"""
QMainWindow { background-color: #f3f3f3; }
QWidget { color: #333333; font-family: "Consolas", monospace; font-size: 10pt; }
QToolBar { background-color: #ffffff; border-bottom: 1px solid #e0e0e0; spacing: 10px; padding: 5px; }
QToolButton { background-color: transparent; border: 1px solid transparent; border-radius: 3px; padding: 4px; color: #444; }
QToolButton:hover { background-color: #f0f0f0; border: 1px solid #c0c0c0; }
QLabel#PanelHeader { font-weight: bold; color: #0078d4; padding: 8px; background-color: #f9f9f9; border-bottom: 2px solid #0078d4; }
QListWidget, QLineEdit, QComboBox, QFontComboBox, QTextEdit { background-color: #ffffff; border: 1px solid #a0a0a0; border-radius: 2px; padding: 4px; }
QListWidget::item:selected { background-color: #eff6fc; border: 1px solid #0078d4; color: #000; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #0078d4; }
QPushButton { background-color: #ffffff; border: 1px solid #a0a0a0; color: #333; padding: 5px 12px; border-radius: 3px; }
QPushButton:hover { background-color: #f0f0f0; border-color: #0078d4; color: #0078d4; }
QPushButton#DelBtn { border: none; background-color: transparent; padding: 4px; }
QPushButton#DelBtn:hover { background-color: #ffe6e6; border-radius: 3px; }
QPushButton#RenderBtn { background-color: #0078d4; color: white; border: none; font-weight: bold; padding: 6px 15px; }
QPushButton#RenderBtn:hover { background-color: #106ebe; }
QWidget#ZoomBar { background-color: #f3f3f3; border-top: 1px solid #e0e0e0; }
"""
        )
        self.init_ui()

    def init_ui(self) -> None:
        self.act_undo = QAction("撤销 (Ctrl+Z)", self)
        self.act_undo.setShortcut("Ctrl+Z")
        self.act_undo.triggered.connect(self.undo_action)
        self.addAction(self.act_undo)

        self.act_redo = QAction("重做 (Ctrl+Y)", self)
        self.act_redo.setShortcut("Ctrl+Y")
        self.act_redo.triggered.connect(self.redo_action)
        self.addAction(self.act_redo)
        
        self.act_delete = QAction("删除", self)
        self.act_delete.setShortcut(QKeySequence(Qt.Key.Key_Delete))
        self.act_delete.triggered.connect(self.delete_selected)
        self.addAction(self.act_delete)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        
        self.act_add_mob = QAction(qta.icon('fa5s.plus-square', color='#444'), "插入对象", self)
        self.act_add_mob.triggered.connect(self.add_mobject_dialog)
        
        self.act_add_anim = QAction(qta.icon('fa5s.magic', color='#444'), "添加动画", self)
        self.act_add_anim.triggered.connect(self.add_animation_dialog)
        
        toolbar.addAction(self.act_add_mob)
        toolbar.addAction(self.act_add_anim)
        toolbar.addSeparator()
        toolbar.addAction(self.act_undo)
        toolbar.addAction(self.act_redo)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        main_layout.addWidget(splitter)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.addWidget(QLabel("对象列表", objectName="PanelHeader"))
        
        self.mob_list_widget = QListWidget()
        self.mob_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.mob_list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.mob_list_widget.itemDoubleClicked.connect(self.edit_mobject_dialog)
        self.mob_list_widget.itemSelectionChanged.connect(self.sync_selection_list_to_canvas)
        left_layout.addWidget(self.mob_list_widget)
        splitter.addWidget(left_panel)
        
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0,0,0,0)
        center_layout.setSpacing(0)
        
        center_header = QLabel("预览画布", objectName="PanelHeader")
        center_header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        center_layout.addWidget(center_header)
        
        canvas_container = QWidget()
        canvas_container.setStyleSheet("background-color: #dcdcdc; border-bottom: 1px solid #ccc;") 
        canvas_container.setFixedHeight(600)
        cc_layout = QVBoxLayout(canvas_container)
        cc_layout.setContentsMargins(0,0,0,0)
        
        self.canvas = ManimCanvas()
        self.canvas.scene.selectionChanged.connect(self.sync_selection_canvas_to_list)
        cc_layout.addWidget(self.canvas)
        
        self.zoom_bar = QWidget()
        self.zoom_bar.setObjectName("ZoomBar")
        zoom_layout = QHBoxLayout(self.zoom_bar)
        zoom_layout.setContentsMargins(10, 4, 10, 4)
        
        self.render_progress_bar = QProgressBar()
        self.render_progress_bar.setVisible(False)
        self.render_progress_bar.setFixedWidth(200)
        self.render_progress_bar.setStyleSheet("max-height: 8px;")
        
        zoom_layout.addWidget(self.render_progress_bar)
        zoom_layout.addStretch() 
        
        self.zoom_out_btn = QToolButton()
        self.zoom_out_btn.setObjectName("ZoomBtn")
        self.zoom_out_btn.setIcon(qta.icon('fa5s.search-minus', color='#555'))
        self.zoom_out_btn.setFixedSize(24, 24)
        self.zoom_out_btn.clicked.connect(lambda: self.zoom_slider.setValue(self.zoom_slider.value() - 10))
        
        self.zoom_slider = JumpSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 400)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150)
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_change)
        
        self.zoom_in_btn = QToolButton()
        self.zoom_in_btn.setObjectName("ZoomBtn")
        self.zoom_in_btn.setIcon(qta.icon('fa5s.search-plus', color='#555'))
        self.zoom_in_btn.setFixedSize(24, 24)
        self.zoom_in_btn.clicked.connect(lambda: self.zoom_slider.setValue(self.zoom_slider.value() + 10))
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(40)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setStyleSheet("border: 1px solid #ccc; background: white; border-radius: 2px;")
        
        zoom_layout.addWidget(self.zoom_out_btn)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_in_btn)
        zoom_layout.addWidget(self.zoom_label)
        
        self.canvas.scale_changed.connect(self.sync_zoom_ui)
        
        cc_layout.addWidget(self.zoom_bar)
        center_layout.addWidget(canvas_container)
        
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setMinimumHeight(150)
        self.console_output.setPlaceholderText("准备就绪...")
        center_layout.addWidget(self.console_output)
        
        settings_bar = QWidget()
        sb_layout = QHBoxLayout(settings_bar)
        sb_layout.setContentsMargins(5, 5, 5, 5)
        
        self.input_scene_name = QLineEdit("MyScene")
        self.input_scene_name.setFixedWidth(150)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(list(QUALITY_MAP.keys()))
        self.quality_combo.setCurrentIndex(2)

        self.frame_rate_combo = QComboBox()
        self.frame_rate_combo.addItems(["15", "30", "60"])
        self.frame_rate_combo.setCurrentIndex(2)
        
        self.btn_render_big = QPushButton(" 开始渲染")
        self.btn_render_big.setObjectName("RenderBtn")
        self.btn_render_big.setIcon(qta.icon('fa5s.play', color='white'))
        self.btn_render_big.clicked.connect(self.render_video)
        
        sb_layout.addWidget(QLabel("文件:"))
        sb_layout.addWidget(self.input_scene_name)
        sb_layout.addWidget(QLabel("画质:"))
        sb_layout.addWidget(self.quality_combo)
        sb_layout.addWidget(QLabel("帧率:"))
        sb_layout.addWidget(self.frame_rate_combo)
        sb_layout.addStretch()
        sb_layout.addWidget(self.btn_render_big)
        
        center_layout.addWidget(settings_bar)
        splitter.addWidget(center_panel)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.addWidget(QLabel("动画序列", objectName="PanelHeader"))
        
        self.anim_list_widget = QListWidget()
        self.anim_list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.anim_list_widget.itemDoubleClicked.connect(self.edit_animation_dialog)
        right_layout.addWidget(self.anim_list_widget)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([250, 700, 250]) 
        self.update_undo_redo_actions()

    def on_zoom_slider_change(self, value: int) -> None:
        self.zoom_label.setText(f"{value}%")
        self.canvas.set_zoom(value)

    def sync_zoom_ui(self, percent: int) -> None:
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(percent)
        self.zoom_label.setText(f"{percent}%")
        self.zoom_slider.blockSignals(False)

    def set_ui_locked(self, locked: bool) -> None:
        self.act_add_mob.setEnabled(not locked)
        self.act_add_anim.setEnabled(not locked)
        self.btn_render_big.setEnabled(not locked)
        self.input_scene_name.setEnabled(not locked)
        self.quality_combo.setEnabled(not locked)
        self.frame_rate_combo.setEnabled(not locked)
        if locked: QApplication.setOverrideCursor(Qt.CursorShape.ForbiddenCursor)
        else: QApplication.restoreOverrideCursor()

    def sync_selection_list_to_canvas(self) -> None:
        if self.is_syncing_selection: return
        self.is_syncing_selection = True
        selected_items = self.mob_list_widget.selectedItems()
        selected_ids = {item.data(Qt.ItemDataRole.UserRole) for item in selected_items}
        self.canvas.scene.clearSelection()
        for mob_id, item in self.canvas.items_map.items():
            if mob_id in selected_ids: item.setSelected(True)
        self.is_syncing_selection = False

    def sync_selection_canvas_to_list(self) -> None:
        if self.is_syncing_selection: return
        self.is_syncing_selection = True
        selected_items = self.canvas.scene.selectedItems()
        selected_ids = set()
        for item in selected_items:
            if isinstance(item, VisualMobjectItem):
                selected_ids.add(item.mob_data.id)
        self.mob_list_widget.clearSelection()
        for i in range(self.mob_list_widget.count()):
            item = self.mob_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) in selected_ids:
                item.setSelected(True)
        self.is_syncing_selection = False

    # --- 历史记录管理核心方法 ---

    def capture_state(self) -> Tuple[List[MobjectData], List[AnimationData]]:
        """返回当前状态的深拷贝"""
        return (copy.deepcopy(self.mobjects), copy.deepcopy(self.animations))

    def save_to_history(self) -> None:
        """在执行修改前调用，保存当前状态到 undo 栈，并清空 redo 栈"""
        state = self.capture_state()
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self.update_undo_redo_actions()

    def update_undo_redo_actions(self) -> None:
        self.act_undo.setEnabled(len(self.undo_stack) > 0)
        self.act_redo.setEnabled(len(self.redo_stack) > 0)

    def undo_action(self) -> None:
        if not self.undo_stack: return
        # 1. 保存当前状态到 redo
        current_state = self.capture_state()
        self.redo_stack.append(current_state)
        # 2. 弹出 undo 栈顶
        prev_state = self.undo_stack.pop()
        # 3. 恢复
        self.restore_state(prev_state)
        self.update_undo_redo_actions()

    def redo_action(self) -> None:
        if not self.redo_stack: return
        # 1. 保存当前状态到 undo
        current_state = self.capture_state()
        self.undo_stack.append(current_state)
        # 2. 弹出 redo 栈顶
        next_state = self.redo_stack.pop()
        # 3. 恢复
        self.restore_state(next_state)
        self.update_undo_redo_actions()

    def restore_state(self, state: Tuple[List[MobjectData], List[AnimationData]]) -> None:
        """从状态元组中恢复数据，并刷新所有视图"""
        mobs_snapshot, anims_snapshot = state
        self.mobjects = mobs_snapshot
        self.animations = anims_snapshot
        self.refresh_ui() 
        self.sync_canvas_visuals()

    def sync_canvas_visuals(self) -> None:
        """根据 self.mobjects 列表强制同步画布上的图形"""
        current_ids = set()
        for mob in self.mobjects:
            current_ids.add(mob.id)
            if mob.id in self.canvas.items_map:
                item: VisualMobjectItem = self.canvas.items_map[mob.id]
                item.mob_data = mob 
                item.setScale(mob.scale)
                item.update_position_from_data()
                item.update_content()
                item.update_tooltip()
                item.update()
            else:
                self.canvas.add_visual_item(mob, self.refresh_ui_dummy, self.handle_item_manipulation)

        ids_to_remove = []
        for mid in self.canvas.items_map.keys():
            if mid not in current_ids:
                ids_to_remove.append(mid)
        for mid in ids_to_remove:
            self.canvas.remove_visual_item(mid)

    def handle_item_manipulation(self, state_type: str) -> None:
        """VisualMobjectItem 移动/缩放时的回调"""
        if state_type == "start":
            self.temp_state_snapshot = self.capture_state()
        elif state_type == "end":
            if self.temp_state_snapshot:
                if self.has_state_changed(self.temp_state_snapshot):
                    self.undo_stack.append(self.temp_state_snapshot)
                    if len(self.undo_stack) > self.max_history:
                        self.undo_stack.pop(0)
                    self.redo_stack.clear()
                    self.update_undo_redo_actions()
                self.temp_state_snapshot = None

    def has_state_changed(self, old_state: Tuple[List[MobjectData], List[AnimationData]]) -> bool:
        old_mobs, old_anims = old_state
        if len(old_mobs) != len(self.mobjects): return True
        for om, nm in zip(old_mobs, self.mobjects):
            if (om.x != nm.x or om.y != nm.y or om.scale != nm.scale):
                return True
        return False

    def delete_selected(self) -> None:
        selected_items = self.mob_list_widget.selectedItems()
        if not selected_items: return
        self.save_to_history() 
        ids_to_delete = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        for mob_id in ids_to_delete:
            self.delete_mobject(mob_id, record_history=False) 

    def add_mobject_dialog(self) -> None:
        items = [
            ("Square", None, 'fa5s.square'),
            ("Circle", None, 'fa5s.circle'),
            ("Text", None, 'fa5s.font'),
            ("MathTex", None, 'fa5s.square-root-alt')
        ]
        sel_dlg = TypeSelectorDialog("选择对象类型", items, self)
        if not sel_dlg.exec(): return
        
        selected_type = sel_dlg.selected_item 
        dlg = MobjectEditDialog(self, existing_names=self.mobjects, default_type=selected_type)
        if dlg.exec():
            self.save_to_history()
            data = dlg.get_data()
            new_mob = MobjectData(str(uuid.uuid4()), data["name"], data["type"], data["color"], data["content"], data["font"])
            self.mobjects.append(new_mob)
            self.canvas.add_visual_item(new_mob, self.refresh_ui_dummy, self.handle_item_manipulation)
            self.refresh_ui()

    def edit_mobject_dialog(self, item: QListWidgetItem) -> None:
        mob: MobjectData = next((m for m in self.mobjects if m.id == item.data(Qt.ItemDataRole.UserRole)), None)
        if not mob: return
        dlg = MobjectEditDialog(self, mobject=mob)
        if dlg.exec():
            self.save_to_history()
            data = dlg.get_data()
            mob.name = data["name"]
            mob.color = data["color"]
            mob.content = data["content"]
            mob.font = data["font"]
            self.canvas.update_item_content(mob.id)
            self.refresh_ui()

    def add_animation_dialog(self) -> None:
        if not self.mobjects: 
            QMessageBox.warning(self, "警告", "请先添加对象")
            return
        items = [
            ("Create", findfile("Create.gif"), 'fa5s.magic'),
            ("FadeIn", findfile("FadeIn.gif"), 'fa5s.cloud'),
            ("Write", findfile("Write.gif"), 'fa5s.pen'),
            ("Transform", findfile("Transform.gif"), 'fa5s.random'),
            ("Uncreate", findfile("Uncreate.gif"), 'fa5s.eraser'),
            ("FadeOut", findfile("FadeOut.gif"), 'fa5s.cloud')
        ]
        sel_dlg = TypeSelectorDialog("选择动画效果", items, self)
        if not sel_dlg.exec(): return
        anim_type = sel_dlg.selected_item
        dlg = AnimationEditDialog(self, self.mobjects, default_type=anim_type)
        if dlg.exec():
            self.save_to_history()
            d = dlg.get_data()
            self.animations.append(AnimationData(str(uuid.uuid4()), d["type"], d["target_id"], d["target_name"], d["replacement_id"], d["replacement_name"], d["duration"]))
            self.refresh_ui()

    def edit_animation_dialog(self, item: QListWidgetItem) -> None:
        anim = next((a for a in self.animations if a.id == item.data(Qt.ItemDataRole.UserRole)), None)
        if not anim: return
        target_obj = next((m for m in self.mobjects if m.id == anim.target_id), None)
        if not target_obj:
            replacement_obj = next((m for m in self.mobjects if m.name == anim.target_name_snapshot), None)
            if replacement_obj:
                anim.target_id = replacement_obj.id
                target_obj = replacement_obj
            else:
                QMessageBox.warning(self, "禁止编辑", "该动画绑定的对象已丢失，无法编辑属性。\n请恢复对象或删除此动画。")
                return

        dlg = AnimationEditDialog(self, self.mobjects, animation=anim)
        if dlg.exec():
            self.save_to_history()
            d = dlg.get_data()
            anim.target_id = d["target_id"]
            anim.target_name_snapshot = d["target_name"]
            anim.replacement_id = d["replacement_id"]
            anim.replacement_name_snapshot = d["replacement_name"]
            anim.duration = d["duration"]
            self.refresh_ui()

    def delete_mobject(self, mob_id: str, record_history: bool = True) -> None:
        if record_history: self.save_to_history()
        mob = next((m for m in self.mobjects if m.id == mob_id), None)
        if not mob: return
        self.mobjects.remove(mob)
        self.canvas.remove_visual_item(mob_id)
        self.refresh_ui()

    def delete_animation(self, anim_id: str) -> None:
        self.save_to_history()
        anim = next((a for a in self.animations if a.id == anim_id), None)
        if anim:
            self.animations.remove(anim)
            self.refresh_ui()

    def refresh_ui_dummy(self, mid: str) -> None: pass 

    def refresh_ui(self) -> None:
        self.mob_list_widget.blockSignals(True)
        self.mob_list_widget.clear()
        visual_selected = self.canvas.scene.selectedItems()
        visual_ids = set()
        for v in visual_selected:
            if isinstance(v, VisualMobjectItem):
                visual_ids.add(v.mob_data.id)

        for mob in self.mobjects:
            item = QListWidgetItem(self.mob_list_widget)
            item.setSizeHint(QSize(0, 42))
            item.setData(Qt.ItemDataRole.UserRole, mob.id)
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(5,2,5,2)
            l.addWidget(QLabel(mob.name, styleSheet="font-weight:bold;"))
            l.addStretch()
            l.addWidget(QLabel(mob.mob_type, styleSheet="color:#888; font-size:9pt; margin-right:5px;"))
            btn_del = QPushButton()
            btn_del.setObjectName("DelBtn")
            btn_del.setIcon(qta.icon('fa5s.trash-alt', color='#d13438'))
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setToolTip("删除对象")
            btn_del.clicked.connect(lambda checked, mid=mob.id: self.delete_mobject(mid))
            l.addWidget(btn_del)
            self.mob_list_widget.setItemWidget(item, w)
            if mob.id in visual_ids: item.setSelected(True)

        self.mob_list_widget.blockSignals(False)

        self.anim_list_widget.clear()
        for i, anim in enumerate(self.animations):
            item = QListWidgetItem(self.anim_list_widget)
            item.setSizeHint(QSize(0, 36))
            item.setData(Qt.ItemDataRole.UserRole, anim.id)
            target_obj = next((m for m in self.mobjects if m.id == anim.target_id), None)
            if not target_obj:
                replacement_obj = next((m for m in self.mobjects if m.name == anim.target_name_snapshot), None)
                if replacement_obj:
                    anim.target_id = replacement_obj.id
                    target_obj = replacement_obj
            is_valid = (target_obj is not None)
            display_name = anim.target_name_snapshot
            if target_obj:
                display_name = target_obj.name
                anim.target_name_snapshot = target_obj.name 
            txt = f"{i+1}. {anim.anim_type}: {display_name}"
            if anim.anim_type == "Transform": 
                rep_obj = next((m for m in self.mobjects if m.id == anim.replacement_id), None)
                if not rep_obj and anim.replacement_name_snapshot:
                    found_rep = next((m for m in self.mobjects if m.name == anim.replacement_name_snapshot), None)
                    if found_rep:
                        anim.replacement_id = found_rep.id
                        rep_obj = found_rep
                if not rep_obj: is_valid = False
                else: anim.replacement_name_snapshot = rep_obj.name
                txt += f" -> {anim.replacement_name_snapshot}"
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(5,2,5,2)
            label = QLabel(txt)
            if not is_valid: label.setStyleSheet("color: red;")
            l.addWidget(label)
            l.addStretch()
            btn_del = QPushButton()
            btn_del.setObjectName("DelBtn")
            btn_del.setIcon(qta.icon('fa5s.trash-alt', color='#d13438'))
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setToolTip("删除动画")
            btn_del.clicked.connect(lambda checked, aid=anim.id: self.delete_animation(aid))
            l.addWidget(btn_del)
            self.anim_list_widget.setItemWidget(item, w)

    def generate_script(self) -> str:
        scene_name = self.input_scene_name.text().strip()
        if not scene_name: scene_name = "MyScene"
        class_name = scene_name.replace(' ', '_')

        script = "from manim import *\n"
        script += f"class {class_name}(Scene):\n" 
        script += "    def construct(self):\n"
        
        var_map = {}
        for i, mob in enumerate(self.mobjects):
            var_name = f"m{i}"
            var_map[mob.id] = var_name

            if mob.mob_type == "Square":
                code = f"Square(side_length=2, color='{mob.color}', fill_opacity=0.5)"
            elif mob.mob_type == "Circle":
                code = f"Circle(radius=1, color='{mob.color}', fill_opacity=0.5)"
            elif mob.mob_type == "Text":
                code = f"Text('{mob.content}', color='{mob.color}', font='{mob.font}')"
            elif mob.mob_type == "MathTex":
                code = f"MathTex(r'{mob.content}', color='{mob.color}')"
            else:
                code = "Square()"
            
            line = f"        {var_name} = {code}\n"
            line += f"        {var_name}.move_to([{mob.x}, {mob.y}, 0])\n"
            if mob.scale != 1.0:
                line += f"        {var_name}.scale({mob.scale})\n"
            script += line
            
        script += "\n"
        for anim in self.animations:
            if anim.target_id in var_map:
                target = var_map[anim.target_id]
                if anim.anim_type == "Transform" and anim.replacement_id in var_map:
                    replacement = var_map[anim.replacement_id]
                    script += f"        self.play(Transform({target}, {replacement}), run_time={anim.duration})\n"
                elif anim.anim_type != "Transform":
                    script += f"        self.play({anim.anim_type}({target}), run_time={anim.duration})\n"
                    
        script += "        self.wait(1)\n"
        return script

    def render_video(self) -> None:
        self.render_progress_bar.setVisible(True)
        self.render_progress_bar.setRange(0, 0)
        self.set_ui_locked(True)
        self.console_output.clear()
        self.console_output.append("启动渲染...")
        
        script_content = self.generate_script()
        
        if not os.path.exists("temp_assets"): os.makedirs("temp_assets")
        
        script_file = "temp_assets/final_scene.py"
        try:
            with open(script_file, "w", encoding="utf-8") as f:
                f.write(script_content)
        except Exception as e:
            self.console_output.append(f"写入脚本失败：{e}")
            self.set_ui_locked(False)
            return
        
        raw_name = self.input_scene_name.text().strip()
        if not raw_name: raw_name = "MyScene"
        scene_class_name = raw_name.replace(' ', '_') 
        
        quality_flag = QUALITY_MAP[self.quality_combo.currentText()]
        frame_rate = self.frame_rate_combo.currentText()

        command = f"-m manim -p --resolution {quality_flag} --fps {frame_rate} -o {raw_name} {script_file} {scene_class_name}"
        
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.render_finished)

        self.console_output.append(f"Manim> {command}\n")
        self.process.start(sys.executable, command.split(" "))

    def handle_output(self) -> None:
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")
        self.console_output.insertPlainText(text)
        self.console_output.ensureCursorVisible()

    def render_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self.set_ui_locked(False)
        self.render_progress_bar.setVisible(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ManimEditor()
    window.showMaximized()
    sys.exit(app.exec())