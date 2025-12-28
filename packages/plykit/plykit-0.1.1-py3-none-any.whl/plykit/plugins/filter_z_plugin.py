from plugin_base import BasePlugin
import open3d as o3d
import numpy as np


class FilterZPlugin(BasePlugin):
    name = "Z轴高度过滤"
    description = "保留 Z <= max_height 的点"
    default_params = {"z_max": 3.75}

    def run(self, input_obj, params: dict, logger):
        if isinstance(input_obj, str):
            pcd = o3d.io.read_point_cloud(input_obj)
        else:
            pcd = input_obj

        z_max = float(params.get("z_max", 3.75))
        points = np.asarray(pcd.points)
        mask = points[:, 2] <= z_max
        filtered_points = points[mask]

        filtered_pcd = o3d.geometry.PointCloud()
        filtered_pcd.points = o3d.utility.Vector3dVector(filtered_points)
        if pcd.has_colors():
            colors = np.asarray(pcd.colors)
            filtered_pcd.colors = o3d.utility.Vector3dVector(colors[mask])

        logger(f"✅ 已过滤 Z > {z_max} 的点，剩余 {len(filtered_points)} 个点")
        return {"updated_pcd": filtered_pcd}


def get_plugin():
    return FilterZPlugin()
