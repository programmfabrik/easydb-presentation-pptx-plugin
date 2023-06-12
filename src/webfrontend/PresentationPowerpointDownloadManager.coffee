class PresentationPowerpointDownloadManager extends PresentationDownloadManager

	readOpts: ->
		# map eas ids of originals to the eas id of the actually exported version
		@version_ids = {}
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
		version = Asset.getBestImageForViewport(asset, @pptx_form.quality, @pptx_form.quality)

		if not version
			[]
		else
			# for fylr it is necessary to save the id of the generated version,
			# else for easydb the id of the original can always be used instead
			_eas_id = version._id
			if not _eas_id
				_eas_id = asset.value._id
			if _eas_id
				@version_ids[asset.value._id] = _eas_id
			[ version ]

	filterDownloadableFiles: (files) ->
		for f in files
			if f.path.endsWith(".pptx")
				return [ f ]
		return []

	__enrich_slide: (s) ->
		if s.global_object_id
			if @data_by_gid[s.global_object_id]?.standard_info
				s.standard_info = {}
				for k, v of @data_by_gid[s.global_object_id].standard_info
					if not v || v == ''
						continue
					s.standard_info[k] = v

		if s.asset_id
			s.version_id = @version_ids[s.asset_id]

		return s

	getExportSaveData: ->
		data = super()
		data.export.produce_options.pptx_form = CUI.util.copyObject(@pptx_form, true)
		data.export.produce_options.plugin = "easydb-presentation-pptx-plugin:create_pptx"

		# for each slide with asset(s) add the id of the exported version
		# and add the standard info for the object
		for s in data.export.produce_options.presentation.slides
			if s.center
				s.center = @__enrich_slide(s.center)
			if s.left
				s.left = @__enrich_slide(s.left)
			if s.right
				s.right = @__enrich_slide(s.right)

		# data by gid is not needed since the slide structure was simplified
		delete(data.export.produce_options.presentation.data_by_gid)

		delete(data.export.produce_options.pptx_form._undo)
		# console.debug "export save data:", CUI.util.dump(data)
		data

	getContent: ->
		pptx_config = ez5.pluginManager.getPlugin("easydb-presentation-pptx-plugin").getOpts()
		# console.debug @__cls, "getContent", pptx_config

		@pptx_form = {}

		fields = []

		template_opts = []
		for tmpl in pptx_config["custom"]?.templates or []
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
		for quality in pptx_config["custom"]?.qualities or []
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
