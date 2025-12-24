var smt_syscharts = `
<div class="chart-types">
<div class="chart-type"><img class="chartimg" id="barChart" src="/static/smartchart/editor/echart/img/bar.webp"></div>
<div class="chart-type"><img class="chartimg" id="lineChart" src="/static/smartchart/editor/echart/img/line.webp"></div>
<div class="chart-type"><img class="chartimg" id="pieChart" src="/static/smartchart/editor/echart/img/pie.webp"></div>
<div class="chart-type"><img class="chartimg" id="gaugeChart" src="/static/smartchart/editor/echart/img/gauge.webp"></div>
</div>
<div class="chart-options">
  <!-- 主要图表类型 -->
  <div class="option-section">
    <div class="section-title">常规图表</div>
    <button class="option-btn iconfont iconrefresh1" id="lastChart">恢复原始</button>
    <button class="option-btn iconfont iconmianban" id="h1Chart">大字报</button>
    <button class="option-btn iconfont iconchart-trend-full" id="diyChart">线柱图</button>
    <button class="option-btn iconfont iconchart-trend-full" id="dlineChart">细节线图</button>
    <button class="option-btn iconfont iconleidatu" id="radarChart">雷达图</button>
    <button class="option-btn iconfont iconxuritu" id="sunburstChart">旭日图</button>
    <button class="option-btn iconfont iconzidantu" id="zdChart">子弹图</button>
    <button class="option-btn iconfont iconloudoutu" id="funnelChart">漏斗图</button>
    <button class="option-btn iconfont iconsandiantu" id="scatterChart">散点图</button>
    <button class="option-btn iconfont icontimelinechart" id="timelinechart">时间轴图</button>
    <button class="option-btn iconfont iconPipedepth" id="drillchart">钻取图</button>
  </div>

  <!-- 表格相关功能 -->
  <div class="option-section">
    <div class="section-title">表格功能</div>
    <button class="option-btn iconfont iconbiaoge" id="tableChart">表格</button>
    <button class="option-btn iconfont iconbiaoge" id="vuetableChart">V表格</button>
    <button class="option-btn iconfont iconlunbobiaoge" id="liMTable">滚动表格</button>
    <button class="option-btn iconfont icondanganziliao-biaogetianxie" id="excelChart">Excel表格</button>
    <button class="option-btn iconfont iconbiaoge" id="lineUpChart">lineUp图</button>
    <button class="option-btn iconfont icondanganziliao-biaogetianxie" id="pivotchart">透视图</button>
  </div>
  
    <!-- V系列功能 -->
  <div class="option-section">
    <div class="section-title">Vue组件</div>
    <button class="option-btn iconfont iconvuejs" id="vueChart">V筛选器</button>
    <button class="option-btn iconfont iconvuejs" id="vueStat">V统计</button>
    <button class="option-btn iconfont iconvuejs" id="vueDesc">V描述</button>
    <button class="option-btn iconfont iconshuxingtu" id="vueTree">V树形</button>
    <button class="option-btn iconfont icontime" id="vueTimeline">V时间线</button>
    <button class="option-btn iconfont iconbiaoge" id="vueForm">V表单</button>
    <button class="option-btn iconfont iconbiaoge" id="vuePrint">V打印</button>
  </div>

  <!-- 地图相关 -->
  <div class="option-section">
    <div class="section-title">地图相关</div>
    <button class="option-btn iconfont iconditu" id="mapChart">标准地图</button>
    <button class="option-btn iconfont iconditu_guangdong" id="zmapChart">全能地图</button>
    <button class="option-btn iconfont iconditu" id="bmapChart">百度地图</button>
  </div>
  
    <!-- 其他功能 -->
  <div class="option-section">
    <div class="section-title">其他图形</div>
    <button class="option-btn iconfont iconicon-test" id="mutiChart">多区域图</button>
    <button class="option-btn iconfont iconchartwordcloud" id="wordChart">词云图</button>
    <button class="option-btn iconfont iconshuiqiutu" id="liquidChart">水球图</button>
    <button class="option-btn iconfont icongantetu" id="gantChart">甘特图</ketton>
    <button class="option-btn iconfont iconrilitu" id="calendarChart">日历图</button>
    <button class="option-btn iconfont iconKxiantu" id="candleChart">K线图</button>
    <button class="option-btn iconfont iconsangjitu" id="sankeyChart">桑基图</button>
    <button class="option-btn iconfont iconxiangxiantu" id="boxplotChart">箱线图</button>
    <button class="option-btn iconfont iconheliutu" id="riverChart">河流图</button>
    <button class="option-btn iconfont iconuizujian" id="textChart">文字图</button>
    <button class="option-btn iconfont iconbiaodanzujian-xialakuang" id="filterChart">筛选器</button>
    <button class="option-btn iconfont icontime" id="timechart">时间</button>
    <button class="option-btn iconfont iconed_div" id="qrChart">二维码</button>
    <button class="option-btn iconfont iconline-slideshowhuandengpianfangying-02" id="swaperTable">连播</button>
  </div>

  <!-- 3D相关 -->
  <div class="option-section">
    <div class="section-title">3D模型</div>
    <button class="option-btn iconfont iconed_ds" id="d3Chart">3D模型</button>
  </div>


</div>

`;
var barChart = `let series =[];
let dataset = __dataset__;
for (let i=1;i<dataset[0].length;i++){
    series.push({
        type: 'bar',
        itemStyle: {
            borderRadius: 6,
         },
        emphasis:{
            focus: "data"
        },
        //stack: 'A', //开启堆叠
      }
    )
}

option__name__= {
    dataset:{source:dataset },
    title: {
        text: "",
        textStyle: {
         fontSize: '20px',
       },
    },
    legend: {
        show:true,
        textStyle: {
         fontSize: "12px",
       },
    },
    tooltip: {},
    xAxis: {
        type: 'category',
        axisLabel: {
            textStyle: {
                fontSize:"12px"
            }
       },
    },
    yAxis: {
        type: 'value',
        axisLabel: {
            textStyle: {
                fontSize:"12px"
            }
       },
    },
    series: series
};
`;

var lineChart =`let series =[];
let dataset = __dataset__;
for (let i=1;i<dataset[0].length;i++){
    series.push({
        type: 'line',
        smooth: true,
        //stack: 'A', //开启堆叠
        //areaStyle: {}, //面积图
        //step:'start', //阶梯图middle,end
      }
    )
}

option__name__= {
    dataset:{source:dataset },
    title: {
        text: "",
        textStyle: {
         fontSize: "20px",
       },
    },
    legend: {
        show:true,
        textStyle: {
         fontSize: "12px",
       },
    },
    tooltip: {},
    xAxis: {
        type: 'category',
        axisLabel: {
            textStyle: {
                fontSize:"12px"
            }
       },
    },
    yAxis: {
        type: 'value',
        axisLabel: {
            textStyle: {
                fontSize:"12px"
            }
       },
    },
    series: series
};
`;

var pieChart =`let dataset = __dataset__; 
let series =[];
for (let i=1;i<dataset.length;i++){
    series.push({
        name: dataset[i][0],
        value: dataset[i][1],
        emphasis:{
            focus: "data"
        }
    })
}

option__name__ = {
    title: {
        text: dataset[0][1],
        left: 'center',
        top: 20,
        textStyle: {
            fontSize: "20px"
        }
    },
    tooltip : {
        trigger: 'item',
    },
    series : [
        {
            name:dataset[0][1],
            type:'pie',
            radius : ['10%', '55%'],
            center: ['50%', '50%'],
            //roseType: 'radius', 
            label: {
                textStyle: {
                    fontSize: "12px"
                }
            },
            itemStyle: {
                borderRadius: 6
            },
            data: series
        }
    ]
};
`;

var gaugeChart = `let dataset=__dataset__;
option__name__={ 
    tooltip : {},
    title:{
        text:''
    },
    series: [
    {
        name: dataset[0][1],
        type: 'gauge',
        min: 0,
        max: dataset[1][2],
        splitNumber: 10,
        axisLabel:{
           fontSize: "6px" 
        },
        axisTick:{
            distance: 2,
            length: "24px",
            splitNumber: 5
        },
        splitLine:{
            distance: 8,
            length: "5%"
        },
        pointer:{
            icon: '', //circle,rect,roundRect,triangle,diamond,pin,arrow
            length: '60%',
            width: 6
        },
        detail: {
            formatter:'{value}',
            textStyle:{
                fontSize:"12px"
            },
        },
        data: [
            {value: dataset[1][1],name:dataset[1][0],
             title:{
                show: true,
                fontSize: "10px"
           }
        }]
    }
    ]                        
 };
`;

var filterChart = `let dataset=__dataset__;
let table =\`
<label style="margin-right:5px">选择</label>
<select id="id_select__name__"
 style="width:100px;height:25px;">
\`;
table = table + '<option value="" selected>----</option>';
 for(let i=1;i<dataset.length;i++){ 
  table = table + '<option>' + dataset[i][0] + '</option>';
 }
table = table + '</select>'

dom__name__.innerHTML=table;
`;

var tableChart = `let dataset=__dataset__;
let table = '<div ><table class="table">';
//头部
table += '<thead ><tr>';
for(let j=0; j<dataset[0].length;j++){
  table = table + "<td>" + dataset[0][j] + "</td>";
};
table += "</tr></thead>";

//表主体
table += "<tbody>";
 for(let i=1;i<dataset.length;i++){
    if(i%2==0){table += "<tr style='background-color:#cfe2f3'>";}
     else{table += "<tr>"};
    for (j=0; j<dataset[i].length;j++){
       table = table + "<td>" + dataset[i][j] + "</td>";
      };
      table += "</tr>";
 };
 table += "</tbody></table></div>";

dom__name__.innerHTML=table;`;

var vueChart = `
let dataset = __dataset__;
let table = \`
<div id="v__name__">
<el-select v-model="param.value" placeholder="请选择" @change="refresh" clearable>
<el-option v-for="item in ds.slice(1)" :key="item[0]" :label="item[0]" :value="item[0]"></el-option>
</el-select></div>\`;
dom__name__.innerHTML=table;
ds_vue('#v__name__',dataset,param={value:''},ds_list=[1,2]);

`;
var vueDesc = `
let dataset = __dataset__;
let table = \`
<div id="v__name__">
<el-descriptions size="mini" :column="3" border title="信息">
<el-descriptions-item v-for="(value,item) in ds[0]" :key="item" :label="item">
<span >{{value}}</span></el-descriptions-item></el-descriptions></div>\`;
dom__name__.innerHTML=table;
ds_vue('#v__name__',ds_createMap_all(dataset));
`;

var vueStat = `
let dataset = __dataset__;
dataset = ds_getStatistic(dataset);
dataset = ds_createMap_all(dataset)[0];

let table = \`
<div id="v__name__" style="display:flex;height:100%;align-items:center">
<el-statistic  v-for="(value, key) in ds" :title='key'>
<template slot="formatter">{{value}}</template>
</el-statistic></div>\`;

dom__name__.innerHTML=table;
ds_vue('#v__name__',dataset);
`;
var vueTimeline = `
let dataset = __dataset__;
dataset = 
[["content","timestamp","color","icon"],
["支持使用图标","2018-04-12 20:46","green","el-icon-more"],
["支持自定义颜色","2018-04-03 20:46",'red',''],
["支持自定义尺寸","2018-04-03 20:46","",'']];
let table = \`
<div id="v__name__">
  <el-timeline>
    <el-timeline-item
      v-for="(activity, index) in ds"
      :key="index"
      :icon="activity.icon"
      :color="activity.color"
      :timestamp="activity.timestamp">
      {{activity.content}}
    </el-timeline-item>
  </el-timeline>
 </div>\`;
dom__name__.innerHTML=table;
ds_vue('#v__name__',ds_createMap_all(dataset));
`;
var vueForm = `
let dataset = __dataset__;
let table = \`
<div id="v__name__" style="overflow:auto;height:100%">
<el-form ref="form" :model="form" size="small" :inline="false" label-width="80px" id="v__name__">
  <el-form-item label="活动名称">
    <el-input v-model="form.name"></el-input>
  </el-form-item>
  <el-form-item label="活动区域">
    <el-select v-model="form.region" placeholder="请选择活动区域">
      <el-option label="区域一" value="shanghai"></el-option>
      <el-option label="区域二" value="beijing"></el-option>
    </el-select>
  </el-form-item>
  <el-form-item label="活动时间">
    <el-col :span="11">
      <el-date-picker type="date" placeholder="选择日期" v-model="form.date1" style="width: 100%;"></el-date-picker>
    </el-col>
    <el-col class="line" :span="2">-</el-col>
    <el-col :span="11">
      <el-time-picker placeholder="选择时间" v-model="form.date2" style="width: 100%;"></el-time-picker>
    </el-col>
  </el-form-item>
  <el-form-item label="即时配送">
    <el-switch v-model="form.delivery"></el-switch>
  </el-form-item>
  <el-form-item label="活动性质">
    <el-checkbox-group v-model="form.type">
      <el-checkbox label="线下主题活动" name="type"></el-checkbox>
      <el-checkbox label="单纯品牌曝光" name="type"></el-checkbox>
    </el-checkbox-group>
  </el-form-item>
  <el-form-item label="特殊资源">
    <el-radio-group v-model="form.resource">
      <el-radio label="线上品牌商赞助"></el-radio>
      <el-radio label="线下场地免费"></el-radio>
    </el-radio-group>
  </el-form-item>
  <el-form-item label="活动形式">
    <el-input type="textarea" v-model="form.desc"></el-input>
  </el-form-item>
  <el-form-item>
    <el-button type="primary" @click="onSubmit">立即创建</el-button>
    <el-button>取消</el-button>
  </el-form-item>
</el-form>
</div>\`;
dom__name__.innerHTML=table;
loadVue().then(
 ()=>{
new Vue({el:'#v__name__',
 data:{
   form: {
      name: '',
      region: '',
      date1: '',
      date2: '',
      delivery: false,
      type: [],
      resource: '',
      desc: ''
        }
    },
 methods:{
    onSubmit() {
        //ds_save(1,this.form)
    }
 }
});
});
`;

var vueTree = `
let dataset = __dataset__;
let table = \`
<div id="v__name__" style="overflow:auto;height:100%">
<el-tree :data="ds"  @node-click="refresh"></el-tree>
</div>\`;
dom__name__.innerHTML=table;
loadVue().then(
 ()=>{
new Vue({el:'#v__name__',data:{ds:ds_tree(dataset)},methods:{
 refresh(node, data){
     if(data.isLeaf){
        let param = data.data.id;
        if(param == filter_param._label){param = ''}
        ds_setParam('_label',param);
        //ds_refresh(1)
    }
 }
}});
});
`;
var vuePrint=`
let dataset = __dataset__;
dataset={
        products: [
            {
                name: "xxxxxx",
                quantity: 1
            }
        ]
};

let table = \`
<div id="v__name__" style="overflow:auto;height:100%">
<div class="container" id="printCard">
    <div class="header">
        <div class="company-name">xx有限公司</div>
        <div class="document-title">发货单</div>
    </div>
    <table class="master-table">
        <tr>
            <td class="info-label">供货:</td>
            <td class="info-value">XXX有限公司</td>
            <td class="info-label">客户名称:</td>
            <td class="info-value">电商</td>
        </tr>
    </table>
    <table class="products-table">
        <thead>
            <tr>
                <th width="10%">序号</th>
                <th width="70%">名称</th>
                <th width="20%">数量</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="(product, index) in products" :key="index">
                <td>{{ index+1 }}</td>
                <td>{{ product.name }}</td>
                <td>{{ product.quantity }}</td>
            </tr>
            <tr><td>合计</td><td></td><td>120</td></tr>
        </tbody>
    </table>
   <div style="padding:4px"><span class="info-label">备注:</span><span class="info-value">补发单</span></div>
    <div class="action-buttons">
        <button class="btn btn-primary" @click="printDocument('printCard')">打印</button>
    </div>
</div>
</div>\`;
ds_loadcss('printJS');
setTimeout(function() {
  ds_chart(table);
  loadVue().then(()=>{
    new Vue({el:'#v__name__',
      data: dataset,
      methods: {
        async printDocument(t) {
            await ds_loadjs('printJS',True);
            printJS({
                    printable: t,
                    type: 'html',
                    scanStyles: false,
                    style: \`@page {size: auto;}body{font-size: 12px}.action-buttons{display:none}\`,
                    css:'/static/smartchart/opt/printJS.css'
            });
        }
       }
     });
  });
 },100);
`;

var diyChart = `let dataset = __dataset__; 
let legend_label = ds_rowname(dataset);
let xlabel = dataset[0].slice(1);
dataset = ds_createMap(dataset);

option__name__  = {
   title: {
       text: '',
       left: 'center'
    }, 
    tooltip: {
       trigger: 'item',
       formatter: '{a} <br/>{b} : {c}' 
    },
    legend: {
       left: 'center',
       data: legend_label
    }, 
    xAxis: {
       type: 'category',
       data: xlabel
    }, 
    //多Y轴
    yAxis: [{
        type: 'value',
        name:'',
        position:'left'
    },{
        type: 'value',
        name:'差异',
        position : 'right'
    }],
    
   series: [{
        name: legend_label[0],
        data: dataset[legend_label[0]],
        type: 'bar'
   },
   {
        name: legend_label[1],
        data: dataset[legend_label[1]],
        type: 'line',
        yAxisIndex:1 //定义坐标
    }
 ]
};`;

var h1Chart=`//select 指标A，指标B..;select xxx
let dataset = __dataset__;
dataset = ds_getStatistic(dataset);
let imgDict ={"指标":"图片"};
let colorDict = {"指标":"颜色"};

let itemStr='';
for (let i=0;i< dataset[0].length;i++){
let key=dataset[0][i];
let value=dataset[1][i];
let imgsrc = imgDict[key]|| '/static/smartchart/editor/echart/img/bar.webp';
let color = colorDict[key]||'white'
itemStr = \`\${itemStr}
<div class="center" style="flex:1;margin:5px;padding:15px;background-color:\${color};border-radius:5px;">
<img src="\${imgsrc}" width="50px">
<div style="padding:5px;">
<h2>\${key}</h2>
<h3>\${value}</h3>
</div>
</div>\`;
}

let table = \`
<div class="center" style="height:100%">
\${itemStr}
</div>
\`;
dom__name__.innerHTML=table;
`;

var mutiChart = `let dataset = __dataset__; 
let legend_label = ds_rowname(dataset);
let xlabel = dataset[0].slice(1);
dataset = ds_createMap(dataset);

option__name__= {
  title: [
    {
      left: '20%',
      text: legend_label[0]
    },
    {
      right: '25%',
      text: legend_label[1]
    },
    {
      left: '20%',
      bottom: '50%',
      text: legend_label[2]
    },
    {
      right: '25%',
      bottom: '50%',
      text: legend_label[3]
    }
  ],
  tooltip: {
    trigger: 'axis'
  },
  xAxis: [
    {
      data: xlabel
    },
    {
      data: xlabel,
      gridIndex: 1
    },
    {
      data: xlabel,
      gridIndex: 2
    },
    {
      data: xlabel,
      gridIndex: 3
    }
  ],
  yAxis: [
    {},
    {
      gridIndex: 1
    },
    {
      gridIndex: 2
    },
    {
      gridIndex: 3
    }
  ],
  grid: [
    {
      bottom: '60%',
      right: '55%'
    },
    {
      bottom: '60%',
      left: '55%'
    },
    {
      top: '60%',
      right: '55%'
    },
    {
      top: '60%',
      left: '55%'
    },
  ],
  series: [
    {
      type: 'line',
      showSymbol: false,
      data: dataset[legend_label[0]]
    },
    {
      type: 'bar',
      showSymbol: false,
      data: dataset[legend_label[2]],
      xAxisIndex: 1,
      yAxisIndex: 1
    },
    {
      type: 'bar',
      showSymbol: false,
      data: dataset[legend_label[3]],
      xAxisIndex: 2,
      yAxisIndex: 2
    },
    {
      type: 'line',
      showSymbol: false,
      data: dataset[legend_label[3]],
      xAxisIndex: 3,
      yAxisIndex: 3
    }
  ]
};`;

var liMTable= `let dataset = __dataset__; 
let tablehead = '';
let tablebody = '';

for(i=0;i<dataset[0].length; i++){
    tablehead = \`\${tablehead}<span>\${dataset[0][i]}</span>\`;
}

for(let i=1; i<dataset.length; i++){
    let temp='';
    for(let j=0; j<dataset[i].length; j++){
        temp=\`\${temp\}<span>\${dataset[i][j]}</span>\`;
    }
    tablebody=\`\${tablebody}<li>\${temp}</li>\`;
}

let table =\`
<div class="smtlisthead">\${tablehead}</div>
<div class="smtlistnav smtlist__name__">
 <ul>\${tablebody}</ul>
</div>\`;
dom__name__.innerHTML=table;

ds_scroll('.smtlist__name__', interval = 1000, step = 10);
//ds_liMarquee('.smtlist__name__');
`;

var swaperTable = `let dataset = __dataset__;
dataset = [['url'],['/static/smartui/img/smartlogo.png'],['/static/smartui/img/smartviplogo.png']];
let myslides='';

for(i=1;i<dataset.length;i++){
    myslides = \`\${myslides}<div class="swiper-slide"><img src ="\${dataset[i][0]}"></div>\`;
}

let table = \`<div class="swiper swiper__name__" style="width:100%">
<div class="swiper-wrapper">\${myslides}</div></div>\`;
dom__name__.innerHTML=table;

ds_swiper('.swiper__name__');
`;
var lineUpChart = `ds_loadcss('smt_LineUp');
ds_loadjs('smt_LineUp');
let dataset = __dataset__;
dataset = ds_createMap_all(dataset);
try{Ljs__name__.destroy()}catch{}
Ljs__name__ = LineUpJS.asLineUp(dom__name__, dataset);
`;
var funnelChart = `let dataset = __dataset__;
let legend_label = ds_rowname(dataset);
let series =[];
for (let i=1;i<dataset.length;i++){
    series.push({name: dataset[i][0],value: dataset[i][1]})
}

option__name__={
    tooltip: {
        trigger: 'item',
        formatter: "{c}"
    },
    calculable: true,
    series: [
        {
            type:'funnel',
            left: '10%',
            top: 60,
            bottom: 60,
            width: '80%',
            min: 0,
            max: 100,
            minSize: '0%',
            maxSize: '100%',
            sort: 'descending',
            gap: 2,
            label: {
                show: true,
                position: 'inside'
            },
            labelLine: {
                length: 10,
                lineStyle: {
                    width: 1,
                    type: 'solid'
                }
            },
            itemStyle: {
                borderColor: '#fff',
                borderWidth: 1
            },
            emphasis: {
                label: {
                    fontSize: 20
                }
            },
            data: series
        }
    ]                                    
};`;

var scatterChart=`let dataset=__dataset__;
dataset=[['x','y'],[10,12],[11,15],[20,31]];
option__name__ = {
    title: {
        text:dataset[0][0]
    },
    xAxis: {},
    yAxis: {},
    series: [{
        symbolSize: 20,
        data: dataset ,
        type: 'scatter'
    }]
};
`;

var excelChart=`let dataset = __dataset__;
let options = {
    view: true,  //查看发布
    dev_mode: true, //开发方式
    allowEdit:true, //可编辑
    //plugins: ['chart'], //启用图形
};
ds_excel_upload('__name__', dataset, options);
`;

var wordChart=`//select 词名,数量
//需多点一次运行查看,仪表中显示需先在"模板"-->资源中加载词云js文件
ds_loadjs('smt_wordcloud');
let dataset = __dataset__;
let legend_label = ds_rowname(dataset);
dataset = ds_createMap(dataset);

let series=[];
for (let i=0;i<legend_label.length;i++){
 series.push({name:legend_label[i],value:dataset[legend_label[i]]})
}

option__name__={
tooltip: {
        show: true
    },
    series: [{
        type: 'wordCloud',
        sizeRange: [6, 88],//画布范围，如果设置太大会出现少词（溢出屏幕）
        rotationRange: [-45, 90],//数据翻转范围
        //shape: 'circle',
        textPadding: 0,
        autoSize: {
            enable: true,
            minSize: 6
        },
        textStyle: {
                color: function() {
                    return 'rgb(' + [
                        Math.round(Math.random() * 160),
                        Math.round(Math.random() * 160),
                        Math.round(Math.random() * 160)
                    ].join(',') + ')';
            },
            emphasis: {
                shadowBlur: 10,
                shadowColor: '#333'
            }
        },
        data:series 
        }]
                                     
};
`;
var radarChart=`//select 维度,指标1, 指标2,..., 目标  注意最后一列是目标
let dataset = __dataset__; 
dataset = ds_transform(dataset);
legend_label = ds_rowname(dataset);
let title=dataset[0][0];
let xlabel = dataset[0].slice(1);
dataset = ds_createMap(dataset);
let indicator=[];
let series=[];
let target = dataset[legend_label.pop()];
for(i=0; i<target.length;i++){
    indicator.push({name:xlabel[i],max:target[i]})
}
for(i=0; i<legend_label.length;i++){
    series.push({value:dataset[legend_label[i]],name:legend_label[i]});
}

option__name__ = {
    title: {
        text: title
    },
    tooltip: {},
    legend: {
        data: legend_label
    },
    radar: {
        // shape: 'circle',
        name: {
            textStyle: {
                color: '#fff',
                backgroundColor: '#999',
                borderRadius: 3,
                padding: [3, 5]
           }
        },
        indicator:indicator
    },
    series: [{
        name: title ,
        type: 'radar',
        // areaStyle: {normal: {}},
        data :series
    }]
};
`;
var mapChart=`//select province, value
//ds_loadjson('/static/echart/map/广东省.json','mmp'); //自定义
//ds_loadjs('smt_world'); //世界
ds_loadjs('smt_china');
let mapType = 'china';   //world,mmp
//设置值范围
let minvalue=0;
let maxvalue=6000;
let dataset = __dataset__;
let title = dataset[0][0];
let series=[];
for (let i=1;i<dataset.length;i++){
 series.push({name:dataset[i][0],value:dataset[i][1]})
}

option__name__ = {
    title: {},
    tooltip : {
        trigger: 'item'
    },
    dataRange: {
        min : minvalue,
        max : maxvalue,
        calculable : true,
        //orient : horizontal,
        //color: ['#ff3333', 'orange', 'yellow','lime','aqua'],
        textStyle:{
            //color:'#fff'
        }
     },
    series: [
        {
            name: title,
            type: 'map',
            mapType: mapType,
            roam: false,
            label:{
                show: true,
                emphasis: {show: false}
           },
          data:series
        }
      ]
    };
`;
var pivotchart=`let dataset=__dataset__;
ds_loadpivot(); //透视图需购买专业版
let pivotOption = {
    rendererName:'表格',
    aggregatorName: '求和',
    rows: [],cols: [],vals:[],
    rendererOptions:{table:{rowTotals: false,colTotals:true}},
    showUI: true
};
$(dom__name__).pivotUI(dataset, pivotOption,true);`;

var timelinechart=`//select 维度,指标1,指标2,指标3...
let dataset = __dataset__; 
legend_label = ds_rowname(dataset);
xlabel = dataset[0].slice(1);
dataset = ds_createMap(dataset);

let series =[];
for (let i=0;i<legend_label.length;i++){
    series.push({
        title: {
             text: legend_label[i]
         },
        series: [
            {
                data: dataset[legend_label[i]],
            },
        ]
    });
}

option__name__= {
    baseOption: {
        timeline: {
            //loop: false,        
            axisType: 'category',
            show: true,
            autoPlay: true,
            playInterval: 2000,
            data: legend_label
        },
        xAxis: [{type: 'category',name: 'day',data: xlabel}],
        yAxis: { type: 'value', name: 'qty' },
        series: [{type: 'bar'}],
        tooltip: {}
    },
    options:series
}`;

var drillchart=`//select 大类,值;select 大类,小类,值
let dataset = __dataset__; 
df0 = dataset.df0;
df1 = dataset.df1;

let xdata =[];
let seriesdata = [];
let drilldownData = [];
let kv = new Map();
for (let i=1;i<df1.length;i++){
    if(kv.hasOwnProperty(df1[i][0])){
        kv[df1[i][0]].push(df1[i].slice(1));
    }else{
        kv[df1[i][0]] = [df1[i].slice(1)];
    }
}

for (i=1;i<df0.length;i++){
    xdata.push(df0[i][0]);
    seriesdata.push({
        value: df0[i][1],
        groupId: df0[i][0]
      });
    drilldownData.push({
    dataGroupId: df0[i][0],
    data: kv[df0[i][0]]
     });
}

option__name__= {
  xAxis: {
    data: xdata
  },
  yAxis: {},
  dataGroupId: '',
  animationDurationUpdate: 500,
  series: {
    type: 'bar',
    id: 'sales',
    data:seriesdata,
    universalTransition: {
      enabled: true,
      divideShape: 'clone'
    }
  }
};

myChart__name__.on('click', event => {
  if (event.data) {
    const subData = drilldownData.find(data => {
      return data.dataGroupId === event.data.groupId;
    });
    if (!subData) {
      return;
    }
    myChart__name__.setOption({
      xAxis: {
        data: subData.data.map(item => {
          return item[0];
        })
      },
      series: {
        type: 'bar',
        id: 'sales',
        dataGroupId: subData.dataGroupId,
        data: subData.data.map(item => {
          return item[1];
        }),
        universalTransition: {
          enabled: true,
          divideShape: 'clone'
        }
      },
      graphic: [
        {
          type: 'text',
          left: 50,
          top: 20,
          style: {
            text: '返回',
            fontSize: 18
          },
          onclick: function() {
            myChart__name__.setOption(option__name__, true);
          }
        }
      ]
    });
  }
});
myChart__name__.setOption(option__name__);`

var timechart=`let t = setTimeout(time,1000);
function time()
{
   clearTimeout(t);
   let dt = new Date();
   let y=dt.getFullYear();
   let mt=dt.getMonth()+1;
   let day=dt.getDate();
   let h=dt.getHours();
   let m=dt.getMinutes();
   let s=dt.getSeconds();
   dom__name__.innerHTML = y+"年"+mt+"月"+day+"-"+h+"时"+m+"分"+s+"秒";
   t = setTimeout(time,1000);
}`;

var vuetableChart=`
let dataset = __dataset__;
let table = \`<div id="v__name__" style="height:100%">
<el-table :data="ds_createMap_all(ds)"
height="100%" size="mini" border
style="width:100%"
header-cell-style="background:#d9d9d9">
<el-table-column v-for="item of ds[0]" :label="item" :property="item" sortable></el-table-column>
</el-table></div>\`;
dom__name__.innerHTML=table;
ds_vue('#v__name__',dataset);
`;
var calendarChart=`//select 日期, 值
let dataset = __dataset__; 
dataset= dataset.slice(1);
dataset = [['2019-10-01',12],['2019/10/02',1000]];
let month = dataset[1][0].substring(0,7);
option__name__= {
    tooltip: {
        position: 'top'
    },
    visualMap: {
        show: false,
        min: 0,
        max: 1000
    },
    calendar: [{
        left: 'center',
        top: 'middle',
        cellSize: [30, 30],
        yearLabel: {show: true},
        orient: 'vertical',
        dayLabel: {
            firstDay: 1,
            nameMap: 'cn'
        },
        monthLabel: {
            show: true
        },
        range: month
    }],
    series: {
        type: 'heatmap',
        coordinateSystem: 'calendar',
        data: dataset
    }
};`;
var gantChart=`// select 项目名, 开始时间, 结束时间
let dataset = __dataset__; 
let legend_label = ds_rowname(dataset);
dataset = ds_createMap(dataset);

let series =[];
for (let i=0;i<legend_label.length;i++){
    series.push(
        {
            name: legend_label[i],
            type: "bar",
            stack: legend_label[i],
            label: {
                normal: {
                    show: true,
                    color: "#000",
                    position: "right",
                    formatter: function(params) {
                        return params.seriesName
                    }
                }
            },
            itemStyle: {
                normal: {
                    color: "skyblue",
                    borderColor: "#fff",
                    borderWidth: 2
                }
            },
            zlevel: -1,
            data: [new Date(dataset[legend_label[i]][1])]
        },
        {
            name: legend_label[i],
            type: "bar",
            stack: legend_label[i],
            itemStyle: {
                normal: {
                    color: "white",
                }
            },
            zlevel: -1,
            z: 3,
            data:[new Date(dataset[legend_label[i]][0])]
        }
        );
}
option__name__= {
    backgroundColor: "#fff",
    title: {
        text: "甘特图",
        padding: 20,
        textStyle: {
            fontSize: 17,
            fontWeight: "bolder",
            color: "#333"
        },
        subtextStyle: {
            fontSize: 13,
            fontWeight: "bolder"
        }
    },
    legend: {
        data:legend_label,
        align: "right",
        right: 80,
        top: 50
    },
    grid: {
        containLabel: true,
        show: false,
        right: 130,
        left: 40,
        bottom: 40,
        top: 90
    },
    xAxis: {
        type: "time",
        axisLabel: {
            "show": true,
            "interval": 0
        }
    },
    yAxis: {
        axisLabel: {
            show: true,
            interval: 0,
            formatter: function(value, index) {
                let last = ""
                let max = 5;
                let len = value.length;
                let hang = Math.ceil(len / max);
                if (hang > 1) {
                    for (let i = 0; i < hang; i++) {
                        let start = i * max;
                        let end = start + max;
                        let temp = value.substring(start, end) + "\\n";
                        last += temp;
                    }
                    return last;
                } else {
                    return value;
                }
            }
        },
        data: ["维度"]
    },
    tooltip: {
        trigger: "axis",
        formatter: function(params) {
            let res = "";
            let name = "";
            let start = "";
            let end = "";
            for (let i in params) {
                let k = i % 2;
                if (!k) { //偶数
                   start = params[i].data.format('yyyy-MM-dd hh:mm:ss');
                }
                if (k) { //奇数
                    name = params[i].seriesName;
                    end = params[i].data.format('yyyy-MM-dd hh:mm:ss');;
                    res += name + " : " + end + "~" + start + "</br>";

                }
            }
            return res;
        }
    },
    series: series
}`;

var corChart=`let series =[];
let dataset = __dataset__;
for (let i=1;i<dataset[0].length;i++){
    series.push({type: 'bar',coordinateSystem: 'polar',stack: 'a'})
}
option__name__ = {
    angleAxis: {
        type: 'category',
        z: 10
    },
    radiusAxis:{},
    polar:{},
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            },
            position: function (pos, params, el, elRect, size) {
                var obj = {top: 10};
                obj[['left', 'right'][+(pos[0] < size.viewSize[0] / 2)]] = 30;
                return obj;
            },
            extraCssText: 'width: 170px'
        },
    dataset: {source: dataset },
    series: series,
    legend: {}
}`;
var qrChart=`let dataset = __dataset__;
ds_loadjs('QRCode');
let table=\`
<div id="qr__name__"></div>
\`
dom__name__.innerHTML = table;
let qrcode = new QRCode('qr__name__',{width:200, height:200});
qrcode.makeCode(dataset.code);`;

var dlineChart=`let series = [];
let dataset = __dataset__;
let minVal = Infinity, maxVal = -Infinity;
for(let i=1; i<dataset.length; i++){
    for(let j=1; j<dataset[i].length; j++){
        minVal = Math.min(minVal, dataset[i][j]);
        maxVal = Math.max(maxVal, dataset[i][j]);
    }
}
const padding = (maxVal - minVal) * 0.2;
for(let i=1; i<dataset[0].length; i++){
    series.push({
        type: 'line',
        smooth: true,   
        symbol: 'circle',  
        symbolSize: 8,  
        lineStyle: {
            width: 3, 
            shadowColor: 'rgba(0,0,0,0.3)',
            shadowBlur: 8,
            shadowOffsetY: 6
        },
        areaStyle: { 
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                offset: 0,
                color: 'rgba(63, 129, 231, 0.8)'
            }, {
                offset: 1,
                color: 'rgba(63, 129, 231, 0.1)'
            }])
        }
    })
}

option__name__ = {
    legend: {},
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'cross'
        }
    },
    dataset: { source: dataset },
    xAxis: {
        type: 'category',
        axisLabel: {
            rotate: 45 
        }
    },
    yAxis: {
        type: 'value',
        min: Math.floor(minVal - padding),
        max: Math.ceil(maxVal + padding), 
        scale: true,
        splitLine: {
            show: true,
            lineStyle: {
                type: 'dashed'
            }
        }
    },
    series: series,
};`;
var sunburstChart=`//select father,children,value
let dataset = __dataset__; 
dataset[0][3] = 'value';
dataset = ds_tree(dataset,label='name', children='children')
option__name__= {
  series: {
    type: 'sunburst',
    // emphasis: {
    //     focus: 'ancestor'
    // },
    data: dataset,
    radius: [0, '90%'],
    label: {
      rotate: 'radial'
    }
  }
};`;
var candleChart=`let dataset = __dataset__; 
dataset=[['时间','开盘价','收盘价','最低价','最高价'],['A',20,34,10,38],['B',40,35,30,50]]
let xlabel = ds_rowname(dataset); 

option__name__= {
  xAxis: {
    data: xlabel
  },
  yAxis: {},
  series: [
    {
      type: 'candlestick',
      data: ds_remove_column(dataset.slice(1),[0])
    }
  ]
};`;

var zdChart=`//select 维度, 实际值, 百分占比
let dataset = __dataset__; 
dataset = ds_transform(dataset);
let xlabel = dataset[0].slice(1);
let c0 = [100, 100, 100, 100, 100];
let c1 = dataset[1].slice(1);
let c2 = dataset[2].slice(1);
let myColor = ['#1089E7', '#F57474', '#56D0E3', '#F8B448', '#8B78F6'];
option__name__= {
    title: {
        text: '设备使用频率',
        x: 'center',
        textStyle: {
          //  color: '#FFF',
            fontSize: '1rem'
        },
        left: '6%',
        top: '10%'
    },
    //图标位置
    grid: {
        top: '20%',
        left: '32%'
    },
    xAxis: {
        show: false
    },
    yAxis: [{
        show: true,
        data: xlabel,
        inverse: true,
        axisLine: {
            show: false
        },
        splitLine: {
            show: false
        },
        axisTick: {
            show: false
        },
        axisLabel: {
           // color: '#fff',
            formatter: (value, index) => {
                return [\`{lg|\${index + 1}}  \` + '{title|' + value + '} '
                ].join('\\n')
            },
            rich: {
                lg: {
                    backgroundColor: '#339911',
                    color: '#fff',
                    borderRadius: 15,
                    // padding: 5,
                    align: 'center',
                    width: 15,
                    height: 15
                },
            }
        },


    }, {
        show: true,
        inverse: true,
        data: c1,
        axisLabel: {
            textStyle: {
                fontSize: 12,
               // color: '#fff',
            },
        },
        axisLine: {
            show: false
        },
        splitLine: {
            show: false
        },
        axisTick: {
            show: false
        },

    }],
    series: [{
        name: '条',
        type: 'bar',
        yAxisIndex: 0,
        data: c2,
        barWidth: 10,
        itemStyle: {
            normal: {
                barBorderRadius: 20,
                color: function(params) {
                    var num = myColor.length;
                    return myColor[params.dataIndex % num]
                },
            }
        },
        label: {
            normal: {
                show: true,
                position: 'inside',
                formatter: '{c}%'
            }
        },
    }, {
        name: '框',
        type: 'bar',
        yAxisIndex: 1,
        barGap: '-100%',
        data: c0,
        barWidth: 15,
        itemStyle: {
            normal: {
                color: 'none',
                borderColor: '#00c1de',
                borderWidth: 3,
                barBorderRadius: 15,
            }
        }
    }, ]
};
`;
var zmapChart=`//select 城市, 值
let dataset = __dataset__; 
dataset=[['A','B'],['安仁县',123]];
let flyds = [['源','目标','值'],['安仁县','长沙市',100]];

//http://datav.aliyun.com/portal/school/atlas/area_selector
ds_loadjson('/static/echart/map/湖南省.json','mmap');

//https://api.map.baidu.com/lbsapi/getpoint/index.html
//ds_loadjs('chinaCityCoords');
let chinaCityCoords = {
    "安仁县":[113.2829,26.718523],
    "长沙市":[112.951794,28.233617],
};

//水波纹
let scatterList=get_geoscatterList(dataset,chinaCityCoords);

//飞线
let flyList=get_geoflyList(flyds,chinaCityCoords);

option__name__ = {
    backgroundColor: 'rgba(0,0,0,0)',
    //center: []; // 地图中心位置,
    tooltip: {},
    geo: [
            {
              map: 'mmap',
              aspectScale: 1,
              roam: false, //是否允许缩放
              zoom: 1, // 缩放级别
            //  layoutSize: '95%',
             // layoutCenter: ['50%', '50%'],
              label: {
                show: true,
                emphasis: {
                  areaColor: '#fff',
                 // color: '#EEEEEE'
                }
              },
              itemStyle: {
                areaColor: 'transparent',
                borderColor: '#041549',
                borderWidth: 1,
                shadowBlur: 6,
                shadowOffsetY: 0,
                shadowOffsetX: 0,
                shadowColor: '#16ecfc',
                emphasis: {
                //  areaColor: 'rgba(115, 219, 249, 0)',
                  label: {
                   // color: '#fff'
                  }
                }
              },
              z: 4
            }, 
          ],
    series: [
        {
            name: '数量',
            type: 'effectScatter',
            coordinateSystem: 'geo',
            zlevel: 5,
            rippleEffect: { //涟漪特效
                period: 8, //动画时间，值越小速度越快
                brushType: 'stroke', //波纹绘制方式 stroke, fill
                scale: 3 //波纹圆环最大限制，值越大波纹越大
            },
            // z: 8,
            data: scatterList,
            symbolSize: 10,
            symbol: '',
            itemStyle: {
              borderWidth: 1,
              borderColor: 'green',
              color: 'orange',
              shadowBlur: 2
            }
        },
        {
        type: 'lines',
        zlevel: 2,
        effect: {
            show: true,
            period: 4, //箭头指向速度，值越小速度越快
            trailLength: 0.02, //特效尾迹长度[0,1]值越大，尾迹越长重
            symbol: 'arrow', //箭头图标
            symbolSize: 5, //图标大小
        },
        lineStyle: {
            width: 1, //尾迹线条宽度
            opacity: 1, //尾迹线条透明度
            curveness: .3, //尾迹线条曲直度
            // color:'red'
        },
        data: flyList
       }    
    ]
}
`;
var bmapChart=`//select 城市, 值

ds_loadBmap(); //请填写百度地图开发者ak

let dataset = __dataset__; 
dataset=[['A','B'],['安仁县',123]];

//ds_loadjs('chinaCityCoords');
let chinaCityCoords = {
    "安仁县":[113.2829,26.718523],
    "长沙市":[112.951794,28.233617],
};
let center = chinaCityCoords[dataset[1][0]]||[113.2829,26.718523];
//水波纹
let scatterList=get_geoscatterList(dataset,chinaCityCoords);

option__name__ = {
    tooltip: {},
    bmap: {
        // 百度地图中心经纬度。
        center:center,
        // 百度地图缩放级别。默认为 5。
        zoom: 10,
        // 是否开启拖拽缩放，可以只设置 'scale' 或者 'move'。默认关闭。
        roam: true,
        // 百度地图的旧版自定义样式，见 https://lbsyun.baidu.com/custom/index.htm
        mapStyle: {},
        // 百度地图 3.0 之后的新版自定义样式，见 https://lbsyun.baidu.com/index.php?title=open/custom
        mapStyleV2: {},
        // 百度地图的初始化配置，见 https://lbsyun.baidu.com/cms/jsapi/reference/jsapi_reference.html#a0b1
        mapOptions: {
            // 禁用百度地图自带的底图可点功能
            enableMapClick: false
        }
    },
    series: [
        {
            name: '数量',
            type: 'effectScatter',
            coordinateSystem: 'bmap',
            zlevel: 5,
            rippleEffect: { //涟漪特效
                period: 8, //动画时间，值越小速度越快
                brushType: 'stroke', //波纹绘制方式 stroke, fill
                scale: 10 //波纹圆环最大限制，值越大波纹越大
            },
            // z: 8,
            data: scatterList,
            symbolSize: 20,
            symbol: '',
            itemStyle: {
              borderWidth: 1,
              borderColor: 'green',
              color: 'red',
              shadowBlur: 2
            }
        },
    ]
};
ds_chart(option__name__,__name__);
`;
var d3Chart=`ds_load3d();
//加载模型
threeDict.modelUrl='/static/smartchart/opt/three/car.obj';
// threeDict.mtlUrl=''//材质URL[可选];
// threeDict.textureUrl=''//贴图URL[可选];
threeDict.cameraZ=10;//越大模型看起来越小
// threeDict.cameraPosition=[-100,60,200];//相机坐标XYZ
//环境光颜色及光强
threeDict.ambientLightColor=0xff0000;
// threeDict.ambientLightH=0.4;
//点光源颜色及光强
threeDict.pointLightColor=0xffffff;
// threeDict.pointLightH=0.6;
//背景颜色及透明度
threeDict.backgroundColor='white';
threeDict.backgroundOpacity=1;
//如看不到模型,调整位置
// threeDict.objPositonY=0;
// threeDict.objPositonX=0;
//xy轴旋转动画速度,0不旋转
//threeDict.animateX=0;
threeDict.animateY=1;

dom__name__.innerHTML='';
init_three(dom__name__);
`;
var liquidChart=`ds_loadjs('smt_liquidfill');
let dataset=__dataset__;
dataset = [['指标名','达成','目标'],['销售',60,100]]
let value = dataset[1][1]/dataset[1][2]
let tmpdata = [value,value]
option__name__ = {
    series: [{
        type: 'liquidFill',
        radius: '80%',
        data: tmpdata,
        backgroundStyle: {
            borderWidth: 5,
            borderColor: 'rgb(255,0,255,0.9)',
            color: 'rgb(255,0,255,0.01)'
        },
        label: {
            formatter: (value * 100).toFixed(1) + '%\\n' + dataset[1][0],
            textStyle: {
                fontSize: 25
            }
        }
    }]
};
`;
var sankeyChart=`//select source,target,值, 1 as flag
let dataset = __dataset__; //传入dataset
dataset=[['source','target','data','flag'],['a','a1',5,1],
         ['e','b',3,1],['a','b1',3,1],['b1','a1',1,1],
         ['b1','c',2,1],['b','c',1,1]];
let links = [];
let allnames = [];
for (let i=1;i<dataset.length;i++){
    links.push({source: dataset[i][0],target:dataset[i][1],value:dataset[i][2]});
    allnames.push(dataset[i][0]);
    allnames.push(dataset[i][1]);
}
allnames = ds_distinct(allnames);
let names = [];
for (let i=0;i<allnames.length;i++){
    names.push({name:allnames[i]});
}

option__name__= {
    tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove'
    },
    animation: false,
    series: [
        {
            type: 'sankey',
            bottom: '10%',
            focusNodeAdjacency: 'allEdges',
            data: names,
            links: links,
           // orient: 'vertical',
            label: {
                position: 'top'
            },
            lineStyle: {
                color: 'source',
                curveness: 0.5
            },
            
            //分级显示，不分级删除level
            levels: [{
                    depth: 0,
                    itemStyle: {
                        color: '#fbb4ae'
                    },
                    lineStyle: {
                        color: 'source',
                        opacity: 0.6
                    }
                }, {
                    depth: 1,
                    itemStyle: {
                        color: '#b3cde3'
                    },
                    lineStyle: {
                        color: 'source',
                        opacity: 0.6
                    }
                }, {
                    depth: 2,
                    itemStyle: {
                        color: '#ccebc5'
                    },
                    lineStyle: {
                        color: 'source',
                        opacity: 0.6
                    }
                }, {
                    depth: 3,
                    itemStyle: {
                        color: '#decbe4'
                    },
                    lineStyle: {
                        color: 'source',
                        opacity: 0.6
                    }
                }],
        }
    ]
}
`;
var boxplotChart=`//select 度量1,度量2...
let dataset = __dataset__;
dataset = ds_transform(dataset);
option__name__= {
  title: [
    {
      text: 'experiment',
      left: 'center'
    },
    {
      text: 'upper: Q3 + 1.5 * IQR \\nlower: Q1 - 1.5 * IQR',
      borderColor: '#999',
      borderWidth: 1,
      textStyle: {
        fontWeight: 'normal',
        fontSize: 14,
        lineHeight: 20
      },
      left: '10%',
      top: '90%'
    }
  ],
  dataset: [
    {source:dataset},
    {
      transform: {
        type: 'boxplot',
        config: { itemNameFormatter: 'expr {value}' }
      }
    },
    {
      fromDatasetIndex: 1,
      fromTransformResult: 1
    }
  ],
  tooltip: {
    trigger: 'item',
    axisPointer: {
      type: 'shadow'
    }
  },
  grid: {
    left: '10%',
    right: '10%',
    bottom: '15%'
  },
  xAxis: {
    type: 'category',
    boundaryGap: true,
    nameGap: 30,
    splitArea: {
      show: false
    },
    splitLine: {
      show: false
    }
  },
  yAxis: {
    type: 'value',
    name: 'data',
    splitArea: {
      show: true
    }
  },
  series: [
    {
      name: 'boxplot',
      type: 'boxplot',
      datasetIndex: 1
    },
    {
      name: 'outlier',
      type: 'scatter',
      datasetIndex: 2
    }
  ]
};
`;
var textChart=`let dataset = __dataset__;
let text='smartchart';
option__name__= {
  graphic: {
    elements: [
      {
        type: 'text',
        left: 'center',
        top: 'center',
        style: {
          text: text,
          fontSize: 50,
          fontWeight: 'bold',
          lineDash: [0, 200],
          lineDashOffset: 0,
          fill: 'transparent',
          stroke: '#000',
          lineWidth: 1
        },
        keyframeAnimation: {
          duration: 3000,
          loop: true,
          keyframes: [
            {
              percent: 0.7,
              style: {
                fill: 'transparent',
                lineDashOffset: 200,
                lineDash: [200, 0]
              }
            },
            {
              // Stop for a while.
              percent: 0.8,
              style: {
                fill: 'transparent'
              }
            },
            {
              percent: 1,
              style: {
                fill: 'black'
              }
            }
          ]
        }
      }
    ]
  }
};
`;
var riverChart=`//select 维度,维度,值
let dataset = __dataset__;
let data = [];
let labels =[];
for (let j = 1; j < dataset[0].length; j++) {
    labels[j-1] = dataset[0][j];
    for (let i = 1; i < dataset.length; i++) {
        data.push([
             i-1, dataset[i][j], labels[j-1]
        ]);
    }
}

option__name__ = {
    singleAxis: {
        max: 'dataMax'
    },
    series: [{
        type: 'themeRiver',
        data: data,
        label: {show: true}
    }]
};
`;