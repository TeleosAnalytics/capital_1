"""Convert .svs files to OME-Zarr at 20x (~0.505 um/pixel)."""

import json
from pathlib import Path

import numpy as np
import openslide
import zarr

TARGET_MPP = 0.505  # 2x downsample from 40x @ 0.2525 um/px
TILE_SIZE = 1024    # read tile size from SVS (in output coords)
CHUNK_SIZE = 512    # zarr chunk size
N_PYRAMID_LEVELS = 5


def svs_to_ome_zarr(svs_path: Path, out_dir: Path) -> Path:
    svs_path = Path(svs_path)
    slide = openslide.OpenSlide(svs_path)

    base_mpp = float(slide.properties[openslide.PROPERTY_NAME_MPP_X])
    ds_factor = TARGET_MPP / base_mpp  # ~2.0
    actual_mpp = base_mpp * ds_factor

    w0, h0 = slide.level_dimensions[0]
    out_w = int(w0 / ds_factor)
    out_h = int(h0 / ds_factor)

    out_path = out_dir / (svs_path.stem + ".ome.zarr")
    store = zarr.storage.LocalStore(str(out_path))
    root = zarr.open_group(store, mode="w")

    print(f"  Source: {svs_path.name}")
    print(f"  Base MPP: {base_mpp:.4f} um/px  ->  output MPP: {actual_mpp:.4f} um/px")
    print(f"  Output dims: {out_w} x {out_h}")

    # --- write pyramid level 0 (full 20x) tiled ---
    arr0 = root.create_array(
        "0",
        shape=(out_h, out_w, 3),
        chunks=(CHUNK_SIZE, CHUNK_SIZE, 3),
        dtype=np.uint8,
    )

    n_tiles_x = (out_w + TILE_SIZE - 1) // TILE_SIZE
    n_tiles_y = (out_h + TILE_SIZE - 1) // TILE_SIZE
    total = n_tiles_x * n_tiles_y
    done = 0

    for ty in range(n_tiles_y):
        for tx in range(n_tiles_x):
            ox = tx * TILE_SIZE
            oy = ty * TILE_SIZE
            tw = min(TILE_SIZE, out_w - ox)
            th = min(TILE_SIZE, out_h - oy)

            # map output coords back to level-0 SVS coords
            src_x = int(ox * ds_factor)
            src_y = int(oy * ds_factor)
            src_w = int(tw * ds_factor)
            src_h = int(th * ds_factor)

            region = slide.read_region((src_x, src_y), 0, (src_w, src_h))
            region = region.convert("RGB")
            tile = np.array(region, dtype=np.uint8)

            if tile.shape[:2] != (src_h, src_w):
                tile = tile[:src_h, :src_w]

            # downsample using simple area averaging via PIL
            from PIL import Image
            pil = Image.fromarray(tile)
            pil = pil.resize((tw, th), Image.LANCZOS)
            tile_ds = np.array(pil, dtype=np.uint8)

            arr0[oy : oy + th, ox : ox + tw, :] = tile_ds

            done += 1
            if done % max(1, total // 20) == 0:
                print(f"    level 0: {done}/{total} tiles", flush=True)

    # --- build remaining pyramid levels by successive 2x downsampling ---
    prev_arr = arr0
    for level in range(1, N_PYRAMID_LEVELS):
        ph, pw, _ = prev_arr.shape
        lh, lw = max(1, ph // 2), max(1, pw // 2)
        print(f"  Building level {level}: {lw} x {lh}", flush=True)

        arr_l = root.create_array(
            str(level),
            shape=(lh, lw, 3),
            chunks=(CHUNK_SIZE, CHUNK_SIZE, 3),
            dtype=np.uint8,
        )

        # read previous level in row-strips and downsample
        strip_h = CHUNK_SIZE * 2
        for row in range(0, ph, strip_h):
            rh = min(strip_h, ph - row)
            strip = prev_arr[row : row + rh, :, :]
            from PIL import Image
            pil = Image.fromarray(strip)
            out_strip_h = max(1, rh // 2)
            pil_ds = pil.resize((lw, out_strip_h), Image.LANCZOS)
            tile_ds = np.array(pil_ds, dtype=np.uint8)
            out_row = row // 2
            arr_l[out_row : out_row + out_strip_h, :, :] = tile_ds

        prev_arr = arr_l

    # --- write OME-Zarr multiscales metadata ---
    datasets = [
        {
            "path": str(i),
            "coordinateTransformations": [
                {
                    "type": "scale",
                    "scale": [actual_mpp * (2**i), actual_mpp * (2**i), 1.0],
                }
            ],
        }
        for i in range(N_PYRAMID_LEVELS)
    ]

    multiscales = [
        {
            "version": "0.4",
            "name": svs_path.stem,
            "axes": [
                {"name": "y", "type": "space", "unit": "micrometer"},
                {"name": "x", "type": "space", "unit": "micrometer"},
                {"name": "c", "type": "channel"},
            ],
            "datasets": datasets,
            "type": "2x_lanczos_downsample",
        }
    ]
    root.attrs["multiscales"] = multiscales

    slide.close()
    print(f"  Saved -> {out_path}")
    return out_path


if __name__ == "__main__":
    base = Path("/home/ubuntu/mash_model_1_0")
    out_dir = base / "ome_zarr"
    out_dir.mkdir(exist_ok=True)

    svs_files = list(base.rglob("*.svs"))
    print(f"Found {len(svs_files)} SVS files\n")

    for svs in svs_files:
        svs_to_ome_zarr(svs, out_dir)
        print()
