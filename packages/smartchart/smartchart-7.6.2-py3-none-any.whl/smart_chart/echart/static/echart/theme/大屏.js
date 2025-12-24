(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define(['exports', 'echarts'], factory);
    } else if (typeof exports === 'object' && typeof exports.nodeName !== 'string') {
        factory(exports, require('echarts'));
    } else {
        factory({}, root.echarts);
    }
}(this, function (exports, echarts) {
    var log = function (msg) {
        if (typeof console !== 'undefined') {
            console && console.error && console.error(msg);
        }
    };
    if (!echarts) {
        log('ECharts is not Loaded');
        return;
    }
    echarts.registerTheme('大屏', {
        "color": [
            "#1e90ff", // 道奇蓝
            "#32cd32", // 酸橙绿
            "#ff6b6b", // 浅珊瑚红
            "#ffd700", // 金色
            "#9370db"  // 中紫色
        ],
        // "color": [
        //     "#00ced1", // 深天蓝
        //     "#ff69b4", // 热粉色
        //     "#7fffaa", // 薄荷绿
        //     "#ffa07a", // 浅橙红
        //     "#6a5acd"  // 板岩蓝
        // ],
        // "color": [
        //     "#ff4500", // 橙红色
        //     "#40e0d0", // 蓝绿色
        //     "#ff1493", // 深粉色
        //     "#9acd32", // 黄绿色
        //     "#9932cc"  // 暗紫色
        // ],

        // "color": [
        //     "#4169e1", // 蓝宝石色
        //     "#ff8c00", // 暗橙色
        //     "#00ff7f", // 亮绿色
        //     "#da70d6", // 兰紫色
        //     "#ff6347"  // 番茄红
        // ],

        // "color": [
        //     "#8a2be2", // 蓝紫色
        //     "#00fa9a", // 中春绿色
        //     "#ff00ff", // 品红色
        //     "#ffdab9", // 桃色
        //     "#4b0082"  // 靛蓝色
        // ],
        //  "backgroundColor": "rgba(0, 42, 77, 0.8)", // 深海蓝透明（适合科技感大屏）
        //  "backgroundColor": "rgba(34, 50, 80, 0.6)", // 蓝灰透明（现代风适配）
        //  "backgroundColor": "rgba(48, 25, 89, 0.5)", // 蓝紫透明（夜间模式优选）
        //  "backgroundColor": "rgba(0, 73, 83, 0.4)", // 蓝绿透明（动态数据适配）
        //  "backgroundColor": "rgba(15, 25, 35, 0.3)", // 深蓝黑透明（高对比场景）

        "textStyle": {},
        "title": {
            "textStyle": {
                "color": "#666666"
            },
            "subtextStyle": {
                "color": "#999999"
            }
        },
        "line": {
            "itemStyle": {
                "normal": {
                    "borderWidth": "2"
                }
            },
            "lineStyle": {
                "normal": {
                    "width": "3"
                }
            },
            "symbolSize": "8",
            "symbol": "emptyCircle",
            "smooth": false
        },
        "radar": {
            "itemStyle": {
                "normal": {
                    "borderWidth": "2"
                }
            },
            "lineStyle": {
                "normal": {
                    "width": "3"
                }
            },
            "symbolSize": "8",
            "symbol": "emptyCircle",
            "smooth": false
        },
        "bar": {
            "itemStyle": {
                "normal": {
                    "barBorderWidth": 0,
                    "barBorderColor": "#ccc"
                },
                "emphasis": {
                    "barBorderWidth": 0,
                    "barBorderColor": "#ccc"
                }
            }
        },
        "pie": {
            "itemStyle": {
                "normal": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                },
                "emphasis": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                }
            }
        },
        "scatter": {
            "itemStyle": {
                "normal": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                },
                "emphasis": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                }
            }
        },
        "boxplot": {
            "itemStyle": {
                "normal": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                },
                "emphasis": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                }
            }
        },
        "parallel": {
            "itemStyle": {
                "normal": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                },
                "emphasis": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                }
            }
        },
        "sankey": {
            "itemStyle": {
                "normal": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                },
                "emphasis": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                }
            }
        },
        "funnel": {
            "itemStyle": {
                "normal": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                },
                "emphasis": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                }
            }
        },
        "gauge": {
            "itemStyle": {
                "normal": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                },
                "emphasis": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                }
            }
        },
        "candlestick": {
            "itemStyle": {
                "normal": {
                    "color": "#d0648a",
                    "color0": "transparent",
                    "borderColor": "#d0648a",
                    "borderColor0": "#22c3aa",
                    "borderWidth": "1"
                }
            }
        },
        "graph": {
            "itemStyle": {
                "normal": {
                    "borderWidth": 0,
                    "borderColor": "#ccc"
                }
            },
            "lineStyle": {
                "normal": {
                    "width": "1",
                    "color": "#cccccc"
                }
            },
            "symbolSize": "8",
            "symbol": "emptyCircle",
            "smooth": false,
            "color": [
                "#4ea397",
                "#22c3aa",
                "#7bd9a5",
                "#d0648a",
                "#f58db2",
                "#f2b3c9"
            ],
            "label": {
                "normal": {
                    "textStyle": {
                        "color": "#ffffff"
                    }
                }
            }
        },
        "map": {
            "itemStyle": {
                "normal": {
                    "areaColor": "#eeeeee",
                    "borderColor": "#999999",
                    "borderWidth": 0.5
                },
                "emphasis": {
                    "areaColor": "rgba(34,195,170,0.25)",
                    "borderColor": "#22c3aa",
                    "borderWidth": 1
                }
            },
            "label": {
                "normal": {
                    "textStyle": {
                        "color": "#28544e"
                    }
                },
                "emphasis": {
                    "textStyle": {
                        "color": "rgb(52,158,142)"
                    }
                }
            }
        },
        "geo": {
            "itemStyle": {
                "normal": {
                    "areaColor": "#eeeeee",
                    "borderColor": "#999999",
                    "borderWidth": 0.5
                },
                "emphasis": {
                    "areaColor": "rgba(34,195,170,0.25)",
                    "borderColor": "#22c3aa",
                    "borderWidth": 1
                }
            },
            "label": {
                "normal": {
                    "textStyle": {
                        "color": "#28544e"
                    }
                },
                "emphasis": {
                    "textStyle": {
                        "color": "rgb(52,158,142)"
                    }
                }
            }
        },
        "categoryAxis": {
            "axisLine": {
                "show": true,
                "lineStyle": {
                    "color": "#cccccc"
                }
            },
            "axisTick": {
                "show": false,
                "lineStyle": {
                    "color": "#333"
                }
            },
            "axisLabel": {
                "show": true,
                "textStyle": {
                    "color": "#999999"
                }
            },
            "splitLine": {
                "show": false,
                "lineStyle": {
                    "color": [
                        "#eeeeee"
                    ]
                }
            },
            "splitArea": {
                "show": false,
                "areaStyle": {
                    "color": [
                        "rgba(250,250,250,0.05)",
                        "rgba(200,200,200,0.02)"
                    ]
                }
            }
        },
        "valueAxis": {
            "axisLine": {
                "show": true,
                "lineStyle": {
                    "color": "#cccccc"
                }
            },
            "axisTick": {
                "show": false,
                "lineStyle": {
                    "color": "#333"
                }
            },
            "axisLabel": {
                "show": true,
                "textStyle": {
                    "color": "#999999"
                }
            },
            "splitLine": {
                "show": false,
                "lineStyle": {
                    "color": [
                        "#eeeeee"
                    ]
                }
            },
            "splitArea": {
                "show": false,
                "areaStyle": {
                    "color": [
                        "rgba(250,250,250,0.05)",
                        "rgba(200,200,200,0.02)"
                    ]
                }
            }
        },
        "logAxis": {
            "axisLine": {
                "show": true,
                "lineStyle": {
                    "color": "#cccccc"
                }
            },
            "axisTick": {
                "show": false,
                "lineStyle": {
                    "color": "#333"
                }
            },
            "axisLabel": {
                "show": true,
                "textStyle": {
                    "color": "#999999"
                }
            },
            "splitLine": {
                "show": true,
                "lineStyle": {
                    "color": [
                        "#eeeeee"
                    ]
                }
            },
            "splitArea": {
                "show": false,
                "areaStyle": {
                    "color": [
                        "rgba(250,250,250,0.05)",
                        "rgba(200,200,200,0.02)"
                    ]
                }
            }
        },
        "timeAxis": {
            "axisLine": {
                "show": true,
                "lineStyle": {
                    "color": "#cccccc"
                }
            },
            "axisTick": {
                "show": false,
                "lineStyle": {
                    "color": "#333"
                }
            },
            "axisLabel": {
                "show": true,
                "textStyle": {
                    "color": "#999999"
                }
            },
            "splitLine": {
                "show": true,
                "lineStyle": {
                    "color": [
                        "#eeeeee"
                    ]
                }
            },
            "splitArea": {
                "show": false,
                "areaStyle": {
                    "color": [
                        "rgba(250,250,250,0.05)",
                        "rgba(200,200,200,0.02)"
                    ]
                }
            }
        },
        "toolbox": {
            "iconStyle": {
                "normal": {
                    "borderColor": "#999999"
                },
                "emphasis": {
                    "borderColor": "#666666"
                }
            }
        },
        "legend": {
            "textStyle": {
                "color": "#999999"
            }
        },
        "tooltip": {
            "axisPointer": {
                "lineStyle": {
                    "color": "#cccccc",
                    "width": 1
                },
                "crossStyle": {
                    "color": "#cccccc",
                    "width": 1
                }
            }
        },
        "timeline": {
            "lineStyle": {
                "color": "#4ea397",
                "width": 1
            },
            "itemStyle": {
                "normal": {
                    "color": "#4ea397",
                    "borderWidth": 1
                },
                "emphasis": {
                    "color": "#4ea397"
                }
            },
            "controlStyle": {
                "normal": {
                    "color": "#4ea397",
                    "borderColor": "#4ea397",
                    "borderWidth": 0.5
                },
                "emphasis": {
                    "color": "#4ea397",
                    "borderColor": "#4ea397",
                    "borderWidth": 0.5
                }
            },
            "checkpointStyle": {
                "color": "#4ea397",
                "borderColor": "rgba(60,235,210,0.3)"
            },
            "label": {
                "normal": {
                    "textStyle": {
                        "color": "#4ea397"
                    }
                },
                "emphasis": {
                    "textStyle": {
                        "color": "#4ea397"
                    }
                }
            }
        },
        "visualMap": {
            "color": [
                "#d0648a",
                "#22c3aa",
                "#adfff1"
            ]
        },
        "dataZoom": {
            "backgroundColor": "rgba(255,255,255,0)",
            "dataBackgroundColor": "rgba(222,222,222,1)",
            "fillerColor": "rgba(114,230,212,0.25)",
            "handleColor": "#cccccc",
            "handleSize": "100%",
            "textStyle": {
                "color": "#999999"
            }
        },
        "markPoint": {
            "label": {
                "normal": {
                    "textStyle": {
                        "color": "#ffffff"
                    }
                },
                "emphasis": {
                    "textStyle": {
                        "color": "#ffffff"
                    }
                }
            }
        }
    });
}));