from plugin_base import BasePlugin
import open3d as o3d
import numpy as np


class ScalePlugin(BasePlugin):
    name = "点云缩放"
    description = "以几何中心为基准缩放点云"
    default_params = {"scale": 1.0, "update_scale_fields": True}

    def run(self, input_obj, params: dict, logger):
        import numpy as np
        from plykit_global import LOADED_PLY_PATH

        scale = float(params.get("scale", 1.0))
        update_scale_fields = params.get("update_scale_fields", True)

        # 1. 点云缩放
        if isinstance(input_obj, str):
            pcd = o3d.io.read_point_cloud(input_obj)
        else:
            pcd = input_obj
        points = np.asarray(pcd.points)
        center = np.mean(points, axis=0)
        scaled_points = (points - center) * scale + center

        scaled_pcd = o3d.geometry.PointCloud()
        scaled_pcd.points = o3d.utility.Vector3dVector(scaled_points)
        if pcd.has_colors():
            scaled_pcd.colors = pcd.colors

        logger(f"✅ 点云缩放完成，比例: {scale}")

        # 2. scale_0/1/2字段同步放大（如有）
        if LOADED_PLY_PATH:
            try:
                from plyfile import PlyData, PlyElement

                ply = PlyData.read(LOADED_PLY_PATH)
                v = ply["vertex"].data
                dtype = v.dtype
                arr = np.array(v)
                updated = False
                for field in ["scale_0", "scale_1", "scale_2"]:
                    if field in dtype.names:
                        arr[field] = arr[field] * scale
                        updated = True
                        logger(f"已同步放大字段: {field}")
                if updated:
                    el = PlyElement.describe(arr, "vertex")
                    PlyData([el], text=False).write(LOADED_PLY_PATH)
                    logger(f"✅ 已同步更新原始PLY文件: {LOADED_PLY_PATH}")
                else:
                    logger("原始PLY无scale_0/1/2字段，无需更新")
            except Exception as e:
                logger(f"❌ 更新原始PLY文件失败: {e}")

        return {"updated_pcd": scaled_pcd}


def get_plugin():
    return ScalePlugin()
