from pathlib import Path
from plyfile import PlyData, PlyElement
import numpy as np
import plykit_global as global_

EXPORT_PLY_PATH = Path("./outputs/exported_combined.ply")


def export_combined_ply(tmp_ply_path, original_ply_path, output_path=EXPORT_PLY_PATH):
    """
    用处理后的点云xyz（tmp_ply_path）和原始ply的其他属性合成新ply，保存到output_path。
    """
    # 读取tmp点云xyz
    tmp_ply = PlyData.read(str(tmp_ply_path))
    tmp_xyz = np.stack(
        [
            tmp_ply["vertex"].data["x"],
            tmp_ply["vertex"].data["y"],
            tmp_ply["vertex"].data["z"],
        ],
        axis=1,
    )
    N = len(tmp_xyz)

    # 读取原始ply所有属性
    orig_ply = PlyData.read(str(original_ply_path))
    orig_v = orig_ply["vertex"].data
    dtype = orig_v.dtype
    orig_data = np.array(orig_v)
    if len(orig_data) != N:
        raise ValueError(f"点数不一致: tmp({N}) != orig({len(orig_data)})")

    # 替换xyz
    orig_data["x"] = tmp_xyz[:, 0]
    orig_data["y"] = tmp_xyz[:, 1]
    orig_data["z"] = tmp_xyz[:, 2]

    # 保存新ply
    el = PlyElement.describe(orig_data, "vertex")
    PlyData([el], text=False).write(str(output_path))
    return str(output_path)


# 可直接在主界面调用此函数
# export_combined_ply(global_.TMP_PLY, global_.LOADED_PLY_PATH)
