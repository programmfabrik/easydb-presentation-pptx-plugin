// Generated by CoffeeScript 1.12.8
var PresentationPowerpointDownloadManager,
  extend = function(child, parent) { for (var key in parent) { if (hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; },
  hasProp = {}.hasOwnProperty;

PresentationPowerpointDownloadManager = (function(superClass) {
  extend(PresentationPowerpointDownloadManager, superClass);

  function PresentationPowerpointDownloadManager() {
    return PresentationPowerpointDownloadManager.__super__.constructor.apply(this, arguments);
  }

  PresentationPowerpointDownloadManager.prototype.readOpts = function() {
    return PresentationPowerpointDownloadManager.__super__.readOpts.call(this);
  };

  PresentationPowerpointDownloadManager.prototype.loca_key = function(key) {
    return CUI.util.toDot(this.__cls) + "." + key;
  };

  PresentationPowerpointDownloadManager.prototype.getMenuButton = function() {
    return {
      loca_key: this.loca_key("button.menu"),
      onClick: (function(_this) {
        return function() {
          return _this.startExport();
        };
      })(this)
    };
  };

  PresentationPowerpointDownloadManager.prototype.getTitle = function() {
    return $$(this.loca_key("dialog.title"));
  };

  PresentationPowerpointDownloadManager.prototype.getAssetVersionsToExport = function(asset, gid) {
    var base, version;
    if (typeof (base = this.data_by_gid)[gid] === "function" ? base[gid](asset_ids.length >= 1) : void 0) {
      return;
    }
    version = Asset.getBestImageForViewport(asset, this.pptx_form.quality, this.pptx_form.quality);
    if (!version) {
      return [];
    } else {
      return [version];
    }
  };

  PresentationPowerpointDownloadManager.prototype.filterDownloadableFiles = function(files) {
    var f, i, len;
    for (i = 0, len = files.length; i < len; i++) {
      f = files[i];
      if (f.path.endsWith(".pptx")) {
        return [f];
      }
    }
    return [];
  };

  PresentationPowerpointDownloadManager.prototype.getExportSaveData = function() {
    var data;
    data = PresentationPowerpointDownloadManager.__super__.getExportSaveData.call(this);
    data["export"].produce_options.pptx_form = CUI.util.copyObject(this.pptx_form, true);
    data["export"].produce_options.plugin = "presentation-pptx:create_pptx";
    delete data["export"].produce_options.pptx_form._undo;
    return data;
  };

  PresentationPowerpointDownloadManager.prototype.getContent = function() {
    var fields, i, j, len, len1, pptx_config, quality, quality_opts, ref, ref1, template_opts, tmpl;
    pptx_config = ez5.pluginManager.getPlugin("presentation-pptx").getOpts();
    this.pptx_form = {};
    fields = [];
    template_opts = [];
    ref = pptx_config["custom"].templates || [];
    for (i = 0, len = ref.length; i < len; i++) {
      tmpl = ref[i];
      if (!this.pptx_form.template) {
        this.pptx_form.template = tmpl;
      }
      template_opts.push({
        text: $$(this.loca_key("form.template." + tmpl.name)),
        value: tmpl
      });
    }
    fields.push({
      form: {
        label: $$(this.loca_key("form.label.template"))
      },
      type: CUI.Options,
      name: "template",
      options: template_opts,
      radio: true
    });
    quality_opts = [];
    ref1 = pptx_config["custom"].qualities || [];
    for (j = 0, len1 = ref1.length; j < len1; j++) {
      quality = ref1[j];
      if (!this.pptx_form.quality) {
        this.pptx_form.quality = parseInt(quality);
      }
      quality_opts.push({
        text: $$(this.loca_key("form.quality." + quality)),
        value: parseInt(quality)
      });
    }
    fields.push({
      form: {
        label: $$(this.loca_key("form.label.quality"))
      },
      type: CUI.Select,
      name: "quality",
      options: quality_opts
    });
    fields.push({
      type: CUI.Output,
      placeholder: $$(this.loca_key("form.hint"))
    });
    return new CUI.Form({
      data: this.pptx_form,
      fields: fields
    }).start();
  };

  return PresentationPowerpointDownloadManager;

})(PresentationDownloadManager);

Presentation.registerDownloadManager(PresentationPowerpointDownloadManager);
