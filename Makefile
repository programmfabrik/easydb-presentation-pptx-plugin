PLUGIN_NAME = presentation-pptx
INSTALL_FILES = \
	$(WEB)/l10n/cultures.json \
	$(WEB)/l10n/de-DE.json \
	$(WEB)/l10n/en-US.json \
	$(WEB)/l10n/es-ES.json \
	$(WEB)/l10n/it-IT.json \
	$(WEB)/PresentationPowerpoint.js \
	src/server/presentation-pptx.py \
	src/server/default-black.pptx \
	src/server/default-white.pptx \
	presentation-pptx.config.yml

L10N_FILES = l10n/PresentationPowerpoint.csv

L10N_GOOGLE_KEY = 1glXObMmIUd0uXxdFdiPWRZPLCx6qEUaxDfNnmttave4
L10N_GOOGLE_GID = 1786140544

JS = $(WEB)/PresentationPowerpoint.js
COFFEE_FILES = src/webfrontend/PresentationPowerpointDownloadManager.coffee

all: build

include ../../easydb-library/tools/base-plugins.make

build: code

code: $(JS) $(dev_js) $(L10N)

$(dev_js): $(coffee_dev_files)
	#
	# $@
	mkdir -p $(dir $@)
	@cat $^ > $@

clean: clean-base
	rm -f $(dev_js)

wipe: wipe-base