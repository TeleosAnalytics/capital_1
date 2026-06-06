import capital_1 as cptl
import pandas as pd
from pathlib import Path
import openslide
import numpy as np
import zarr
from skimage.color import rgb2hsv
from skimage.filters import threshold_otsu

def get_metadf():
    data_path = cptl.config.proj_path / "data" 
    svs_files = list((data_path / "landing_zone").rglob("*.svs"))
    metadata = []
    for file_path in svs_files:
        file_id = file_path.parent.name
        prefix = file_path.stem 
        patient_id = prefix[:12] if prefix.startswith("TCGA") else "Unknown"
        size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)
        zarr_path = (data_path / "zarr_files") / (prefix + '.ome.zarr')
        metadata.append({
            "id": file_id,
            "prefix": prefix,
            "patient_id": patient_id,
            "original_path": str(file_path.resolve()),
            'zarr_path': zarr_path,
            "size_mb": size_mb
        })
        
    metadf = pd.DataFrame(metadata)
    return metadf

def convert_svs_to_zarr(svs_path, zarr_path, chunk_size = 512):
    
    slide = openslide.OpenSlide(svs_path)
    width, height = slide.dimensions
    
    zarr_out = zarr.open(
        str(zarr_path), 
        mode='w', 
        shape=(height, width, 3), # RGB channels
        chunks=(chunk_size, chunk_size, 3), 
        dtype='uint8'
    )
    
    for y in range(0, height, chunk_size):
        for x in range(0, width, chunk_size):
            
            # Calculate actual tile size (edge tiles will be smaller than 512)
            w = min(chunk_size, width - x)
            h = min(chunk_size, height - y)
            
            # Extract the specific (x, y) region at Level 0
            region = slide.read_region((x, y), 0, (w, h))
            
            # Convert to numpy array and strip the Alpha channel (RGBA -> RGB)
            rgb_tile = np.array(region)[:, :, :3]
            
            # Slot the tile into the corresponding Zarr coordinates on disk
            zarr_out[y:y+h, x:x+w, :] = rgb_tile
    
    slide.close()

def get_tissue_mask(rgb_image):
    """
    Takes an RGB numpy array and returns a boolean tissue mask.
    True = Tissue, False = Background.
    """
    # 1. Convert to HSV color space
    hsv_image = rgb2hsv(rgb_image)
    
    # 2. Extract the Saturation channel (Index 1)
    saturation = hsv_image[:, :, 1]
    
    # 3. Calculate the optimal separation threshold automatically
    try:
        threshold = threshold_otsu(saturation)
    except ValueError:
        # Failsafe: if the image is 100% blank glass, Otsu will fail
        return np.zeros_like(saturation, dtype=bool)
        
    # 4. Generate the binary mask
    tissue_mask = saturation > threshold
    
    return tissue_mask