ace.define("ace/ext/menu_tools/overlay_page",["require","exports","module","ace/lib/dom"], function(require, exports, module) {
'use strict';
var dom = require("../../lib/dom");
var cssText = "#ace_settingsmenu, #kbshortcutmenu {\
background-color: #F7F7F7;\
color: black;font-size: 12px;\
box-shadow: -5px 4px 5px rgba(126, 126, 126, 0.55);\
padding: 1em 0.5em 2em 1em;\
overflow: auto;\
position: absolute;\
margin: 0;\
bottom: 0;\
right: 0;\
top: 0;\
z-index: 9991;\
cursor: default;\
}\
.ace_dark #ace_settingsmenu, .ace_dark #kbshortcutmenu {\
box-shadow: -20px 10px 25px rgba(126, 126, 126, 0.25);\
background-color: rgba(255, 255, 255, 0.6);\
color: black;\
}\
.ace_optionsMenuEntry:hover {\
background-color: rgba(100, 100, 100, 0.1);\
transition: all 0.3s\
}\
.ace_closeButton {\
background: rgba(245, 146, 146, 0.5);\
border: 1px solid #F48A8A;\
border-radius: 50%;\
padding: 7px;\
position: absolute;\
right: -8px;\
top: -8px;\
z-index: 100000;\
}\
.ace_closeButton{\
background: rgba(245, 146, 146, 0.9);\
}\
.ace_optionsMenuKey {\
color: darkslateblue;\
font-weight: bold;\
}\
.ace_optionsMenuCommand {\
color: darkcyan;\
font-weight: normal;\
}\
.ace_optionsMenuEntry input, .ace_optionsMenuEntry button {\
vertical-align: middle;\
}\
.ace_optionsMenuEntry button[ace_selected_button=true] {\
background: #e7e7e7;\
box-shadow: 1px 0px 2px 0px #adadad inset;\
border-color: #adadad;\
}\
.ace_optionsMenuEntry button {\
background: white;\
border: 1px solid lightgray;\
margin: 0px;\
}\
.ace_optionsMenuEntry button:hover{\
background: #f0f0f0;\
}";
dom.importCssString(cssText);
module.exports.overlayPage = function overlayPage(editor, contentElement, top, right, bottom, left) {
    top = top ? 'top: ' + top + ';' : '';
    bottom = bottom ? 'bottom: ' + bottom + ';' : '';
    right = right ? 'right: ' + right + ';' : '';
    left = left ? 'left: ' + left + ';' : '';

    var closer = document.createElement('div');
    var contentContainer = document.createElement('div');

    function documentEscListener(e) {
        if (e.keyCode === 27) {
            closer.click();
        }
    }

    closer.style.cssText = 'margin: 0; padding: 0; ' +
        'position: fixed; top:0; bottom:0; left:0; right:0;' +
        'z-index: 9990; ' +
        'background-color: rgba(0, 0, 0, 0.3);';
    closer.addEventListener('click', function() {
        document.removeEventListener('keydown', documentEscListener);
        closer.parentNode.removeChild(closer);
        editor.focus();
        closer = null;
    });
    document.addEventListener('keydown', documentEscListener);

    contentContainer.style.cssText = top + right + bottom + left;
    contentContainer.addEventListener('click', function(e) {
        e.stopPropagation();
    });

    var wrapper = dom.createElement("div");
    wrapper.style.position = "relative";
    
    var closeButton = dom.createElement("div");
    closeButton.className = "ace_closeButton";
    closeButton.addEventListener('click', function() {
        closer.click();
    });
    
    wrapper.appendChild(closeButton);
    contentContainer.appendChild(wrapper);
    
    contentContainer.appendChild(contentElement);
    closer.appendChild(contentContainer);
    document.body.appendChild(closer);
    editor.blur();
};

});

ace.define("ace/ext/modelist",["require","exports","module"], function(require, exports, module) {
"use strict";

var modes = [];
function getModeForPath(path) {
    var mode = modesByName.text;
    var fileName = path.split(/[\/\\]/).pop();
    for (var i = 0; i < modes.length; i++) {
        if (modes[i].supportsFile(fileName)) {
            mode = modes[i];
            break;
        }
    }
    return mode;
}

var Mode = function(name, caption, extensions) {
    this.name = name;
    this.caption = caption;
    this.mode = "ace/mode/" + name;
    this.extensions = extensions;
    var re;
    if (/\^/.test(extensions)) {
        re = extensions.replace(/\|(\^)?/g, function(a, b){
            return "$|" + (b ? "^" : "^.*\\.");
        }) + "$";
    } else {
        re = "^.*\\.(" + extensions + ")$";
    }

    this.extRe = new RegExp(re, "gi");
};

Mode.prototype.supportsFile = function(filename) {
    return filename.match(this.extRe);
};
var supportedModes = {
    HTML:        ["html|htm|xhtml|vue|we|wpy"],
    JavaScript:  ["js|jsm|jsx"],
    JSON:        ["json"],
    Python:      ["py"],
    SQL:         ["sql"]
};

var nameOverrides = {
};
var modesByName = {};
for (var name in supportedModes) {
    var data = supportedModes[name];
    var displayName = (nameOverrides[name] || name).replace(/_/g, " ");
    var filename = name.toLowerCase();
    var mode = new Mode(filename, displayName, data[0]);
    modesByName[filename] = mode;
    modes.push(mode);
}

module.exports = {
    getModeForPath: getModeForPath,
    modes: modes,
    modesByName: modesByName
};

});

ace.define("ace/ext/themelist",["require","exports","module","ace/lib/fixoldbrowsers"], function(require, exports, module) {
"use strict";
require("ace/lib/fixoldbrowsers");

var themeData = [
    ["Chrome"         ],
    ["Clouds"         ],
    ["Dawn"           ],
    ["Eclipse"        ],
    ["GitHub"         ],
    ["SQL Server"           ,"sqlserver"               , "light"],
    ["Clouds Midnight"      ,"clouds_midnight"         ,  "dark"],
    ["Monokai"              ,"monokai"                 ,  "dark"],
    ["Twilight"             ,"twilight"                ,  "dark"]
];


exports.themesByName = {};
exports.themes = themeData.map(function(data) {
    var name = data[1] || data[0].replace(/ /g, "_").toLowerCase();
    var theme = {
        caption: data[0],
        theme: "ace/theme/" + name,
        isDark: data[2] == "dark",
        name: name
    };
    exports.themesByName[name] = theme;
    return theme;
});

});

ace.define("ace/ext/options",["require","exports","module","ace/ext/menu_tools/overlay_page","ace/lib/dom","ace/lib/oop","ace/lib/event_emitter","ace/ext/modelist","ace/ext/themelist"], function(require, exports, module) {
"use strict";
var overlayPage = require('./menu_tools/overlay_page').overlayPage;

 
var dom = require("../lib/dom");
var oop = require("../lib/oop");
var EventEmitter = require("../lib/event_emitter").EventEmitter;
var buildDom = dom.buildDom;

var modelist = require("./modelist");
var themelist = require("./themelist");

var themes = { Bright: [], Dark: [] };
themelist.themes.forEach(function(x) {
    themes[x.isDark ? "Dark" : "Bright"].push({ caption: x.caption, value: x.theme });
});

var modes = modelist.modes.map(function(x){ 
    return { caption: x.caption, value: x.mode }; 
});


var optionGroups = {
    Main: {
        '模式': {
            path: "mode",
            type: "select",
            items: modes
        },
        '主题': {
            path: "theme",
            type: "select",
            items: themes
        },
        // "Keybinding": {
        //     type: "buttonBar",
        //     path: "keyboardHandler",
        //     items: [
        //         { caption : "Ace", value : null },
        //     ]
        // },
        "字体": {
            path: "fontSize",
            type: "number",
            defaultValue: 12,
            defaults: [
                {caption: "12px", value: 12},
                {caption: "24px", value: 24}
            ]
        },
        "软分行": {
            type: "buttonBar",
            path: "wrap",
            items: [
               { caption : "Off",  value : "off" },
               { caption : "View", value : "free" },
               { caption : "margin", value : "printMargin" },
               { caption : "40",   value : "40" }
            ]
        },
        "光标样式": {
            path: "cursorStyle",
            items: [
               { caption : "Ace",    value : "ace" },
               { caption : "Slim",   value : "slim" },
               { caption : "Smooth", value : "smooth" },
               { caption : "Smooth And Slim", value : "smooth slim" },
               { caption : "Wide",   value : "wide" }
            ]
        },
        "折叠": {
            path: "foldStyle",
            items: [
                { caption : "Manual", value : "manual" },
                { caption : "Mark begin", value : "markbegin" },
                { caption : "Mark begin and end", value : "markbeginend" }
            ]
        },
        "Tabs设定": [{
            path: "useSoftTabs"
        }, {
            path: "tabSize",
            type: "number",
            values: [2, 3, 4, 8, 16]
        }],
        "超出滚动": {
            type: "buttonBar",
            path: "scrollPastEnd",
            items: [
               { caption : "None",  value : 0 },
               { caption : "Half",   value : 0.5 },
               { caption : "Full",   value : 1 }
            ]
        }
    },
    More: {
        // "Atomic soft tabs": {
        //     path: "navigateWithinSoftTabs"
        // },
        "启用动作": {
            path: "behavioursEnabled"
        },
        "整行选中": {
            type: "checkbox",
            values: "text|line",
            path: "selectionStyle"
        },
        "高亮选中行": {
            path: "highlightActiveLine"
        },
        "显示不可见": {
            path: "showInvisibles"
        },
        "显示参考线": {
            path: "displayIndentGuides"
        },
        "滚动条可见": [{
            path: "hScrollBarAlwaysVisible"
        }, {
            path: "vScrollBarAlwaysVisible"
        }],
        "滚动动画": {
            path: "animatedScroll"
        },
        "显示行号": {
            path: "showGutter"
        },
        // "Show Line Numbers": {
        //     path: "showLineNumbers"
        // },
        "相对行号": {
            path: "relativeLineNumbers"
        },
        // "Fixed Gutter Width": {
        //     path: "fixedWidthGutter"
        // },
        "显示打印框": [{
            path: "showPrintMargin"
        }, {
            type: "number",
            path: "printMarginColumn"
        }],
        "换行缩进": {
            path: "indentedSoftWrap"
        },
        // "Highlight selected word": {
        //     path: "highlightSelectedWord"
        // },
        "淡入折叠部件": {
            path: "fadeFoldWidgets"
        },
        // "Use textarea for IME": {
        //     path: "useTextareaForIME"
        // },
        "合并撤销": {
            path: "mergeUndoDeltas",
            items: [
               { caption : "Always",  value : "always" },
               { caption : "Never",   value : "false" },
               { caption : "Timed",   value : "true" }
            ]
        },
        // "Elastic Tabstops": {
        //     path: "useElasticTabstops"
        // },
        // "Incremental Search": {
        //     path: "useIncrementalSearch"
        // },
        "只读": {
            path: "readOnly"
        },
        // "Copy without selection": {
        //     path: "copyWithEmptySelection"
        // },
        "自动填充": {
            path: "enableLiveAutocompletion"
        }
    }
};


var OptionPanel = function(editor, element) {
    this.editor = editor;
    this.container = element || document.createElement("div");
    this.groups = [];
    this.options = {};
};

(function() {
    
    oop.implement(this, EventEmitter);
    
    this.add = function(config) {
        if (config.Main)
            oop.mixin(optionGroups.Main, config.Main);
        if (config.More)
            oop.mixin(optionGroups.More, config.More);
    };
    
    this.render = function() {
        this.container.innerHTML = "";
        buildDom(["table", {id: "controls"}, 
            this.renderOptionGroup(optionGroups.Main),
            ["tr", null, ["td", {colspan: 2},
                ["table", {id: "more-controls"}, 
                    this.renderOptionGroup(optionGroups.More)
                ]
            ]]
        ], this.container);
    };
    
    this.renderOptionGroup = function(group) {
        return Object.keys(group).map(function(key, i) {
            var item = group[key];
            if (!item.position)
                item.position = i / 10000;
            if (!item.label)
                item.label = key;
            return item;
        }).sort(function(a, b) {
            return a.position - b.position;
        }).map(function(item) {
            return this.renderOption(item.label, item);
        }, this);
    };
    
    this.renderOptionControl = function(key, option) {
        var self = this;
        if (Array.isArray(option)) {
            return option.map(function(x) {
                return self.renderOptionControl(key, x);
            });
        }
        var control;
        
        var value = self.getOption(option);
        
        if (option.values && option.type != "checkbox") {
            if (typeof option.values == "string")
                option.values = option.values.split("|");
            option.items = option.values.map(function(v) {
                return { value: v, name: v };
            });
        }
        
        if (option.type == "buttonBar") {
            control = ["div", option.items.map(function(item) {
                return ["button", { 
                    value: item.value, 
                    ace_selected_button: value == item.value, 
                    onclick: function() {
                        self.setOption(option, item.value);
                        var nodes = this.parentNode.querySelectorAll("[ace_selected_button]");
                        for (var i = 0; i < nodes.length; i++) {
                            nodes[i].removeAttribute("ace_selected_button");
                        }
                        this.setAttribute("ace_selected_button", true);
                    } 
                }, item.desc || item.caption || item.name];
            })];
        } else if (option.type == "number") {
            control = ["input", {type: "number", value: value || option.defaultValue, style:"width:3em", oninput: function() {
                self.setOption(option, parseInt(this.value));
            }}];
            if (option.defaults) {
                control = [control, option.defaults.map(function(item) {
                    return ["button", {onclick: function() {
                        var input = this.parentNode.firstChild;
                        input.value = item.value;
                        input.oninput();
                    }}, item.caption];
                })];
            }
        } else if (option.items) {
            var buildItems = function(items) {
                return items.map(function(item) {
                    return ["option", { value: item.value || item.name }, item.desc || item.caption || item.name];
                });
            };
            
            var items = Array.isArray(option.items) 
                ? buildItems(option.items)
                : Object.keys(option.items).map(function(key) {
                    return ["optgroup", {"label": key}, buildItems(option.items[key])];
                });
            control = ["select", { id: key, value: value, onchange: function() {
                self.setOption(option, this.value);
            } }, items];
        } else {
            if (typeof option.values == "string")
                option.values = option.values.split("|");
            if (option.values) value = value == option.values[1];
            control = ["input", { type: "checkbox", id: key, checked: value || null, onchange: function() {
                var value = this.checked;
                if (option.values) value = option.values[value ? 1 : 0];
                self.setOption(option, value);
            }}];
            if (option.type == "checkedNumber") {
                control = [control, []];
            }
        }
        return control;
    };
    
    this.renderOption = function(key, option) {
        if (option.path && !option.onchange && !this.editor.$options[option.path])
            return;
        this.options[option.path] = option;
        var safeKey = "-" + option.path;
        var control = this.renderOptionControl(safeKey, option);
        return ["tr", {class: "ace_optionsMenuEntry"}, ["td",
            ["label", {for: safeKey}, key]
        ], ["td", control]];
    };
    
    this.setOption = function(option, value) {
        if (typeof option == "string")
            option = this.options[option];
        if (value == "false") value = false;
        if (value == "true") value = true;
        if (value == "null") value = null;
        if (value == "undefined") value = undefined;
        if (typeof value == "string" && parseFloat(value).toString() == value)
            value = parseFloat(value);
        if (option.onchange)
            option.onchange(value);
        else if (option.path)
            this.editor.setOption(option.path, value);
        if(option.path === 'theme'){localStorage.setItem('acetheme',value.split('/')[2])}
        this._signal("setOption", {name: option.path, value: value});
    };
    
    this.getOption = function(option) {
        if (option.getValue)
            return option.getValue();
        return this.editor.getOption(option.path);
    };
    
}).call(OptionPanel.prototype);

exports.OptionPanel = OptionPanel;

});

ace.define("ace/ext/settings_menu",["require","exports","module","ace/ext/options","ace/ext/menu_tools/overlay_page","ace/editor"], function(require, exports, module) {
"use strict";
var OptionPanel = require("ace/ext/options").OptionPanel;
var overlayPage = require('./menu_tools/overlay_page').overlayPage;
function showSettingsMenu(editor) {
    if (!document.getElementById('ace_settingsmenu')) {
        var options = new OptionPanel(editor);
        options.render();
        options.container.id = "ace_settingsmenu";
        overlayPage(editor, options.container, '0', '0', '0');
        options.container.querySelector("select,input,button,checkbox").focus();
    }
}
module.exports.init = function(editor) {
    var Editor = require("ace/editor").Editor;
    Editor.prototype.showSettingsMenu = function() {
        showSettingsMenu(this);
    };
};
});
(function() {
    ace.require(["ace/ext/settings_menu"], function(m) {
        if (typeof module == "object" && typeof exports == "object" && module) {
            module.exports = m;
        }
    });
})();
            