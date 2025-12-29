import pathlib
import numpy as np
from typing import Optional, Sequence
from loguru import logger
from plyfile import PlyData, PlyElement
import trimesh

from datatypes import datatypes


# ============================================================
# POINT CLOUD LOADING
# ============================================================

def load_point_cloud(
    filepath: str,
    remove_nan_points: bool = True,
    remove_infinite_points: bool = True,
    remove_duplicated_points: bool = True,
) -> Optional[datatypes.Points3D]:
    """
    Load a PLY point cloud into Points3D.
    """

    path = pathlib.Path(filepath)
    if not path.is_file():
        logger.error(f"Point cloud file does not exist: {filepath}")
        return None

    ply = PlyData.read(str(path))
    if "vertex" not in ply:
        logger.error("PLY file has no vertex element")
        return None

    v = ply["vertex"]

    positions = np.column_stack((v["x"], v["y"], v["z"])).astype(np.float32)

    normals = None
    if all(k in v for k in ("nx", "ny", "nz")):
        normals = np.column_stack((v["nx"], v["ny"], v["nz"])).astype(np.float32)

    colors = None
    if all(k in v for k in ("red", "green", "blue")):
        r = v["red"].astype(np.uint32)
        g = v["green"].astype(np.uint32)
        b = v["blue"].astype(np.uint32)
        a = v["alpha"].astype(np.uint32) if "alpha" in v else np.full_like(r, 255)
        colors = ((r << 24) | (g << 16) | (b << 8) | a).astype(np.uint32)

    # -------- filtering --------
    mask = np.ones(len(positions), dtype=bool)

    if remove_nan_points or remove_infinite_points:
        mask &= np.isfinite(positions).all(axis=1)

    positions = positions[mask]
    if normals is not None:
        normals = normals[mask]
    if colors is not None:
        colors = colors[mask]

    if remove_duplicated_points and len(positions) > 0:
        unique_pos, idx = np.unique(positions, axis=0, return_index=True)
        positions = unique_pos
        if normals is not None:
            normals = normals[idx]
        if colors is not None:
            colors = colors[idx]

    if len(positions) == 0:
        logger.error("Loaded point cloud is empty after filtering")
        return None

    return datatypes.Points3D(
        positions=positions,
        normals=normals,
        colors=colors,
    )


# ============================================================
# POINT CLOUD WRITING
# ============================================================

def save_point_cloud(
    point_clouds: Sequence[datatypes.Points3D],
    filepath: str,
) -> bool:
    """
    Save one or more Points3D objects to a PLY file.
    """

    if not point_clouds:
        logger.error("No point clouds provided for writing")
        return False

    positions = np.vstack([pc.positions for pc in point_clouds])

    colors = None
    if any(pc.colors is not None for pc in point_clouds):
        color_blocks = []
        for pc in point_clouds:
            if pc.colors is not None:
                color_blocks.append(pc.colors)
            else:
                color_blocks.append(
                    np.full(len(pc.positions), 0xFFFFFFFF, dtype=np.uint32)
                )
        colors = np.concatenate(color_blocks)

    dtype = [("x", "f4"), ("y", "f4"), ("z", "f4")]
    data = {
        "x": positions[:, 0],
        "y": positions[:, 1],
        "z": positions[:, 2],
    }

    if colors is not None:
        dtype += [("red", "u1"), ("green", "u1"), ("blue", "u1"), ("alpha", "u1")]
        data["red"]   = (colors >> 24) & 0xFF
        data["green"] = (colors >> 16) & 0xFF
        data["blue"]  = (colors >> 8) & 0xFF
        data["alpha"] = colors & 0xFF

    arr = np.empty(len(positions), dtype=dtype)
    for k, v in data.items():
        arr[k] = v

    path = pathlib.Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    PlyData(
        [PlyElement.describe(arr, "vertex")],
        text=False,
    ).write(str(path))

    return True


# ============================================================
# MESH LOADING
# ============================================================

def load_mesh(
    filepath: str,
    compute_vertex_normals: bool = False,
    postprocess_mesh: bool = False,
) -> Optional[datatypes.Mesh3D]:
    """
    Load a mesh file into Mesh3D.
    Supports: PLY, OBJ, STL, GLB, GLTF.
    """

    path = pathlib.Path(filepath)
    if not path.is_file():
        logger.error(f"Mesh file does not exist: {filepath}")
        return None

    scene = trimesh.load(str(path), force="scene")

    if isinstance(scene, trimesh.Scene):
        if not scene.geometry:
            logger.error("Mesh file contains no geometry")
            return None
        mesh = trimesh.util.concatenate(tuple(scene.geometry.values()))
    else:
        mesh = scene

    if postprocess_mesh:
        mesh.remove_degenerate_faces()
        mesh.remove_duplicate_faces()
        mesh.remove_unreferenced_vertices()
        mesh.merge_vertices()

    if compute_vertex_normals:
        mesh.rezero()
        _ = mesh.vertex_normals  # force computation

    vertex_colors = None
    if mesh.visual.kind == "vertex":
        vc = mesh.visual.vertex_colors
        if vc is not None:
            vertex_colors = vc[:, :4]

    return datatypes.Mesh3D(
        vertex_positions=mesh.vertices.astype(np.float32),
        triangle_indices=mesh.faces.astype(np.int32),
        vertex_normals=mesh.vertex_normals.astype(np.float32)
        if mesh.vertex_normals is not None else None,
        vertex_colors=vertex_colors,
    )


# ============================================================
# MESH WRITING
# ============================================================

def save_mesh(
    mesh: datatypes.Mesh3D,
    filepath: str,
) -> bool:
    """
    Save Mesh3D to PLY / GLB / GLTF / STL / OBJ (based on extension).
    """

    trimesh_mesh = trimesh.Trimesh(
        vertices=mesh.vertex_positions,
        faces=mesh.triangle_indices,
        vertex_normals=mesh.vertex_normals,
        process=False,
    )

    if mesh.vertex_colors is not None:
        rgba = mesh.vertex_colors.astype(np.uint32)
        colors = np.column_stack([
            (rgba >> 24) & 0xFF,
            (rgba >> 16) & 0xFF,
            (rgba >> 8)  & 0xFF,
            rgba & 0xFF,
        ]).astype(np.uint8)
        trimesh_mesh.visual.vertex_colors = colors

    pathlib.Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    trimesh_mesh.export(filepath)

    return True
