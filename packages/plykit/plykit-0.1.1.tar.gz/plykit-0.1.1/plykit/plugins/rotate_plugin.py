from plugin_base import BasePlugin
import open3d as o3d
import numpy as np


class RotatePlugin(BasePlugin):
    name = "点云旋转"
    description = "绕 X/Y/Z 轴旋转点云（角度：正值逆时针）"
    default_params = {
        "axis": "x",  # "x", "y", or "z"
        "degrees": -90,
    }

    def run(self, input_obj, params: dict, logger):
        if isinstance(input_obj, str):
            pcd = o3d.io.read_point_cloud(input_obj)
        else:
            pcd = input_obj

        axis = params.get("axis", "x").lower()
        degrees = float(params.get("degrees", -90))

        points = np.asarray(pcd.points)
        theta = np.radians(degrees)
        cos_t, sin_t = np.cos(theta), np.sin(theta)

        if axis == "x":
            R = np.array([[1, 0, 0], [0, cos_t, -sin_t], [0, sin_t, cos_t]])
        elif axis == "y":
            R = np.array([[cos_t, 0, sin_t], [0, 1, 0], [-sin_t, 0, cos_t]])
        elif axis == "z":
            R = np.array([[cos_t, -sin_t, 0], [sin_t, cos_t, 0], [0, 0, 1]])
        else:
            raise ValueError(f"不支持的旋转轴: {axis}")

        rotated_points = points @ R.T
        rotated_pcd = o3d.geometry.PointCloud()
        rotated_pcd.points = o3d.utility.Vector3dVector(rotated_points)
        if pcd.has_colors():
            rotated_pcd.colors = pcd.colors

        logger(f"✅ 绕 {axis.upper()} 轴旋转 {degrees} 度完成")
        return {"updated_pcd": rotated_pcd}


def get_plugin():
    return RotatePlugin()
