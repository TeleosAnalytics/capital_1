#!/bin/bash

echo "Pulling the heavy MASH dataset..."
./gdc-client download -m accessory_data/TCGA-LIHC_manifest_small.txt
echo "Download complete."