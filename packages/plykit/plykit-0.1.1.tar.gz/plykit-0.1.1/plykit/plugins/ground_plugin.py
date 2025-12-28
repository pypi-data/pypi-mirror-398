# ground_plugin.py
from plugin_base import BasePlugin
import open3d as o3d
import numpy as np


class GroundPlugin(BasePlugin):
    name = "点云置底"
    description = "沿 Z 轴平移，使最低点 Z=0"
    default_params = {"平移基准": 0.0, "保持颜色": True}

    def run(self, input_obj, params: dict, logger):
        logger("开始执行点云置底操作...")

        # 获取参数
        base_z = params.get("平移基准", 0.0)
        keep_colors = params.get("保持颜色", True)

        logger(f"平移基准 Z = {base_z}")
        logger(f"保持颜色 = {keep_colors}")

        if isinstance(input_obj, str):
            logger(f"从文件加载点云: {input_obj}")
            pcd = o3d.io.read_point_cloud(input_obj)
        else:
            logger("使用内存中的点云对象")
            pcd = input_obj

        logger("计算点云统计信息...")
        points = np.asarray(pcd.points)
        logger(f"点云点数: {len(points)}")

        min_z = np.min(points[:, 2])
        logger(f"最低点 Z 坐标: {min_z:.6f}")

        logger("执行坐标变换...")
        translated_points = points.copy()
        translated_points[:, 2] -= min_z - base_z

        logger("创建新的点云对象...")
        grounded_pcd = o3d.geometry.PointCloud()
        grounded_pcd.points = o3d.utility.Vector3dVector(translated_points)

        if pcd.has_colors() and keep_colors:
            grounded_pcd.colors = pcd.colors
            logger("颜色信息已复制")
        else:
            logger("点云无颜色信息或未启用颜色保持")

        logger(f"✅ 点云已置底，平移量: {min_z - base_z:.6f}")
        return {"updated_pcd": grounded_pcd}


def get_plugin():
    return GroundPlugin()
