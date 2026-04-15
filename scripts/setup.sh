#!/bin/bash

# 1. Install Python libraries
pip install -r requirements.txt

# 2. Download and install GDC Client
wget https://gdc.cancer.gov/files/public/file/gdc-client_v1.6.1_Ubuntu_x64.zip 
unzip gdc-client_v1.6.1_Ubuntu_x64.zip 

chmod +x gdc-client
chmod +x scripts/pull_data.sh

echo "Environment setup complete."