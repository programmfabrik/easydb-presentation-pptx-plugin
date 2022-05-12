class PresentationPowerpointDownloadManager extends PresentationDownloadManager

	readOpts: ->
		super()

	loca_key: (key) ->
		CUI.util.toDot(@__cls)+"."+key


	getMenuButton: ->
		loca_key: @loca_key("button.menu")
		ui: "presentation.powerpoint.download.manager.button"
		onClick: =>
			@startExport()

	getTitle: ->
		$$(@loca_key("dialog.title"))


	getAssetVersionsToExport: (asset, gid) ->
		if @data_by_gid[gid]?asset_ids.length >= 1
			# only first asset per object
			return

		version = Asset.getBestImageForViewport(asset, @pptx_form.quality, @pptx_form.quality)
		if not version
			[]
		else
			[ version ]

	filterDownloadableFiles: (files) ->
		for f in files
			if f.path.endsWith(".pptx")
				return [ f ]
		return []

	getExportSaveData: ->
		data = super()
		data.export.produce_options.pptx_form = CUI.util.copyObject(@pptx_form, true)
		delete(data.export.produce_options.pptx_form._undo)
		# console.debug "export save data:", CUI.util.dump(data)
		data

	getContent: ->
		pptx_config = ez5.pluginManager.getPlugin("easydb-presentation-pptx-plugin").getOpts()
		# console.debug @__cls, "getContent", pptx_config

		@pptx_form = {}

		fields = []

		template_opts = []
		for tmpl in pptx_config["python-pptx"].templates or []
			if not @pptx_form.template
				@pptx_form.template = tmpl

			template_opts.push
				text: $$(@loca_key("form.template."+tmpl.name))
				value: tmpl

		# add template options
		fields.push
			form:
				label: $$(@loca_key("form.label.template"))
			type: CUI.Options
			name: "template"
			options: template_opts
			radio: true

		quality_opts = []
		for quality in pptx_config["python-pptx"].qualities or []
			if not @pptx_form.quality
				@pptx_form.quality = parseInt(quality)

			quality_opts.push
				text: $$(@loca_key("form.quality."+quality))
				value: parseInt(quality)

		fields.push
			form:
				label: $$(@loca_key("form.label.quality"))
			type: CUI.Select
			name: "quality"
			options: quality_opts

		# add hint at the end
		fields.push
			type: CUI.Output
			placeholder: $$(@loca_key("form.hint"))

		# console.debug "pptx_form", @pptx_form

		new CUI.Form
			data: @pptx_form
			fields: fields
		.start()

Presentation.registerDownloadManager(PresentationPowerpointDownloadManager)
