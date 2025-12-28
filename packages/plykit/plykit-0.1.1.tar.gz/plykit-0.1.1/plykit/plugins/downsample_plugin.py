from plugin_base import BasePlugin
import open3d as o3d


class DownsamplePlugin(BasePlugin):
    name = "体素降采样"
    description = "使用体素网格对点云进行降采样"
    default_params = {"voxel_size": 0.05}

    def run(self, input_obj, params: dict, logger):
        if isinstance(input_obj, str):
            pcd = o3d.io.read_point_cloud(input_obj)
        else:
            pcd = input_obj

        voxel_size = float(params.get("voxel_size", 0.05))
        downsampled_pcd = pcd.voxel_down_sample(voxel_size=voxel_size)

        logger(
            f"✅ 降采样完成，体素大小: {voxel_size}，点数: {len(downsampled_pcd.points)}"
        )
        return {"updated_pcd": downsampled_pcd}


def get_plugin():
    return DownsamplePlugin()
