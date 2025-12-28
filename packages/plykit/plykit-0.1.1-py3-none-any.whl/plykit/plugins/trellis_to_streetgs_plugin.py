from plugin_base import BasePlugin
import numpy as np
from plyfile import PlyData, PlyElement
from pathlib import Path
import plykit_global as global_


class TrellisToStreetGSPlugin(BasePlugin):
    name = "TRELLIS转STREET_GS"
    description = "将TRELLIS模型PLY转换为STREET_GS格式"
    default_params = {"is_replace_ply_by_current_ply": False}

    def run(self, input_obj, params: dict, logger):
        is_replace = params.get("is_replace_ply_by_current_ply", False)
        if not global_.LOADED_PLY_PATH:
            raise ValueError(
                f"LOADED_PLY_PATH 未设置{global_.LOADED_PLY_PATH}，无法生成输出文件名"
            )

        # 1. 解析原始文件路径
        original_path = Path(global_.LOADED_PLY_PATH)
        # 2. 构造输出文件名: ./outputs/{stem}_stgs.ply
        output_dir = Path("./outputs")
        output_dir.mkdir(exist_ok=True)  # 自动创建 outputs 目录

        new_filename = f"{original_path.stem}_stgs.ply"
        output_file = output_dir / new_filename

        # 3. 调用转换逻辑
        if is_replace:
            logger(
                "is_replace_ply_by_current_ply=True，使用TMP_PLY的xyz，其他属性从源PLY获取"
            )

            # 读取TMP_PLY的xyz
            tmp_ply = PlyData.read(str(global_.TMP_PLY))
            tmp_xyz = np.stack(
                [
                    tmp_ply["vertex"].data["x"],
                    tmp_ply["vertex"].data["y"],
                    tmp_ply["vertex"].data["z"],
                ],
                axis=1,
            )

            # 读取源PLY所有属性
            data, ply = convert_simple_to_full(global_.LOADED_PLY_PATH)
            # 用TMP_PLY的xyz替换data的xyz
            if len(data) != len(tmp_xyz):
                raise ValueError(
                    f"TMP_PLY点数({len(tmp_xyz)})与源PLY点数({len(data)})不一致"
                )
            data["x"] = tmp_xyz[:, 0]
            data["y"] = tmp_xyz[:, 1]
            data["z"] = tmp_xyz[:, 2]
        else:
            data, ply = convert_simple_to_full(global_.LOADED_PLY_PATH)

        save_ply(data, str(output_file))  # 确保传字符串（部分库需要）

        logger(f"✅ 转换完成，输出文件: {output_file}")

        return {"output_path": str(output_file)}


def get_plugin():
    return TrellisToStreetGSPlugin()


def save_ply(data, output_path):
    el = PlyElement.describe(data, "vertex")
    PlyData([el], text=False).write(output_path)
    print("保存完成 →", output_path)


def convert_simple_to_full(input_ply):
    """
    读取简化 PLY，生成完整版结构（f_dc 15维 + f_rest 9维）
    返回结构化 numpy 数组和原 PlyData 对象
    """
    ply = PlyData.read(input_ply)
    v = ply["vertex"].data
    N = len(v)

    # 准备字段
    x = v["x"]
    y = v["y"]
    z = v["z"]
    nx = v["nx"]
    ny = v["ny"]
    nz = v["nz"]

    f_dc = np.vstack([v["f_dc_0"], v["f_dc_1"], v["f_dc_2"]]).T
    f_dc_full = np.zeros((N, 15), dtype=np.float32)
    f_dc_full[:, :3] = f_dc

    f_rest_full = np.zeros((N, 9), dtype=np.float32)
    opacity = v["opacity"]

    scale = np.vstack([v["scale_0"], v["scale_1"], v["scale_2"]]).T
    rot = np.vstack([v["rot_0"], v["rot_1"], v["rot_2"], v["rot_3"]]).T

    # 定义 dtype
    dtype = [
        ("x", "f4"),
        ("y", "f4"),
        ("z", "f4"),
        ("nx", "f4"),
        ("ny", "f4"),
        ("nz", "f4"),
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
    new_data["nx"] = nx
    new_data["ny"] = ny
    new_data["nz"] = nz

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
