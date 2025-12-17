import sys
import os
import uuid
from dataclasses import dataclass
from typing import Optional
from io import BytesIO
from manim import Text

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QListWidgetItem, QPushButton, QLabel, QLineEdit, 
    QComboBox, QTextEdit, QDialog, QSplitter, QToolBar,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QFormLayout, 
    QMessageBox, QAbstractItemView, QSizePolicy, QFontComboBox, 
    QProgressBar, QGraphicsRectItem, QSlider, QToolButton,
    QScrollArea
)
from PyQt6.QtCore import Qt, QSize, QProcess, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QAction, QColor, QBrush, QPainter, QPixmap, QFont, QIcon, QMovie, 
    QPen, QFontMetrics, QKeyEvent, QKeySequence
)
import qtawesome as qta
import matplotlib.pyplot as plt

os.environ["QT_API"] = "pyqt6"

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "Consolas",
    "font.serif": ["Computer Modern Roman"],
    "mathtext.fontset": "cm",
    "font.size": 14,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "axes.unicode_minus": False
})

QUALITY_MAP = {
    "480p (854*480)": "854,480",
    "720p (1280*720)": "1280,720",
    "1080p (1920*1080)": "1920,1080",
    "4K (3840*2160)": "3840,2160"
}

def findfile(file_name, search_dir=".") -> str | None:
    for root, dirs, files in os.walk(search_dir):
        if file_name in files:
            return os.path.abspath(os.path.join(root, file_name))
    return None

def get_qt_color(color_name):
    c = color_name.lower()
    if c == "white": return QColor("#FFFFFF")
    if c == "black": return QColor("#000000")
    if c == "red": return QColor("#FC6255")
    if c == "blue": return QColor("#58C4DD")
    if c == "green": return QColor("#83C167")
    if c == "yellow": return QColor("#FFFF00")
    if c == "gold": return QColor("#F9A602")
    if c == "purple": return QColor("#9A72AC")
    if c == "grey": return QColor("#888888")
    
    qt_c = QColor(color_name)
    if qt_c.isValid():
        return qt_c
    return QColor("#FFFFFF") 

def render_latex_to_pixmap(latex_text, color_str="#FFFFFF"):
    """
    使用 Matplotlib 在内存中渲染 LaTeX 并返回 (QPixmap, error_message)。
    修复：去除了额外的边距 (bbox_inches='tight', pad_inches=0.0)，调整字号以匹配Manim比例。
    """
    if not latex_text.strip():
        return QPixmap(), None

    fig = None
    try:
        # 使用较小的figsize，但主要依赖bbox_inches='tight'来确定最终大小
        fig = plt.figure(figsize=(1, 1), dpi=100) 
        fig.patch.set_alpha(0)
        
        c = get_qt_color(color_str)
        mpl_color = c.name()

        # fontsize=48 大致对应 Manim 的默认 MathTex 大小
        fig.text(
            0.5, 0.5, f"${latex_text}$",
            ha='center', va='center',
            fontsize=48, color=mpl_color
        )

        buf = BytesIO()
        # pad_inches=0.0 去除白边，使 bounding box 紧贴公式
        fig.savefig(
            buf, format='png',
            bbox_inches='tight', pad_inches=0.0,
            facecolor='none', dpi=100
        )
        buf.seek(0)
        
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        plt.close(fig)
        buf.close()
        return pixmap, None
    except Exception as e:
        if fig:
            plt.close(fig)
        return QPixmap(), str(e)

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

class GifItemWidget(QWidget):
    def __init__(self, text, gif_path=None, icon_fallback=None, parent=None):
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

class TypeSelectorDialog(QDialog):
    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(350, 450)
        self.selected_item = None
        
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
        
    def accept_selection(self):
        current = self.list_widget.currentItem()
        if current:
            self.selected_item = current.data(Qt.ItemDataRole.UserRole)
            self.accept()

class MobjectEditDialog(QDialog):
    def __init__(self, parent=None, mobject: MobjectData = None, existing_names=None, default_type="Square"):
        super().__init__(parent)
        self.setWindowTitle("对象属性设置")
        self.resize(420, 0) 
        
        self.layout = QFormLayout(self)
        self.layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.name_edit = QLineEdit()
        if mobject: 
            self.name_edit.setText(mobject.name)
        elif existing_names is not None: 
            self.name_edit.setText(f"{default_type}_{len(existing_names) + 1}")
            
        self.type_label = QLabel(mobject.mob_type if mobject else default_type)
        
        self.color_edit = QLineEdit("WHITE") 
        if mobject: self.color_edit.setText(mobject.color)
        
        self.content_edit = QLineEdit("E=mc^2")
        if mobject: self.content_edit.setText(mobject.content)
        self.content_edit.textChanged.connect(self.on_content_changed)
        
        self.font_combo = QFontComboBox()
        self.font_combo.clear()
        self.font_combo.addItems(Text.font_list())
        if mobject and mobject.font:
            self.font_combo.setCurrentFont(QFont(mobject.font))
        
        self.content_label = QLabel("内容:")
        self.font_label = QLabel("字体:")
        
        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        self.preview_area.setFixedHeight(140)
        self.preview_area.setVisible(False)
        self.preview_label = QLabel("公式预览")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        self.preview_area.setWidget(self.preview_label)

        self.layout.addRow("类型:", self.type_label)
        self.layout.addRow("名称:", self.name_edit)
        self.layout.addRow("颜色:", self.color_edit)
        
        self.layout.addRow(self.content_label, self.content_edit)
        self.layout.addRow(self.font_label, self.font_combo)
        self.layout.addRow(self.preview_area)
        
        btn_ok = QPushButton("应用")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet("background-color: #0078d4; color: white; border: none; padding: 6px; font-weight: bold;")
        btn_ok.clicked.connect(self.validate_and_accept)
        self.layout.addRow(btn_ok)

        self.update_fields(self.type_label.text())

    def update_fields(self, text):
        is_text = (text == "Text")
        is_math = (text == "MathTex")
        
        self.content_label.setVisible(is_text or is_math)
        self.content_edit.setVisible(is_text or is_math)
        
        self.font_label.setVisible(is_text)
        self.font_combo.setVisible(is_text)
        
        self.preview_area.setVisible(is_math)
        
        if is_math:
            self.content_label.setText("LaTeX:")
            self.update_preview(self.content_edit.text())
        else:
            self.content_label.setText("文本:")

    def on_content_changed(self, text):
        if self.type_label.text() == "MathTex":
            self.update_preview(text)

    def update_preview(self, latex_text):
        pixmap, error = render_latex_to_pixmap(latex_text, "black")
        
        if error:
            self.preview_label.setText(error.strip())
            self.preview_label.setStyleSheet("background-color: #fff0f0; border: 1px solid red; color: #d13438; padding: 5px;")
        elif not pixmap.isNull():
            # 缩略图预览不需要像canvas那样严格，自适应宽度即可
            current_width = self.preview_area.width()
            max_width = 360 if (current_width < 100 or current_width > 600) else current_width - 25
            if pixmap.width() > max_width:
                pixmap = pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
            
            self.preview_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
            self.preview_label.setPixmap(pixmap)
        else:
            self.preview_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
            self.preview_label.setText("Empty")

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "提示", "名称不能为空！")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "type": self.type_label.text(),
            "color": self.color_edit.text(),
            "content": self.content_edit.text(),
            "font": self.font_combo.currentFont().family()
        }

class AnimationEditDialog(QDialog):
    def __init__(self, parent=None, mobjects=[], animation: AnimationData = None, default_type="Create"):
        super().__init__(parent)
        self.setWindowTitle("动画属性设置")
        self.resize(350, 0)
        
        self.mobjects = mobjects
        self.layout = QFormLayout(self)
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

    def get_data(self):
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

class ResizeHandle(QGraphicsRectItem):
    def __init__(self: "ResizeHandle", parent, cursor_shape):
        super().__init__(-5, -5, 10, 10, parent)
        self.setBrush(QBrush(QColor("white")))
        self.setPen(QPen(QColor("#0078d4"), 1))
        self.setCursor(cursor_shape)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIgnoresParentOpacity)
        self.setZValue(99) 

    def mouseMoveEvent(self, event):
        self.parentItem().handle_resize_event(self, event.scenePos())

class VisualMobjectItem(QGraphicsItem):
    BASE_TEXT_SIZE = 32 

    def __init__(self, mobject_data: MobjectData, scene_scale, on_move_callback):
        super().__init__()
        self.mob_data = mobject_data
        self.scene_scale = scene_scale 
        self.on_move_callback = on_move_callback
        
        self.setZValue(1)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable | 
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        self.cached_pixmap = None
        self.last_content_signature = None 
        self.has_render_error = False

        self.update_content()
        
        self.setScale(self.mob_data.scale)
        self.update_position_from_data()
        self.update_tooltip()
        
        self.handles = []
        self.is_resizing = False

    def update_content(self):
        sig = (self.mob_data.content, self.mob_data.color, self.mob_data.font, self.mob_data.mob_type)
        if sig == self.last_content_signature:
            return
        
        self.last_content_signature = sig
        self.prepareGeometryChange()
        self.has_render_error = False
        
        if self.mob_data.mob_type == "MathTex":
            self.cached_pixmap, error = render_latex_to_pixmap(self.mob_data.content, self.mob_data.color)
            if error:
                self.has_render_error = True
        
        self._bounding_rect = self._calculate_bounding_rect()

    def _calculate_bounding_rect(self):
        factor = 1.0 / self.scene_scale 
        
        if self.mob_data.mob_type == "Square":
            s = 2.0 * factor
            return QRectF(-s/2, -s/2, s, s)
        elif self.mob_data.mob_type == "Circle":
            d = 2.0 * factor 
            return QRectF(-d/2, -d/2, d, d)
        elif self.mob_data.mob_type == "Text":
            font = QFont(self.mob_data.font, self.BASE_TEXT_SIZE) 
            fm = QFontMetrics(font)
            rect = fm.boundingRect(self.mob_data.content)
            return QRectF(-rect.width()/2, -rect.height()/2, rect.width(), rect.height())
        elif self.mob_data.mob_type == "MathTex":
            if self.cached_pixmap and not self.cached_pixmap.isNull():
                w, h = self.cached_pixmap.width(), self.cached_pixmap.height()
                # 修复：缩放 MathTex 以匹配 Canvas (540p) 和 Manim (1080p) 之间的比例差异
                # render_latex_to_pixmap 使用字号48渲染出的像素高度约为66px
                # 在540p Canvas上直接显示会显得过大（看起来像1080p的一样大，但画布只有一半大）
                # 乘以 0.5 使其视觉比例与 Square 等对象协调
                scale_fix = 0.5 
                w_scaled = w * scale_fix
                h_scaled = h * scale_fix
                return QRectF(-w_scaled/2, -h_scaled/2, w_scaled, h_scaled)
            else:
                return QRectF(-50, -25, 100, 50)
        
        return QRectF(-50, -50, 100, 100)

    def boundingRect(self):
        base_rect = self._bounding_rect
        padding = 5.0 
        if self.mob_data.mob_type == "Text":
            padding = 10.0
        return base_rect.adjusted(-padding, -padding, padding, padding)

    def paint(self, painter, option, widget):
        color = get_qt_color(self.mob_data.color)
        
        if self.has_render_error and self.mob_data.mob_type == "MathTex":
            color = Qt.GlobalColor.red
            
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        rect = self._bounding_rect
        
        if self.mob_data.mob_type == "Square":
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color.lighter(150)))
            c = QColor(color)
            c.setAlphaF(0.5)
            painter.setBrush(QBrush(c))
            painter.drawRect(rect)
            
        elif self.mob_data.mob_type == "Circle":
            painter.setPen(QPen(color, 2))
            c = QColor(color)
            c.setAlphaF(0.5)
            painter.setBrush(QBrush(c))
            painter.drawEllipse(rect)
            
        elif self.mob_data.mob_type == "Text":
            painter.setPen(QPen(color))
            font = QFont(self.mob_data.font, self.BASE_TEXT_SIZE)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextDontClip, self.mob_data.content)
            
        elif self.mob_data.mob_type == "MathTex":
            if self.has_render_error:
                painter.setPen(QPen(Qt.GlobalColor.red, 2))
                painter.drawRect(rect)
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "LaTeX Error")
            elif self.cached_pixmap and not self.cached_pixmap.isNull():
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                # 需要按照 bounding rect 的大小绘制 pixmap
                painter.drawPixmap(rect.toRect(), self.cached_pixmap)
            else:
                painter.setPen(QPen(color))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Empty")

        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.blue, 1, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())

    def update_position_from_data(self):
        self.setPos(self.mob_data.x / self.scene_scale, -self.mob_data.y / self.scene_scale)
        
    def update_tooltip(self):
        self.setToolTip(f"{self.mob_data.name}\nPos: ({self.mob_data.x:.2f}, {self.mob_data.y:.2f})\nScale: {self.mob_data.scale:.2f}")
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and not self.is_resizing:
            new_pos = value
            self.mob_data.x = round(new_pos.x() * self.scene_scale, 2)
            self.mob_data.y = round(-new_pos.y() * self.scene_scale, 2)
            self.update_tooltip()
            if self.on_move_callback: self.on_move_callback(self.mob_data.id)
            
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value:
                self.create_handles()
            else:
                self.remove_handles()
                
        return super().itemChange(change, value)

    def create_handles(self):
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

    def remove_handles(self):
        for h in self.handles:
            self.scene().removeItem(h)
        self.handles.clear()

    def handle_resize_event(self, handle, mouse_scene_pos):
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
        for h in self.handles:
            h.setScale(inv_scale)
            
        self.is_resizing = False

class ManimCanvas(QGraphicsView):
    scale_changed = pyqtSignal(int) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_width = 960
        self.scene_height = 540
        self.units_to_pixels = 540 / 8.0 
        self.pixels_to_units = 1.0 / self.units_to_pixels
        
        self.scene = QGraphicsScene(-2000, -2000, 4000, 4000)
        self.setScene(self.scene)
        self.setBackgroundBrush(QBrush(QColor("#555555"))) 
        
        self.black_board = QGraphicsRectItem(-self.scene_width/2, -self.scene_height/2, self.scene_width, self.scene_height)
        self.black_board.setBrush(QBrush(Qt.GlobalColor.black))
        self.black_board.setZValue(-1) 
        self.scene.addItem(self.black_board)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        self.items_map = {}
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.current_zoom_percent = 100

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.set_zoom(self.current_zoom_percent + 10)
            else:
                self.set_zoom(self.current_zoom_percent - 10)
        else:
            super().wheelEvent(event)

    def set_zoom(self, percent):
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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            fake_event = event
            super().mousePressEvent(fake_event)
        else:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        super().mouseReleaseEvent(event)

    def add_visual_item(self, mobject: MobjectData, on_move_cb):
        if mobject.id in self.items_map: 
            self.remove_visual_item(mobject.id)
            
        item = VisualMobjectItem(mobject, self.pixels_to_units, on_move_cb)
        self.scene.addItem(item)
        self.items_map[mobject.id] = item

    def update_item_content(self, mob_id):
        if mob_id in self.items_map:
            item = self.items_map[mob_id]
            item.update_content()
            item.update()

    def remove_visual_item(self, mob_id):
        if mob_id in self.items_map:
            self.scene.removeItem(self.items_map[mob_id])
            del self.items_map[mob_id]
            
    def set_item_visible(self, mob_id, visible):
        if mob_id in self.items_map:
            self.items_map[mob_id].setVisible(visible)

class ManimEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manim Visual Editor")
        self.setWindowIcon(QIcon(findfile("ManimCELogo.png")))
        self.mobjects = []
        self.animations = []
        
        self.is_syncing_selection = False

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

    def init_ui(self):
        self.act_undo = QAction("撤销 (Ctrl+Z)", self)
        self.act_undo.setShortcut("Ctrl+Z")
        self.act_undo.triggered.connect(self.undo_action)
        self.addAction(self.act_undo)
        
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
        toolbar.addAction(self.act_undo)

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
        self.zoom_out_btn.setIcon(qta.icon('fa5s.minus', color='#555'))
        self.zoom_out_btn.setFixedSize(24, 24)
        self.zoom_out_btn.clicked.connect(lambda: self.zoom_slider.setValue(self.zoom_slider.value() - 10))
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 400)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150)
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_change)
        
        self.zoom_in_btn = QToolButton()
        self.zoom_in_btn.setObjectName("ZoomBtn")
        self.zoom_in_btn.setIcon(qta.icon('fa5s.plus', color='#555'))
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

    def on_zoom_slider_change(self, value):
        self.zoom_label.setText(f"{value}%")
        self.canvas.set_zoom(value)

    def sync_zoom_ui(self, percent):
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(percent)
        self.zoom_label.setText(f"{percent}%")
        self.zoom_slider.blockSignals(False)

    def set_ui_locked(self, locked: bool):
        self.act_add_mob.setEnabled(not locked)
        self.act_add_anim.setEnabled(not locked)
        self.btn_render_big.setEnabled(not locked)
        self.input_scene_name.setEnabled(not locked)
        self.quality_combo.setEnabled(not locked)
        self.frame_rate_combo.setEnabled(not locked)
        if locked:
            QApplication.setOverrideCursor(Qt.CursorShape.ForbiddenCursor)
        else:
            QApplication.restoreOverrideCursor()

    def sync_selection_list_to_canvas(self):
        if self.is_syncing_selection: return
        self.is_syncing_selection = True
        
        selected_items = self.mob_list_widget.selectedItems()
        selected_ids = {item.data(Qt.ItemDataRole.UserRole) for item in selected_items}
        
        self.canvas.scene.clearSelection()
        for mob_id, item in self.canvas.items_map.items():
            if mob_id in selected_ids:
                item.setSelected(True)
        
        self.is_syncing_selection = False

    def sync_selection_canvas_to_list(self):
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

    def delete_selected(self):
        selected_items = self.mob_list_widget.selectedItems()
        if not selected_items:
            return
            
        ids_to_delete = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        
        for mob_id in ids_to_delete:
            self.delete_mobject(mob_id)

    def add_mobject_dialog(self):
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
            data = dlg.get_data()
            new_mob = MobjectData(str(uuid.uuid4()), data["name"], data["type"], data["color"], data["content"], data["font"])
            self.mobjects.append(new_mob)
            self.canvas.add_visual_item(new_mob, self.refresh_ui_dummy)
            self.refresh_ui()

    def edit_mobject_dialog(self, item):
        mob = next((m for m in self.mobjects if m.id == item.data(Qt.ItemDataRole.UserRole)), None)
        if not mob: return
        dlg = MobjectEditDialog(self, mobject=mob)
        if dlg.exec():
            data = dlg.get_data()
            mob.name = data["name"]
            mob.color = data["color"]
            mob.content = data["content"]
            mob.font = data["font"]
            self.canvas.update_item_content(mob.id)
            self.refresh_ui()

    def add_animation_dialog(self):
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
            d = dlg.get_data()
            self.animations.append(AnimationData(str(uuid.uuid4()), d["type"], d["target_id"], d["target_name"], d["replacement_id"], d["replacement_name"], d["duration"]))
            self.refresh_ui()

    def edit_animation_dialog(self, item):
        anim = next((a for a in self.animations if a.id == item.data(Qt.ItemDataRole.UserRole)), None)
        if not anim: return
        
        # 修复：检查动画关联的对象是否存在，如果对象已丢失，禁止编辑属性
        target_obj = next((m for m in self.mobjects if m.id == anim.target_id), None)
        if not target_obj:
             # 尝试通过名称查找（自动修复逻辑）
            replacement_obj = next((m for m in self.mobjects if m.name == anim.target_name_snapshot), None)
            if replacement_obj:
                anim.target_id = replacement_obj.id
                target_obj = replacement_obj
            else:
                QMessageBox.warning(self, "禁止编辑", "该动画绑定的对象已丢失，无法编辑属性。\n请恢复对象或删除此动画。")
                return

        dlg = AnimationEditDialog(self, self.mobjects, animation=anim)
        if dlg.exec():
            d = dlg.get_data()
            anim.target_id = d["target_id"]
            anim.target_name_snapshot = d["target_name"]
            anim.replacement_id = d["replacement_id"]
            anim.replacement_name_snapshot = d["replacement_name"]
            anim.duration = d["duration"]
            self.refresh_ui()

    def delete_mobject(self, mob_id):
        mob = next((m for m in self.mobjects if m.id == mob_id), None)
        if not mob: return
        self.mobjects.remove(mob)
        self.canvas.remove_visual_item(mob_id)
        self.refresh_ui()

    def delete_animation(self, anim_id):
        anim = next((a for a in self.animations if a.id == anim_id), None)
        if anim:
            self.animations.remove(anim)
            self.refresh_ui()

    def refresh_ui_dummy(self, mid): pass 

    def refresh_ui(self):
        self.mob_list_widget.blockSignals(True)
        self.mob_list_widget.clear()
        
        selection_preserved = []
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
            
            if mob.id in visual_ids:
                item.setSelected(True)

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
                
                if not rep_obj:
                    is_valid = False
                else:
                    anim.replacement_name_snapshot = rep_obj.name
                    
                txt += f" -> {anim.replacement_name_snapshot}"

            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(5,2,5,2)
            
            label = QLabel(txt)
            if not is_valid:
                label.setStyleSheet("color: red;")
            
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

    def undo_action(self):
        pass 

    def generate_script(self):
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
            
            color_param = f"color='{mob.color}'" if mob.color else ""
            if mob.mob_type == "Square":
                code = f"Square(side_length=2, {color_param}, fill_opacity=0.5)"
            elif mob.mob_type == "Circle":
                code = f"Circle(radius=1, {color_param}, fill_opacity=0.5)"
            elif mob.mob_type == "Text":
                f_p = f", font='{mob.font}'" if mob.font else ""
                code = f"Text('{mob.content}', {color_param}{f_p})"
            elif mob.mob_type == "MathTex":
                code = f"MathTex(r'{mob.content}', {color_param})"
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

    def render_video(self):
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

    def handle_output(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")
        self.console_output.insertPlainText(text)
        self.console_output.ensureCursorVisible()

    def render_finished(self, exit_code, exit_status):
        self.set_ui_locked(False)
        self.render_progress_bar.setVisible(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ManimEditor()
    window.showMaximized()
    sys.exit(app.exec())