PLUGIN_NAME = presentation-pptx
PLUGIN_PATH = easydb-presentation-pptx-plugin

SRC = $(CURDIR)/src
SRC_WEB = $(SRC)/webfrontend
SRC_SERVER = $(SRC)/server
SRC_TEMPLATES = $(SRC)/templates
JS = $(SRC_WEB)/$(PLUGIN_NAME).js

FYLR_LIBRARY = $(SRC_SERVER)/fylr_lib_plugin_python3
EASYDB_LIBRARY = $(CURDIR)/easydb-library/tools

BUILD_DIR = $(CURDIR)/build
BUILD_WEB = $(BUILD_DIR)/webfrontend
BUILD_L10N = $(BUILD_WEB)/l10n
BUILD_SERVER = $(BUILD_DIR)/server
BUILD_TEMPLATES = $(BUILD_DIR)/templates

BUILD_INFO = build-info.json

COFFEE_FILES = $(shell find $(SRC_WEB) -name '*.coffee')

L10N_DIR = $(CURDIR)/l10n
L10N_CSV = $(L10N_DIR)/$(PLUGIN_NAME).csv

L10N_GOOGLE_KEY = 1glXObMmIUd0uXxdFdiPWRZPLCx6qEUaxDfNnmttave4
L10N_GOOGLE_GID = 1786140544

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = "(:|##)"}; {printf "\033[36m%-30s\033[0m %s\n", $$2, $$4}'

all: clean build zip ## pull CSV & build & zip

google-csv: ## get loca CSV from google
	mkdir -p $(L10N_DIR)
	curl --silent -L -o - "https://docs.google.com/spreadsheets/u/1/d/$(L10N_GOOGLE_KEY)/export?format=csv&gid=$(L10N_GOOGLE_GID)" | tr -d "\r" > $(L10N_CSV)

code: $(JS) ## build Coffeescript code

build: l10n2json code buildinfojson ## build all (creates build folder)
	mkdir -p $(BUILD_SERVER)
	cp -r $(SRC_SERVER)/* $(BUILD_SERVER)
	mkdir -p $(BUILD_WEB)
	cp -r $(JS) $(BUILD_WEB)
	mkdir -p $(BUILD_L10N)
	cp -r $(L10N_CSV) $(BUILD_L10N)
	cp -r $(SRC_TEMPLATES) $(BUILD_DIR)
	cp manifest.master.yml $(BUILD_DIR)/manifest.yml
	cp $(BUILD_INFO) $(BUILD_DIR)

clean: ## clean build and temporary files
	rm -f $(SRC_SERVER)/*.pyc
	rm -rf $(SRC_SERVER)/__pycache__
	rm -f $(FYLR_LIBRARY)/*.pyc
	rm -rf $(FYLR_LIBRARY)/__pycache__
	rm -f $(SRC_WEB)/*.js
	rm -f $(JS)
	rm -rf $(L10N_DIR)/*.json
	rm -rf $(BUILD_DIR)
	rm -f $(BUILD_INFO)


##############################
# fylr only

zip: build ## build zip file for publishing (fylr only)
	mkdir -p tmp
	(rm $(BUILD_DIR)/$(PLUGIN_NAME).zip || true)
	cp -r $(BUILD_DIR) tmp/$(PLUGIN_PATH)
	cd tmp && zip $(BUILD_DIR)/$(PLUGIN_NAME).zip -x */l10n/*.json -x *.pyc -x */__pycache__/* -r $(PLUGIN_PATH)
	cd ..
	rm -rf tmp


##############################
# easydb only

include $(EASYDB_LIBRARY)/base-plugins.make

l10n2json: google-csv ## build l10n json files (easydb5 only)
	mkdir -p $(BUILD_L10N)
	$(EASYDB_LIBRARY)/l10n2json.py $(L10N_CSV) $(BUILD_L10N)

INSTALL_FILES = \
	$(BUILD_L10N)/cultures.json \
	$(BUILD_L10N)/cs-CZ.json \
	$(BUILD_L10N)/da-DK.json \
	$(BUILD_L10N)/de-DE.json \
	$(BUILD_L10N)/en-US.json \
	$(BUILD_L10N)/es-ES.json \
	$(BUILD_L10N)/fi-FI.json \
	$(BUILD_L10N)/fr-FR.json \
	$(BUILD_L10N)/it-IT.json \
	$(BUILD_L10N)/pl-PL.json \
	$(BUILD_L10N)/ru-RU.json \
	$(BUILD_L10N)/sv-SE.json \
	$(BUILD_WEB)/$(PLUGIN_NAME).js \
	$(BUILD_SERVER)/presentation-pptx.py \
	$(BUILD_SERVER)/fylr_lib_plugin_python3 \
	$(BUILD_SERVER)/fylr_lib_plugin_python3/__init__.py \
	$(BUILD_SERVER)/fylr_lib_plugin_python3/util.py \
	$(BUILD_TEMPLATES)/default-black.pptx \
	$(BUILD_TEMPLATES)/default-white.pptx \
	$(BUILD_TEMPLATES)/default-black-4-3.pptx \
	$(BUILD_TEMPLATES)/default-white-4-3.pptx \
	manifest.master.yml
