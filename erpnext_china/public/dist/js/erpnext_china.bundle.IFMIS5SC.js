(() => {
  // ../erpnext_china/erpnext_china/public/js/form_button_permission.js
  var PermissionForm = class PermissionForm2 extends frappe.ui.form.Form {
    add_custom_button(label, fn, group) {
      var storedJsonString = localStorage.getItem("button_perms_jsonString");
      var button_perms = JSON.parse(storedJsonString);
      if (this.doctype in button_perms) {
        if (!button_perms[this.doctype]["label_info"].includes((label + "__" + group).replace("undefined", ""))) {
          if (group && group.indexOf("fa fa-") !== -1)
            group = null;
          let btn = this.page.add_inner_button(label, fn, group);
          if (btn) {
            let menu_item_label = group ? `${group} > ${label}` : label;
            let menu_item = this.page.add_menu_item(menu_item_label, fn, false);
            menu_item.parent().addClass("hidden-xl");
            this.custom_buttons[label] = btn;
          }
          return btn;
        }
      } else {
        if (group && group.indexOf("fa fa-") !== -1)
          group = null;
        let btn = this.page.add_inner_button(label, fn, group);
        if (btn) {
          let menu_item_label = group ? `${group} > ${label}` : label;
          let menu_item = this.page.add_menu_item(menu_item_label, fn, false);
          menu_item.parent().addClass("hidden-xl");
          this.custom_buttons[label] = btn;
        }
        return btn;
      }
    }
  };
  frappe.ui.form.Form = PermissionForm;

  // ../erpnext_china/erpnext_china/public/js/button_permissions.js
  $(document).on("app_ready", function() {
    if (document.referrer.includes("/login")) {
      frappe.call({
        "method": "erpnext_china.erpnext_china.doctype.button_permission.button_permission.get_button_permission",
        "callback": function(response) {
          if (response.message) {
            var button_perms = response.message;
            var button_perms_jsonString = JSON.stringify(button_perms);
            localStorage.setItem("button_perms_jsonString", button_perms_jsonString);
          }
        }
      });
    }
  });

  // ../erpnext_china/erpnext_china/public/js/theme_switcher.js
  frappe.provide("frappe.ui");
  frappe.ui.ThemeSwitcher = class CustomThemeSwitcher extends frappe.ui.ThemeSwitcher {
    constructor() {
      super();
    }
    fetch_themes() {
      return new Promise((resolve) => {
        this.themes = [
          {
            name: "light",
            label: __("Frappe Light"),
            info: "Light Theme"
          },
          {
            name: "dark",
            label: __("Timeless Night"),
            info: "Dark Theme"
          },
          {
            name: "automatic",
            label: __("Automatic"),
            info: "Uses system's theme to switch between light and dark mode"
          },
          {
            name: "business",
            label: __("Business"),
            info: "\u4E3B\u9898\u6B63\u5728\u5F00\u53D1\u4E2D"
          }
        ];
        resolve(this.themes);
      });
    }
  };
})();
//# sourceMappingURL=erpnext_china.bundle.IFMIS5SC.js.map
