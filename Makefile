PLUGIN_NAME = presentation-pptx
PLUGIN_PATH = easydb-presentation-pptx-plugin

SRC = $(CURDIR)/src
SRC_WEB = $(SRC)/webfrontend
SRC_SERVER = $(SRC)/server
SRC_TEMPLATES = $(SRC)/templates
SRC_PLACEHOLDERS = $(SRC)/placeholders
JS = $(SRC_WEB)/$(PLUGIN_NAME).js

FYLR_LIBRARY = $(SRC_SERVER)/fylr_lib_plugin_python3
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

build: code buildinfojson ## build all (creates build folder)
	mkdir -p $(BUILD_SERVER)
	cp -r $(SRC_SERVER)/* $(BUILD_SERVER)
	mkdir -p $(BUILD_WEB)
	cp -r $(JS) $(BUILD_WEB)
	mkdir -p $(BUILD_L10N)
	cp -r $(L10N_FILES) $(BUILD_L10N)
	cp -r $(SRC_TEMPLATES) $(BUILD_DIR)
	cp -r $(SRC_PLACEHOLDERS) $(BUILD_DIR)
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
	(rm $(BUILD_DIR)/$(PLUGIN_NAME).zip || true)
	cp -r $(BUILD_DIR) $(PLUGIN_PATH)
	zip $(BUILD_DIR)/$(PLUGIN_NAME).zip -x */l10n/*.json -x *.pyc -x */__pycache__/* -r $(PLUGIN_PATH)/
	rm -rf $(PLUGIN_PATH)


##############################
# easydb only

INSTALL_FILES = \
	$(BUILD_L10N)/*.json \
	$(BUILD_WEB)/$(PLUGIN_NAME).js \
	$(BUILD_SERVER)/presentation-pptx.py \
	$(BUILD_SERVER)/fylr_lib_plugin_python3/* \
	$(BUILD_TEMPLATES)/*.pptx \
	$(BUILD_PLACEHOLDERS)/*.png \
	manifest.master.yml
