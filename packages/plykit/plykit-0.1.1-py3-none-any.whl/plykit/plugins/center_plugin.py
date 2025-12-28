# center_plugin.py
from plugin_base import BasePlugin
import open3d as o3d
import numpy as np


class CenterPlugin(BasePlugin):
    name = "点云居中"
    description = "将点云几何中心移动到坐标原点 (x, y, z 均为 -a~+a)"
    default_params = {"保持颜色": True}

    def run(self, input_obj, params: dict, logger):
        logger("开始执行点云居中操作...")

        keep_colors = params.get("保持颜色", True)

        if isinstance(input_obj, str):
            logger(f"从文件加载点云: {input_obj}")
            pcd = o3d.io.read_point_cloud(input_obj)
        else:
            logger("使用内存中的点云对象")
            pcd = input_obj

        logger("计算点云统计信息...")
        points = np.asarray(pcd.points)
        logger(f"点云点数: {len(points)}")

        min_xyz = np.min(points, axis=0)
        max_xyz = np.max(points, axis=0)
        center = (min_xyz + max_xyz) / 2.0
        logger(f"点云包围盒最小值: {min_xyz}")
        logger(f"点云包围盒最大值: {max_xyz}")
        logger(f"几何中心: {center}")

        logger("执行坐标变换...")
        centered_points = points - center

        logger("创建新的点云对象...")
        centered_pcd = o3d.geometry.PointCloud()
        centered_pcd.points = o3d.utility.Vector3dVector(centered_points)

        if pcd.has_colors() and keep_colors:
            centered_pcd.colors = pcd.colors
            logger("颜色信息已复制")
        else:
            logger("点云无颜色信息或未启用颜色保持")

        logger("✅ 点云已居中")
        return {"updated_pcd": centered_pcd}


def get_plugin():
    return CenterPlugin()
