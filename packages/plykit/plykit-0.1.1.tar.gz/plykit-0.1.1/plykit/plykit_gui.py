"""Simple PyQt5 GUI for ply tools with plugin system"""

import sys
import threading
import traceback
import importlib.util
import struct
from pathlib import Path
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFormLayout,
    QLineEdit,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QScrollArea,
    QDialog,
    QDialogButtonBox,
    QTreeView,
    QSplitter,
    QFileSystemModel,
)
from plykit_global import *
import plykit_global as global_


class CustomFileDialog(QDialog):
    """自定义文件对话框，支持路径输入和树形浏览"""

    def __init__(self, parent=None, initial_path="", name_filter=""):
        super().__init__(parent)
        self.selected_file = ""
        self.name_filter = name_filter
        # 如果没有提供初始路径，使用当前工作目录
        if not initial_path:
            initial_path = str(Path.cwd())
        self.setup_ui(initial_path)

    def setup_ui(self, initial_path):
        self.setWindowTitle("选择点云文件")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout()

        # 路径输入区域
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("路径:"))
        self.path_edit = QLineEdit()
        self.path_edit.setText(initial_path)
        path_layout.addWidget(self.path_edit)

        go_btn = QPushButton("转到")
        go_btn.clicked.connect(self.go_to_path)
        path_layout.addWidget(go_btn)

        layout.addLayout(path_layout)

        # 文件浏览器
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")
        self.file_model.setNameFilters(self.get_name_filters())
        self.file_model.setNameFilterDisables(False)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIndex(self.file_model.index(initial_path or "/"))
        self.tree_view.setColumnWidth(0, 250)
        self.tree_view.doubleClicked.connect(self.on_double_click)

        # 只显示文件名和大小列
        self.tree_view.setColumnHidden(1, False)  # 大小
        self.tree_view.setColumnHidden(2, True)  # 类型
        self.tree_view.setColumnHidden(3, True)  # 修改日期

        layout.addWidget(self.tree_view)

        # 文件名输入
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("文件名:"))
        self.file_edit = QLineEdit()
        file_layout.addWidget(self.file_edit)
        layout.addLayout(file_layout)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        # 设置初始路径
        if initial_path and Path(initial_path).exists():
            if Path(initial_path).is_file():
                self.path_edit.setText(str(Path(initial_path).parent))
                self.file_edit.setText(Path(initial_path).name)
                self.tree_view.setRootIndex(
                    self.file_model.index(str(Path(initial_path).parent))
                )
            else:
                self.path_edit.setText(initial_path)
                self.tree_view.setRootIndex(self.file_model.index(initial_path))

    def get_name_filters(self):
        """根据 name_filter 解析文件扩展名"""
        if not self.name_filter:
            return []

        # 解析过滤器，如 "PLY Files (*.ply);;TXT Files (*.txt);;COLMAP Points3D (*.bin)"
        filters = []
        for part in self.name_filter.split(";;"):
            if "(*." in part:
                ext_part = part.split("(*.")[1].rstrip(")")
                exts = [f"*.{ext.strip()}" for ext in ext_part.split()]
                filters.extend(exts)
        return filters if filters else ["*"]

    def go_to_path(self):
        """转到输入的路径"""
        path = self.path_edit.text().strip()
        if path and Path(path).exists():
            if Path(path).is_file():
                self.path_edit.setText(str(Path(path).parent))
                self.file_edit.setText(Path(path).name)
                self.tree_view.setRootIndex(
                    self.file_model.index(str(Path(path).parent))
                )
            else:
                self.tree_view.setRootIndex(self.file_model.index(path))
        else:
            QMessageBox.warning(self, "警告", f"路径不存在: {path}")

    def on_double_click(self, index):
        """双击文件时填充文件名"""
        file_path = self.file_model.filePath(index)
        if Path(file_path).is_file():
            self.path_edit.setText(str(Path(file_path).parent))
            self.file_edit.setText(Path(file_path).name)

    def accept(self):
        """确定按钮处理"""
        path = self.path_edit.text().strip()
        filename = self.file_edit.text().strip()

        if not path or not filename:
            QMessageBox.warning(self, "警告", "请选择文件")
            return

        full_path = Path(path) / filename
        if not full_path.exists():
            QMessageBox.warning(self, "警告", f"文件不存在: {full_path}")
            return

        self.selected_file = str(full_path)
        super().accept()


# =========================
# 读取 COLMAP points3D.bin
# =========================
def read_points3D_binary(path):
    points3D = {}
    with open(path, "rb") as f:
        # 读取点数量（int64）
        num_points = struct.unpack("Q", f.read(8))[0]
        for _ in range(num_points):
            # 读取 point_id (int64)
            point_id = struct.unpack("Q", f.read(8))[0]
            # 读取 xyz (3 * float64)
            xyz = struct.unpack("ddd", f.read(24))
            # 读取 rgb (3 * uint8)
            rgb = struct.unpack("BBB", f.read(3))
            # 读取 error (float64)
            error = struct.unpack("d", f.read(8))[0]
            # 读取 track length (uint64)
            track_length = struct.unpack("Q", f.read(8))[0]
            # 跳过 track (每个观测 2 * int32)
            f.read(track_length * 2 * 4)
            # 保存
            points3D[point_id] = {"xyz": xyz, "rgb": rgb}
    return points3D


def load_plugins_from_dir(folder: Path):
    plugins = []
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
        CUSTOM_LOGGER.info(f"插件目录不存在，已创建: {folder}")

    for py in folder.glob("*_plugin.py"):
        try:
            CUSTOM_LOGGER.info(f"尝试加载插件: {py}")
            spec = importlib.util.spec_from_file_location(py.stem, str(py))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "get_plugin"):
                plugin = mod.get_plugin()
                plugins.append((py.stem, plugin))
                CUSTOM_LOGGER.info(f"✅ 成功加载插件: {plugin.name}")
            else:
                CUSTOM_LOGGER.info(f"❌ 插件 {py} 没有 get_plugin 函数")
        except Exception as e:
            CUSTOM_LOGGER.info(f"❌ 加载插件 {py} 失败: {e}")
            traceback.print_exc()
    return plugins


class PluginWorker(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, plugin, input_pcd, params):
        super().__init__()
        self.plugin = plugin
        self.input_pcd = input_pcd
        self.params = params

    def run(self):
        """在工作线程中执行插件"""
        result_container = {
            "logs": [],
            "error": None,
            "output": None,
            "plugin_name": self.plugin.name,
        }

        try:
            import open3d as o3d
            import numpy as np

            # 在线程内创建点云的深拷贝
            points_copy = np.asarray(self.input_pcd.points).copy()
            pcd_copy = o3d.geometry.PointCloud()
            pcd_copy.points = o3d.utility.Vector3dVector(points_copy)

            if self.input_pcd.has_colors():
                colors_copy = np.asarray(self.input_pcd.colors).copy()
                pcd_copy.colors = o3d.utility.Vector3dVector(colors_copy)

            # 定义线程安全的日志函数
            def thread_logger(msg):
                result_container["logs"].append(str(msg))
                CUSTOM_LOGGER.info(f"[插件] {msg}")

            # 执行插件
            thread_logger("🔄 插件执行中...")
            output = self.plugin.run(pcd_copy, self.params, thread_logger)
            result_container["output"] = output
            thread_logger("✅ 插件执行完成")

        except Exception as e:
            error_msg = f"❌ 插件执行异常: {str(e)}"
            result_container["error"] = error_msg
            result_container["logs"].append(error_msg)
            # 打印详细错误信息到控制台
            CUSTOM_LOGGER.error(f"插件执行错误: {e}")
            traceback.print_exc()

        # 发射完成信号
        self.finished.emit(result_container)


class ParameterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.param_widgets = {}
        self.layout = QFormLayout()
        self.setLayout(self.layout)

    def setup_parameters(self, default_params):
        """根据默认参数创建对应的控件"""
        # 清空现有控件
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)
        self.param_widgets.clear()

        for param_name, default_value in default_params.items():
            label = QLabel(param_name)

            if isinstance(default_value, bool):
                widget = QCheckBox()
                widget.setChecked(default_value)
                self.param_widgets[param_name] = widget

            elif isinstance(default_value, int):
                widget = QSpinBox()
                widget.setRange(-1000000, 1000000)
                widget.setValue(default_value)
                self.param_widgets[param_name] = widget

            elif isinstance(default_value, float):
                widget = QDoubleSpinBox()
                widget.setRange(-1000000.0, 1000000.0)
                widget.setDecimals(6)
                widget.setSingleStep(0.1)
                widget.setValue(default_value)
                self.param_widgets[param_name] = widget

            elif isinstance(default_value, str):
                widget = QLineEdit(default_value)
                self.param_widgets[param_name] = widget

            elif isinstance(default_value, list) and all(
                isinstance(x, str) for x in default_value
            ):
                widget = QComboBox()
                for item in default_value:
                    widget.addItem(item)
                self.param_widgets[param_name] = widget

            else:
                # 对于其他类型，使用文本输入
                widget = QLineEdit(str(default_value))
                self.param_widgets[param_name] = widget

            self.layout.addRow(label, widget)

    def get_parameters(self):
        """从控件获取参数值"""
        params = {}
        for param_name, widget in self.param_widgets.items():
            if isinstance(widget, QCheckBox):
                params[param_name] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                params[param_name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                params[param_name] = widget.value()
            elif isinstance(widget, QLineEdit):
                # 尝试自动转换类型
                value = widget.text().strip()
                if value.lower() == "true":
                    params[param_name] = True
                elif value.lower() == "false":
                    params[param_name] = False
                else:
                    try:
                        # 尝试转换为数字
                        if "." in value:
                            params[param_name] = float(value)
                        else:
                            params[param_name] = int(value)
                    except ValueError:
                        # 保持为字符串
                        params[param_name] = value
            elif isinstance(widget, QComboBox):
                params[param_name] = widget.currentText()

        return params


class EnhancedVisualizer:
    """增强的可视化类，显示坐标系和点云信息"""

    @staticmethod
    def create_coordinate_frame(size=1.0, origin=[0, 0, 0]):
        """创建带文字标签的坐标系"""
        import open3d as o3d
        import numpy as np

        # 创建坐标轴线段
        points = [
            origin,  # 原点
            [origin[0] + size, origin[1], origin[2]],  # X轴
            [origin[0], origin[1] + size, origin[2]],  # Y轴
            [origin[0], origin[1], origin[2] + size],  # Z轴
        ]

        lines = [
            [0, 1],  # X轴
            [0, 2],  # Y轴
            [0, 3],  # Z轴
        ]

        colors = [
            [1, 0, 0],  # X轴 - 红色
            [0, 1, 0],  # Y轴 - 绿色
            [0, 0, 1],  # Z轴 - 蓝色
        ]

        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(points)
        line_set.lines = o3d.utility.Vector2iVector(lines)
        line_set.colors = o3d.utility.Vector3dVector(colors)

        return line_set

    @staticmethod
    def create_coordinate_labels(size=1.0, origin=[0, 0, 0]):
        """创建坐标轴文字标签"""
        import open3d as o3d
        import numpy as np

        geometries = []

        try:
            # 尝试使用 Open3D 的文本功能（0.16.0+ 版本）
            # X轴标签 - 红色文字
            x_label = o3d.t.geometry.TriangleMesh.create_text(f"X", depth=0.01)
            x_label.paint_uniform_color([1, 0, 0])  # 红色
            x_label = x_label.translate([origin[0] + size + 0.1, origin[1], origin[2]])
            geometries.append(x_label.to_legacy())

            # Y轴标签 - 绿色文字
            y_label = o3d.t.geometry.TriangleMesh.create_text(f"Y", depth=0.01)
            y_label.paint_uniform_color([0, 1, 0])  # 绿色
            y_label = y_label.translate([origin[0], origin[1] + size + 0.1, origin[2]])
            geometries.append(y_label.to_legacy())

            # Z轴标签 - 蓝色文字
            z_label = o3d.t.geometry.TriangleMesh.create_text(f"Z", depth=0.01)
            z_label.paint_uniform_color([0, 0, 1])  # 蓝色
            z_label = z_label.translate([origin[0], origin[1], origin[2] + size + 0.1])
            geometries.append(z_label.to_legacy())

        except (AttributeError, ImportError):
            # 如果不支持文本功能，使用球体作为标记
            CUSTOM_LOGGER.info("⚠️ Open3D 文本功能不可用，使用球体标记坐标轴")

            # X轴标记 - 红色球体
            x_sphere = o3d.geometry.TriangleMesh.create_sphere(radius=size * 0.05)
            x_sphere.paint_uniform_color([1, 0, 0])
            x_sphere.translate([origin[0] + size + 0.1, origin[1], origin[2]])
            geometries.append(x_sphere)

            # Y轴标记 - 绿色球体
            y_sphere = o3d.geometry.TriangleMesh.create_sphere(radius=size * 0.05)
            y_sphere.paint_uniform_color([0, 1, 0])
            y_sphere.translate([origin[0], origin[1] + size + 0.1, origin[2]])
            geometries.append(y_sphere)

            # Z轴标记 - 蓝色球体
            z_sphere = o3d.geometry.TriangleMesh.create_sphere(radius=size * 0.05)
            z_sphere.paint_uniform_color([0, 0, 1])
            z_sphere.translate([origin[0], origin[1], origin[2] + size + 0.1])
            geometries.append(z_sphere)

        return geometries

    @staticmethod
    def create_info_board(pcd, position=[0, 0, 0]):
        """创建信息显示板（3D文字）"""
        import open3d as o3d
        import numpy as np

        geometries = []

        try:
            # 获取点云信息
            points = np.asarray(pcd.points)
            num_points = len(points)
            min_pt = np.min(points, axis=0)
            max_pt = np.max(points, axis=0)
            bbox_size = max_pt - min_pt

            # 创建信息文本
            info_lines = [
                f"Points: {num_points:,}",
                f"Size: {bbox_size[0]:.2f}x{bbox_size[1]:.2f}x{bbox_size[2]:.2f}",
                "Colors: Red=X, Green=Y, Blue=Z",
            ]

            # 在3D空间中创建文本
            for i, line in enumerate(info_lines):
                text_mesh = o3d.t.geometry.TriangleMesh.create_text(line, depth=0.005)
                text_mesh.paint_uniform_color([1, 1, 1])  # 白色文字
                text_mesh = text_mesh.translate(
                    [position[0], position[1] - i * 0.2, position[2]]
                )
                geometries.append(text_mesh.to_legacy())

        except (AttributeError, ImportError):
            CUSTOM_LOGGER.info("⚠️ 信息板创建失败，使用控制台输出")

        return geometries

    @staticmethod
    def create_bounding_box(pcd):
        """创建彩色边界框"""
        import open3d as o3d

        bbox = pcd.get_axis_aligned_bounding_box()
        bbox.color = [1, 1, 0]  # 黄色边界框
        return bbox

    @staticmethod
    def get_point_cloud_info(pcd):
        """获取点云详细信息"""
        import numpy as np

        points = np.asarray(pcd.points)
        num_points = len(points)

        if num_points == 0:
            return "点云为空"

        # 计算点云范围
        min_pt = np.min(points, axis=0)
        max_pt = np.max(points, axis=0)
        bbox_size = max_pt - min_pt
        center = (min_pt + max_pt) / 2

        info = "=== 点云信息 ===\n"
        info += f"点数: {num_points:,}\n"
        info += f"尺寸: {bbox_size[0]:.3f} x {bbox_size[1]:.3f} x {bbox_size[2]:.3f}\n"
        info += f"中心: ({center[0]:.3f}, {center[1]:.3f}, {center[2]:.3f})\n"
        info += f"X范围: [{min_pt[0]:.3f}, {max_pt[0]:.3f}]\n"
        info += f"Y范围: [{min_pt[1]:.3f}, {max_pt[1]:.3f}]\n"
        info += f"Z范围: [{min_pt[2]:.3f}, {max_pt[2]:.3f}]\n"
        info += "=== 坐标轴颜色 ===\n"
        info += "🔴 红色 = X轴\n"
        info += "🟢 绿色 = Y轴\n"
        info += "🔵 蓝色 = Z轴"

        return info

    @staticmethod
    def visualize_with_info(pcd, window_name="点云可视化"):
        """带坐标系和信息的可视化（修复暗色不可见问题）"""
        import open3d as o3d
        import numpy as np

        try:
            points = np.asarray(pcd.points)
            if len(points) == 0:
                CUSTOM_LOGGER.info("点云为空")
                return "点云为空"

            # === 关键修复：确保点云可见 ===
            # 如果没有颜色，赋予统一中灰色（在白色背景下清晰）
            if not pcd.has_colors():
                n = len(points)
                if n > 0:
                    gray_color = np.full((n, 3), 0.45)  # 中灰色，避免纯黑/纯白
                    pcd.colors = o3d.utility.Vector3dVector(gray_color)

            # 计算点云边界和中心
            min_pt = np.min(points, axis=0)
            max_pt = np.max(points, axis=0)
            center = (min_pt + max_pt) / 2
            bbox_size = max_pt - min_pt

            # 坐标系大小（基于点云尺寸）
            coord_size = max(bbox_size) * 0.3

            # 坐标系放在点云底部中心
            coord_origin = [center[0], center[1], min_pt[2]]
            coordinate_frame = EnhancedVisualizer.create_coordinate_frame(
                coord_size, coord_origin
            )
            coordinate_labels = EnhancedVisualizer.create_coordinate_labels(
                coord_size, coord_origin
            )

            # 信息板位置（右上角）
            info_position = [max_pt[0] + 0.1, max_pt[1], center[2]]
            info_board = EnhancedVisualizer.create_info_board(pcd, info_position)

            # 边界框（黄色）
            bbox = EnhancedVisualizer.create_bounding_box(pcd)

            # 所有几何体
            geometries = [pcd, coordinate_frame, bbox]
            geometries.extend(coordinate_labels)
            geometries.extend(info_board)

            # 获取点云信息文本
            info_text = EnhancedVisualizer.get_point_cloud_info(pcd)

            # 创建可视化窗口
            vis = o3d.visualization.Visualizer()
            vis.create_window(
                window_name=f"{window_name} - 点数: {len(points):,}",
                width=1400,
                height=900,
            )

            for geometry in geometries:
                vis.add_geometry(geometry)

            # === 关键修复：使用白色背景 ===
            render_option = vis.get_render_option()
            render_option.background_color = [1.0, 1.0, 1.0]  # 白色背景，点云清晰可见
            render_option.point_size = 2.0
            render_option.line_width = 3.0
            render_option.light_on = True  # 启用光照

            # 设置视角
            view_control = vis.get_view_control()
            if bbox_size[2] > bbox_size[0] and bbox_size[2] > bbox_size[1]:
                view_control.set_front([0, -1, 0])
                view_control.set_up([0, 0, 1])
            else:
                view_control.set_front([0, -1, -0.3])
                view_control.set_up([0, -0.3, 1])
            view_control.set_zoom(0.7)

            # 日志输出
            CUSTOM_LOGGER.info("=" * 60)
            CUSTOM_LOGGER.info("点云可视化信息:")
            CUSTOM_LOGGER.info(info_text)
            CUSTOM_LOGGER.info("=" * 60)

            vis.run()
            vis.destroy_window()

            return info_text

        except Exception as e:
            CUSTOM_LOGGER.error(f"增强可视化失败: {e}")
            traceback.print_exc()

            # 回退到基础可视化（同样修复背景和颜色）
            try:
                # 再次确保颜色
                if not pcd.has_colors():
                    pts = np.asarray(pcd.points)
                    if len(pts) > 0:
                        pcd.colors = o3d.utility.Vector3dVector(
                            np.full((len(pts), 3), 0.45)
                        )

                info_text = EnhancedVisualizer.get_point_cloud_info(pcd)
                CUSTOM_LOGGER.info("使用基础可视化模式（已修复颜色）")
                CUSTOM_LOGGER.info(info_text)

                o3d.visualization.draw_geometries(
                    [pcd],
                    window_name=f"{window_name} (基础模式)",
                    width=1200,
                    height=800,
                    left=50,
                    top=50,
                )
                return info_text

            except Exception as e2:
                CUSTOM_LOGGER.error(f"基础可视化也失败: {e2}")
                return f"可视化失败: {e}"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PLY Tools - 专业点云处理工具")
        self.resize(1000, 700)

        self.selected_file = None
        self.loaded_pcd = None
        self.plugins = load_plugins_from_dir(PLUGIN_FOLDER)
        self.current_worker = None
        self.original_pcd = None  # 保存原始点云用于重加载

        self._build_ui()
        self._setup_connections()

    def _build_ui(self):
        w = QWidget()
        self.setCentralWidget(w)

        # 左侧控件
        open_btn = QPushButton("打开点云文件 (PLY/TXT/COLMAP)")
        open_btn.clicked.connect(self.open_file)

        reload_btn = QPushButton("重新加载原始点云")
        reload_btn.clicked.connect(self.reload_original)

        export_btn = QPushButton("导出合成PLY")
        export_btn.clicked.connect(self.export_combined_ply)
        self.export_btn = export_btn

        self.file_label = QLabel("未选择文件")
        self.info_label = QLabel("点云信息：无")
        self.info_label.setWordWrap(True)

        self.plugin_list = QListWidget()
        self.plugin_list.setSelectionMode(QListWidget.SingleSelection)
        for name, plugin in self.plugins:
            self.plugin_list.addItem(f"{plugin.name} | {plugin.description}")

        # 参数控件区域
        param_scroll = QScrollArea()
        param_scroll.setWidgetResizable(True)
        self.param_widget = ParameterWidget()
        param_scroll.setWidget(self.param_widget)

        run_btn = QPushButton("运行插件")
        run_btn.clicked.connect(self.run_plugin)
        self.run_btn = run_btn

        vis_btn = QPushButton("点云弹窗可视化 (Open3D)")
        vis_btn.clicked.connect(self.visualize_pcd)

        left_layout = QVBoxLayout()
        left_layout.addWidget(open_btn)
        left_layout.addWidget(reload_btn)
        left_layout.addWidget(export_btn)
        left_layout.addWidget(self.file_label)
        left_layout.addWidget(self.info_label)
        left_layout.addWidget(QLabel("插件列表:"))
        left_layout.addWidget(self.plugin_list)
        left_layout.addWidget(QLabel("插件参数:"))
        left_layout.addWidget(param_scroll)
        left_layout.addWidget(run_btn)
        left_layout.addWidget(vis_btn)

        # 右侧日志
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("日志输出:"))
        right_layout.addWidget(self.log)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 2)

        w.setLayout(main_layout)

    def export_combined_ply(self):
        try:
            from plugins.export_combined_ply import export_combined_ply

            output_path = export_combined_ply(global_.TMP_PLY, global_.LOADED_PLY_PATH)
            self.append_log(f"✅ 已导出合成PLY: {output_path}")
            QMessageBox.information(self, "导出成功", f"已导出合成PLY:\n{output_path}")
        except Exception as e:
            self.append_log(f"❌ 导出合成PLY失败: {e}")
            QMessageBox.critical(self, "导出失败", f"导出失败:\n{e}")

    def _setup_connections(self):
        self.plugin_list.currentRowChanged.connect(self.on_plugin_selected)

    def append_log(self, text: str):
        """添加日志到界面，同时使用自定义日志库"""
        self.log.append(text)
        # 自动滚动到底部
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

        # 移除emoji等特殊字符，只保留纯文本
        clean_text = "".join(char for char in text if char.isprintable())
        CUSTOM_LOGGER.info(clean_text)

    def open_file(self):
        # 使用自定义文件对话框，支持路径输入和树形浏览
        dialog = CustomFileDialog(
            self,
            name_filter="PLY Files (*.ply);;TXT Files (*.txt);;COLMAP Points3D (*.bin);;All files (*)",
        )

        if dialog.exec_():
            fn = dialog.selected_file
            if fn:
                self.selected_file = fn
                self.file_label.setText(f"文件: {Path(fn).name}")
                CUSTOM_LOGGER.info(f"✅ 成功加载点云：{fn}")
                self.append_log(f"📁 已选择文件: {fn}")
                self.load_and_show_info(fn)
                global_.LOADED_PLY_PATH = fn

    def reload_original(self):
        """重新加载原始点云文件"""
        if self.selected_file:
            self.append_log("🔄 重新加载原始点云...")
            CUSTOM_LOGGER.info(f"重新加载原始点云：{self.selected_file}")
            self.load_and_show_info(self.selected_file)
        else:
            QMessageBox.warning(self, "警告", "请先打开一个点云文件")

    def load_and_show_info(self, fn):
        try:
            import open3d as o3d

            self.append_log(f"🔄 正在加载点云文件...")

            # 检查文件扩展名
            supported_extensions = [".ply", ".txt", ".bin"]
            file_ext = Path(fn).suffix.lower()

            if file_ext not in supported_extensions:
                raise ValueError(
                    f"不支持的文件格式: {file_ext}。支持的格式: {', '.join(supported_extensions)}"
                )

            if fn.endswith(".ply"):
                pcd = o3d.io.read_point_cloud(fn)
            elif fn.endswith(".bin"):
                # 读取 COLMAP points3D.bin 文件
                points3D = read_points3D_binary(fn)
                import numpy as np

                points = np.array([p["xyz"] for p in points3D.values()])
                colors = np.array([p["rgb"] for p in points3D.values()]) / 255.0

                pcd = o3d.geometry.PointCloud()
                pcd.points = o3d.utility.Vector3dVector(points)
                pcd.colors = o3d.utility.Vector3dVector(colors)
            else:  # .txt files
                import numpy as np

                data = np.loadtxt(fn)
                pcd = o3d.geometry.PointCloud()
                if data.shape[1] >= 3:
                    pcd.points = o3d.utility.Vector3dVector(data[:, :3])
                if data.shape[1] >= 6:
                    pcd.colors = o3d.utility.Vector3dVector(data[:, 3:6] / 255.0)

            # 保存原始点云和当前点云
            self.original_pcd = pcd
            self.loaded_pcd = pcd

            # 自动保存到临时文件
            o3d.io.write_point_cloud(str(TMP_PLY), pcd)
            self.append_log(f"💾 已自动保存点云到: {TMP_PLY}")

            info = self.get_pcd_info(pcd)
            self.info_label.setText(f"点云信息：\n{info}")
            self.append_log(f"✅ 点云加载成功")
            self.append_log(f"📊 {info.replace(chr(10), ', ')}")

        except Exception as e:
            error_msg = f"❌ 点云加载失败: {e}"
            self.info_label.setText(error_msg)
            self.append_log(error_msg)
            CUSTOM_LOGGER.error(f"点云加载失败：{e}")
            traceback.print_exc()

    def get_pcd_info(self, pcd):
        try:
            import numpy as np

            pts = np.asarray(pcd.points)
            count = len(pts)
            if count == 0:
                return "无点"

            min_xyz = np.min(pts, axis=0)
            max_xyz = np.max(pts, axis=0)
            center = np.mean(pts, axis=0)

            info = f"点数: {count}\n范围: x[{min_xyz[0]:.3f},{max_xyz[0]:.3f}] y[{min_xyz[1]:.3f},{max_xyz[1]:.3f}] z[{min_xyz[2]:.3f},{max_xyz[2]:.3f}]\n中心: ({center[0]:.3f},{center[1]:.3f},{center[2]:.3f})"
            return info
        except Exception as e:
            return f"统计失败: {e}"

    def run_plugin(self):
        idx = self.plugin_list.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "未选择插件", "请先选择一个插件")
            return

        if self.loaded_pcd is None:
            QMessageBox.warning(self, "未加载点云", "请先加载点云文件")
            return

        plugin_name, plugin = self.plugins[idx]

        # 从界面控件获取参数
        try:
            params = self.param_widget.get_parameters()
            self.append_log(f"📋 使用参数: {params}")
            CUSTOM_LOGGER.info(f"执行插件 {plugin_name}，参数: {params}")
        except Exception as e:
            QMessageBox.critical(self, "参数错误", f"参数获取失败: {e}")
            return

        self.run_btn.setEnabled(False)
        self.append_log(f"🚀 开始执行插件: {plugin.name}")

        # 创建 worker
        self.current_worker = PluginWorker(plugin, self.loaded_pcd, params)
        self.current_worker.finished.connect(self._on_plugin_finished)

        # 启动工作线程
        thread = threading.Thread(target=self.current_worker.run, daemon=True)
        thread.start()
        self.append_log("🔄 插件线程已启动...")

    def _on_plugin_finished(self, result_container):
        """在主线程中处理插件完成结果"""
        plugin_name = result_container["plugin_name"]
        logs = result_container["logs"]
        error = result_container["error"]
        output = result_container["output"]

        # 输出所有日志
        for msg in logs:
            self.append_log(msg)

        if error:
            self.append_log(f"❌ 插件 '{plugin_name}' 运行失败")
            QMessageBox.critical(self, "插件错误", f"执行失败:\n{error}")
            CUSTOM_LOGGER.error(f"插件 {plugin_name} 运行失败: {error}")
        else:
            self.append_log(f"✅ 插件 '{plugin_name}' 运行成功")
            CUSTOM_LOGGER.info(f"插件 {plugin_name} 运行成功")

            # 处理插件输出
            if isinstance(output, dict) and "updated_pcd" in output:
                self.loaded_pcd = output["updated_pcd"]
                info = self.get_pcd_info(self.loaded_pcd)
                self.info_label.setText(f"点云信息：\n{info}")

                # 保存结果
                try:
                    import open3d as o3d

                    o3d.io.write_point_cloud(str(TMP_PLY), self.loaded_pcd)
                    self.append_log(f"💾 已保存最新点云: {TMP_PLY}")
                except Exception as e:
                    self.append_log(f"⚠️ 保存PLY失败: {e}")
            else:
                self.append_log("ℹ️ 插件未返回更新后的点云")

        # 重新启用按钮
        self.run_btn.setEnabled(True)
        self.append_log("--- 插件执行结束 ---")

        # 清理 worker
        self.current_worker = None

    def visualize_pcd(self):
        try:
            import open3d as o3d

            CUSTOM_LOGGER.info("启动点云可视化")

            self.append_log("👀 启动点云可视化...")

            if TMP_PLY.exists():
                pcd = o3d.io.read_point_cloud(str(TMP_PLY))
                info_text = EnhancedVisualizer.visualize_with_info(
                    pcd, "点云可视化 - 最新结果"
                )
                self.append_log("✅ 点云可视化窗口已打开")
                if info_text:
                    self.append_log(f"📊 点云信息:\n{info_text}")
            elif self.loaded_pcd is not None:
                info_text = EnhancedVisualizer.visualize_with_info(
                    self.loaded_pcd, "点云可视化 - 当前加载"
                )
                self.append_log("✅ 点云可视化窗口已打开")
                if info_text:
                    self.append_log(f"📊 点云信息:\n{info_text}")
            else:
                self.append_log("❌ 未加载点云或点云为空")

        except Exception as e:
            error_msg = f"❌ 可视化失败: {e}"
            self.append_log(error_msg)
            CUSTOM_LOGGER.error(f"点云可视化失败: {e}")
            traceback.print_exc()

    def on_plugin_selected(self, idx):
        if idx < 0 or idx >= len(self.plugins):
            return

        _, plugin = self.plugins[idx]
        # 设置参数控件
        self.param_widget.setup_parameters(plugin.default_params)
        self.append_log(f"🔧 已切换到插件: {plugin.name}")
        CUSTOM_LOGGER.info(f"切换到插件: {plugin.name}")


def main():
    app = QApplication(sys.argv)

    try:
        import open3d as o3d
        import numpy as np
    except ImportError as e:
        CUSTOM_LOGGER.info(f"❌ 缺少必要依赖: {e}")
        CUSTOM_LOGGER.info("请安装: pip install open3d numpy PyQt5")
        return 1

    mw = MainWindow()
    mw.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
