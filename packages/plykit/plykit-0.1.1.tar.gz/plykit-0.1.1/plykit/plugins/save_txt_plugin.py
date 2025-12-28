from plugin_base import BasePlugin
import numpy as np
import os


class SaveTxtPlugin(BasePlugin):
    name = "保存为 TXT"
    description = "将点云保存为 TXT 文件（x y z [r g b]）"
    default_params = {"output_path": "./outputs/output.txt", "save_color": True}

    def run(self, input_obj, params: dict, logger):
        import open3d as o3d

        if isinstance(input_obj, str):
            pcd = o3d.io.read_point_cloud(input_obj)
        else:
            pcd = input_obj

        output_path = params.get("output_path", "./outputs/output.txt")
        save_color = params.get("save_color", True)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        points = np.asarray(pcd.points)
        data = [points]
        if save_color and pcd.has_colors():
            colors = np.asarray(pcd.colors)
            data.append(colors)

        full_data = np.hstack(data)
        np.savetxt(output_path, full_data, fmt="%.6f", delimiter=" ")

        logger(f"✅ 点云已保存为 TXT: {output_path}")
        return {"output_path": output_path}


def get_plugin():
    return SaveTxtPlugin()
