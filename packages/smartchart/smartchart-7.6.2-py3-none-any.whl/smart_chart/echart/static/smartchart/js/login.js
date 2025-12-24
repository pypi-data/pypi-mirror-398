document.getElementById('main').innerHTML=`
<div class="left">
    <div class="logo">
        <img src="/static/smartui/img/smartviplogo.png" alt="SmartChart Logo">
    </div>
    <p>欢迎使用SmartChart <span class="version-badge">V7</span> - <span class="ai-highlight">AI Agent Inside</span> </p>

    <div class="features">
        <div class="feature">
            <i class="fas fa-chart-line"></i>
            <span>强大的数据可视化能力</span>
        </div>
        <div class="feature">
            <i class="fas fa-robot"></i>
            <span>集成AI智能体功能</span>
        </div>
        <div class="feature">
            <i class="fas fa-qrcode"></i>
            <span>集成数据中台功能</span>
        </div>
        <div class="feature">
            <i class="fas fa-shield-alt"></i>
            <span>企业级安全与权限管理</span>
        </div>
    </div>
</div>

<div class="right">
    <div class="login-tabs">
        <div class="tab active" data-tab="password">密码登录</div>
        <div class="tab" data-tab="qrcode">扫码登录</div>
    </div>

    <div class="form-container">
        <!-- 密码登录表单 -->
        <form class="form active" id="password-form">
            <label for="username">用户名</label>
            <div class="input-with-icon">
                <i class="fas fa-user"></i>
                <input type="text" id="username" class="form-control" placeholder="请输入用户名或手机" required>
            </div>

            <label for="password">密码</label>
            <div class="input-with-icon">
                <i class="fas fa-lock"></i>
                <input type="password" id="password" class="form-control" placeholder="请输入密码" required>
            </div>

            <div class="error-message" id="errorMessage"></div>

            <button type="button" class="btn-login" id="loginBtn">
                登录
            </button>
        </form>

        <!-- 扫码登录表单 -->
        <div class="form" id="qrcode-form">
            <div class="qrcode-container">
                <div class="qrcode">
                    <div class="qrcode-placeholder">
                        <i class="fas fa-qrcode"></i>
                    </div>
                </div>
                <div class="qrcode-text">
                    使用SmartChart App扫描二维码登录
                </div>
            </div>

            <div class="third-login">
                <p class="split-line"><span>或使用以下方式登录</span></p>
                <div class="platform-icons">
                    <a title="钉钉登录"><i class="iconfont icondingding"></i></a>
                    <a title="企微登录"><i class="iconfont iconqiwei"></i></a>
                    <a title="飞书登录"><i class="iconfont iconfeishu"></i></a>
                    <a title="SSO登录"><i class="iconfont iconzhinengti"></i></a>
                </div>
            </div>
        </div>
    </div>
</div>
`;

document.addEventListener("DOMContentLoaded",function(){parent.callback&&parent.callback();const n=document.querySelectorAll(".tab"),a=document.querySelectorAll(".form");n.forEach(e=>{e.addEventListener("click",function(){const t=this.getAttribute("data-tab");n.forEach(e=>e.classList.remove("active")),this.classList.add("active"),a.forEach(e=>{e.classList.remove("active"),e.id===t+"-form"&&e.classList.add("active")})})}),document.getElementById("loginBtn").addEventListener("click",function(){var e,t,n=document.getElementById("username").value,a=document.getElementById("password").value;const o=document.getElementById("loginBtn"),c=document.getElementById("errorMessage");o.classList.add("loading"),c.textContent="",n&&a?(e=document.querySelector("[name=csrfmiddlewaretoken]").value,t=new URLSearchParams(window.location.search).get("next")||"/",n=JSON.stringify({username:n,password:a,next:t}),a=btoa(encodeURIComponent(n).replace(/%([0-9A-F]{2})/g,function(e,t){return String.fromCharCode("0x"+t)})),fetch("/lg/",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded","X-CSRFToken":e},body:new URLSearchParams({data:a})}).then(e=>{if(!e.redirected)return e.json();window.location.href=e.url}).then(e=>{e&&!1===e.success&&(c.textContent=e.message||"\u7528\u6237\u540d\u6216\u5bc6\u7801\u9519\u8bef")}).catch(e=>{console.error("\u767b\u5f55\u8bf7\u6c42\u5931\u8d25:",e),c.textContent="\u767b\u5f55\u8bf7\u6c42\u5931\u8d25\uff0c\u8bf7\u5237\u65b0\u518d\u8bd5"}).finally(()=>{o.classList.remove("loading")})):(c.textContent="\u8bf7\u8f93\u5165\u7528\u6237\u540d\u548c\u5bc6\u7801!",o.classList.remove("loading"))}),document.querySelectorAll(".platform-icons a").forEach(e=>{e.addEventListener("click",function(){var e;let t="";switch(this.getAttribute("title")){case"\u9489\u9489\u767b\u5f55":t="dingding";break;case"\u4f01\u5fae\u767b\u5f55":t="qiwei";break;case"\u98de\u4e66\u767b\u5f55":t="feishu";break;case"SSO\u767b\u5f55":t="sso"}t&&(e=t,fetch("/echart/third_login/?t="+e).then(async e=>{e=await e.json();200===e.status?window.location.href=e.msg:alert(e.msg)}).catch(e=>{console.error("\u7b2c\u4e09\u65b9\u767b\u5f55\u8bf7\u6c42\u5931\u8d25:",e),alert("\u7b2c\u4e09\u65b9\u767b\u5f55\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u518d\u8bd5")}))})})});