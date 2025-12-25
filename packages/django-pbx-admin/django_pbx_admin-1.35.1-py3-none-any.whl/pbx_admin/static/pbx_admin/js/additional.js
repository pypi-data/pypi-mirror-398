// if embedded inside iframe, send height to properly handle window resize
(function () {
    if (window.self !== window.top) {
        // remove Main tab name if admin is embedded in Presta
        $('ol#breadcrumbs li:first').remove();
        // do not show list in breadcrumbs for product family
        // Presta already shows product family list in menu
        if (window.location.href.match(/(productfamily|editormodule|editortranslation)\//)) {
            $('ol#breadcrumbs li:first').remove();
        }
        window.addEventListener('message', handleWidthChange, false);

        $(function () {
            $('body').css('background-color', 'transparent').css('overflow-y', 'hidden');
            $('#content').addClass('clearfix');
        });

        $('#instance-messages').remove();

        function handleWidthChange(event) {
            var height = $('#content').outerHeight();

            parent.postMessage({
                scrollHeight: height
            }, '*');
        }
    }
})($);

/////////////////////////////////////////////////////////////////////////////////////////
// Uploaded image manipulation

function _base64ToArrayBuffer(base64Data) {
  // Convert dataUrl to array buffer 
  var binary_string = window.atob(base64Data);
  var len = binary_string.length;
  var bytes = new Uint8Array(len);
  for (var i = 0; i < len; i++) {
      bytes[i] = binary_string.charCodeAt(i);
  }
  return bytes.buffer;
}

function _getChromeVersion () {
    var raw = navigator.userAgent.match(/Chrom(e|ium)\/([0-9]+)\./);
    return raw ? parseInt(raw[2], 10) : false;
}

function getOrientation(dataUrl, callback) {
  // Find orientation of image in dataUrl
  let splits = dataUrl.split(',', 2);
  let base64Str = splits[1];
  let arrayBuffer = _base64ToArrayBuffer(base64Str);
  let view = new DataView(arrayBuffer);
  if (view.getUint16(0, false) != 0xFFD8) {
      return -2;
  }
  var length = view.byteLength, offset = 2;
  while (offset < length) {
      if (view.getUint16(offset+2, false) <= 8) return callback(-1);
      var marker = view.getUint16(offset, false);
      offset += 2;
      if (marker == 0xFFE1) {
          if (view.getUint32(offset += 2, false) != 0x45786966) {
              return -1;
          }

          var little = view.getUint16(offset += 6, false) == 0x4949;
          offset += view.getUint32(offset + 4, little);
          var tags = view.getUint16(offset, little);
          offset += 2;
          for (var i = 0; i < tags; i++) {
              if (view.getUint16(offset + (i * 12), little) == 0x0112) {
                  return view.getUint16(offset + (i * 12) + 8, little);
              }
          }
      }
      else if ((marker & 0xFF00) != 0xFF00) {
          break;
      }
      else {
          offset += view.getUint16(offset, false);
      }
  }
  return -1;
}

function resetOrientation(srcBase64, srcOrientation, callback) {
  // Create correctly oriented dataUrl and pass it to callback
  let img = new Image();

  img.onload = function() {
    var width = img.width,
        height = img.height,
        canvas = document.createElement('canvas'),
        ctx = canvas.getContext("2d");

    // set proper canvas dimensions before transform & export
    if (4 < srcOrientation && srcOrientation < 9) {
      canvas.width = height;
      canvas.height = width;
    } else {
      canvas.width = width;
      canvas.height = height;
    }

    // transform context before drawing image
    switch (srcOrientation) {
      case 2: ctx.transform(-1, 0, 0, 1, width, 0); break;
      case 3: ctx.transform(-1, 0, 0, -1, width, height); break;
      case 4: ctx.transform(1, 0, 0, -1, 0, height); break;
      case 5: ctx.transform(0, 1, 1, 0, 0, 0); break;
      case 6: ctx.transform(0, 1, -1, 0, height, 0); break;
      case 7: ctx.transform(0, -1, -1, 0, height, width); break;
      case 8: ctx.transform(0, -1, 1, 0, 0, width); break;
      default: break;
    }

    // draw image
    ctx.drawImage(img, 0, 0);

    // export base64
    callback(canvas.toDataURL());
  };

  img.src = srcBase64;
};

/////////////////////////////////////////////////////////////////////////////////////////

$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();
});
//menu tabs
$(document).ready(function () {
    if ($('#js-tabs').length) {
        var iniitTab = $(".active").attr("href");
        $(iniitTab).fadeIn();

        $("#js-tabs a").click(function (event) {
            event.preventDefault();
            var $this = $(this);
            $this.addClass("active");
            $this.siblings().removeClass("active");
            var tab = $this.attr("href");
            $(".tab-menu-content").not(tab).css("display", "none");
            $(tab).fadeIn();
            // Modify url if available
            if (window.history.replaceState) {
                window.history.replaceState({}, '', $this.attr("data-url"));
            }

            // Modify breadcrumbs
            var breadcrumbs = $('.breadcrumb');
            $('li.dynamic', breadcrumbs).remove();
            $('<li />').addClass('dynamic').html('<a href="' + $this.attr('data-url') + '">' + $this.html().toUpperCase() + '</a>').appendTo(breadcrumbs);
        });
    }
});

function handleThemeThumb(obj) {
  // Handle themes thumbnails that aren't loading
  var spinner_data = 'data:image/png;base64,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';
  var api_url = '/api/v1.4/themes/generate-thumb/';
  var hash = $(obj).attr('data-hash');
  var img_url = $(obj).attr('src');

  $(obj).attr('data-src', img_url);
  $(obj).attr('src', spinner_data);

  console.log('Requesting new thumbnail for theme ' + hash);
  $.ajax({
    url: api_url,
    data: JSON.stringify({ 'theme_hash': hash }),
    dataType: 'json',
    contentType: 'application/json',
    type: 'post'
  });

  var interval = setInterval(
    function() {
      thumbChecker(img_url);
    },
    5000
  );

  function thumbChecker(url) {
    $.ajax({
      url: url,
      type: 'GET',
      success: function() {
        $(obj).attr('src', url);
        clearInterval(interval);
      }
    });
  }
}

function bindImageInputs() {
  $('body').on('click', '[data-action="upload-image"]', function(event) {
    event.preventDefault();
    var $this = $(this),
      $removeBtn = $this.closest('form').find('[data-action="remove-image"]');
    $($this.attr('href')).click();
    $removeBtn.show();
  });

  //delete img
  $('body').on('click', '[data-action="remove-image"]', function(event) {
    event.preventDefault();
    var $this = $(this),
      //$img = $($this.attr('data-target')),
      $img = $this.prev().prev().find('img'),
      $label = $($this.attr('data-label')),
      $input = $this.next().find('input'),
      $to_delete = $this.closest('form').find('[name="' + $this.attr('data-target') + '"]');
    $to_delete.val('true');
    $img.attr('src', $img.attr('data-default'));
    $label.text($label.attr('data-default'));
//    $input.attr('value', 'removed');
    $this.hide();
  });

  //input upload img
  $('body').on('change', 'input[type="file"]', function(event) {
    event.preventDefault();
    var reader = new FileReader();

    reader.onload = function (e) {
      var img = $(this).parent().find('img');

      // Callback to be called from function changing orientation of image
      function setSrc(base64Image) {
          this.src = base64Image;
      }
      let srcCallback = setSrc.bind(img.get(0));

      let chromeVersion = _getChromeVersion();

      if (!chromeVersion || chromeVersion < 81) {
          resetOrientation(e.target.result, getOrientation(e.target.result, srcCallback), srcCallback);
      }
      else {
          img.attr('src', e.target.result);
      }

      img.not('.set-no-sizes')
         .css('max-width','300px')
         .css('max-height', '300px');
      $(this).parent().find('img.set-no-sizes').closest('div')
        .addClass('selected-image');
      $(this).parent().find('.btn-download').hide();
      img = img.get(0);
      img.onload = function() {
        $(this).data('width', this.naturalWidth);
        $(this).data('height', this.naturalHeight);
        $(this).closest('.image-input').find('.image-size').html(this.naturalWidth + 'x' + this.naturalHeight + 'px');
      };
    }.bind(this);

    reader.readAsDataURL(this.files[0]);
    var val = $(this).val().split('\\'),
      filename = val[val.length - 1];
    $(this).parent().find('[data-content="label"]').html(filename);
  });
}


$(function() {
    bindImageInputs();

  $('[data-action="alert-confirm"]').click(function(event) {
    event.preventDefault();
    var $this = $(this),
      result = confirm($this.attr('data-title'));
    if (result) {
      $this.parent().find('[type="submit"]').click();
    }
  });

  $('input[name$="spine_type"]').change(function() {
    var $this = $(this),
      $info = $this.closest('.tab-pane').find('[data-toggle="spine_type"]');
    if ($this.val() == 'dynamic') {
      $info.css('visibility', 'visible');
    } else {
      $info.css('visibility', 'hidden');
    }
  });

  $('input[type="radio"][readonly]').click(function(event) {
    event.preventDefault();
    return false;
  });

  function bindCustomBookShadows() {
    var $customBookShadowsInput = $('input[name$="custom_book_shadows"]');

    function toggleCustomBookShadows() {
      if ($customBookShadowsInput.prop('checked')) {
        $('.field-spine').show();
        $('.field-spread_shadow').show();
        $('.field-half_page_shadow').show();
      } else {
        $('.field-spine').hide();
        $('.field-spread_shadow').hide();
        $('.field-half_page_shadow').hide();
      }
    }

    $customBookShadowsInput.change(function () {
      toggleCustomBookShadows();
    });

    if ($customBookShadowsInput) {
      toggleCustomBookShadows();
    }
  }
  bindCustomBookShadows();

  function bindDatatableForm($bulkActions) {
    var $table = $('#content-main .tableDnD');
    var $submitForm = $bulkActions.find('#bulk-action-submit-form');
    var $selectedVisibleMessage = $('#selected-visible');
    var $selectedAllMessage = $('#selected-all');

    $table.find('input[type="checkbox"]').change(function() {
      $table.find('input[name="everything-selected"]').val('');
      $selectedVisibleMessage.addClass('hidden');
      $selectedAllMessage.addClass('hidden');
    });

    $bulkActions.on('click', '[data-action="select-all"]', function(event) {
      event.preventDefault();
      $table.find('input[type="checkbox"]').prop('checked', true);
      $table.find('input[name="everything-selected"]').val('').trigger('change');
      $selectedVisibleMessage.removeClass('hidden');
      $selectedAllMessage.addClass('hidden');
    });

    $bulkActions.on('click', '[data-action="select-all-all"]', function(event) {
      event.preventDefault();
      $table.find('input[type="checkbox"]').prop('checked', true);
      $table.find('input[name="everything-selected"]').val(true).trigger('change');
      $selectedVisibleMessage.addClass('hidden');
      $selectedAllMessage.removeClass('hidden');
    });

    $bulkActions.on('click', '[data-action="unselect-all"]', function(event) {
      event.preventDefault();
      $table.find('input[type="checkbox"]').prop('checked', false);
      $table.find('input[name="everything-selected"]').val('').trigger('change');
      $selectedVisibleMessage.addClass('hidden');
      $selectedAllMessage.addClass('hidden');
    });

    $bulkActions.on('click', '[data-action="link-submit"]', function(event) {
      event.preventDefault();
      if ($table.find('input[name="everything-selected"]').val()) {
        $submitForm.find('input[name="ids"]').val('all');
        $submitForm.find('input[name="search_params"]').val(location.search);
      } else {
        var ids = [];
        $table.find('input[type="checkbox"]:checked').each(function() {
          ids.push($(this).val());
        });
        $submitForm.find('input[name="ids"]').val(ids.join(','));
      }
      $submitForm.attr('action', $(this).attr('href'));
      $submitForm.submit();
    });

    $bulkActions.on('click', '[data-action="link-query-params"]', function() {
      $(this).attr('href', function(i, href) {
        if ($table.find('input[name="everything-selected"]').val()) {
          return href + '?ids=all';
        } else {
          var ids = [];
          $table.find('input[type="checkbox"]:checked').each(function() {
            ids.push($(this).val());
          });
          if (ids) {
            return href + '?ids=' + ids.join(',');
          }
          return '';
        }
      })
    });

    $bulkActions.on('click', 'button[data-target="selected-items"]', function() {
      var ids = [];
      $table.find('input[type="checkbox"]:checked').each(function() {
        ids.push($(this).val('data-id'));
      });
      $(this).val(ids.join(','));
    });

    $bulkActions.on('click', '[data-action="bulk-action-selected-items"]', function() {
      var ids = [];
      $table.find('input[type="checkbox"]:checked').each(function() {
        ids.push($(this).val());
      });
      $(this).attr('href', this.href + '?id=' + ids.join(','));
    });

    $bulkActions.on('click', 'tr>td[data-url]', function(event) {
      var url = $(this).attr('data-url');
      if (event.which == 2) {
        window.open(url);
      } else {
        window.location = url;
      }
    });
  }
  bindDatatableForm($('.bulk-actions'));

  // Drag & drop for assigned themes in products types
  if ($('table.assigned-themes').length > 0) {
    try {
      $('table.assigned-themes tbody').sortable().on('drop',
        function() {
          // Save ordering of themes
          var theme_ids = $('table.assigned-themes tr td:last-child input:last-child')
            .map(function() {
              return $(this).attr('value');
            }).get();
          $('#id_themes_order').attr('value', theme_ids);
        }
      );
    }
    catch(err) {
      console.log('ERROR: ' + err);
    }
  }

});


// Prices calculation in product family main tab

function recompute_gross() {
    var tax_rate = parseFloat($('#form_productfamily #' + this.id.replace('value', 'tax_rate')).val());
    var tgt = $('#form_productfamily #' + this.id + '_gross');
    tgt.off('change');
    var $this = $(this);
    var gross_val = parseFloat($this.val()) + tax_rate*parseFloat($this.val());
    tgt.val(gross_val.toFixed(6));
    tgt.change(recompute_net);
}
function recompute_net() {
    var tax_rate = parseFloat($('#form_productfamily #' + this.id.replace('value_gross', 'tax_rate')).val());
    var tgt = $('#form_productfamily #' + this.id.replace('_gross', ''));
    tgt.off('change');
    var net_val = parseFloat($(this).val())/(1 + tax_rate);
    tgt.val(net_val.toFixed(6));
    tgt.change(recompute_gross);
}
function set_tax_rate() {
    var base = this.id.replace('-tax_rule', '');
    var new_tax_id = $(this).val();
    $('#form_productfamily #' + base + '-tax_rate').val(pbx_tax_rates[parseInt(new_tax_id)]);
    $('#form_productfamily #' + base + '-value').trigger('change');
}
$('#form_productfamily input[id$="value"]').change(recompute_gross);
$('#form_productfamily input[id$="value_gross"]').change(recompute_net);
$('#form_productfamily select[id$="tax_rule"]').change(set_tax_rate);

function attr_val_recompute_gross() {
    var tax_rate = parseFloat($('#form_attributevalue #' + this.id.replace('value', 'tax_rate')).val());
    var tgt = $('#form_attributevalue #' + this.id + '_gross');
    tgt.off('change');
    var $this = $(this);
    var gross_val = parseFloat($this.val()) + tax_rate*parseFloat($this.val());
    tgt.val(gross_val.toFixed(6));
    tgt.change(attr_val_recompute_net);
}
function attr_val_recompute_net() {
    var tax_rate = parseFloat($('#form_attributevalue #' + this.id.replace('value_gross', 'tax_rate')).val());
    var tgt = $('#form_attributevalue #' + this.id.replace('_gross', ''));
    tgt.off('change');
    var net_val = parseFloat($(this).val())/(1 + tax_rate);
    tgt.val(net_val.toFixed(6));
    tgt.change(attr_val_recompute_gross);
}
$('#form_attributevalue input[id$="value"]').change(attr_val_recompute_gross);
$('#form_attributevalue input[id$="value_gross"]').change(attr_val_recompute_net);
$('#form_attributevalue input[id$="value_net"]').trigger('change');

function pages_settings_recompute_gross() {
    var tax_rate = parseFloat($(this).attr('data-tax'));
    var tgt = $('#form_pagessettings #' + this.id.replace('-value', '-value_gross'));
    tgt.off('change');
    var $this = $(this);
    var gross_val = parseFloat($this.val()) + parseFloat(tax_rate)*parseFloat($this.val());
    tgt.val(gross_val.toFixed(6));
    tgt.change(pages_settings_recompute_net);
}
function pages_settings_recompute_net() {
    var tax_rate = parseFloat($('#form_pagessettings #' + this.id.replace('-value_gross', '-value')).attr('data-tax'));
    var tgt = $('#form_pagessettings #' + this.id.replace('-value_gross', '-value'));
    tgt.off('change');
    var net_val = parseFloat($(this).val())/(1 + parseFloat(tax_rate));
    tgt.val(net_val.toFixed(6));
    tgt.change(pages_settings_recompute_gross);
}
$('#form_pagessettings input[id$="-value"]').change(pages_settings_recompute_gross);
$('#form_pagessettings input[id$="-value_gross"]').change(pages_settings_recompute_net);
$('#form_pagessettings input[id$="-value"]').trigger('change');

function attrs_combinations_recompute_gross() {
//    var tax_rate = parseFloat($('#form_prices #' + this.id.replace('-value', '-tax_rate')).val());
    var tax_rate = $('#current-tax-rate').html();
    var tgt = $('#form_prices #' + this.id.replace('-value', '-value_gross'));
    tgt.off('change');
    var $this = $(this);
    var gross_val = parseFloat($this.val()) + parseFloat(tax_rate)*parseFloat($this.val());
    tgt.val(gross_val.toFixed(6));
    tgt.change(attrs_combinations_recompute_net);
}
function attrs_combinations_recompute_net() {
//    var tax_rate = parseFloat($('#form_prices #' + this.id.replace('-value_gross', '-tax_rate')).val());
    var tax_rate = $('#current-tax-rate').html();
    var tgt = $('#form_prices #' + this.id.replace('-value_gross', '-value'));
    tgt.off('change');
    var net_val = parseFloat($(this).val())/(1 + parseFloat(tax_rate));
    tgt.val(net_val.toFixed(6));
    tgt.change(attrs_combinations_recompute_gross);
}
$('#form_prices input[id$="-value"]').change(attrs_combinations_recompute_gross);
$('#form_prices input[id$="-value_gross"]').change(attrs_combinations_recompute_net);
//$('#form_prices input[id$="-value"]').trigger('change');

var AFValueDirty = false;
function add_field_sel(inner_sel) {
    return '#form_attributeadditionalfield ' + inner_sel + ', #form_productfamilyadditionalfield ' + inner_sel;
}
function reload_with_new_type() {
    var type = $(this).val(),
      name = $(this).closest('fieldset').find('input[name=name]').val();
    var url = window.location.href.split('?')[0];

    if (AFValueDirty) {
      if (!window.confirm('Are you sure? Value changes will be lost if you don`t save')) {
        $(this).val($.data(this, 'current'));
        return false;
      }
    }

    $.data(this, 'current', $(this).val());
    window.location = url + '?value_type=' + type + '&name=' + name;
}
if ($('#form_attributeadditionalfield, #form_productfamilyadditionalfield').length > 0) {
    var type_sel = $(add_field_sel('#id_type'));
    type_sel.data('current', type_sel.val());
    type_sel.change(reload_with_new_type);
    $(add_field_sel('[name^=value]')).change(function() {
      AFValueDirty = true;
    });
}

// Translated fields hiding and showing
function activate_translated_fields() {
  $('input[id*=translated]').change(function() {
    var $this = $(this);
    var shinar_wrapper = $this.closest('[data-type=shinar]');
    var default_field = shinar_wrapper.find('[data-type=shinar-input]').first();
    var default_field_label = default_field.find('label span');
    var lang_fields = shinar_wrapper.find('[data-type=shinar-input]');
    if ($this.prop('checked')) {
      lang_fields.removeClass('hidden');
      default_field_label.removeClass('hidden');
    }
    else {
      lang_fields.not('.hidden').addClass('hidden');
      default_field.removeClass('hidden');
      default_field_label.addClass('hidden');
    }
  });
  $('input[id*=translated]').trigger('change');
}

activate_translated_fields();

// Advanced_values in workspace page form
$('input[id$=advanced_values]').change(function() {
    var $this = $(this);
    var fieldset = $this.parents('fieldset.formset').get(0);
    if ($this.prop('checked')) {
        $('.advanced', fieldset).removeClass('hidden')
        $('div[id$=safe_width].form-group', fieldset).not('.hidden').addClass('hidden')
        $('div[id$=snap_width].form-group', fieldset).not('.hidden').addClass('hidden')
        $('div[id$=edge_width].form-group', fieldset).not('.hidden').addClass('hidden')
    }
    else {
        $('.advanced', fieldset).not('.hidden').addClass('hidden')
        $('div[id$=safe_width].form-group', fieldset).removeClass('hidden')
        $('div[id$=snap_width].form-group', fieldset).removeClass('hidden')
        $('div[id$=edge_width].form-group', fieldset).removeClass('hidden')
    }
});
$('input[id$=advanced_values]').trigger('change');

// Mediabox settings
function set_mediabox_fields(radio) {
    if (radio.prop('checked')) {
        var $fields = radio.closest('fieldset').find('input[name$=mediabox_width],input[name$=mediabox_height],select[name$=_align]');
        if (radio.val() == 'bleedbox') {
            $fields.closest('.form-group').not('.hidden').addClass('hidden');
        }
        else {
            $fields.closest('.form-group').removeClass('hidden');
        }
    }
}
$('input[name$=mediabox]').each(function(i, obj) {
    set_mediabox_fields($(obj));
});
$('input[name$=mediabox]').change(function() {
    set_mediabox_fields($(this));
});

// Cut markers workspace page form
function set_crop_marks() {
    const inputsToHide =
        this.closest("fieldset")
            .querySelectorAll("input[name$=crop_mark_length],input[name$=crop_mark_space]");

    inputsToHide.forEach(node => {
        node.closest(".form-group").hidden = !this.checked;
    });
}

document.querySelectorAll("input[name$=render_crop_marks]").forEach(node => {
    node.onchange = set_crop_marks;
    set_crop_marks.bind(node)();
});

function set_render_bleedbox_markers() {
    const renderBleedboxMarkersFormGroup =
        this.closest("fieldset")
            .querySelector("input[name$=render_bleedbox_marks]")
            .closest(".form-group");

    const isBiggerThanBleedboxChecked = this.value === "bigger" && this.checked;
    renderBleedboxMarkersFormGroup.hidden = !isBiggerThanBleedboxChecked;
}

document.querySelectorAll("input[name$=mediabox]").forEach(node => {
    set_render_bleedbox_markers.bind(node)();
    node.onchange = set_render_bleedbox_markers;
});


// SKU in attribute values
let skuBlank = document.getElementById("id_sku_blank")

if (skuBlank){
    changeSkuAvailability.bind(skuBlank)()
    skuBlank.addEventListener('change', changeSkuAvailability);
}

function changeSkuAvailability(){
    let skuSnippet = document.getElementById("id_sku_snippet")
    skuSnippet.disabled = this.checked;
}

// Lock content workspace page form
function set_lock_content_fields(radio) {
    if (radio.prop('checked')) {
        var $fieldset = radio.closest('fieldset');
        var $fields = $fieldset.find('select[data-is-lockable]');
        if (radio.val() == 'locked') {
            $fields.closest('.form-group').removeClass('hidden');
        }
        else {
            $fields.closest('.form-group').not('.hidden').addClass('hidden');
        }
    }
}
$('input[name$=lock_content]').each(function(i, obj) {
    set_lock_content_fields($(obj));
});
$('input[name$=lock_content]').change(function() {
    set_lock_content_fields($(this));
});

$('select[id$=output_type]').change(function() {
    var $this = $(this);
    if ($this.val() == 'one_pdf') {
        $('select[id$=output_type]').val('one_pdf')
    } else {
        $.each($('select[id$=output_type]'), function(idx, sel) {
          if ($(sel).val() == 'one_pdf') {
            $('option[value=""]', sel).attr('selected', true);
          }
        });
    }
});

$(function () {
    var $workspaceContent = $('#workspace-content'),
        $workspaceForm = $('#form_workspace, #form_coverworkspace, #form_blockworkspace, #form_projectvisualization');

    function bindDynamicPages() {
        $workspaceContent.on('click', '[data-action="add-page"]', function (event) {
            event.preventDefault();
            var $tabs = $workspaceContent.find('.nav-tabs li');
            var $hidden_tabs = $workspaceContent.find('.nav-tabs li.hidden');
            var $new_tab = $hidden_tabs.first();
            $new_tab.removeClass('hidden');
            var newTabHref = $('a', $new_tab).attr('href');
            $('[href=' + newTabHref + ']', $workspaceContent)[0].click();
            $('input[name$="DELETE"]', $(newTabHref)).prop('checked', false);
        });

        $workspaceContent.on('click', '[data-action="delete-page"]', function (event) {
            event.preventDefault();
            var $tabs = $workspaceContent.find('.nav-tabs li');
            var $tab = $(this).parent();
            var $tabContent = $($tab.find('a').attr('href'));
            $tab.addClass('hidden');
            // clear names fields
            $('input[name$="-name"]', $tabContent).val('');
            $('input[name$="_name"]', $tabContent).val('');
            $('input[name$="DELETE"]', $tabContent).prop('checked', true);
            $tabs.removeClass('active').first().removeClass('hidden').find('a').tab('show');
        });

        $workspaceForm.on('keyup', '#id_name', function (event) {
            var visible_tabs = $('.nav-tabs li', $workspaceContent).not('.hidden');
            if (visible_tabs.length == 2) {
                $(visible_tabs.first().find('a').attr('href') + ' input[id$=-name]').val($(this).val());
            }
        });

        $workspaceForm.submit(function() {
            // Move name from workspace to wpage if there is only one page visible
            var visible_tabs = $('.nav-tabs li', $workspaceContent).not('.hidden');
            if (visible_tabs.length == 2) {
                $(visible_tabs.first().find('a').attr('href') + ' input[id$=-name]').val($('#id_name', $workspaceForm).val());
            }
        });

        $('input', $workspaceForm).on('invalid', function(e) {
            let input = $(this);
            let tab_content = input.closest('.tab-pane')
            let tab = $('[href=#' + tab_content.attr('id') + ']');
            tab.tab('show');
        })
    }

    if ($workspaceContent.attr('data-dynamic-pages')) {
        bindDynamicPages();
    }
});

$(function () {
    var $skinForm = $('#form_skin'),
        $skinDesignForm = $('#form_skindesign'),
        $visualizationForm = $('#form_projectvisualization');

    function recomputeHeight() {
        var $this = $(this);
        if (!$this.closest('.layer-form').find('input[id$=-slide_keep_ratio]').is(':checked')) {
            return
        }
        var ratio = parseFloat($this.closest('.layer-formset').data('ratio'));
        var tgt = $('#' + this.id.replace('width', 'height'), $skinDesignForm);
        tgt.off('change');
        var new_height = parseFloat($this.val() / ratio);
        tgt.val(new_height.toFixed());
        tgt.change(recomputeWidth);
    }
    function recomputeWidth() {
        var $this = $(this);
        if (!$this.closest('.layer-form').find('input[id$=-slide_keep_ratio]').is(':checked')) {
            return
        }
        var ratio = parseFloat($this.closest('.layer-formset').data('ratio'));
        var tgt = $('#' + this.id.replace('height', 'width'), $skinDesignForm);
        tgt.off('change');
        var new_width = parseFloat($this.val() * ratio);
        tgt.val(new_width.toFixed());
        tgt.change(recomputeHeight);
    }

    function initSkinLayerForm($form) {
        // init recompute width & height
        $('input[id$=-slide_width]', $form).change(recomputeHeight);
        $('input[id$=-slide_height]', $form).change(recomputeWidth);

        // init label with image size in slide to scale layer section
        var $imageInput = $('.image-input', $form);
        var $imageSize = $('.image-size', $imageInput);
        function copyImageSize() {
            if ($imageSize.html()) {
                $('.image-size-copy', $form).html($imageSize.html());
            }
        }
        $imageSize.bind("DOMNodeInserted DOMSubtreeModified", copyImageSize);
        copyImageSize();

        // copy edge input value to label
        $.each($('[data-action="html-from-input"]', $form), function() {
            var $this = $(this);
            var $input = $('#' + $this.data('id'));
            $input.change(function() {
                $this.html($input.val());
            });
        });

        // calculate slide percentage
        var $offsetX = $('[name$="offset_x"]', $form);
        var $offsetY = $('[name$="offset_y"]', $form);
        var $slideWidth = $('[name$="slide_width"]', $form);
        var $slideHeight = $('[name$="slide_height"]', $form);
        function calculateSlidePercentage() {
            var imgWidth = $('img', $form).data('width');
            var imgHeight = $('img', $form).data('height');
            if (imgWidth && imgHeight) {
                var imgArea = imgWidth * imgHeight;
                var slideWidth = Math.min(imgWidth - $offsetX.val(), $slideWidth.val());
                var slideHeight = Math.min(imgHeight - $offsetY.val(), $slideHeight.val());
                var slideArea = slideWidth * slideHeight;
                var percentage = Math.max(Math.min(slideArea / imgArea * 100, 100), 0);
                $('[data-id="slide-percentage"]', $form).html(Math.round(percentage));
            }
        }
        var inputs = [$offsetX, $offsetY, $slideWidth, $slideHeight];
        for (var i in inputs) {
            inputs[i].change(calculateSlidePercentage);
        }
        $imageSize.bind("DOMSubtreeModified", calculateSlidePercentage);
        calculateSlidePercentage();

        // set initial slide width on first image upload
        // when slide width is set to 0
        $imageSize.bind("DOMSubtreeModified", function() {
            if ($slideWidth.val() == '0') {
                var imgWidth = $('img', $form).data('width');
                $slideWidth.val(imgWidth);
                $slideWidth.trigger('change');
            }
        });
    }

    function removeFormClick(e) {
        e.preventDefault();
        var href = $(this).attr('href');
        var $input = $(href);
        $input.prop('checked', true);
        $(this).closest('.layer-form').hide();
    }

    function initFormButtons() {
        $('a[data-action="add-empty-layer-form"]').click(function(e) {
            e.preventDefault();
            var href = $(this).attr('href');
            var $form = $(href).clone();
            $form.removeAttr('id');
            $form.addClass('layer-form');
            var $totalForms = $(this).closest('.layer-formset').find('input[name$="TOTAL_FORMS"]');
            var total = parseInt($totalForms.val());
            $totalForms.val(total + 1);
            $form.html(function(i, oldHTML) {
                return oldHTML.replace(/__prefix__/g, total);
            });
            $(this).closest('.layer-formset').find('.layer-forms').append($form);
            $('a[data-action="remove-layer-form"]', $form).click(removeFormClick);
            initSkinLayerForm($form);
            $form.show();
        });
        $('a[data-action="remove-layer-form"]').click(removeFormClick);
    }

    if ($skinForm || $skinDesignForm || $visualizationForm) {
        initFormButtons();
    }
    if ($skinDesignForm) {
        $('.layer-form', $skinDesignForm).each(function() {initSkinLayerForm($(this))});
    }

    $('input', $skinDesignForm).on('invalid', function(e) {
        let input = $(this);
        let tab_content = input.closest('.tab-pane')
        let tab = $('[href=#' + tab_content.attr('id') + ']');
        tab.tab('show');
    })
});


$(function () {
    var $modal = $('#confirm-modal'),
        counter = 1,
        limit = 1;

    const $everythingSelectedInput = $('input[name="everything-selected"], input.action-select[type=checkbox]')
    if ($everythingSelectedInput.length) {
      $everythingSelectedInput.on('change', updateSelectedItemsCount);
      updateSelectedItemsCount();
    }

    function updateSelectedItemsCount() {
      const count = getSelectedItemsCount();
      const span = document.getElementById('selectedItemsCount');
      if (span) {
        span.innerText = count;
      }
    }

    function initialBinding() {
        $('.modal-confirm-click').click(modalConfirm);
    }

    function modalConfirm(e) {
        e.preventDefault();
        e.stopPropagation();
        var $this = $(this);
        var $input = $modal.find('#modal-input').not('.hidden');

        var selector = $this.attr('data-multiple-selector');
        if ((selector && $(selector).length > 0) || !selector) {
            counter = 1;
            $('.confirm-btn', $modal).not('.confirm-again').not('.hidden').addClass('hidden');
            var new_limit = $this.attr('data-modal-number');
            if (new_limit) {
                limit = parseInt(new_limit);
            }
            if (counter < limit) {
                $('.confirm-again', $modal).removeClass('hidden');
                $('.modal-footer input', $modal).not('.hidden').addClass('hidden');
            }
            $('.modal-footer form', $modal).attr('action', $this.attr('href'));
            $('[data-dismiss=modal]', $modal).click(function(e) {
                if ($(this).hasClass('confirm-again')) {
                    if (getSelectedItemsCount() === parseInt($input.val(), 10)) {
                      counter++
                    }
                    $input.val('');
                    $modal.off('hidden.bs.modal');
                    $modal.on('hidden.bs.modal', function() {
                        setTimeout(function() {iterateConfirm($this);}, 300);
                    });
                }
                else {
                    $modal.off('hidden.bs.modal');
                    if ($this.attr('data-click-after') && $(e.target).attr('data-next-action') == 'submit') {
                      $($this.attr('data-click-after')).trigger('click');
                    }
                }
            });
            $modal.modal({'show': false});
            iterateConfirm($this);
        }
        else {
            alert('Select something to use this action');
        }
    }

    function iterateConfirm($this) {
        var selectedItems = getSelectedItemsCount();
        var title = $this.attr('data-modal-title-' + counter);
        if (title) {
            title = title.replace('[[selectedItems]]', selectedItems);
            $('.modal-title', $modal).html(title);
        }
        var body = $this.attr('data-modal-body-' + counter);
        if (body) {
            body = body.replace('[[selectedItems]]', selectedItems);
            $('.modal-body p', $modal).html(body);
        }
        var cancelMsg = $this.attr('data-modal-cancel-msg-' + counter);
        if (cancelMsg) {
            $('.modal-footer .cancel-btn', $modal).html(cancelMsg);
        }
        var confirmMsgHide = $this.is('[data-modal-confirm-msg-hide-' + counter +']');
        if (confirmMsgHide) {
          $('.modal-footer button.confirm-btn.confirm-again', $modal).addClass('hidden');
        }
        var confirmMsg = $this.attr('data-modal-confirm-msg-' + counter);
        if (confirmMsg) {
            confirmMsg = confirmMsg.replace('[[selectedItems]]', selectedItems);
            $('.modal-footer button.confirm-btn', $modal).html(confirmMsg);
            $('.modal-footer input.confirm-btn', $modal).val(confirmMsg);
        }
        var input = $this.attr('data-modal-input-' + counter);
        if (input) {
            $('.modal-body-input', $modal).removeClass('hidden');
            $('#modal-label-tooltip', $modal).html(input);
        } else {
            $('.modal-body-input', $modal).addClass('hidden');
        }
        if (counter == limit) {
            $('.confirm-again', $modal).not('.hidden').addClass('hidden');
            if ($this.attr('data-click-after')) {
                $('.modal-footer [data-next-action="submit"]', $modal).removeClass('hidden');
            }
            else {
                $('.modal-footer input', $modal).removeClass('hidden');
            }
            $modal.off('hidden.bs.modal');
        }
        $modal.modal('show');
        counter++;
    }

    function getSelectedItemsCount() {
        if ($('input[name="everything-selected"]').val()) {
          return parseInt($('input#id_total').val(), 10);
        } else {
          return $('input.action-select[type=checkbox]:checked').length;
        }
    }

    if ($modal) {
        initialBinding();
    }
});

function initTinyMCE(inputSelector, IsEditorComponentHtmlBox) {
  if (inputSelector === undefined) {
    inputSelector = 'textarea.formatted-text'
  }
  let inputElement = document.querySelector(inputSelector);
  let additionalConfig = {readonly: inputElement && inputElement.disabled};
  let fileBrowserUrl = '/pb-admin/images-file-browser/browse/?pop=4';
  if (IsEditorComponentHtmlBox) {
    additionalConfig = {
      file_browser_callback: function(input_id, input_value, type, win){
        const url = fileBrowserUrl + '&type=' + type;

        tinymce.activeEditor.windowManager.open({
            file: url,
            width: 800,
            height: 600,
            resizable: 'yes',
            scrollbars: 'yes',
            inline: 'yes',  // This parameter only has an effect if you use the inlinepopups plugin!
            close_previous: 'no'
        }, {
            window: win,
            input: input_id,
        });
        return false;
      },
      ...additionalConfig
    }
  }

  tinymce.init({
    schema: "html5",
    selector: inputSelector,
    setup: function (editor) {
      // workaround chrome validation failure https://github.com/tinymce/tinymce/issues/2584
      editor.on('change', function (e) {
        editor.save();
      });

      if (typeof FILES_UPLOAD_URL !== 'undefined') {
        editor.on('BeforeSetContent', function (e) {
          e.content = e.content.replaceAll(FILES_UPLOAD_PATTERN, FILES_UPLOAD_URL);
        });
        editor.on('SetContent', function (e) {
          e.content = e.content.replaceAll(FILES_UPLOAD_PATTERN, FILES_UPLOAD_URL);
        });
        editor.on('GetContent', function (e) {
          e.content = e.content.replaceAll(FILES_UPLOAD_URL, FILES_UPLOAD_PATTERN);
        });
      }
    },
    plugins: "link image paste pagebreak table contextmenu table code media textcolor anchor",
    browser_spellcheck: true,
    toolbar1: "code,|,bold,italic,underline,strikethrough,|,alignleft,aligncenter,alignright,alignfull,formatselect,|,blockquote,pasteword,|,bullist,numlist,|,outdent,indent,|,link,unlink,|,anchor,|,media,image",
    toolbar2: "",
    statusbar: true,
    relative_urls: false,
    convert_urls: false,
    entity_encoding: "raw",
    forced_root_block: false,
    allow_html_in_named_anchor: true,
    valid_elements : ""
      +"@[accesskey|draggable|style|class|hidden|tabindex|contenteditable|id|title|contextmenu|lang|dir<ltr?rtl|spellcheck|"
      +"aria-autocomplete|aria-checked|aria-disabled|aria-errormessage|aria-expanded|aria-haspopup|aria-hidden|aria-invalid|aria-label|aria-level|aria-modal|aria-multiline|aria-multiselectable|aria-orientation|aria-placeholder|aria-pressed|aria-readonly|aria-required|aria-selected|aria-sort|aria-valuemax|aria-valuemin|aria-valuenow|aria-valuetext|aria-busy|aria-live|aria-relevant|aria-atomic|aria-dropeffect|aria-grabbed|aria-activedescendant|aria-colcount|aria-colindex|aria-colspan|aria-controls|aria-describedby|aria-description|aria-details|aria-flowto|aria-labelledby|aria-owns|aria-posinset|aria-rowcount|aria-rowindex|aria-rowspan|aria-setsize|aria-current|aria-keyshortcuts|aria-roledescription|"
      +"onabort|onerror|onmousewheel|onblur|onfocus|onpause|oncanplay|onformchange|onplay|oncanplaythrough|onforminput|onplaying|onchange|oninput|onprogress|onclick|oninvalid|onratechange|oncontextmenu|onkeydown|onreadystatechange|ondblclick|onkeypress|onscroll|ondrag|onkeyup|onseeked|ondragend|onload|onseeking|ondragenter|onloadeddata|onselect|ondragleave|onloadedmetadata|onshow|ondragover|onloadstart|onstalled|ondragstart|onmousedown|onsubmit|ondrop|onmousemove|onsuspend|ondurationmouseout|ontimeupdate|onemptied|onmouseover|onvolumechange|onended|onmouseup|onwaiting],"
      +"a[target<_blank?_self?_top?_parent|ping|media|href|hreflang|type"
      +"|rel<alternate?archives?author?bookmark?external?feed?first?help?index?last?license?next?nofollow?noreferrer?prev?search?sidebar?tag?up"
      +"],"
      +"abbr,"
      +"address,"
      +"area[alt|coords|shape|href|target<_blank?_self?_top?_parent|ping|media|hreflang|type|shape<circle?default?poly?rect"
      +"|rel<alternate?archives?author?bookmark?external?feed?first?help?index?last?license?next?nofollow?noreferrer?prev?search?sidebar?tag?up"
      +"],"
      +"article,"
      +"aside,"
      +"audio[src|preload<none?metadata?auto|autoplay<autoplay|loop<loop|controls<controls|mediagroup],"
      +"blockquote[cite],"
      +"body,"
      +"br,"
      +"button[autofocus<autofocus|disabled<disabled|form|formaction|formenctype|formmethod<get?put?post?delete|formnovalidate?novalidate|"
      +"formtarget<_blank?_self?_top?_parent|name|type<reset?submit?button|value],"
      +"canvas[width,height],"
      +"caption,"
      +"cite,"
      +"code,"
      +"col[span],"
      +"colgroup[span],"
      +"command[type<command?checkbox?radio|label|icon|disabled<disabled|checked<checked|radiogroup|default<default],"
      +"datalist[data],"
      +"dd,"
      +"del[cite|datetime],"
      +"details[open<open],"
      +"dfn,"
      +"div,"
      +"dl,"
      +"dt,"
      +"-em/i,"
      +"embed[src|type|width|height],"
      +"eventsource[src],"
      +"fieldset[disabled<disabled|form|name],"
      +"figcaption,"
      +"figure,"
      +"footer,"
      +"form[accept-charset|action|enctype|method<get?post?put?delete|name|novalidate<novalidate|target<_blank?_self?_top?_parent],"
      +"-h1,-h2,-h3,-h4,-h5,-h6,"
      +"header,"
      +"hgroup,"
      +"hr,"
      +"iframe[name|src|srcdoc|seamless<seamless|width|height|sandbox],"
      +"img[alt=|src|ismap|usemap|width|height],"
      +"input[accept|alt|autocomplete<on?off|autofocus<autofocus|checked<checked|disabled<disabled"
      +"|form|formaction|formenctype|formmethod<get?put?post?delete|formnovalidate?novalidate|formtarget<_blank?_self?_top?_parent"
      +"|height|list|max|maxlength|min|multiple<multiple|name|pattern|placeholder|readonly<readonly|required<required"
      +"|size|src|step|type<hidden?text?search?tel?url?email?password?datetime?date?month?week?time?datetime-local?number?range?color"
      +"?checkbox?radio?file?submit?image?reset?button?value|width],"
      +"ins[cite|datetime],"
      +"kbd,"
      +"keygen[autofocus<autofocus|challenge|disabled<disabled|form|name],"
      +"label[for|form],"
      +"legend,"
      +"li[value],"
      +"mark,"
      +"map[name],"
      +"menu[type<context?toolbar?list|label],"
      +"meter[value|min|low|high|max|optimum],"
      +"nav,"
      +"noscript,"
      +"object[data|type|name|usemap|form|width|height],"
      +"ol[reversed|start],"
      +"optgroup[disabled<disabled|label],"
      +"option[disabled<disabled|label|selected<selected|value],"
      +"output[for|form|name],"
      +"-p,"
      +"param[name,value],"
      +"-pre,"
      +"progress[value,max],"
      +"q[cite],"
      +"ruby,"
      +"rp,"
      +"rt,"
      +"samp,"
      +"script[src|async<async|defer<defer|type|charset],"
      +"section,"
      +"select[autofocus<autofocus|disabled<disabled|form|multiple<multiple|name|size],"
      +"small,"
      +"source[src|type|media],"
      +"-span,"
      +"-strong/b,"
      +"-sub,"
      +"summary,"
      +"-sup,"
      +"table,"
      +"tbody,"
      +"td[colspan|rowspan|headers],"
      +"textarea[autofocus<autofocus|disabled<disabled|form|maxlength|name|placeholder|readonly<readonly|required<required|rows|cols|wrap<soft|hard],"
      +"tfoot,"
      +"th[colspan|rowspan|headers|scope],"
      +"thead,"
      +"time[datetime],"
      +"tr,"
      +"ul,"
      +"var,"
      +"video[preload<none?metadata?auto|src|crossorigin|poster|autoplay<autoplay|"
      +"mediagroup|loop<loop|muted<muted|controls<controls|width|height],"
      +"wbr,"
      +"svg[*],"
      +"altGlyph[*],"
      +"altGlyphDef[*],"
      +"altGlyphItem[*],"
      +"animate[*],"
      +"animateColor[*],"
      +"animateMotion[*],"
      +"animateTransform[*],"
      +"circle[*],"
      +"clipPath[*],"
      +"color-profile[*],"
      +"cursor[*],"
      +"defs[*],"
      +"desc[*],"
      +"ellipse[*],"
      +"feBlend[*],"
      +"feColorMatrix[*],"
      +"feComponentTransfer[*],"
      +"feComposite[*],"
      +"feConvolveMatrix[*],"
      +"feDiffuseLighting[*],"
      +"feDisplacementMap[*],"
      +"deDistantLight[*],"
      +"feFlood[*],"
      +"feFuncA[*],"
      +"feFuncB[*],"
      +"feFuncG[*],"
      +"feFuncR[*],"
      +"feGaussianBlur[*],"
      +"feImage[*],"
      +"feMerge[*],"
      +"feMergeNode[*],"
      +"feMorphology[*],"
      +"feOffset[*],"
      +"fePointLight[*],"
      +"feSpecularLighting[*],"
      +"feSpotLight[*],"
      +"feTile[*],"
      +"feTurbulance[*],"
      +"filter[*],"
      +"font[*],"
      +"font-face[*],"
      +"font-face-format[*],"
      +"font-face-name[*],"
      +"font-face-src[*],"
      +"font-face-url[*],"
      +"foreignObject[*],"
      +"g[*],"
      +"glyph[*],"
      +"glyphRef[*],"
      +"hkern[*],"
      +"image[*],"
      +"line[*],"
      +"lineGradient[*],"
      +"marker[*],"
      +"mask[*],"
      +"metadata[*],"
      +"missing-glyph[*],"
      +"pmath[*],"
      +"path[*],"
      +"pattern[*],"
      +"polygon[*],"
      +"polyline[*],"
      +"radialGradient[*],"
      +"rect[*],"
      +"script[*],"
      +"set[*],"
      +"stop[*],"
      +"style[*],"
      +"svg[*],"
      +"switch[*],"
      +"symbol[*],"
      +"text[*],"
      +"textPath[*],"
      +"title[*],"
      +"tref[*],"
      +"tspan[*],"
      +"use[*],"
      +"view[*],"
      +"vkern[*]",
    extended_valid_elements: "em[class|name|id]",
    valid_children: "+a[div|h1|h2|h3|h4|h5|h6|p|span|#text]",
    menu: {
      edit: {title: 'Edit', items: 'undo redo | cut copy paste | selectall'},
      insert: {title: 'Insert', items: 'media image link | pagebreak'},
      view: {title: 'View', items: 'visualaid'},
      format: {
        title: 'Format',
        items: 'bold italic underline strikethrough superscript subscript | formats | removeformat'
      },
      table: {
        title: 'Table',
        items: 'inserttable tableprops deletetable | cell row column'
      },
      tools: {title: 'Tools', items: 'code'}
    },
    ...additionalConfig
  });
}

jQuery(document).ready(function($) {
  const IsEditorComponentHtmlBox = $('#id_type > option:selected').val() === "content_div_html_box";
  initTinyMCE('textarea.formatted-text', IsEditorComponentHtmlBox);
});

function initSelectize(inputSelector) {
    $(inputSelector).each(function() {
        $(this).selectize({
            plugins: ['copy_selection', 'drag_drop', 'remove_button'],
            delimiter: ',',
            openOnFocus: false,
            closeAfterSelect: true,
            valueField: 'id',
            labelField: 'name',
            searchField: ['name'],
            options: $(this).data('options'),
            create: function (input) {
                for (var id in this.options) {
                    var option = this.options[id];
                    if (option.name == input && $.inArray(option.id, this.items) == -1) {
                        return option;
                    }
                }
                return false;
            },
            onInitialize: function () {
                var selectize = this;
                this.forceOpen = false;
                this.$control.click(function (e) {
                    // open only when click on empty input
                    if (selectize.isOpen || $(e.target).hasClass('item')) {
                        selectize.close();
                    } else {
                        selectize.forceOpen = true;
                        selectize.open();
                    }
                });
            },
            onType: function (str) {
                if (!str) {
                    this.close();
                }
            },
            onDropdownOpen: function ($dropdown) {
                // workaround for selectize dropdown
                // open only on click and when query not empty
                if (!this.lastQuery && !this.forceOpen) {
                    this.close();
                } else if (this.forceOpen) {
                    this.forceOpen = false;
                }
            }
        });
    });
}

function initDuplicateModal(modalSelector, linkSelector) {
    var $modal = $(modalSelector);
    var $link = $(linkSelector);

    var $form = $modal.find('form');
    var formAction = $form.attr('action');

    $link.click(function () {
        $form.attr('action', $(this).data('id') + '/' + formAction);
    });
}

function initCodeMirror(inputSelector) {
        const initCodeMirrorOnTextArea = (item) => {
        codeMirror = CodeMirror.fromTextArea(
            item,
            {
                lineNumbers: true,
                mode: item.getAttribute("data-mode"),
                gutters: ["CodeMirror-lint-markers"],
                lint: true,
                readOnly: item.disabled
            }
        )
        codeMirror.setOption("lint", !!codeMirror.getValue().trim());
        codeMirror.on("change", () => codeMirror.setOption("lint", !!codeMirror.getValue().trim()))
    };
    const hiddenClassRemoved = (mutation) => (
        mutation.type === "attributes" &&
        mutation.attributeName === "class" &&
        mutation.oldValue.includes("hidden") &&
        !mutation.target.classList.contains("hidden")
    );
    const mutationCallback = (mutations, observer) => {
        mutations
            .filter((mutation) => hiddenClassRemoved(mutation))
            .forEach((mutation) => {
                initCodeMirrorOnTextArea(
                    mutation.target.querySelector(inputSelector)
                );
                observer.disconnect();
            });
    };
    document.querySelectorAll(inputSelector).forEach((textarea) => {
        const container = textarea.parentElement.parentElement;
        if (!container.classList.contains("hidden")) {
            initCodeMirrorOnTextArea(textarea);
        } else {
            // for shinar translated fields
            const containerObserver = new MutationObserver(mutationCallback);
            containerObserver.observe(container, { attributes: true, attributeFilter: ["class"], attributeOldValue: true });
        }
    })
}

function initThemeTranslations() {
    var $div = $('div[data-type="theme-translations"]');
    var $totalForms = $('input[name$="TOTAL_FORMS"]', $div);

    var onDelete = function() {
        $(this).parent().find('input[name$="DELETE"]').prop('checked', true);
        $(this).closest('tr').addClass('hidden');
        // always show at least 1 empty form
        if ($(this).closest('tbody').find('tr:visible').length === 0) {
            $('a[data-action="add"]').click();
        }
    };
    $('a[data-action="delete"]', $div).click(onDelete);

    var initTextarea = function() {
        var offset = this.offsetHeight - this.clientHeight;
        var resizeTextarea = function(el) {
            $(el).css('height', 'auto').css('height', el.scrollHeight + offset);
        };
        $(this).on('keyup input', function() {
            resizeTextarea(this);
        });
        resizeTextarea(this);
    };
    // resizeTextarea works only on visible elements
    $('textarea:visible', $div).each(initTextarea);

    $('a[data-action="add"]', $div).click(function() {
        var $tr = $('table tbody tr:last', $div).clone();
        var total = parseInt($totalForms.val());
        // replace name & id fields
        $tr.find(':input').each(function() {
            var name = $(this).attr('name').replace(
                '-' + (total - 1) + '-', '-' + total + '-'
            );
            $(this).attr({'name': name, 'id': 'id_' + name});
        });
        // increase total form count
        $totalForms.val(total + 1);
        // show hidden extra form and init auto textarea height
        $('table tbody tr:last').removeClass('hidden');
        $('textarea', 'table tbody tr:last').each(initTextarea);
        // bind delete action and apped to tbody
        $('a[data-action="delete"]', $tr).click(onDelete);
        $('table tbody').append($tr);
    });
}

$('#id_family', '#form_report').change(function() {
    var family = $(this).val();
    window.location = location.toString().replace(location.search, "?family=" + family);
});

function initNewTabModals() {
  $('#add-modal form[target="_blank"] button[type="submit"]').on('click', function() {
    var $this = $(this);
    $this.closest('#add-modal').modal('hide');
    $('#content').prepend(
      $('<div />')
        .addClass('alert alert-warning')
        .html(
          '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button>'
          + $this.attr('data-warn'))
    );
  });
}


function initRenderingStateInput() {
    var $select = $('#id_rendering_state');
    var $datePicker = $('#div_id_rendering_disable_date');
    var $datePickerInput = $datePicker.find('input');
    var $datePickerText = $('<span></span>');
    $datePickerText.css('padding-left', '10px');
    $datePickerText.insertAfter($datePickerInput);
    var state;

    $select.change(function () {
        state = $(this).val();
        if (state === 'disabled_after_date') {
            changeText();
            $datePicker.show();
        } else {
            $datePicker.hide();
        }
    });

    function changeText() {
        if (state === 'disabled_after_date') {
            var text = '';
            var color = '';
            var dateValue = $datePickerInput.val();
            if (dateValue) {
                dateValue = new Date($datePickerInput.val());
                var dateNow = new Date();
                if (dateValue <= dateNow) {
                    text = $datePickerInput.attr('data-text-disabled');
                    color = 'red';
                } else {
                    text = $datePickerInput.attr('data-text-disabled-after-date');
                    text = text.replace('%s', dateValue.toISOString().slice(0, 10));
                }
                $datePickerText.text(text);
                $datePickerText.css('color', color);
            }
        }
    }
    $datePickerInput.change(changeText);

    $select.trigger('change');
}

function preventDoubleFormSubmit() {
    $('form').bind('submit', function () {
        var $form = $(this);
        if ($form.is('[disabled]')) {
            return false;
        }
        $form.attr('disabled', 'disabled');
        setTimeout(function () {
            $form.removeAttr('disabled');
        }, 1200);
    });
}

function initTriggerClick() {
    $('input[data-action="form-submit"]').change(function () {
        $(this).closest('form').submit();
    });
    $('a[data-action="trigger-click"]').click(function (e) {
        e.preventDefault();
        var inputName = $(this).data('target');
        $(inputName).trigger('click');
    });
}

function initAsyncTaskWaiter() {
    const interval = 2000;
    const taskUuidQueryParamKey = "task-uuid";

    const asyncTaskModal = document.getElementById("async-task-modal");
    const asyncTasks = [...document.getElementById("async-tasks").querySelectorAll(".alert")];
    const urlQueryParams = new URLSearchParams(window.location.search);

    asyncTasks.forEach((taskElement) => {
        const taskId = taskElement.getAttribute("data-id");
        setTimeout(checkAsyncTaskStatus.bind(this, taskElement, taskId), interval);
    });

    if (
        urlQueryParams.get(taskUuidQueryParamKey) !== null
        &&
        !asyncTasks
            .map((element) => element.getAttribute("data-id"))
            .includes(urlQueryParams.get(taskUuidQueryParamKey))
    ) {
        const taskId = urlQueryParams.get(taskUuidQueryParamKey);
        setTimeout(checkAsyncTaskStatus.bind(this, null, taskId), interval);
    }

    function checkAsyncTaskStatus(taskElement, taskId) {
        $.ajax({
            type: "GET",
            url: `/pb-admin/async-task/${taskId}/`,
            success: (data) => {
                if (!["NEW", "PENDING"].includes(data["status"])) {
                    if (taskElement != null) {
                        taskElement.hidden = true;
                    }

                    const modalData = data["modal_data"];
                    if (modalData) {
                        const modalHeader = asyncTaskModal.querySelector('[data-target="header"]');
                        const modalBody = asyncTaskModal.querySelector('[data-target="body"]');
                        const modalButton = asyncTaskModal.querySelector('[data-target="button"]');

                        modalHeader.innerHTML = modalData["header"];
                        modalBody.innerHTML = modalData["body"];
                        modalButton.innerHTML = modalData["button"];

                        modalButton.removeAttribute("href");
                        modalButton.setAttribute("data-dismiss", "modal");

                        if ("button_url" in modalData) {
                            modalButton.setAttribute("href", modalData["button_url"]);
                            modalButton.removeAttribute("data-dismiss");
                        }

                        $("#async-task-modal").modal("show");
                    }
                }
            },
            complete: (data) => {
                if (data["responseJSON"]["status"] == "PENDING") {
                    setTimeout(checkAsyncTaskStatus.bind(this, taskElement, taskId), interval);
                }
            },
        });
    }
}



function setPerPage(value) {
    let url = new URL(window.location);
    url.searchParams.set("set-per-page", value);
    window.location = url;
}

function setPage(value) {
    let url = new URL(window.location);
    url.searchParams.set("page", value);
    window.location = url;
}


function updateRelatedFieldUrl(formField) {
    let redirectButton = document.getElementById(`${formField.name}_redirect`)
    if (formField.value !== "") {
      redirectButton.classList.remove("disabled")
      redirectButton.href = redirectButton.dataset.relatedUrl + formField.value
    } else {
      redirectButton.classList.add("disabled")
    }
}

function initPaginationHandlers() {
  $('.pagination-items-page').on('click', function(e) {
      e.preventDefault();
      const value = $(this).text();
      setPerPage(value);
  });
}

function initTinyMCEDialogHandlers() {
  $(document).on('click', '[data-action="close-tinymce-window"]', function() {
    if (top.tinymce && top.tinymce.activeEditor) {
      const windows = top.tinymce.activeEditor.windowManager.getWindows();
      if (windows[0]) {
        windows[0].close();
      }
    }
  });
}

function initRelatedFieldHandlers() {
  $('.related-field-container select').each(function() {
    updateRelatedFieldUrl(this);
  });
  
  $(document).on('change', '.related-field-container select', function() {
    updateRelatedFieldUrl(this);
  });
}

$(document).ready(function() {
    initCodeMirror('textarea[data-type="code"]');
    initSelectize('input[data-type="selectize"]');
    initThemeTranslations();
    initNewTabModals();
    initRenderingStateInput();
    initTriggerClick();
    initAsyncTaskWaiter();
    preventDoubleFormSubmit();
    initPaginationHandlers();
    initTinyMCEDialogHandlers();
    initRelatedFieldHandlers();
});

async function controlWarningAlerts() {
    const checkboxWithWarnings = document.querySelectorAll("input[type=checkbox][warning_alert_on_enabled]");

    for (let checkboxWithWarning of checkboxWithWarnings) {
        const warningDiv = checkboxWithWarning.closest(".controls").querySelector(".field-warning");
        checkboxWithWarning.onclick = () => {
            warningDiv.hidden = !checkboxWithWarning.checked;
        }
    }
}

controlWarningAlerts();
