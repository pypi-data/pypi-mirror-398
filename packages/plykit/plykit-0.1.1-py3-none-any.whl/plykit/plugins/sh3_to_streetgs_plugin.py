from plugin_base import BasePlugin
import numpy as np
from plyfile import PlyData, PlyElement
from pathlib import Path
import plykit_global as global_


class SH3ToStreetGSPlugin(BasePlugin):
    name = "3阶球谐PLY转STREET_GS"
    description = "将3阶球谐系数PLY转换为STREET_GS格式"
    default_params = {}

    def run(self, input_obj, params: dict, logger):
        if not global_.LOADED_PLY_PATH:
            raise ValueError(
                f"LOADED_PLY_PATH 未设置{global_.LOADED_PLY_PATH}，无法生成输出文件名"
            )

        original_path = Path(global_.LOADED_PLY_PATH)
        output_dir = Path("./outputs")
        output_dir.mkdir(exist_ok=True)
        new_filename = f"{original_path.stem}_stgs.ply"
        output_file = output_dir / new_filename

        data, ply = convert_sh3_to_streetgs(global_.LOADED_PLY_PATH)
        save_ply(data, str(output_file))
        logger(f"✅ 转换完成，输出文件: {output_file}")
        return {"output_path": str(output_file)}


def get_plugin():
    return SH3ToStreetGSPlugin()


def save_ply(data, output_path):
    el = PlyElement.describe(data, "vertex")
    PlyData([el], text=False).write(output_path)
    print("保存完成 →", output_path)


def convert_sh3_to_streetgs(input_ply):
    ply = PlyData.read(input_ply)
    v = ply["vertex"].data
    N = len(v)

    # 只保留3阶球谐的前15维f_dc和9维f_rest
    # f_dc: 0~2, f_rest: 0~8
    x = v["x"]
    y = v["y"]
    z = v["z"]
    f_dc = np.vstack([v["f_dc_0"], v["f_dc_1"], v["f_dc_2"]]).T
    f_dc_full = np.zeros((N, 15), dtype=np.float32)
    f_dc_full[:, :3] = f_dc

    f_rest_full = np.zeros((N, 9), dtype=np.float32)
    for i in range(9):
        f_rest_full[:, i] = v[f"f_rest_{i}"]

    opacity = v["opacity"]
    scale = np.vstack([v["scale_0"], v["scale_1"], v["scale_2"]]).T
    rot = np.vstack([v["rot_0"], v["rot_1"], v["rot_2"], v["rot_3"]]).T

    dtype = [
        ("x", "f4"),
        ("y", "f4"),
        ("z", "f4"),
        *[(f"f_dc_{i}", "f4") for i in range(15)],
        *[(f"f_rest_{i}", "f4") for i in range(9)],
        ("opacity", "f4"),
        ("scale_0", "f4"),
        ("scale_1", "f4"),
        ("scale_2", "f4"),
        ("rot_0", "f4"),
        ("rot_1", "f4"),
        ("rot_2", "f4"),
        ("rot_3", "f4"),
    ]

    new_data = np.empty(N, dtype=dtype)
    new_data["x"] = x
    new_data["y"] = y
    new_data["z"] = z
    for i in range(15):
        new_data[f"f_dc_{i}"] = f_dc_full[:, i]
    for i in range(9):
        new_data[f"f_rest_{i}"] = f_rest_full[:, i]
    new_data["opacity"] = opacity
    new_data["scale_0"] = scale[:, 0]
    new_data["scale_1"] = scale[:, 1]
    new_data["scale_2"] = scale[:, 2]
    new_data["rot_0"] = rot[:, 0]
    new_data["rot_1"] = rot[:, 1]
    new_data["rot_2"] = rot[:, 2]
    new_data["rot_3"] = rot[:, 3]

    return new_data, ply
