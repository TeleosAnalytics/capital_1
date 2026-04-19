# Professional Bootstrap for MASH Project
.PHONY: setup pull connect all claude-setup claude-privacy

# The "One Command" to rule them all
all: setup pull claude-privacy

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
