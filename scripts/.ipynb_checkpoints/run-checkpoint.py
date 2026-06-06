#!/usr/bin/env python
# coding: utf-8

import capital_1 as cptl
import pandas as pd
import os

metadf = cptl.IO.get_metadf()

#conver .svs files to ome.zarr
for _, row in metadf.iterrows():
    svs_path = row['original_path']
    zarr_path = row['zarr_path']
    zarr_path.parent.mkdir(parents=True, exist_ok=True)
    if not zarr_path.exists():
            print(f"Converting: {row['prefix']}")
            cptl.IO.convert_svs_to_zarr(svs_path, zarr_path, chunk_size=512)
    print('all images stored as zarr')
