import sys
import os

# --- 强制使用 PyQt6 ---
os.environ["QT_API"] = "pyqt6"

import uuid
from dataclasses import dataclass
from typing import Optional

# 图标库
import qtawesome as qta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QListWidgetItem, QPushButton, QLabel, QLineEdit, 
    QComboBox, QTextEdit, QDialog, QSplitter, 
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem, 
    QFormLayout, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, QSize, QProcess, QUrl, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import (
    QAction, QColor, QPalette, QTextCursor, QBrush, QPen, 
    QDesktopServices, QPainter, QPixmap, QFont
)

# --- 数据模型 ---

@dataclass
class MobjectData:
    id: str
    name: str
    mob_type: str
    color: str
    content: str = "" 
    x: float = 0.0
    y: float = 0.0
    image_path: str = "" 
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

# --- 对话框 ---

class MobjectEditDialog(QDialog):
    def __init__(self, parent=None, mobject: MobjectData = None, existing_names=None):
        super().__init__(parent)
        self.setWindowTitle("Mobject Settings")
        self.resize(300, 200)
        self.layout = QFormLayout(self)
        
        self.name_edit = QLineEdit()
        if mobject: 
            self.name_edit.setText(mobject.name)
        elif existing_names is not None: 
            self.name_edit.setText(f"mob_{len(existing_names)}")
            
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Square", "Circle", "Text"])
        if mobject: self.type_combo.setCurrentText(mobject.mob_type)
        
        self.color_edit = QLineEdit("BLUE")
        if mobject: self.color_edit.setText(mobject.color)
        
        self.content_edit = QLineEdit("Hello World")
        if mobject: self.content_edit.setText(mobject.content)
        
        self.content_label = QLabel("Content:")
        
        self.layout.addRow("Name:", self.name_edit)
        self.layout.addRow("Type:", self.type_combo)
        self.layout.addRow("Color:", self.color_edit)
        self.layout.addRow(self.content_label, self.content_edit)
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.validate_and_accept)
        self.layout.addRow(btn_ok)
        
        self.type_combo.currentTextChanged.connect(self.update_fields)
        self.update_fields(self.type_combo.currentText()) 

    def update_fields(self, text):
        is_text = (text == "Text")
        self.content_label.setVisible(is_text)
        self.content_edit.setVisible(is_text)

    def validate_and_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Name cannot be empty!")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "type": self.type_combo.currentText(),
            "color": self.color_edit.text(),
            "content": self.content_edit.text()
        }

class AnimationEditDialog(QDialog):
    def __init__(self, parent=None, mobjects=[], animation: AnimationData = None):
        super().__init__(parent)
        self.setWindowTitle("Animation Settings")
        self.resize(300, 200)
        self.mobjects = mobjects
        self.layout = QFormLayout(self)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Create", "FadeIn", "Write", "Uncreate", "FadeOut", "Transform"])
        if animation: self.type_combo.setCurrentText(animation.anim_type)
        
        self.target_combo = QComboBox()
        for m in mobjects: self.target_combo.addItem(m.name, m.id)
        if animation: 
            idx = self.target_combo.findData(animation.target_id)
            if idx >= 0: self.target_combo.setCurrentIndex(idx)
            
        self.replacement_label = QLabel("Transform To:")
        self.replacement_combo = QComboBox()
        for m in mobjects: self.replacement_combo.addItem(m.name, m.id)
        if animation and animation.replacement_id:
            idx = self.replacement_combo.findData(animation.replacement_id)
            if idx >= 0: self.replacement_combo.setCurrentIndex(idx)
            
        self.dur_edit = QLineEdit("1.0")
        if animation: self.dur_edit.setText(str(animation.duration))
        
        self.layout.addRow("Type:", self.type_combo)
        self.layout.addRow("Target:", self.target_combo)
        self.layout.addRow(self.replacement_label, self.replacement_combo)
        self.layout.addRow("Duration:", self.dur_edit)
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        self.layout.addRow(btn_ok)
        
        self.type_combo.currentTextChanged.connect(self.update_fields)
        self.update_fields(self.type_combo.currentText())

    def update_fields(self, text):
        is_transform = (text == "Transform")
        self.replacement_label.setVisible(is_transform)
        self.replacement_combo.setVisible(is_transform)

    def get_data(self):
        try: dur = float(self.dur_edit.text())
        except: dur = 1.0
        
        rep_id = None
        rep_name = None
        if self.type_combo.currentText() == "Transform":
            rep_id = self.replacement_combo.currentData()
            rep_name = self.replacement_combo.currentText()

        return {
            "type": self.type_combo.currentText(),
            "target_id": self.target_combo.currentData(),
            "target_name": self.target_combo.currentText(),
            "replacement_id": rep_id,
            "replacement_name": rep_name,
            "duration": dur
        }

# --- 1. 后台渲染线程 ---

class MobjectRenderThread(QThread):
    finished_signal = pyqtSignal(str, str) 
    error_signal = pyqtSignal(str)

    def __init__(self, mob_data: MobjectData):
        super().__init__()
        self.mob_data = mob_data
        self.temp_dir = os.path.join(os.getcwd(), "temp_assets")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def run(self):
        try:
            filename = f"{self.mob_data.id}.png"
            abs_img_path = os.path.join(self.temp_dir, filename).replace("\\", "/")
            
            creation_code = ""
            if self.mob_data.mob_type == "Square":
                creation_code = f"Square(color='{self.mob_data.color}', fill_opacity=0.5)"
            elif self.mob_data.mob_type == "Circle":
                creation_code = f"Circle(color='{self.mob_data.color}', fill_opacity=0.5)"
            elif self.mob_data.mob_type == "Text":
                creation_code = f"Text('{self.mob_data.content}', color='{self.mob_data.color}')"
            
            script = f"""
from manim import *
config.verbosity = "CRITICAL"
config.background_opacity = 0.0 

class Gen(Scene):
    def construct(self):
        try:
            mob = {creation_code}
            mob.move_to(ORIGIN)
            img = mob.get_image()
            bbox = img.getbbox()
            if bbox: img = img.crop(bbox)
            img.save(r"{abs_img_path}")
        except Exception as e:
            print(f"PYTHON_SCRIPT_ERROR: {{e}}")
"""
            script_filename = f"gen_{self.mob_data.id}.py"
            script_path = os.path.join(self.temp_dir, script_filename)
            with open(script_path, "w", encoding="utf-8") as f: f.write(script)

            process = QProcess()
            process.setWorkingDirectory(self.temp_dir)
            process.start("manim", ["-ql", "--dry_run", script_filename, "Gen"])
            process.waitForFinished()
            
            if os.path.exists(abs_img_path):
                self.finished_signal.emit(self.mob_data.id, abs_img_path)
            else:
                raw_err = process.readAllStandardError().data().decode("utf-8", errors="replace")
                if not raw_err.strip():
                    raw_err = process.readAllStandardOutput().data().decode("utf-8", errors="replace")
                self.error_signal.emit(f"Failed to render preview.\nOutput: {raw_err}")

        except Exception as e:
            self.error_signal.emit(str(e))

# --- 2. Canvas Items ---

class DraggableItem:
    def __init__(self, mobject_data: MobjectData, scene_scale, on_move_callback):
        self.mob_data = mobject_data
        self.scene_scale = scene_scale 
        self.on_move_callback = on_move_callback
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        self.update_position_from_data()
        self.update_tooltip()
        self.setVisible(self.mob_data.visible)

    def update_position_from_data(self):
        pixel_x = self.mob_data.x / self.scene_scale
        pixel_y = -self.mob_data.y / self.scene_scale 
        self.setPos(pixel_x, pixel_y)

    def update_tooltip(self):
        self.setToolTip(f"{self.mob_data.name}\n({self.mob_data.x:.2f}, {self.mob_data.y:.2f})")

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value
            mx = new_pos.x() * self.scene_scale
            my = -new_pos.y() * self.scene_scale
            self.mob_data.x = round(mx, 2)
            self.mob_data.y = round(my, 2)
            self.update_tooltip()
            if self.on_move_callback:
                self.on_move_callback(self.mob_data.id)
        return super().itemChange(change, value)

class DraggableManimImage(DraggableItem, QGraphicsPixmapItem):
    def __init__(self, mobject_data, pixmap, scene_scale, on_move_callback):
        QGraphicsPixmapItem.__init__(self, pixmap)
        DraggableItem.__init__(self, mobject_data, scene_scale, on_move_callback)
        w = pixmap.width()
        h = pixmap.height()
        self.setOffset(-w/2, -h/2)
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
    def itemChange(self, change, value): return DraggableItem.itemChange(self, change, value)

# --- 3. Canvas ---

class ManimCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_width = 800
        self.scene_height = 450
        self.units_to_pixels = 450 / 8.0 
        self.pixels_to_units = 1.0 / self.units_to_pixels
        
        self.scene = QGraphicsScene(
            -self.scene_width/2, -self.scene_height/2, 
            self.scene_width, self.scene_height
        )
        self.setScene(self.scene)
        self.setBackgroundBrush(QBrush(Qt.GlobalColor.black))
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.items_map = {}

    def add_image_item(self, mobject: MobjectData, image_path: str, on_move_cb):
        if not os.path.exists(image_path): return
        pixmap = QPixmap(image_path)
        if pixmap.width() > 1000: pixmap = pixmap.scaledToWidth(1000, Qt.TransformationMode.SmoothTransformation)

        if mobject.id in self.items_map: self.remove_visual_item(mobject.id)

        item = DraggableManimImage(mobject, pixmap, self.pixels_to_units, on_move_cb)
        self.scene.addItem(item)
        self.items_map[mobject.id] = item

    def remove_visual_item(self, mob_id):
        if mob_id in self.items_map:
            item = self.items_map[mob_id]
            self.scene.removeItem(item)
            del self.items_map[mob_id]
            
    def set_item_visible(self, mob_id, visible):
        if mob_id in self.items_map:
            self.items_map[mob_id].setVisible(visible)

# --- 4. Main Window ---

class ConsoleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Render Console")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas;")
        layout.addWidget(self.text_area)

    def append_output(self, text, is_error=False):
        cursor = self.text_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.text_area.setTextCursor(cursor)
        if is_error or "Error" in text or "Exception" in text:
            html = f'<span style="color: #ff5555;">{text}</span><br>'
        else:
            html = f'<span style="color: #d4d4d4;">{text}</span><br>'
        self.text_area.insertHtml(html)
        self.text_area.ensureCursorVisible()

class ManimEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manim Visual Editor - Pro V9")
        self.resize(1300, 800)
        self.mobjects = []
        self.animations = []
        self.undo_stack = [] 
        self.render_threads = {}
        self.init_ui()

    def init_ui(self):
        # 【关键修改】移除了 MenuBar，仅保留 Undo 的 Action 绑定
        undo_action = QAction("Undo Delete", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_action)
        # 将 Action 添加到主窗口，这样快捷键依然有效
        self.addAction(undo_action)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left Panel
        left_panel = QWidget()
        l_layout = QVBoxLayout(left_panel)
        l_header = QHBoxLayout()
        l_header.addWidget(QLabel("<b>Mobjects</b>"))
        
        btn_add = QPushButton()
        btn_add.setIcon(qta.icon('fa5s.plus', color='white')) 
        btn_add.clicked.connect(self.add_mobject_dialog)
        l_header.addWidget(btn_add)
        l_layout.addLayout(l_header)
        
        self.mob_list_widget = QListWidget()
        self.mob_list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.mob_list_widget.itemDoubleClicked.connect(self.edit_mobject_dialog)
        
        # 【修改】移除了 itemClicked 连接，单击不再触发隐藏
        # self.mob_list_widget.itemClicked.connect(self.on_mob_list_item_clicked)
        
        self.mob_list_widget.setStyleSheet(
            "QListWidget::item:selected { background-color: transparent; border: 1px solid #555; }"
        )
        l_layout.addWidget(self.mob_list_widget)
        l_layout.addWidget(QLabel("<small>Eye icon: visibility. Double-click: edit.</small>"))
        splitter.addWidget(left_panel)
        
        # Center Panel
        center_panel = QWidget()
        c_layout = QVBoxLayout(center_panel)
        c_layout.addWidget(QLabel("<b>Preview Canvas</b>"))
        
        self.canvas = ManimCanvas()
        self.canvas.setFixedSize(820, 470) 
        
        canvas_container = QWidget()
        cc_layout = QHBoxLayout(canvas_container)
        cc_layout.addWidget(self.canvas)
        cc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.addWidget(canvas_container)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #aaa;")
        c_layout.addWidget(self.status_label)

        # Settings
        settings_widget = QWidget()
        form_layout = QFormLayout(settings_widget)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        self.input_scene_name = QLineEdit("MyScene")
        self.input_scene_name.setPlaceholderText("Scene Name (Space safe)")
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("480p @ 15fps (Low) [-ql]", "-ql")
        self.quality_combo.addItem("720p @ 30fps (Medium) [-qm]", "-qm")
        self.quality_combo.addItem("1080p @ 60fps (High) [-qh]", "-qh")
        self.quality_combo.addItem("2160p @ 60fps (4K) [-qk]", "-qk")
        self.quality_combo.setCurrentIndex(2) 
        
        self.btn_render = QPushButton(" Render Video")
        self.btn_render.setIcon(qta.icon('fa5s.video', color='white')) 
        # Flat style
        self.btn_render.setStyleSheet("""
            QPushButton {
                background-color: #2a82da; 
                color: white; 
                border: none;
                border-radius: 4px;
                padding: 8px; 
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
            QPushButton:pressed {
                background-color: #1a72ca;
            }
        """)
        self.btn_render.clicked.connect(self.render_video)
        
        form_layout.addRow("Scene Name:", self.input_scene_name)
        form_layout.addRow("Quality:", self.quality_combo)
        form_layout.addRow(self.btn_render)
        
        c_layout.addWidget(settings_widget)
        splitter.addWidget(center_panel)
        
        # Right Panel
        right_panel = QWidget()
        r_layout = QVBoxLayout(right_panel)
        r_header = QHBoxLayout()
        r_header.addWidget(QLabel("<b>Animations</b>"))
        
        btn_add_anim = QPushButton()
        btn_add_anim.setIcon(qta.icon('fa5s.plus', color='white')) 
        btn_add_anim.clicked.connect(self.add_animation_dialog)
        r_header.addWidget(btn_add_anim)
        r_layout.addLayout(r_header)
        
        self.anim_list_widget = QListWidget()
        self.anim_list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.anim_list_widget.itemDoubleClicked.connect(self.edit_animation_dialog)
        self.anim_list_widget.setStyleSheet(
            "QListWidget::item:selected { background-color: transparent; border: 1px solid #555; }"
        )
        r_layout.addWidget(self.anim_list_widget)
        r_layout.addWidget(QLabel("<small>Double-click to edit. Drag to reorder.</small>"))
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)

    # --- Item Widgets ---

    def create_mob_item_widget(self, mob):
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        btn_eye = QPushButton()
        btn_eye.setFixedSize(24, 24)
        btn_eye.setStyleSheet("border: none; background: transparent;")
        btn_eye.setCursor(Qt.CursorShape.PointingHandCursor) 
        
        if mob.visible:
            btn_eye.setIcon(qta.icon('fa5s.eye', color='white'))
        else:
            btn_eye.setIcon(qta.icon('fa5s.eye-slash', color='grey'))
        
        btn_eye.clicked.connect(lambda: self.toggle_mobject_visibility(mob.id))
        layout.addWidget(btn_eye)

        txt = f"{mob.name} ({mob.mob_type})\nPos: x={mob.x}, y={mob.y}"
        lbl = QLabel(txt)
        if not mob.visible:
            lbl.setStyleSheet("color: grey; text-decoration: line-through;")
        else:
            lbl.setStyleSheet("color: white;")
        layout.addWidget(lbl)
        
        btn_del = QPushButton()
        btn_del.setFixedSize(24, 24)
        btn_del.setStyleSheet("border: none; background: transparent;")
        btn_del.setIcon(qta.icon('fa5s.trash-alt', color='#ff5555'))
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor) 
        
        btn_del.clicked.connect(lambda: self.delete_mobject(mob.id))
        layout.addWidget(btn_del)
        return widget

    def create_anim_item_widget(self, anim):
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        mob_exists = any(m.id == anim.target_id for m in self.mobjects)
        display_name = anim.target_name_snapshot
        if mob_exists:
             curr_mob = next(m for m in self.mobjects if m.id == anim.target_id)
             display_name = curr_mob.name
        
        if anim.anim_type == "Transform" and anim.replacement_name_snapshot:
            rep_exists = any(m.id == anim.replacement_id for m in self.mobjects)
            rep_display = anim.replacement_name_snapshot
            if rep_exists:
                rep_mob = next(m for m in self.mobjects if m.id == anim.replacement_id)
                rep_display = rep_mob.name
            text_str = f"Transform({display_name}, {rep_display})"
            is_broken = (not mob_exists) or (not rep_exists)
        else:
            text_str = f"{anim.anim_type}({display_name})"
            is_broken = not mob_exists

        lbl = QLabel(text_str)
        if is_broken:
            lbl.setStyleSheet("color: #ff5555; font-weight: bold;") 
        layout.addWidget(lbl)
        
        btn_del = QPushButton()
        btn_del.setFixedSize(24, 24)
        btn_del.setStyleSheet("border: none; background: transparent;")
        btn_del.setIcon(qta.icon('fa5s.trash-alt', color='#ff5555'))
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor) 
        
        btn_del.clicked.connect(lambda: self.delete_animation(anim.id))
        layout.addWidget(btn_del)
        return widget

    # --- Logic ---

    def sync_data_order(self):
        new_mobs = []
        for i in range(self.mob_list_widget.count()):
            item = self.mob_list_widget.item(i)
            mob_id = item.data(Qt.ItemDataRole.UserRole)
            mob = next((m for m in self.mobjects if m.id == mob_id), None)
            if mob: new_mobs.append(mob)
        self.mobjects = new_mobs

        new_anims = []
        for i in range(self.anim_list_widget.count()):
            item = self.anim_list_widget.item(i)
            anim_id = item.data(Qt.ItemDataRole.UserRole)
            anim = next((a for a in self.animations if a.id == anim_id), None)
            if anim: new_anims.append(anim)
        self.animations = new_anims

    def toggle_mobject_visibility(self, mob_id):
        mob = next((m for m in self.mobjects if m.id == mob_id), None)
        if mob:
            mob.visible = not mob.visible
            self.canvas.set_item_visible(mob.id, mob.visible)
            # Refresh row to update text style
            for i in range(self.mob_list_widget.count()):
                it = self.mob_list_widget.item(i)
                if it.data(Qt.ItemDataRole.UserRole) == mob_id:
                    self.mob_list_widget.setItemWidget(it, self.create_mob_item_widget(mob))
                    break

    def add_mobject_dialog(self):
        dlg = MobjectEditDialog(self, existing_names=self.mobjects)
        if dlg.exec():
            data = dlg.get_data()
            new_mob = MobjectData(
                id=str(uuid.uuid4()),
                name=data["name"],
                mob_type=data["type"],
                color=data["color"],
                content=data["content"],
                x=0.0, y=0.0
            )
            self.mobjects.append(new_mob)
            self.start_mobject_render(new_mob)
            self.refresh_ui()

    def edit_mobject_dialog(self, item):
        mob_id = item.data(Qt.ItemDataRole.UserRole)
        mob = next((m for m in self.mobjects if m.id == mob_id), None)
        if not mob: return

        dlg = MobjectEditDialog(self, mobject=mob)
        if dlg.exec():
            data = dlg.get_data()
            mob.name = data["name"]
            mob.mob_type = data["type"] 
            mob.color = data["color"]
            if mob.mob_type == "Text":
                mob.content = data["content"]
            
            self.start_mobject_render(mob)
            self.refresh_ui()

    def start_mobject_render(self, mob):
        self.status_label.setText(f"Rendering preview for {mob.name}...")
        thread = MobjectRenderThread(mob)
        thread.finished_signal.connect(self.on_render_success)
        thread.error_signal.connect(self.on_render_error)
        self.render_threads[mob.id] = thread
        thread.start()

    def on_render_success(self, mob_id, image_path):
        self.status_label.setText(f"Render complete for {mob_id[:4]}.")
        if mob_id in self.render_threads: del self.render_threads[mob_id]
        mob = next((m for m in self.mobjects if m.id == mob_id), None)
        if mob:
            mob.image_path = image_path
            self.canvas.add_image_item(mob, image_path, self.on_canvas_item_moved)
            self.canvas.set_item_visible(mob.id, mob.visible)
            self.refresh_ui()

    def on_render_error(self, error_msg):
        self.status_label.setText("Error rendering mobject.")
        QMessageBox.warning(self, "Render Error", f"Details:\n{error_msg}")

    def delete_mobject(self, mob_id):
        self.sync_data_order()
        mob = next((m for m in self.mobjects if m.id == mob_id), None)
        if mob:
            self.mobjects.remove(mob)
            self.canvas.remove_visual_item(mob_id)
            self.undo_stack.append(('mobject', mob))
            self.refresh_ui()

    def on_canvas_item_moved(self, mob_id):
        for i in range(self.mob_list_widget.count()):
            item = self.mob_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == mob_id:
                mob = next((m for m in self.mobjects if m.id == mob_id), None)
                if mob:
                    widget = self.create_mob_item_widget(mob)
                    self.mob_list_widget.setItemWidget(item, widget)
                break

    def add_animation_dialog(self):
        if not self.mobjects:
            QMessageBox.warning(self, "Warning", "No Mobjects available!")
            return
        
        dlg = AnimationEditDialog(self, self.mobjects)
        if dlg.exec():
            data = dlg.get_data()
            new_anim = AnimationData(
                id=str(uuid.uuid4()),
                anim_type=data["type"],
                target_id=data["target_id"],
                target_name_snapshot=data["target_name"],
                replacement_id=data["replacement_id"],
                replacement_name_snapshot=data["replacement_name"],
                duration=data["duration"]
            )
            self.animations.append(new_anim)
            self.refresh_ui()

    def edit_animation_dialog(self, item):
        anim_id = item.data(Qt.ItemDataRole.UserRole)
        anim = next((a for a in self.animations if a.id == anim_id), None)
        if not anim: return

        dlg = AnimationEditDialog(self, self.mobjects, animation=anim)
        if dlg.exec():
            data = dlg.get_data()
            anim.anim_type = data["type"]
            anim.target_id = data["target_id"]
            anim.target_name_snapshot = data["target_name"]
            anim.replacement_id = data["replacement_id"]
            anim.replacement_name_snapshot = data["replacement_name"]
            anim.duration = data["duration"]
            self.refresh_ui()

    def delete_animation(self, anim_id):
        self.sync_data_order()
        anim = next((a for a in self.animations if a.id == anim_id), None)
        if anim:
            self.animations.remove(anim)
            self.undo_stack.append(('animation', anim))
            self.refresh_ui()

    def undo_action(self):
        if not self.undo_stack: return
        action_type, item = self.undo_stack.pop()
        if action_type == 'mobject':
            self.mobjects.append(item)
            if item.image_path and os.path.exists(item.image_path):
                self.canvas.add_image_item(item, item.image_path, self.on_canvas_item_moved)
            else:
                self.start_mobject_render(item)
        elif action_type == 'animation':
            self.animations.append(item)
        self.refresh_ui()

    def refresh_ui(self):
        self.mob_list_widget.clear()
        for mob in self.mobjects:
            item = QListWidgetItem(self.mob_list_widget)
            item.setSizeHint(QSize(200, 50))
            item.setData(Qt.ItemDataRole.UserRole, mob.id) 
            widget = self.create_mob_item_widget(mob)
            self.mob_list_widget.setItemWidget(item, widget)

        self.anim_list_widget.clear()
        for anim in self.animations:
            item = QListWidgetItem(self.anim_list_widget)
            item.setSizeHint(QSize(200, 40))
            item.setData(Qt.ItemDataRole.UserRole, anim.id)
            widget = self.create_anim_item_widget(anim)
            self.anim_list_widget.setItemWidget(item, widget)

    def generate_script(self):
        self.sync_data_order()
        scene_name = self.input_scene_name.text().strip()
        if not scene_name:
            scene_name = "MyScene"
            
        script = "from manim import *\n"
        script += f'config.output_file = r"{scene_name}"\n\n'
        
        script += f"class {scene_name.replace(' ', '_')}(Scene):\n" 
        script += "    def construct(self):\n"
        var_map = {}
        for i, mob in enumerate(self.mobjects):
            var_name = f"m{i}"
            var_map[mob.id] = var_name
            if mob.mob_type == "Square":
                line = f"        {var_name} = Square(color='{mob.color}', fill_opacity=0.5)"
            elif mob.mob_type == "Circle":
                line = f"        {var_name} = Circle(color='{mob.color}', fill_opacity=0.5)"
            elif mob.mob_type == "Text":
                line = f"        {var_name} = Text('{mob.content}', color='{mob.color}')"
            else: line = f"        {var_name} = Square()"
            line += f".move_to([{mob.x}, {mob.y}, 0])\n"
            script += line
        script += "\n"
        for anim in self.animations:
            if anim.target_id in var_map:
                target = var_map[anim.target_id]
                if anim.anim_type == "Transform" and anim.replacement_id in var_map:
                    replacement = var_map[anim.replacement_id]
                    script += f"        self.play(Transform({target}, {replacement}), run_time={anim.duration})\n"
                else:
                    script += f"        self.play({anim.anim_type}({target}), run_time={anim.duration})\n"
        script += "        self.wait(1)\n"
        return script

    def render_video(self):
        script_content = self.generate_script()
        script_file = "final_scene.py"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        self.console = ConsoleDialog(self)
        self.console.show()
        self.console.append_output("Starting final render...", False)
        
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        
        raw_name = self.input_scene_name.text().strip()
        if not raw_name: raw_name = "MyScene"
        scene_class_name = raw_name.replace(' ', '_') 
        
        quality_flag = self.quality_combo.currentData()
        args = [quality_flag, script_file, scene_class_name]
        
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.render_finished)
        self.process.start("manim", args)

    def handle_output(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")
        self.console.append_output(text)

    def render_finished(self, exit_code, exit_status):
        if exit_code == 0:
            self.console.append_output("Final Render Success!", False)
            QTimer.singleShot(1000, self.console.close)
            
            raw_name = self.input_scene_name.text().strip()
            if not raw_name: raw_name = "MyScene"
            
            base = os.path.join(os.getcwd(), "media", "videos", "final_scene")
            found = False
            for root, dirs, files in os.walk(base):
                if f"{raw_name}.mp4" in files:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.join(root, f"{raw_name}.mp4")))
                    found = True
                    break
            
            if not found:
                self.console.append_output(f"Warning: Could not auto-locate video {raw_name}.mp4 in {base}", True)
                self.console.show()
        else:
            self.console.append_output(f"Render Failed (Code {exit_code})", True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Consolas")
    font.setPointSize(10)
    app.setFont(font)
    app.setStyle("Fusion")
    
    # 【关键修改】修复字体，保留箭头
    app.setStyleSheet("""
        QPushButton {
            background-color: #555;
            border: none;
            color: white;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #666;
        }
        QPushButton:pressed {
            background-color: #444;
        }
        QComboBox {
            background-color: #333;
            border: 1px solid #555;
            color: white;
            padding: 4px;
            border-radius: 3px;
        }
        /* 显式设置字体 */
        QComboBox QAbstractItemView {
            background-color: #333;
            color: white;
            selection-background-color: #555;
            font-family: "Consolas"; 
        }
        QLineEdit {
            background-color: #333;
            color: white;
            border: 1px solid #555;
            padding: 4px;
            border-radius: 3px;
        }
    """)
    
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)

    window = ManimEditor()
    window.show()
    sys.exit(app.exec())