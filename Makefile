# Professional Bootstrap for MASH Project
.PHONY: setup pull connect all

# The "One Command" to rule them all
all: setup pull

setup:
	@echo "--- Installing Dependencies ---"
	pip install -r requirements.txt
	@echo "--- Fetching GDC Client ---"
	wget -q -O gdc.zip https://gdc.cancer.gov/files/public/file/gdc-client_v1.6.1_Ubuntu_x64.zip
	unzip -o gdc.zip
	rm gdc.zip
	chmod +x gdc-client

pull:
	@echo "--- Pulling MASH Dataset ---"
	./gdc-client download -m accessory_data/TCGA-LIHC_manifest_small.txt

clean:
	rm -rf gdc-client gdc.zip
