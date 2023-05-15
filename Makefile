PLUGIN_NAME = presentation-pptx
PLUGIN_PATH = easydb-presentation-pptx-plugin

BUILD_DIR = build/$(PLUGIN_PATH)
DIR_WEB = $(BUILD_DIR)/webfrontend
DIR_SERVER = $(BUILD_DIR)/server
DIR_TEMPLATES = $(BUILD_DIR)/templates
DIR_L10N = $(BUILD_DIR)/l10n

SRC_WEB = src/webfrontend
SRC_SERVER = src/server
SRC_TEMPLATES = src/templates
FYLR_LIB = fylr_lib_plugin_python3

INSTALL_FILES = \
	$(DIR_L10N)/cultures.json \
	$(DIR_L10N)/cs-CZ.json \
	$(DIR_L10N)/da-DK.json \
	$(DIR_L10N)/de-DE.json \
	$(DIR_L10N)/en-US.json \
	$(DIR_L10N)/es-ES.json \
	$(DIR_L10N)/fi-FI.json \
	$(DIR_L10N)/fr-FR.json \
	$(DIR_L10N)/it-IT.json \
	$(DIR_L10N)/pl-PL.json \
	$(DIR_L10N)/ru-RU.json \
	$(DIR_L10N)/sv-SE.json \
	$(DIR_WEB)/PresentationPowerpoint.js \
	$(DIR_SERVER)/presentation-pptx.py \
	$(DIR_TEMPLATES)/default-black.pptx \
	$(DIR_TEMPLATES)/default-white.pptx \
	$(DIR_TEMPLATES)/default-black-4-3.pptx \
	$(DIR_TEMPLATES)/default-white-4-3.pptx \
	manifest.yml

L10N_FILES = l10n/PresentationPowerpoint.csv

L10N_GOOGLE_KEY = 1glXObMmIUd0uXxdFdiPWRZPLCx6qEUaxDfNnmttave4
L10N_GOOGLE_GID = 1786140544

JS = $(DIR_WEB)/PresentationPowerpoint.js
COFFEE_FILES = $(SRC_WEB)/PresentationPowerpointDownloadManager.coffee

all: build

include ../easydb-library/tools/base-plugins.make

build: code buildinfojson
	mkdir -p $(DIR_SERVER)/$(FYLR_LIB)
	cp $(SRC_SERVER)/*.py $(DIR_SERVER)
	cp $(SRC_SERVER)/$(FYLR_LIB)/*.py $(DIR_SERVER)/$(FYLR_LIB)
	mkdir -p $(DIR_TEMPLATES)
	cp $(SRC_TEMPLATES)/*.pptx $(DIR_TEMPLATES)
	mkdir -p $(DIR_L10N)
	cp $(L10N_FILES) $(DIR_L10N)
	(mv $(WEB)/l10n/*.json $(DIR_L10N) || true)
	(rm -r $(WEB) || true)
	cp manifest.master.yml $(BUILD_DIR)/manifest.yml

code: $(JS) $(dev_js) $(L10N)

$(dev_js): $(coffee_dev_files)
	#
	# $@
	mkdir -p $(dir $@)
	@cat $^ > $@

clean: clean-base
	rm -f $(dev_js)

wipe: wipe-base
