PLUGIN_NAME = presentation-pptx
PLUGIN_PATH = easydb-presentation-pptx-plugin

SRC = $(CURDIR)/src
SRC_WEB = $(SRC)/webfrontend
SRC_SERVER = $(SRC)/server
SRC_TEMPLATES = $(SRC)/templates
SRC_PLACEHOLDERS = $(SRC)/placeholders
JS = $(SRC_WEB)/$(PLUGIN_NAME).js

EASYDB_LIBRARY = $(CURDIR)/easydb-library/tools

BUILD_DIR = build
BUILD_WEB = $(BUILD_DIR)/webfrontend
BUILD_L10N = $(BUILD_WEB)/l10n
BUILD_SERVER = $(BUILD_DIR)/server
BUILD_TEMPLATES = $(BUILD_DIR)/templates
BUILD_PLACEHOLDERS = $(BUILD_DIR)/placeholders

BUILD_INFO = build-info.json

COFFEE_FILES = $(shell find $(SRC_WEB) -name '*.coffee')

L10N_DIR = $(CURDIR)/l10n
L10N_FILES = $(L10N_DIR)/$(PLUGIN_NAME).csv

L10N_GOOGLE_KEY = 1glXObMmIUd0uXxdFdiPWRZPLCx6qEUaxDfNnmttave4
L10N_GOOGLE_GID = 1786140544

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = "(:|##)"}; {printf "\033[36m%-30s\033[0m %s\n", $$2, $$4}'

include $(EASYDB_LIBRARY)/base-plugins.make

all: clean build ## pull CSV & build

code: $(JS) ## build Coffeescript code

build: code build-stamp-l10n buildinfojson ## build all (creates build folder)
	mkdir -p $(BUILD_SERVER)
	cp -r $(SRC_SERVER)/* $(BUILD_SERVER)
	mkdir -p $(BUILD_WEB)
	cp -r $(JS) $(BUILD_WEB)
	mkdir -p $(BUILD_L10N)
	chmod 777 $(L10N_FILES)
	cp -r $(L10N_FILES) $(BUILD_L10N)
	cp -r $(SRC_TEMPLATES) $(BUILD_DIR)
	cp -r $(SRC_PLACEHOLDERS) $(BUILD_DIR)
	cp manifest.master.yml $(BUILD_DIR)/manifest.yml
	cp $(BUILD_INFO) $(BUILD_DIR)

clean: ## clean build and temporary files
	rm -f $(SRC_SERVER)/*.pyc
	rm -rf $(SRC_SERVER)/__pycache__
	rm -f $(SRC_WEB)/*.js
	rm -f $(JS)
	rm -rf $(L10N_DIR)/*.json
	rm -rf $(BUILD_DIR)
	rm -f $(BUILD_INFO)
	rm -f build-stamp-l10n


##############################
# fylr only

zip: build ## build zip file for publishing (fylr only)
	(rm $(BUILD_DIR)/$(PLUGIN_NAME).zip || true)
	cp -r $(BUILD_DIR) $(PLUGIN_PATH)
	zip $(BUILD_DIR)/$(PLUGIN_NAME).zip -x *.pyc -x */__pycache__/* -r $(PLUGIN_PATH)/
	rm -rf $(PLUGIN_PATH)


##############################
# easydb only

INSTALL_FILES = \
	$(BUILD_L10N)/cultures.json \
	$(BUILD_L10N)/de-DE.json \
	$(BUILD_L10N)/en-US.json \
	$(BUILD_L10N)/da-DK.json \
	$(BUILD_L10N)/fi-FI.json \
	$(BUILD_L10N)/sv-SE.json \
	$(BUILD_L10N)/fr-FR.json \
	$(BUILD_L10N)/it-IT.json \
	$(BUILD_L10N)/es-ES.json \
	$(BUILD_L10N)/cs-CZ.json \
	$(BUILD_L10N)/pl-PL.json \
	$(BUILD_L10N)/ru-RU.json \
	$(BUILD_WEB)/$(PLUGIN_NAME).js \
	$(BUILD_SERVER)/presentation_pptx_easydb5.py \
	$(BUILD_SERVER)/presentation_pptx_modules/__init__.py \
	$(BUILD_SERVER)/presentation_pptx_modules/build_pptx.py \
	$(BUILD_SERVER)/presentation_pptx_modules/pptx_util.py \
	$(BUILD_TEMPLATES)/default-black.pptx \
	$(BUILD_TEMPLATES)/default-white.pptx \
	$(BUILD_TEMPLATES)/default-black-4-3.pptx \
	$(BUILD_TEMPLATES)/default-white-4-3.pptx \
	$(BUILD_PLACEHOLDERS)/dark.png \
	$(BUILD_PLACEHOLDERS)/light.png \
	$(BUILD_DIR)/manifest.yml
