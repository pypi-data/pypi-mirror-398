async function load_flow(){
    if(typeof Core === 'undefined'){
    await ds_loadjs('/static/smartchart/opt/flow/logicflow.js',True);
    ds_loadcss('/static/smartchart/opt/flow/logicflow.css');
    await ds_loadjs('/static/smartchart/opt/flow/logicflowext.js',True);
    ds_loadcss('/static/smartchart/opt/flow/logicflowext.css');
}
}
function createFlow(container,edit=true){
    // 注册自定义节点
    const StartNode = {type: 'start', view: Core.CircleNode, model: Core.CircleNodeModel};
    const ApprovalNode = {type: 'approval', view: Core.RectNode, model: Core.RectNodeModel};
    const EndNode = {type: 'end', view: Core.CircleNode, model: Core.CircleNodeModel};
    const Patterns = [
        {
            type: 'start',
            text: '开始',
            label: '开始',
            icon: 'https://cdn.jsdelivr.net/gh/Logic-Flow/static@latest/core/start.png',
        },
        {
            type: 'approval',
            text: '审批',
            label: '审批',
            icon: 'https://cdn.jsdelivr.net/gh/Logic-Flow/static@latest/core/rect.png',
            className: 'import_icon',
        },
        {
            type: 'end',
            text: '结束',
            label: '结束',
            icon: 'https://cdn.jsdelivr.net/gh/Logic-Flow/static@latest/core/end.png',
        },
    ];
    const LFThemes = {
        circle: {
            stroke: '#67C23A',
            strokeWidth: 2
        },
        rect: {
            stroke: '#409EFF',
            strokeWidth: 2,
            borderRadius: 6
        },
        polygon: {
            stroke: '#909399',
            strokeWidth: 2
        },
        polyline: {
            stroke: '#409EFF',
            strokeWidth: 2
        },
        nodeText: {
            color: '#303133',
            fontSize: 14
        },
        edgeText: {
            color: '#409EFF',
            fontSize: 12,
            background: {
                fill: '#fff'
            }
        },
    };
    const AddMenu={
        nodeMenu: [
            {
                text: 'xx',
                callback(node) {
                    lf.deleteNode(node.id);
                },
            },
        ]
    };
    let lf;
    if(edit){
        Core.LogicFlow.use(Extension.Control);
        Core.LogicFlow.use(Extension.Menu);
        Core.LogicFlow.use(Extension.DndPanel);
        lf = new Core.LogicFlow({
            container,
            grid: true,
            isSilentMode: false,
            stopScrollGraph: true,
            stopZoomGraph: true,
            width: container.clientWidth,
            height: container.clientHeight,
            edgeTextDraggable: true,
            nodeTextDraggable: true,
            metaKeyMultipleSelected: true,
            keyboard: {
                enabled: true,
            },
        });
        // 设置菜单
        lf.addMenuConfig(AddMenu);
        // 设置面板元素
        lf.setPatternItems(Patterns);

    }else{
         lf = new Core.LogicFlow({
            container,
            grid: false,
            isSilentMode: true,  // 只读模式
            stopScrollGraph: false,
            stopZoomGraph: false,
            width: container.clientWidth,
            height: container.clientHeight,
            metaKeyMultipleSelected: false
          });
    }
        lf.register(StartNode);
        lf.register(ApprovalNode);
        lf.register(EndNode);
        // 设置样式
        lf.setTheme(LFThemes);

        return lf
}

    // 获取指定流程定义
function getDefinition(ds){
      if(ds.length<2){return}
      let definition = ds_createMap_all(ds)[0];
      let flow = JSON.parse(definition.flow);
      delete definition.flow;
      definition.nodes = flow.nodes;
      definition.edges = flow.edges;
      return definition;
}


function handleApproveNode(instance,task,definition,ds_insid,ds_taskid) {
      ds_save(ds_taskid,{status:task.status,comment:task.comment,id:task.id},1) //任务状态变更
      // 获取当前节点的所有出边
      const outgoingEdges = definition.edges.filter(e => e.sourceNodeId === task.nodeId);
      let t_instance ={id:instance.id};
      // 如果没有出边，流程结束
      if (outgoingEdges.length === 0||task.status === "REJECTED") {
        t_instance.status = task.status;
        t_instance.currentNodeId = '';
        return ds_save(ds_insid,t_instance,1);
      }

      // 根据条件选择正确的边
      let selectedEdges = [];
      for (const edge of outgoingEdges) {
        if (evaluateCondition(edge.properties?.condition, instance.variables)) {
          selectedEdges.push(edge);
        }
      }
      // 为每条出边创建任务
      for (const edge of selectedEdges) {
        const nextNode = definition.nodes.find(n => n.id === edge.targetNodeId);
        if (nextNode) {
            if(nextNode.type==='end'){
                t_instance.status = 'APPROVED';
                t_instance.currentNodeId = '';
            }else{
              // 创建新任务
              const newTask = {
                uuid: ds_generateUUID(),
                instanceId: instance.uuid,
                nodeId: nextNode.id,
                nodeName: nextNode.properties?.name || nextNode.type,
                assignee: nextNode.properties?.assignee,
                instructions: nextNode.properties?.instructions,
                status: "PENDING",
                instanceTitle: instance.title,
                // parallelGroup: task.nodeId // 标记为同一个并行组
              };
             t_instance.currentNodeId = nextNode.id;
             ds_save(ds_taskid,newTask);
            }
        }
      }
       return ds_save(ds_insid,t_instance,1);
    }

    // 评估条件表达式
   function evaluateCondition(condition, variables) {
      if (!condition) return true; // 没有条件默认通过

      try {
        // 简单的条件表达式解析
        // 支持格式如: amount > 1000, status === "urgent", !isApproved
        const conditionParts = condition.split(/\s+/);

        if (conditionParts.length === 1) {
          // 单个条件，如变量名或取反
          if (condition.startsWith('!')) {
            const varName = condition.substring(1);
            return !variables[varName];
          }
          return !!variables[condition];
        }

        if (conditionParts.length === 3) {
          // 三部分条件: 变量 操作符 值
          const [varName, operator, value] = conditionParts;
          const varValue = variables[varName];

          switch (operator) {
            case '==': return varValue == value;
            case '===': return varValue === value;
            case '!=': return varValue != value;
            case '!==': return varValue !== value;
            case '>': return Number(varValue) > Number(value);
            case '>=': return Number(varValue) >= Number(value);
            case '<': return Number(varValue) < Number(value);
            case '<=': return Number(varValue) <= Number(value);
            default: return true;
          }
        }

        return true; // 无法解析的条件默认通过
      } catch (e) {
        console.error("条件解析错误:", e);
        return true; // 解析错误默认通过
      }
    }
 function  startInstance(definition,config,ds_insid,ds_taskid) {
      const newId = ds_generateUUID();
      newInstance = {
        uuid: newId,
        status: "RUNNING",
        definitionId: definition.uuid,
        currentNodeId: "",...config
      };
      // 添加第一个任务（开始节点）
      const startNode = definition.nodes.find(n => n.type === "start");
      // 添加第一个审批任务
      const nextEdge = definition.edges.find(e => e.sourceNodeId === startNode?.id);
      if (nextEdge) {
        const nextNode = definition.nodes.find(n => n.id === nextEdge.targetNodeId);
        if (nextNode) {
          const task = {
            uuid: ds_generateUUID(),
            instanceId: newId,
            nodeId: nextNode.id,
            nodeName: nextNode.properties?.name || "审批",
            assignee: nextNode.properties?.assignee,
            instructions: nextNode.properties?.instructions,
            status: "PENDING",
            instanceTitle: newInstance.title
          };
          newInstance.currentNodeId = nextNode.id;
          let res = ds_save(ds_insid,newInstance);
          if(res.status!==200){
              console.error(res.msg)
              return false
          }
          res = ds_save(ds_taskid,task);
          if(res.status!==200){
              console.error(res.msg)
              return false
          }
        }
      }
      return newInstance;

    }

    //审批页面
async function init_approve(eid='vue_app',dsids={}){
    await load_flow();
    ds_loadcss('/static/smartchart/opt/flow/flow.css');
    await loadVue();
    const flowhtml=`<div class="flow_body">
<div class="header">
  <div class="header-title">流程审批</div>
</div>
<div class="tabs">
  <div class="tab" :class="{active: currentTab === 'instances'}" @click="switchTab('instances')">
    <i class="el-icon-tickets"></i> 流程实例
  </div>
  <div class="tab" :class="{active: currentTab === 'tasks'}" @click="switchTab('tasks')">
    <i class="el-icon-finished"></i> 审批任务
  </div>
</div>

<div class="app-container">
  <div class="panel-left">
    <div class="panel-content">
      <!-- 流程实例面板 -->
      <template v-if="currentTab === 'instances'">
        <div class="section">
          <div class="section-title">
            <i class="el-icon-folder-opened"></i> 可启动流程
          </div>
          <div class="list-item" 
               v-for="def in definitions" 
               :key="def.uuid" 
               :class="{active: selectedDef === def.uuid}"
               @click="selectDefinition(def)">
            <div class="instance-header">
              <div class="instance-title">{[ def.name ]}</div>
              <span class="status-tag DRAFT">{[def.category]}</span>
            </div>
            <div class="instance-meta">
              <div class="meta-item">
                <i class="el-icon-document"></i>
                <span>{[def.description]}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="selectedDef" class="form-container">
          <div class="section-title">
            <i class="el-icon-circle-plus"></i> 启动新流程
          </div>
          <el-form label-position="top">
            <el-form-item label="流程名称" required>
              <el-input 
                v-model="newInstance.title" 
                placeholder="输入流程名称"
                size="small"
              ></el-input>
            </el-form-item>
            
            <el-form-item label="关联表单">
              <el-input 
                v-model="newInstance.formId" 
                placeholder="填写关联表单"
                size="small"
                style="width: 100%;"
              >
              </el-input>
            </el-form-item>
            
            <el-form-item label="备注">
              <el-input 
                type="textarea" 
                v-model="newInstance.remark" 
                placeholder="添加流程说明或备注"
                rows="2"
                size="small"
              ></el-input>
            </el-form-item>
            
            <el-button 
              type="primary" 
              style="width: 100%;" 
              :disabled="!newInstance.title"
              @click="startNewInstance"
              size="small"
            >
              启动流程
            </el-button>
          </el-form>
        </div>
        
        <div class="section">
          <div class="section-title">
            <i class="el-icon-timer"></i> 进行中的流程
          </div>
          <div v-if="instances.length === 0" class="no-data">
            <i class="el-icon-document"></i>
            <div>暂无流程实例</div>
          </div>
          
          <div class="list-item" 
               v-for="instance in instances" 
               :key="instance.uuid" 
               :class="{active: activeInstance === instance.uuid}"
               @click="viewInstance(instance)">
            <div class="instance-header">
              <div class="instance-title">{[ instance.title ]}</div>
              <span class="status-tag" :class="instance.status">
                {[ instance.status ]}
              </span>
            </div>
            
            <div class="instance-meta">
              <div class="meta-item">
                <i class="el-icon-user"></i>
                <span>{[ instance.applicant ]}</span>
              </div>
              
              <div class="meta-item">
                <i class="el-icon-time"></i>
                <span>{[ formatTime(instance.update_time) ]}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
      
      <!-- 审批任务面板 -->
      <template v-else-if="currentTab === 'tasks'">
        <div class="section">
          <div class="section-title">
            <i class="el-icon-notebook-2"></i> 待办任务
          </div>
          <div v-if="tasks.length === 0" class="no-data">
            <i class="el-icon-finished"></i>
            <div>暂无待办任务</div>
          </div>
          
          <div class="task-item" 
               v-for="task in tasks" 
               :key="task.uuid"
               :class="{active: activeTask === task.uuid}"
               @click="loadTaskDetail(task)">
            <div class="task-header">
              <div class="task-title">{[ task.instanceTitle ]}</div>
              <span class="priority-tag" :class="'priority-'+task.priority">
                {[ task.priority === 'high' ? '紧急' : task.priority === 'normal' ? '普通' : '低' ]}
              </span>
            </div>
            
            <div class="task-node">
              <i class="el-icon-position"></i>
              <span>当前节点: {[ task.nodeName ]}</span>
            </div>
            
            <div class="task-meta">
              <div class="meta-item">
                <i class="el-icon-user"></i>
                <span>{[ task.updater ]}</span>
              </div>              
              <div class="meta-item">
                <i class="el-icon-warning-outline"></i>
                <span>{[ task.instructions ]}</span>
              </div>              
              <div class="meta-item">
                <i class="el-icon-document"></i>
                <span>关联表单</span>
              </div>
              
              <div class="meta-item">
                <i class="el-icon-time"></i>
                <span>{[ formatTime(task.update_time) ]}</span>
              </div>
            </div>
            
            <div class="task-actions">
              <el-button type="success" size="small" @click.stop="approveTask(task)">
                <i class="el-icon-check"></i> 批准
              </el-button>
              <el-button type="danger" size="small" @click.stop="rejectTask(task)">
                <i class="el-icon-close"></i> 驳回
              </el-button>
              <el-button type="info" size="small" @click.stop="delegateTask(task)">
                <i class="el-icon-more"></i> 转办
              </el-button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</div>

<!-- 抽屉式流程图容器 -->
<div class="overlay" :class="{active: drawerOpen}" @click="toggleDrawer"></div>
<div class="drawer-container" :class="{open: drawerOpen}">
  <div class="drawer-header">
    <div class="drawer-title">流程审批详情</div>
    <button class="drawer-close" @click="toggleDrawer">
      <i class="el-icon-close"></i>
    </button>
  </div>
  
  <div class="drawer-content">
    <div class="drawer-viewer">
      <div style="height:40%">
        <div id="instance-viewer" style="height: 100%; width: 100%;"></div>
      </div>
      <div class="section">
        <div class="section-title">
          <i class="el-icon-document"></i> 审批记录时间线
        </div>
        
        <div class="approval-timeline" v-if="taskList.length > 0">
          <div class="timeline-header">
            <div class="header-item" style="flex: 2.5">审批节点</div>
            <div class="header-item" style="flex: 2">审批人</div>
            <div class="header-item" style="flex: 2">状态</div>
            <div class="header-item" style="flex: 3.5">审批意见</div>
            <div class="header-item" style="flex: 2">操作时间</div>
          </div>
          
          <div class="timeline-content">
            <el-timeline>
              <el-timeline-item
                v-for="(task, index) in taskList"
                :key="index"
                :timestamp="task.update_time"
                placement="top"
                :color="getStatusColor(task.status)"
              >
                <div class="timeline-card">
                  <div class="timeline-node">{[task.nodeName]}</div>
                  <div class="timeline-user">
                    <i class="el-icon-user"></i>
                    <span>{[task.assignee]}</span>
                  </div>
                  <div class="timeline-status">
                    <el-tag 
                      :type="getStatusTagType(task.status)" 
                      size="small" 
                      effect="light"
                    >
                      {[getStatusText(task.status)]}
                    </el-tag>
                  </div>
                  <div class="timeline-comment">
                    <i class="el-icon-chat-dot-round"></i>
                    {[task.comment || '暂无意见']}
                  </div>
                  <div class="timeline-time">
                    <i class="el-icon-time"></i>
                    {[formatTime(task.update_time)]}
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>
        </div>
        
        <div class="no-records" v-else>
          <i class="el-icon-document-delete"></i>
          <p>暂无审批记录</p>
        </div>
      </div>
    </div>
  </div>
  </div>
</div>`;
    document.getElementById(eid).innerHTML=flowhtml;
   return new Vue({
   el: '#'+eid,
   delimiters: ['{[', ']}'],
   data: {
    currentTab: "tasks", // 默认显示审批任务
    selectedDef: null,
    activeInstance: null,
    activeTask: null,
    drawerOpen: false, // 控制抽屉显示状态

    ds_insid:dsids.ds_insid||0, //写入流程实例
    ds_taskid:dsids.ds_taskid||1, //写入任务实例
    ds_proclistid:dsids.ds_proclistid||2,
    ds_inslistid:dsids.ds_inslistid||3,
    ds_deflistid:dsids.ds_deflistid||4,


    users: [],
    definitions: [],
    instances: [],
    tasks: [],
    lfViewer: null,  // 只读查看器
    newInstance: {
        title: "",
        applicant: filter_param.username,
        formId: null,
        remark: ""
  },

    taskDetail: {},
    taskList:[]
  },
  mounted() {
    // 初始化流程图查看器
    setTimeout(() => {
      this.initFlowViewer();
    }, 300);
    this.get_processes();
    this.get_instances();
  },
  methods: {
      // 时间格式化方法
  formatTime(timeStr) {
    if (!timeStr) return "";

    const time = new Date(timeStr);
    const now = new Date();
    const diff = Math.floor((now - time) / 1000);

    if (diff < 60) return "刚刚";
    if (diff < 3600) return `${Math.floor(diff/60)}分钟前`;
    if (diff < 86400) return `${Math.floor(diff/3600)}小时前`;

    return time.toLocaleDateString();
  },

  // 获取状态颜色
  getStatusColor(status) {
    switch(status) {
      case 'APPROVED': return '#67c23a';
      case 'REJECTED': return '#f56c6c';
      case 'PENDING': return '#409eff';
      default: return '#909399';
    }
  },

  // 获取状态标签类型
  getStatusTagType(status) {
    switch(status) {
      case 'APPROVED': return 'success';
      case 'REJECTED': return 'danger';
      case 'PENDING': return 'primary';
      default: return 'info';
    }
  },

  // 获取状态文本
  getStatusText(status) {
    switch(status) {
      case 'APPROVED': return '已批准';
      case 'REJECTED': return '已驳回';
      case 'PENDING': return '待处理';
      case 'TRANS': return '已转办';
      default: return '未知';
    }
    },

    // 初始化流程图查看器
    initFlowViewer() {
      const container = document.querySelector("#instance-viewer");
      if (container) {
        this.lfViewer = createFlow(container, false);
      }
    },
    // 获取指定流程定义
    get_definition(uuid){
        let ds = ds_refresh(this.ds_deflistid,{uuid:uuid},'list');
        return getDefinition(ds);
    },

    // 流程管理
    get_processes() {
      let dataset = ds_refresh(this.ds_proclistid,null,'list');
      this.users = ds_createMap_all(dataset.df1);
      this.definitions = ds_createMap_all(dataset.df0);
    },

    // 获取流程实例和任务
    get_instances() {
      let dataset = ds_refresh(this.ds_inslistid, { status: 'PENDING' },'list');
      this.instances = ds_createMap_all(dataset.df0);
      this.tasks = ds_createMap_all(dataset.df1);
    },

    // 选项卡切换
    switchTab(tab) {
      this.currentTab = tab;
      if (tab === 'tasks') {
        this.get_instances();
      }
    },

    // 选择流程定义
    selectDefinition(definition) {
      this.selectedDef = definition.uuid;
      this.newInstance.title = `[${filter_param.username}][${definition.name}]`;
    },

    // 启动新流程实例
    startNewInstance() {
      if (!this.selectedDef) {
        this.$message.warning("请先选择流程");
        return;
      }

      let definition = this.get_definition(this.selectedDef);
      let newInstance = startInstance(definition, {
        title: this.newInstance.title,
        applicant: this.newInstance.applicant
      }, this.ds_insid,this.ds_taskid);

      if (newInstance) {
        this.$message.success(`流程 [${newInstance.title}] 已启动！`);
        this.newInstance.title = "";
        this.get_instances();
        this.viewInstance(newInstance);
      }
    },

    // 查看流程实例
    viewInstance(instance) {
      this.activeInstance = instance.uuid;
      this.renderInstanceFlow(instance);
      this.taskList=ds_refresh(5,{instanceId:instance.uuid},r='map');
      this.drawerOpen = true; // 显示抽屉
    },

    // 渲染流程实例图
    renderInstanceFlow(instance) {
      // 加载流程定义
      const definition = this.get_definition(instance.definitionId);

      // 渲染流程图
      if (this.lfViewer) {
        this.lfViewer.render({nodes:definition.nodes,edges:definition.edges});
        this.lfViewer.fitView(20);
        // 高亮当前节点
        if (instance.currentNodeId) {
          this.lfViewer.selectElementById(instance.currentNodeId);
        }
      }
    },

    // 加载任务详情
    loadTaskDetail(task) {
      this.activeTask = task;
      const instance = this.instances.find(i => i.uuid === task.instanceId);
      this.viewInstance(instance);
    },

    // 切换抽屉显示状态
    toggleDrawer() {
      this.drawerOpen = !this.drawerOpen;
    },

    // 批准任务
    approveTask(task) {
        this.updateTaskStatus(task, "APPROVED");
    },

    // 拒绝任务
    rejectTask(task) {
      this.updateTaskStatus(task, "REJECTED");
    },

      // 转办任务
   delegateTask(task) {
    this.$prompt('请输入转办人员姓名', '任务转办', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    }).then(({ value }) => {
      ds_save(this.ds_taskid,{id:task.id,status:'TRANS'},1);
      let newTask={
            uuid: ds_generateUUID(),
            instanceId: task.instanceId,
            nodeId: task.nodeId,
            nodeName: task.nodeName,
            assignee: value,
            instructions: task.instructions,
            status:  task.status,
            instanceTitle: task.instanceTitle
      }
      ds_save(this.ds_taskid,newTask);

      this.$message({
        type: 'success',
        message: `已成功转办给 ${value}`
      });
      this.get_instances();
    }).catch(() => {});
  },

    // 更新任务状态
    updateTaskStatus(task, status) {
      this.$prompt('审批意见', '审批', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
        }).then(({ value }) => {
              task.comment = value;
              task.status = status;
              const instance = this.instances.find(i => i.uuid === task.instanceId);
              const definition = this.get_definition(instance.definitionId);
              // 执行审批逻辑
              const success = handleApproveNode(instance, task, definition, this.ds_insid,this.ds_taskid);
              if (success.status==200) {
                this.$message.success(`任务 [${task.nodeName}] 已${status === "APPROVED" ? "批准" : "拒绝"}`);
                // 刷新数据
                this.activeTask = null;
                this.taskDetail = {};
                this.get_instances();
              }
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '取消提交'
          });
        });
    },

  }
});
}