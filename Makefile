UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
	GDC_URL = https://gdc.cancer.gov/files/public/file/gdc-client_v1.6.1_Ubuntu_x64.zip
else
	GDC_URL = https://gdc.cancer.gov/files/public/file/gdc-client_v1.6.1_OSX_x64.zip
endif
.PHONY: setup pull connect all tools claude-login claude-setup claude-privacy clean

# The "One Command" to rule them all
all: setup pull tools claude-privacy claude-login jupyter

tools:
	#sudo apt-get update
	#sudo apt-get install -y --no-install-recommends ca-certificates curl gnupg
	#sudo apt-get purge -y nodejs npm libnode-dev libnode72 nodejs-doc || true
	#sudo apt-get autoremove -y || true
	#curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
	#sudo apt-get install -y --no-install-recommends nodejs
	#sudo npm install -g @anthropic-ai/claude-code

claude-login:
	#claude


setup:
	@echo "--- Installing Dependencies ---"
	pip install -r requirements.txt
	python -m ipykernel install --user --name capital_1
	@echo "--- Injecting JupyterLab Shortcuts ---"
	mkdir -p ~/.jupyter/lab/user-settings/@jupyterlab/shortcuts-extension/
	echo '{"shortcuts":[{"command":"notebook:run-cell-and-insert-below","keys":["Alt Enter"],"selector":".jp-Notebook.jp-mod-editMode","disabled":true},{"command":"notebook:run-in-console","keys":["Alt Enter"],"selector":".jp-Notebook.jp-mod-editMode"}]}' > ~/.jupyter/lab/user-settings/@jupyterlab/shortcuts-extension/shortcuts.jupyterlab-settings
	@echo "--- Fetching GDC Client ---"
	#wget -q -O gdc.zip https://gdc.cancer.gov/files/public/file/gdc-client_v1.6.1_OSX_x64.zip
	wget -q -O gdc.zip $(GDC_URL)
	unzip -o gdc.zip
	rm gdc.zip
	chmod +x gdc-client

pull:
	@echo "--- Pulling Liver HE Dataset ---"
	mkdir -p data/landing_zone
	./gdc-client download -m accessory_data/TCGA-LIHC_manifest_small.txt -d data/landing_zone/

claude-setup:
	@echo "--- Installing Claude Code ---"
	npm install -g @anthropic-ai/claude-code
	@echo "--- Initializing Claude Code for this project ---"
	claude init

claude-privacy:
	@mkdir -p ~/.claude
	@python3 -c "\
import json, os, sys; \
p = os.path.expanduser('~/.claude/settings.json'); \
cfg = json.load(open(p)) if os.path.exists(p) else {}; \
env = cfg.setdefault('env', {}); \
keys = ['DISABLE_TELEMETRY','DISABLE_ERROR_REPORTING','DISABLE_BUG_COMMAND','DISABLE_AUTOUPDATER','DISABLE_NON_ESSENTIAL_MODEL_CALLS']; \
[env.update({k: '1'}) for k in keys if env.get(k) != '1']; \
json.dump(cfg, open(p, 'w'), indent=2); \
print('claude-privacy: ~/.claude/settings.json updated with strict privacy posture')"

clean:
	rm -rf gdc-client gdc.zip

jupyter:
	@echo "--- Starting JupyterLab on Port 8888 ---"
	jupyter lab --no-browser --port=8888
