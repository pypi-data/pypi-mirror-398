from plugin_base import BasePlugin
import open3d as o3d
import numpy as np
from pathlib import Path
import plykit_global as global_


class StatsPlugin(BasePlugin):
    name = "点云信息统计"
    description = "统计点云基本信息（数量、边界、尺寸、质心、颜色信息），并可读取 PLY 文件头部（head -n）"
    default_params = {
        "header_lines": 20,  # how many header lines to read from a PLY file (like `head -n`)
    }

    def run(self, input_obj, params: dict, logger):
        """
        点云统计插件：始终用 global_.LOADED_PLY_PATH 读取 PLY 文件（用 plyfile），入参仅用于 Open3D fallback。
        统计点数、坐标、所有 vertex 属性名。
        """

        results = {}
        path = None
        header_lines = int(
            params.get("header_lines", self.default_params["header_lines"])
        )

        # Always use global_.LOADED_PLY_PATH for file-based stats
        if global_.LOADED_PLY_PATH:
            path = Path(global_.LOADED_PLY_PATH)
        else:
            logger("❌ global_.LOADED_PLY_PATH 未设置，无法读取点云文件")
            # fallback: try input_obj if it's Open3D
            if input_obj is not None:
                try:
                    points = np.asarray(input_obj.points)
                    results["stats"] = {"count": int(points.shape[0])}
                    return results
                except Exception:
                    results["stats"] = {"count": 0}
                    return results
            return results

        # Read header until end_header
        header = []
        try:
            with open(path, "r", errors="ignore") as f:
                for i in range(header_lines):
                    line = f.readline()
                    if not line:
                        break
                    header.append(line.rstrip("\n"))
                    if line.strip().lower() == "end_header":
                        break
            results["header"] = header
        except Exception as e:
            logger(f"⚠️ 读取 header 失败: {e}")

        # Parse header for format, vertex count, property names
        fmt = None
        vertex_count = None
        vertex_properties = []
        in_vertex_element = False
        for ln in header:
            parts = ln.strip().split()
            if not parts:
                continue
            key = parts[0].lower()
            if key == "format" and len(parts) >= 2:
                fmt = " ".join(parts[1:])
            elif key == "element" and len(parts) >= 3:
                if parts[1].lower() == "vertex":
                    try:
                        vertex_count = int(parts[2])
                    except Exception:
                        vertex_count = None
                    in_vertex_element = True
                else:
                    in_vertex_element = False
            elif key == "property" and in_vertex_element:
                if len(parts) >= 3:
                    prop_type = parts[1]
                    prop_name = parts[2]
                    vertex_properties.append({"name": prop_name, "type": prop_type})
        results["parsed_header"] = {
            "format": fmt,
            "vertex_count": vertex_count,
            "vertex_properties": vertex_properties,
            "raw": header,
        }

        # Use plyfile to read vertex properties
        vertex_props_list = []
        points = None
        try:
            from plyfile import PlyData

            plydata = PlyData.read(str(path))
            vertex = plydata["vertex"]
            props = [p.name for p in vertex.properties]
            results["vertex_properties"] = props

            # Try to get x, y, z
            def safe_get(prop_name):
                return vertex[prop_name] if prop_name in props else None

            x = safe_get("x")
            y = safe_get("y")
            z = safe_get("z")
            if x is not None and y is not None and z is not None:
                points = np.stack([x, y, z], axis=1)
                count = points.shape[0]
                min_xyz = points.min(axis=0).tolist()
                max_xyz = points.max(axis=0).tolist()
                size = [max_xyz[i] - min_xyz[i] for i in range(3)]
                centroid = points.mean(axis=0).tolist()
                std = points.std(axis=0).tolist()
                stats = {
                    "count": count,
                    "bounds": {"min": min_xyz, "max": max_xyz},
                    "size": size,
                    "centroid": centroid,
                    "std": std,
                    "vertex_properties": props,
                }
                results["stats"] = stats
                logger(
                    f"✅ 点云统计完成 — 点数: {count}, 尺寸: {size}, 质心: {centroid}"
                )
            else:
                logger("⚠️ vertex 不包含 x/y/z 属性，无法统计坐标")
                results["stats"] = {"count": len(vertex), "vertex_properties": props}
        except Exception as e:
            logger(f"⚠️ 使用 plyfile 读取 vertex 属性失败: {e}")
            results["stats"] = {"count": 0}
        import json

        logger(
            "results:\n" + json.dumps(results["header"], ensure_ascii=False, indent=2)
        )
        return results


def get_plugin():
    return StatsPlugin()
