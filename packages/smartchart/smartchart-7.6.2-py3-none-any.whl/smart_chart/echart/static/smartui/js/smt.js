let t=`<link v-if="theme && theme!=''" rel="stylesheet" :href="theme">
<link v-else rel="stylesheet" :href="home&&home.theme?home.theme:'/static/smartui/theme/dark.green.css'">
<!-- mobile -->
<el-drawer
        class="lite-menus"
        title="SmartChart"
        :visible.sync="drawer"
        :show-close="false"
        size="50%"
        direction="ltr">
    <el-menu unique-opened="true" :default-active="menuActive">
        <div v-for="(item,i) in menus" :key="item">
            <el-menu-item v-if="!item.models" :index="item.eid+''" @click="openTab(item,item.eid)">
                <i :class="item.icon"></i>
                <span slot="title" v-text="item.name"></span>
            </el-menu-item>
            <el-submenu v-else :index="item.eid+''">
                <template slot="title">
                    <i :class="item.icon"></i>
                    <span slot="title" v-text="item.name"></span>
                </template>
                    <el-menu-item  v-for="(sub,j) in item.models"  :index="sub.eid+''" @click="openTab(sub,item.eid)">
                        <i :class="sub.icon"></i>
                        <span slot="title" v-text="sub.name"></span>
                    </el-menu-item>
            </el-submenu>
        </div>
    </el-menu>
</el-drawer>
<el-container :style="{height: height+'px'}"  v-if="!floading">
<el-aside v-show="!mobile" width="auto" class="menu">
<div class="logo-wrap" v-if="!fold">
    <div class="float-wrap"><span v-if="home&&home.logo&&!home.logo.includes('/')" v-text="home.logo"></span><a href="https://www.smartchart.cn" v-else>
        <img v-if="vip" :src="home&&home.logo?home.logo:'/static/smartui/img/smartviplogo.png'" :width="home&&home.logoWidth?home.logoWidth:''">
        <img v-else src="/static/smartui/img/smartlogo.png"></a>
    </div>
</div>
<!-- menu -->
<transition name="el-zoom-in-center">
    <multiple-menu :menus="menus" :menu-active="menuActive" :fold="fold"></multiple-menu>
</transition>
</el-aside>
<el-container>
<el-header class="navbar" style="font-size: 12px;padding: 1px;height: auto">
    <div class="float-wrap">
        <div class="left">
            <el-button v-waves circle icon="fas fa-bars" style="margin-right: 10px;border: none" @click="foldClick()"></el-button>
            <el-breadcrumb v-if="!mobile" style="display: inline-block;" separator="/">
                <el-breadcrumb-item><i :class="menus[0].icon" :key="menus[0].name"></i>{{ menus[0].name }}
                </el-breadcrumb-item>
                <el-breadcrumb-item v-for="item in breadcrumbs" :key="item">
                    <span :class="item.icon"></span>
                    <span v-text="item.name"></span>
                </el-breadcrumb-item>
            </el-breadcrumb>
        </div>
        <div class="right">
            <el-button icon="fas fa-font" circle v-waves @click="fontClick()" v-if="!mobile"></el-button>
            <el-button
                    :icon="this.zoom?'fas fa-compress-arrows-alt':'fas fa-expand-arrows-alt'"
                    @click="goZoom()" circle v-if="!mobile"></el-button>
            <el-button icon="fas fa-expand" @click="goZoom(2)" circle></el-button>
            <el-button icon="el-icon-refresh" @click="goRefresh" circle></el-button>
            <el-tooltip :content="loveList.includes(tabModel)?'取消收藏':'加入收藏'" placement="bottom" effect="light"
                        :style="{color:loveList.includes(tabModel)?'red':''}">
            <el-button icon="el-icon-star-off"  @click="addFocus()" circle
                       v-waves></el-button>
            </el-tooltip>
            <el-tooltip content="智能取数" placement="bottom" effect="light">
            <el-button icon="el-icon-chat-dot-round"  @click="openChat" circle
                       v-waves></el-button>
            </el-tooltip>
            <el-tooltip content="切换开发模式" v-if="devflag" placement="bottom" effect="light">
            <el-button :icon="devcolor=='pink'?'fab fa-dev':'fab fa-dev fa-pulse'"
                       @click="goDev()" :style="{color:devcolor}" circle
                       v-waves></el-button>
            </el-tooltip>
            <el-tooltip content="开发管理" v-if="devflag" placement="bottom" effect="light">
            <el-button icon="fa-solid fa-layer-group"
                       @click="openDrawer('/echart/upload_staticfile/')"  circle
                       v-waves></el-button>
            </el-tooltip>
            <el-button @click="themeDialogVisible=true" v-waves>
                <i class="fas fa-palette"></i>
            </el-button>

            <el-dropdown>
                <el-button v-waves>
                    <i class="fas fa-user-circle"></i>
                    {{ username }}<i class="el-icon-arrow-down el-icon--right"></i>
                </el-button>
                <el-dropdown-menu slot="dropdown">
                    <el-dropdown-item v-waves icon="far fa-edit"
                                      @click.native="changePassword()">{{ language.change_password }}
                    </el-dropdown-item>
                    <el-dropdown-item :icon="item.icon" v-if="devflag" v-for="item in devMenus"
                                      @click.native="openDrawer(item.url)"
                                      divided>{{ item.name }}
                    </el-dropdown-item>
                    <el-dropdown-item icon="fab fa-battle-net" v-if="devflag"
                                      @click.native="goIndex('/admin')"
                                      divided>后台管理
                    </el-dropdown-item>
                    <el-dropdown-item icon="fas fa-sign-out-alt"
                                      @click.native="logout()"
                                      divided>{{ language.logout }}
                    </el-dropdown-item>
                </el-dropdown-menu>
            </el-dropdown>
        </div>
    </div>
</el-header>
<el-main>
<el-tabs v-model="tabModel" type="border-card" editable
         :style="isResize?'height:100%':'height: calc(100% - 97px)'" @edit="handleTabsEdit"
         @tab-click="tabClick">
    <el-tab-pane v-for="(item,index) in tabs" :closable="index!=0" :label="item.name" :name="item.id"
                 :key="item.id" lazy="true">
    <span slot="label" @contextmenu.prevent="contextmenu(item,$event)">
    <i :class="item.loading?'el-icon-loading':item.icon"></i><span v-text="item.name"></span>
    </span>
<div v-if="index==0" style="height:100%">
<iframe v-if="home&&home.home"  :src="home.home"></iframe>
<div v-else id="home">
<el-row class="info-card">
<el-col :span="24">
<el-card class="box-card">
    <div slot="header" class="clearfix">
        <el-input v-model.trim="reportKey" @input="filterReport" placeholder="输入关键字模糊查询..." size="mini"><i slot="prefix" class="el-input__icon el-icon-search"></i></el-input>
    </div>
    <el-alert v-if="vk" :title="'请注意: 您的专业版到期还剩' + vk +'天,到期后只能使用免费版功能'" type="warning" show-icon></el-alert>
    <div class="clearfix">
        <el-tag v-for="(c,j) in loveModels" :key="j" closable :disable-transitions="false" @close="addFocus(c.eid)" @click="openTab(c,(j+1000)+'')" :color="c.color" effect="dark"><i :class="c.icon">{{c.name}}</i></el-tag>
    </div>
<div class="clearfix">
 <div :key="c.name" v-for="(c,j) in filterModels||models" :class="c.eid||c.models?'quick-wrap':'divider-section'">
    <a href="javascript:;" @click="openTab(c,(j+1)+'')" v-if="c.breadcrumbs">
        <span v-if="c.image" class="icon">
            <el-image :src="c.image">
                <div slot="error" class="image-slot">
                    <i class="el-icon-picture-outline"></i>
                </div>
            </el-image>
        </span>
        <span v-else class="icon" :class="c.icon" :style="'color:'+c.color"></span>
        <span class="card-name" v-text="c.name"></span>
    </a>
    <el-popover :ref='c.name' :placement="window.innerWidth<768?'bottom':'right-start'" :width="Math.min(400, window.screenWidth-40)"  trigger="click"  v-else-if="c.models">
        <div :key="d.name" v-for="(d,j) in c.models" class="quick-wrap">
            <a href="javascript:;" @click="$refs[c.name + ''][0].doClose(); openTab(d, (j+500)+'')" v-if="d.breadcrumbs">
                <span v-if="d.image" class="icon">
                    <el-image :src="d.image">
                        <div slot="error" class="image-slot">
                            <i class="el-icon-picture-outline"></i>
                        </div>
                    </el-image>
                </span>
                <span v-else class="icon" :class="d.icon" :style="'color:'+d.color"></span>
                <span class="card-name" v-text="d.name"></span>
            </a>
            <el-popover 
                :ref='d.name' 
                :placement="window.innerWidth<768?'bottom':'right-start'" 
                :width="Math.min(400, window.screenWidth-40)" 
                trigger="click" 
                v-else-if="d.models"
            >
                <div :key="e.name" v-for="(e,k) in d.models" class="quick-wrap">
                    <a href="javascript:;" @click="$refs[c.name + ''][0].doClose();$refs[d.name + ''][0].doClose();openTab(e, (k+1000)+'')" v-if="e.breadcrumbs">
                        <span v-if="e.image" class="icon">
                            <el-image :src="e.image">
                                <div slot="error" class="image-slot">
                                    <i class="el-icon-picture-outline"></i>
                                </div>
                            </el-image>
                        </span>
                        <span v-else class="icon" :class="e.icon"></span>
                        <span class="card-name" v-text="e.name"></span>
                    </a>
                    <el-divider content-position="left" v-else>
                        <i :class="e.icon"></i>
                        <span v-text="e.name"></span>
                    </el-divider>
                </div>
                <template #reference>
                    <a href="javascript:;">
                        <span class="icon el-icon-folder" style="background: yellow"></span>
                        <span class="card-name" v-text="d.name"></span>
                    </a>
                </template>
            </el-popover>
            <el-divider content-position="left" v-else>
                <i :class="d.icon"></i>
                <span v-text="d.name"></span>
            </el-divider>
        </div>
        <template #reference>
            <a href="javascript:;">
                <span class="icon el-icon-folder" style="background: #a0cfff"></span>
                <span class="card-name" v-text="c.name"></span>
            </a>
        </template>
    </el-popover>
    <el-divider content-position="left" v-else><i :class="c.icon"></i><span v-text="c.name"></span></el-divider>
</div>
 </div>
</el-card>
</el-col>
</el-row>
</div>
</div>
<div v-else class="iframe-wrap">
    <iframe :src="item.url" :id="item.id" @load="iframeLoad(item,$event)"></iframe>
    <div v-if="loading" class="loading" @dblclick="loading=false">
        <div class="center">
            <span class="el-icon-loading"></span>
            <span>loading...</span>
        </div>
    </div>
</div>
</el-tab-pane>
</el-tabs>
</el-main>
</el-container>
</el-container>
<ul v-if="popup.show" class="el-dropdown-menu el-popper" ref="popupmenu"
    :style="{position: 'absolute',top: popup.top+'px',left: popup.left+'px'}" x-placement="top-end">
    <li v-for="(item,index) in popup.menus" tabindex="-1" class="el-dropdown-menu__item"
        @click="item.handler(popup.tab,item)"><i :class="item.icon"></i><span
            v-text="item.text"></span>
    </li>
</ul>
<el-dialog title="修改密码" :visible.sync="pwdDialog.show">
    <iframe frameborder="0" :src="pwdDialog.url" width="100%" height="500"></iframe>
</el-dialog>
<el-dialog
    :title="getLanuage('Change theme')"
    :visible.sync="themeDialogVisible"
    :width="small?'90%':'50%'">
<div class="change-theme clearfix">
    <div v-waves :class="{'theme-item':true,active:themeName==item.text}" v-for="(item,i) in themes"
         :key="item.text"
         :title="getLanuage(item.text)" @click="setTheme(item)">
        <div class="theme-menu" :style="{background:item.menu}">
            <div class="theme-logo" :style="{background: item.logo}"></div>
        </div>
        <div class="theme-top" :style="{background: item.top}"></div>
    </div>
</div>
</el-dialog>
<el-dialog
    :title="getLanuage('Set font size')"
    :visible.sync="fontDialogVisible"
    :width="small?'90%':'50%'">
<el-slider v-model="fontSlider" :min="12" :max="100" show-input @change="fontSlideChange"></el-slider>
<div style="text-align: right;padding-top: 20px">
    <el-button type="primary" @click="reset()" v-text="getLanuage('Reset')"></el-button>
</div>
</el-dialog>
<el-drawer :with-header="false" :visible.sync="drawerVisible" direction="rtl" :size="mobile?'95%':'60%'">
<iframe :src="drawerURL" style="height:99%;width:100%;border:none"></iframe>
</el-drawer>`;
let part=document.getElementById("main");if(part){part.innerHTML=t}
var lanuageCode = 'zh-hans';
var home = {id: '0', index: '1', eid: '1', name: "首页", icon: 'fas fa-home'};
var menus = [home];