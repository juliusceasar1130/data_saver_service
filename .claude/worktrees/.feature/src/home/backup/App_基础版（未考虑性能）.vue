<!--
  修改时间：2025年9月15日14点05分  
  修改内容：1. 实现页面响应式布局优化，适配手机、平板、桌面设备
           2. 添加Ctrl+M快捷键控制连接控制面板和表格列的显示/隐藏
           3. 默认隐藏连接控制面板和部分表格列，优化界面简洁性
           4. 调整表格列宽度分配，优化数据看板响应式布局
           5. 在隐藏模式下同时隐藏数据卡片header，实现更简洁的界面显示
           6. 优化雪橇数量计算逻辑，支持factor对象格式{norm,e5}
           7. 数据值>5999时使用factor.e5，<=5999时使用factor.norm
           8. 优化Factor列显示格式，支持对象内容展示
           9. 优化WebSocket订阅请求，只发送必要字段(id,type,plc,tag)减少网络传输
           10. 添加雪橇堆垛配置信息点击提示功能，显示常规和Purple配置参数
           11. 调整配置说明按钮布局，实现左对齐显示
           12. 添加页面加载后自动连接WebSocket服务器功能，延迟1秒后自动连接
           13. 在高级列模式下增加区域列(area)和位置序号列(sequence)，提供更多设备信息展示
           14. 新增7区域网格布局，仅在隐藏模式下显示，插入到数据看板和完整表格之间
           15. 实现7区域数据显示功能：基于真实配置数据动态生成区域表格，按area分组按sequence排序
           16. 新增7区域示意图功能：在区域数据监控标题旁添加"7区域示意图"按钮
           17. 实现7区域布局示意图对话框基础框架，内容占位等待后续完善
           18. 将7区域示意图按钮移动到配置说明按钮旁边，统一放在系统头部
           19. 优化头部按钮布局和响应式设计，确保不同屏幕尺寸下的良好显示效果
           20. 完善7区域示意图对话框：添加draggable属性实现拖动功能
           21. 优化对话框关闭按钮样式，采用醒目的红色按钮设计和悬停效果（位置不变）
           22. 集成skid_layout.png背景图片到示意图中，实现响应式显示和错误处理
           23. 实现7区域表格统计信息功能：在每个区域表格右上角显示Purple和常规雪橇数量统计
           24. 添加高效的区域统计计算函数，复用现有计算逻辑确保性能优化
           25. 设计醒目的统计信息样式，采用渐变色背景和悬停效果
           26. 实现响应式统计信息布局，适配移动端显示
           27. 修复7区域统计计算逻辑错误，复用标准calculateSkidCount函数确保与数据看板计算一致
           28. 统一Purple雪橇颜色主题：数据看板卡片和7区域统计标签均采用黄色渐变背景
           29. 优化数据看板视觉效果：将所有统计数值文字颜色改为白色，提高可读性和一致性
           30. 优化7区域统计信息标签样式：改为椭圆形设计，字体增大3号，提升视觉效果
-->
<template>
  <div class="app-container">
    <!-- 系统头部 -->
    <el-header class="system-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="system-title">
            <el-icon class="title-icon"><Connection /></el-icon>
            面漆雪橇返回线监控
          </h1>
          <div class="header-buttons">
            <div class="config-info-container" @click="showSkidConfigInfo" title="点击查看详细配置信息">
              <p class="config-info-item">配置说明</p>        
            </div>
            <el-button type="primary" @click="showAreaDiagram" class="header-diagram-button" size="small">
              <el-icon><Location /></el-icon>
              区域示意图
            </el-button>
          </div>
        </div>
        <div class="connection-status">
          <el-tag 
            :type="connectionStatus === 'connected' ? 'success' : connectionStatus === 'connecting' ? 'warning' : 'danger'"
            effect="dark"
          >
            <el-icon>
              <CircleCheck v-if="connectionStatus === 'connected'" />
              <Loading v-else-if="connectionStatus === 'connecting'" />
              <CircleClose v-else />
            </el-icon>
            {{ connectionStatusText }}
          </el-tag>
        </div>
      </div>
    </el-header>

    <!-- 主内容区域 -->
    <el-container class="main-container">
      <!-- 控制面板 -->
      <transition name="slide-panel">
        <el-aside v-if="showControlPanel" width="300px" class="control-panel">
        <el-card class="control-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>连接控制</span>
            </div>
          </template>
          
          <!-- WebSocket连接配置 -->
          <div class="connection-config">
            <el-form label-position="top" size="small">
              <el-form-item label="WebSocket服务器地址">
                <el-input 
                  v-model="wsUrl" 
                  placeholder="ws://localhost:8088/ws/emosweb"
                  :disabled="connectionStatus === 'connected'"
                >
                  <template #prepend>ws://</template>
                </el-input>
              </el-form-item>
              
              <el-form-item>
                <el-button 
                  type="primary" 
                  @click="connectWebSocket"
                  :disabled="connectionStatus === 'connected' || connectionStatus === 'connecting'"
                  style="width: 100%"
                >
                  <el-icon><VideoPlay /></el-icon>
                  连接服务器
                </el-button>
              </el-form-item>
              
              <el-form-item>
                <el-button 
                  type="danger" 
                  @click="disconnectWebSocket"
                  :disabled="connectionStatus === 'disconnected'"
                  style="width: 100%"
                >
                  <el-icon><VideoPause /></el-icon>
                  断开连接
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 统计信息 -->
          <div class="statistics">
            <el-descriptions title="连接统计" :column="1" size="small" border>
              <el-descriptions-item label="心跳次数">{{ heartbeatCount }}</el-descriptions-item>
              <el-descriptions-item label="收到消息">{{ messageCount }}</el-descriptions-item>
              <el-descriptions-item label="监控点位">{{ deviceData.length }}</el-descriptions-item>
              <el-descriptions-item label="连接时长">{{ connectionDuration }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
        </el-aside>
      </transition>

          <!-- 数据展示区域 -->
      <el-main class="data-display">
        <el-card class="data-card" shadow="hover">
          <template #header v-if="showControlPanel">
            <div class="card-header">                         
              <div class="header-actions">
                <el-button size="small" @click="clearData">
                  <el-icon><Delete /></el-icon>
                  清空数据
                </el-button>
                <el-button size="small" type="primary" @click="refreshData">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>

          <!-- 数据看板 -->
          <div class="data-dashboard">
            <el-row :gutter="20" class="dashboard-row">
              <el-col :span="6">
                <el-card class="dashboard-card purple-card" shadow="hover">
                  <div class="dashboard-item">
                    <div class="dashboard-icon">
                      <el-icon size="24"><TrendCharts /></el-icon>
                    </div>
                    <div class="dashboard-content">
                      <div class="dashboard-label">Purple雪橇数量</div>
                      <div class="dashboard-value purple-value">{{ purpleSkidCount }}</div>
                      <div class="dashboard-desc">雪橇号 > 5999</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="6">
                <el-card class="dashboard-card normal-card" shadow="hover">
                  <div class="dashboard-item">
                    <div class="dashboard-icon">
                      <el-icon size="24"><DataAnalysis /></el-icon>
                    </div>
                    <div class="dashboard-content">
                      <div class="dashboard-label">常规雪橇数量</div>
                      <div class="dashboard-value normal-value">{{ normalSkidCount }}</div>
                      <div class="dashboard-desc">雪橇号 ≤ 5999</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="6">
                <el-card class="dashboard-card total-card" shadow="hover">
                  <div class="dashboard-item">
                    <div class="dashboard-icon">
                      <el-icon size="24"><PieChart /></el-icon>
                    </div>
                    <div class="dashboard-content">
                      <div class="dashboard-label">总雪橇数量</div>
                      <div class="dashboard-value total-value">{{ totalSkidCount }}</div>
                      <div class="dashboard-desc">全部统计</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="6">
                <el-card class="dashboard-card info-card" shadow="hover">
                  <div class="dashboard-item">
                    <div class="dashboard-icon">
                      <el-icon size="24"><DataBoard /></el-icon>
                    </div>
                    <div class="dashboard-content">
                      <div class="dashboard-label">在线设备</div>
                      <div class="dashboard-value info-value">{{ deviceData.filter(row => row.connectionStatus === 'online').length }}</div>
                      <div class="dashboard-desc">实时统计</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <!-- 统一滚动容器 - 包含7区域和主数据表格 -->
          <div v-if="!showControlPanel" class="unified-scroll-container">
            <!-- 7区域数据表格布局 -->
            <div class="areas-grid-layout">
              <h3 class="areas-title">📊 区域数据监控</h3>
              <div class="areas-grid">
                <!-- 动态生成7个区域的数据表格 -->
                <div 
                  v-for="areaNum in [1, 2, 3, 4, 5, 6, 7]" 
                  :key="`area${areaNum}`"
                  :class="`area${areaNum}`"
                >
                  <div class="area-card">
                    <div class="area-header">
                      <div class="area-header-left">
                        <span class="area-badge">Area{{ areaNum }}</span>
                        <span class="area-title">区域{{ areaNum }} - ({{ getAreaDevices(areaNum).length }}设备)</span>
                      </div>
                      <div class="area-header-right">
                        <div class="area-stats">
                          <span class="stats-label"></span>
                          <el-tag 
                            size="large" 
                            type="danger" 
                            effect="dark"
                            class="purple-stats"
                          >
                            {{ getAreaSkidStats(areaNum).purple }}
                          </el-tag>
                          <el-tag 
                            size="large" 
                            type="primary" 
                            effect="dark"
                            class="normal-stats"
                          >
                            {{ getAreaSkidStats(areaNum).normal }}
                          </el-tag>
                        </div>
                      </div>
                    </div>
                    <div class="area-table-container">
                      <table class="mini-table">
                        <thead>
                          <tr>
                            <th>PLC设备</th>
                            <th>滚床编号</th>
                            <th>数据点位</th>
                            <th>数据值</th>
                            <th>雪橇数量</th>
                            <th>状态</th>
                            <th>最后更新</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr 
                            v-for="device in getAreaDevices(areaNum)" 
                            :key="`${device.plc}_${device.tag}`"
                            :class="getAreaDeviceValue(areaNum, device)?.connectionStatus || 'waiting'"
                          >
                            <td>{{ device.plc }}</td>
                            <td>{{ device.RBindex || '-' }}</td>
                            <td :title="device.tag" class="tag-cell">{{ device.tag || '-' }}</td>
                            
                            <!-- 数据值列 -->
                            <td class="data-value-cell">
                              <el-tag 
                                size="small" 
                                :type="getAreaDeviceValue(areaNum, device)?.hasData ? getValueColorType(getAreaDeviceValue(areaNum, device)?.value) : 'info'"
                                :effect="getAreaDeviceValue(areaNum, device)?.updateCount > 0 ? 'dark' : 'plain'"
                                :title="`服务器时间: ${getAreaDeviceValue(areaNum, device)?.serverTimestamp || '未知'}\n数据源: ${getAreaDeviceValue(areaNum, device)?.source || '未知'}`"
                              >
                                {{ getAreaDeviceValue(areaNum, device)?.value || '等待数据' }}
                              </el-tag>
                            </td>
                            
                            <!-- 雪橇数量列 -->
                            <td class="skid-count-cell">
                              <el-tag 
                                size="small"
                                :type="getAreaDeviceValue(areaNum, device)?.hasData ? getValueColorType(getAreaDeviceValue(areaNum, device)?.value) : 'info'"
                                v-if="device.factor && getAreaDeviceValue(areaNum, device)?.value && parseFloat(getAreaDeviceValue(areaNum, device)?.value) > 0"
                              >
                                {{ calculateSkidCount(device.factor, getAreaDeviceValue(areaNum, device)?.value, device.weight) }}
                              </el-tag>
                              <span v-else class="text-gray-400">-</span>
                            </td>
                            
                            <!-- 状态列 -->
                            <td class="status-cell">
                              <span 
                                :class="['status-indicator', getAreaDeviceValue(areaNum, device)?.connectionStatus || 'waiting']"
                              >
                                {{ getStatusText(getAreaDeviceValue(areaNum, device)?.connectionStatus || 'waiting') }}
                              </span>
                            </td>
                            
                            <!-- 最后更新列 -->
                            <td class="update-time-cell">
                              <el-tag 
                                size="small"
                                :type="getAreaDeviceValue(areaNum, device)?.lastUpdateTime ? 'success' : 'info'"
                              >
                                {{ getAreaDeviceValue(areaNum, device)?.lastUpdateTime ? 
                                   formatTime(getAreaDeviceValue(areaNum, device).lastUpdateTime) : '等待数据' }}
                              </el-tag>
                            </td>
                          </tr>
                          <tr v-if="getAreaDevices(areaNum).length === 0">
                            <td colspan="7" class="no-data">暂无设备数据</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 数据表格 -->
            <h3 class="areas-title">📊 全部数据监控</h3>
            <el-table 
              :data="deviceData" 
              stripe 
              highlight-current-row
              style="width: 100%;"
              size="small"
              v-loading="tableLoading"
              element-loading-text="正在接收数据..."
              :fit="true"
              :table-layout="showAdvancedColumns ? 'fixed' : 'auto'"
              :class="{'table-simplified': !showAdvancedColumns, 'larger-table-font': true, 'main-data-table': true}"
            >
                <el-table-column type="index" label="序号" width="60" align="center" />
                <el-table-column 
                prop="plc" 
                label="PLC设备" 
                :width="showAdvancedColumns ? '100' : null"
                :min-width="showAdvancedColumns ? '100' : '150'"
                align="center"
              >
                <template #default="scope">
                  <el-tag size="small" type="primary">{{ scope.row.plc }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column 
              prop="RBindex" 
              label="滚床编号" 
              :width="showAdvancedColumns ? '120' : null"
              :min-width="showAdvancedColumns ? '120' : '150'"
              align="center"
            >
              <template #default="scope">
                <el-tag size="small" type="primary" v-if="scope.row.RBindex">
                  {{ scope.row.RBindex }}
                </el-tag>
                <span v-else class="text-gray-400">-</span>
              </template>
            </el-table-column>
            
              <el-table-column 
              prop="value" 
              label="数据值" 
              :width="showAdvancedColumns ? '100' : null"
              :min-width="showAdvancedColumns ? '100' : '100'"
              align="center" 
              show-overflow-tooltip
            >
              <template #default="scope">
                <el-tooltip 
                  :content="`服务器时间: ${scope.row.serverTimestamp || '未知'}\n数据源: ${scope.row.source || '未知'}`"
                  placement="top"
                  :disabled="!scope.row.hasData"
                >
                  <el-tag 
                    size="small" 
                    :type="scope.row.hasData ? getValueColorType(scope.row.value) : 'info'"
                    :effect="scope.row.updateCount > 0 ? 'dark' : 'plain'"
                  >
                    {{ scope.row.value || '等待数据' }}
                  </el-tag>
                </el-tooltip>
              </template>
            </el-table-column>
            
              <el-table-column 
              prop="skidCount" 
              label="雪橇数量" 
              :width="showAdvancedColumns ? '100' : null"
              :min-width="showAdvancedColumns ? '100' : '120'"
              align="center"
            >
              <template #default="scope">
                <el-tag 
                  size="small" 
                  :type="scope.row.hasData ? getValueColorType(scope.row.value) : 'info'"
                  v-if="scope.row.factor && scope.row.value && parseFloat(scope.row.value) > 0"
                >
                  {{ calculateSkidCount(scope.row.factor, scope.row.value, scope.row.weight) }}
                </el-tag>
                <span v-else class="text-gray-400">-</span>
              </template>
            </el-table-column>
            
              <el-table-column 
              prop="connectionStatus" 
              label="连接状态" 
              :width="showAdvancedColumns ? '100' : null"
              :min-width="showAdvancedColumns ? '100' : '100'"
              align="center"
            >
              <template #default="scope">
                <el-tag 
                  size="small" 
                  :type="getStatusType(scope.row.connectionStatus)"
                >
                  <el-icon>
                    <CircleCheck v-if="scope.row.connectionStatus === 'online'" />
                    <Loading v-else-if="scope.row.connectionStatus === 'waiting'" />
                    <CircleClose v-else />
                  </el-icon>
                  {{ getStatusText(scope.row.connectionStatus) }}
                </el-tag>
              </template>
            </el-table-column>
            
              <el-table-column 
              prop="lastUpdateTime" 
              label="最后更新" 
              :width="showAdvancedColumns ? '180' : null"
              :min-width="showAdvancedColumns ? '180' : '180'"
              align="center"
            >
              <template #default="scope">
                <el-tag 
                  size="small" 
                  :type="scope.row.lastUpdateTime ? 'success' : 'info'"
                >
                  {{ scope.row.lastUpdateTime ? formatTime(scope.row.lastUpdateTime) : '等待数据' }}
                </el-tag>
              </template>
            </el-table-column>           

            
            <!-- 高级列 - 默认隐藏，通过Ctrl+M切换 -->
              <el-table-column v-if="showAdvancedColumns" prop="tag" label="数据点位标签" align="center" min-width="300" show-overflow-tooltip />
            
              <el-table-column v-if="showAdvancedColumns" prop="quality" label="数据质量" width="80" align="center">
              <template #default="scope">
                <el-tag 
                  size="small" 
                  :type="getQualityType(scope.row.quality)"
                  v-if="scope.row.quality !== null"
                >
                  {{ scope.row.quality }}
                </el-tag>
                <span v-else class="text-gray-400">-</span>
              </template>
            </el-table-column>
            
              <el-table-column v-if="showAdvancedColumns" prop="updateCount" label="更新次数" width="80" align="center">
              <template #default="scope">
                <el-tag size="small" type="info">{{ scope.row.updateCount }}</el-tag>
              </template>
            </el-table-column>
            
              <el-table-column v-if="showAdvancedColumns" prop="factor" label="Factor" width="120" align="center">
              <template #default="scope">
                <el-tag size="small" type="info" v-if="scope.row.factor">
                  <span v-if="typeof scope.row.factor === 'object'">
                    norm:{{ scope.row.factor.norm || 0 }}, e5:{{ scope.row.factor.e5 || 0 }}
                  </span>
                  <span v-else>{{ scope.row.factor }}</span>
                </el-tag>
                <span v-else class="text-gray-400">-</span>
              </template>
            </el-table-column>
            
              <el-table-column v-if="showAdvancedColumns" prop="weight" label="Weight" width="80" align="center">
              <template #default="scope">
                <el-tag size="small" type="info" v-if="scope.row.weight">
                  {{ scope.row.weight }}
                </el-tag>
                <span v-else class="text-gray-400">-</span>
              </template>
            </el-table-column>
            
              <el-table-column v-if="showAdvancedColumns" prop="type" label="消息类型" width="100" align="center">
              <template #default="scope">
                <el-tag size="small" type="warning">{{ scope.row.type }}</el-tag>
              </template>
            </el-table-column>
            
              <el-table-column v-if="showAdvancedColumns" prop="area" label="区域" width="80" align="center">
              <template #default="scope">
                <el-tag 
                  size="small" 
                  type="info" 
                  v-if="scope.row.area !== null && scope.row.area !== undefined"
                >
                  {{ scope.row.area }}
                </el-tag>
                <span v-else class="text-gray-400">-</span>
              </template>
            </el-table-column>
            
              <el-table-column v-if="showAdvancedColumns" prop="sequence" label="位置序号" width="100" align="center">
              <template #default="scope">
                <el-tag 
                  size="small" 
                  type="info" 
                  v-if="scope.row.sequence !== null && scope.row.sequence !== undefined"
                >
                  {{ scope.row.sequence }}
                </el-tag>
                <span v-else class="text-gray-400">-</span>
              </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 正常模式下的数据表格（删除） -->

        </el-card>
      </el-main>
    </el-container>
    
    <!-- 7区域示意图对话框 -->
    <el-dialog
      v-model="showAreaDiagramDialog"
      title="7区域实际布局示意图"
      :width="'90%'"
      :center="false"
      :close-on-click-modal="false"
      :destroy-on-close="true"
      draggable
    >
      <template #header>
        <div class="diagram-dialog-header">
          <el-icon><Location /></el-icon>
          <span>7区域实际布局示意图</span>
        </div>
      </template>
      
      <div class="area-diagram-container">     
        
        <!-- 示意图主体 -->
        <div class="diagram-content">
          <div class="diagram-layout">
            <div class="layout-diagram-container">
              <div class="background-image-container">
                <img 
                  src="./config/skid_layout.png" 
                  alt="布局示意图" 
                  class="layout-background-image"
                  @load="onImageLoad"
                  @error="onImageError"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElNotification, ElMessageBox } from 'element-plus'
import { 
  Connection, 
  CircleCheck, 
  Loading, 
  CircleClose, 
  Setting, 
  VideoPlay, 
  VideoPause, 
  Monitor, 
  Delete, 
  Refresh,
  TrendCharts,
  DataAnalysis,
  PieChart,
  DataBoard,
  Location,
  DocumentAdd
} from '@element-plus/icons-vue'
import deviceConfig from './config/deviceConfig_7areas.json'

// ==================== 响应式数据定义 ====================
const wsUrl = ref('localhost:8088/ws/emosweb')
const socket = ref(null)
const connectionStatus = ref('disconnected') // 连接状态: disconnected, connecting, connected
const heartbeatCount = ref(0)
const messageCount = ref(0)
const connectionStartTime = ref(null)
const connectionDuration = ref('00:00:00')
const deviceData = ref([])
const tableLoading = ref(false)

// UI控制状态
const showControlPanel = ref(false) // 控制面板显示状态，默认隐藏
const showAdvancedColumns = ref(true) // 高级表格列显示状态，默认显示（隐藏模式也显示完整数据）
const showAreaDiagramDialog = ref(false) // 7区域示意图对话框显示状态

// 设备行标识映射表 - 用于快速查找设备对应的表格行索引
const deviceRowMap = ref(new Map())

// 设备参数配置 - 从外部JSON配置文件加载，便于维护
const deviceParams = ref([
  // 动态展开 deviceConfig.config 中所有键的内容
  // Object.values() 获取 config 对象中所有值（数组），然后使用 flat() 将嵌套数组扁平化为单一数组
  ...Object.values(deviceConfig.config).flat()
])
// 引入配置参数用于说明
const e5factor = ref(deviceConfig.factor.e5)
const normfactor = ref(deviceConfig.factor.norm)

// 7区域数据分组
const areaGroupedData = ref({})

// 计算属性
const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connected':
      return '已连接'
    case 'connecting':
      return '连接中...'
    case 'disconnected':
    default:
      return '未连接'
  }
})

// ==================== 表格数据初始化方法 ====================

/**
 * 初始化设备数据表格
 * 根据配置文件创建固定的表格行结构，每个设备点位对应一行
 */
const initializeDeviceTable = () => {
  console.log('正在初始化设备数据表格...')
  
  // 清空现有数据
  deviceData.value = []
  deviceRowMap.value.clear()
  
  // 根据配置文件生成表格行
  deviceParams.value.forEach((param, index) => {
    // 创建设备行标识符 (plc + tag 的组合)
    const deviceKey = `${param.plc}_${param.tag}`
    
    // 创建设备数据行对象
    const deviceRow = {
      id: deviceKey,
      plc: param.plc,
      tag: param.tag,
      value: null,                           // 当前数据值
      type: param.type,                      // 消息类型
      connectionStatus: 'waiting',           // 连接状态: waiting/online/offline
      lastUpdateTime: null,                  // 最后更新时间（客户端时间）
      hasData: false,                        // 是否已收到数据
      updateCount: 0,                        // 数据更新次数
      timestamp: null,                       // 首次接收时间
      quality: null,                         // 数据质量（来自服务器）
      source: null,                          // 数据源（来自服务器）
      serverTimestamp: null,                 // 服务器时间戳
      RBindex: param.RBindex || null,        // 滚床编号
      factor: param.factor || null,          // 系数
      weight: param.weight || null,          // 权重
      area: param.area || null,              // 区域标识
      sequence: param.sequence || null       // 位置序号
    }
    
    // 添加到表格数据数组
    deviceData.value.push(deviceRow)
    
    // 建立设备标识与行索引的映射关系，便于快速查找
    deviceRowMap.value.set(deviceKey, index)
  })
  
  console.log(`表格初始化完成，共创建 ${deviceData.value.length} 个设备监控行`)
}

/**
 * 根据plc和tag查找对应的设备行
 */
const findDeviceRow = (plc, tag) => {
  const deviceKey = `${plc}_${tag}`
  const rowIndex = deviceRowMap.value.get(deviceKey)
  
  if (rowIndex !== undefined && rowIndex < deviceData.value.length) {
    return {
      row: deviceData.value[rowIndex],
      index: rowIndex
    }
  }
  
  return null
}

/**
 * 按区域分组设备数据并按sequence排序
 * 生成7区域数据显示所需的数据结构
 */
const groupDevicesByArea = () => {
  console.log('正在按区域分组设备数据...')
  
  // 清空现有分组数据
  areaGroupedData.value = {}
  
  // 按area字段分组
  deviceParams.value.forEach(device => {
    const area = device.area || 1 // 默认为区域1
    
    if (!areaGroupedData.value[area]) {
      areaGroupedData.value[area] = []
    }
    
    areaGroupedData.value[area].push(device)
  })
  
  // 对每个区域内的设备按sequence字段排序
  Object.keys(areaGroupedData.value).forEach(area => {
    areaGroupedData.value[area].sort((a, b) => {
      const seqA = a.sequence || 0
      const seqB = b.sequence || 0
      return seqA - seqB
    })
  })
  
  console.log('区域分组完成：', areaGroupedData.value)
  console.log(`共分为${Object.keys(areaGroupedData.value).length}个区域`)
  
  // 打印每个区域的设备数量
  Object.keys(areaGroupedData.value).forEach(area => {
    console.log(`区域${area}: ${areaGroupedData.value[area].length}个设备`)
  })
}

/**
 * 获取指定区域的设备数据（用于动态表格渲染）
 */
const getAreaDevices = (areaNumber) => {
  return areaGroupedData.value[areaNumber] || []
}

/**
 * 根据区域和设备获取实时数据值
 */
const getAreaDeviceValue = (areaNumber, device) => {
  const deviceRow = findDeviceRow(device.plc, device.tag)
  return deviceRow ? deviceRow.row : null
}

/**
 * 计算指定区域的Purple和常规雪橇数量统计
 * 复用标准的calculateSkidCount函数，确保与数据看板计算逻辑完全一致
 * @param {number} areaNumber 区域编号(1-7)
 * @returns {object} {purple: number, normal: number}
 */
const getAreaSkidStats = (areaNumber) => {
  const areaDevices = getAreaDevices(areaNumber)
  let purpleCount = 0
  let normalCount = 0
  
  areaDevices.forEach(device => {
    const deviceValue = getAreaDeviceValue(areaNumber, device)
    if (deviceValue?.hasData && deviceValue.value) {
      const numValue = parseFloat(deviceValue.value)
      
      if (!isNaN(numValue) && numValue > 0) {
        // 使用标准的calculateSkidCount函数计算单个设备的雪橇数量
        const skidCount = calculateSkidCount(device.factor, deviceValue.value, device.weight)
        
        if (numValue > 5999) {
          // Purple雪橇：数据值>5999的雪橇数量
          purpleCount += skidCount
        } else {
          // 常规雪橇：数据值<=5999的雪橇数量
          normalCount += skidCount
        }
      }
    }
  })
  
  return { 
    purple: Math.round(purpleCount), 
    normal: Math.round(normalCount) 
  }
}

// ==================== WebSocket相关方法 ====================

/**
 * 连接WebSocket服务器
 */
const connectWebSocket = () => {
  if (socket.value && socket.value.readyState === WebSocket.OPEN) {
    ElMessage.warning('WebSocket已经连接')
    return
  }

  connectionStatus.value = 'connecting'
  tableLoading.value = true

  try {
    const wsUrl_full = `ws://${wsUrl.value}`
    console.log('正在连接WebSocket服务器:', wsUrl_full)
    
    socket.value = new WebSocket(wsUrl_full)
    
    // WebSocket事件处理
    socket.value.onopen = onSocketOpen
    socket.value.onmessage = onSocketMessage
    socket.value.onclose = onSocketClose
    socket.value.onerror = onSocketError
    
  } catch (error) {
    console.error('WebSocket连接失败:', error)
    ElMessage.error('WebSocket连接失败: ' + error.message)
    connectionStatus.value = 'disconnected'
    tableLoading.value = false
  }
}

/**
 * 断开WebSocket连接
 */
const disconnectWebSocket = () => {
  if (socket.value) {
    socket.value.close()
    socket.value = null
  }
  connectionStatus.value = 'disconnected'
  stopDurationTimer()
  ElMessage.info('已断开WebSocket连接')
}

/**
 * WebSocket连接成功处理
 */
const onSocketOpen = () => {
  console.log('WebSocket连接已建立')
  connectionStatus.value = 'connected'
  connectionStartTime.value = new Date()
  tableLoading.value = false
  startDurationTimer()
  
  ElNotification({
    title: '连接成功',
    message: 'WebSocket连接已建立，开始订阅设备数据',
    type: 'success'
  })

  // 发送设备点位订阅请求（优化版）
  // 注意：只发送服务器必需的字段(id,type,plc,tag)，其他字段(factor,RBindex,weight)保留在客户端用于本地计算
  deviceParams.value.forEach((param, index) => {
    setTimeout(() => {
      // 优化后的订阅流程：
      // 1. 客户端连接WebSocket服务器
      // 2. 客户端遍历所有设备参数，提取必要字段发送订阅请求（sendDeviceSubscription(param)）
      // 3. 服务器收到精简的订阅请求后，将该客户端加入对应设备点位的数据推送列表
      // 4. 服务器有新数据时，主动推送给已订阅的客户端
      // 5. 客户端收到推送数据后，结合本地配置的factor等字段进行处理和展示
      sendDeviceSubscription(param)
    }, index * 100) // 间隔100ms发送，避免一次性发送太多请求
  })

  // 启动心跳保活
  startHeartbeat()
}

/**
 * WebSocket消息接收处理
 * 根据服务器返回的数据格式解析并更新对应表格行
 */
const onSocketMessage = (event) => {
  messageCount.value++
  console.log('收到WebSocket数据:', event.data)
  
  try {
    // 服务器返回的实际数据格式：
    // {
    //   "type": "dataChange",
    //   "id": "",
    //   "tag": "L3FUB2.L3FUB2_1D_1D130RB_1D130RB.ILO.SD.M1003_BodyID",
    //   "ts": "2025-09-05T14:27:34.781+08:00",
    //   "value": "782025836495102N54Y2T2TMQB000-",
    //   "quality": 192,
    //   "source": "CNSVWSFVM131",
    //   "userRights": 0
    // }
    const data = JSON.parse(event.data)
    
    // 解析服务器返回的tag字段，提取PLC名称和标签路径
    if (data.tag && data.tag.includes('.')) {
      // 从 "L3FUB2.L3FUB2_1D_1D130RB_1D130RB.ILO.SD.M1003_BodyID" 中提取：
      // plc: "L3FUB2" 
      // tagPath: ".L3FUB2_1D_1D130RB_1D130RB.ILO.SD.M1003_BodyID"
      const tagParts = data.tag.split('.')
      const extractedPlc = tagParts[0]  // PLC名称是第一个点号前的部分
      const extractedTag = '.' + tagParts.slice(1).join('.')  // 标签路径是第一个点号后的部分，前面加上点号
      
      console.log(`解析服务器数据 - PLC: ${extractedPlc}, Tag: ${extractedTag}`)
      
      // 查找对应的设备行
      const deviceResult = findDeviceRow(extractedPlc, extractedTag)
      
      if (deviceResult) {
        const { row } = deviceResult
        const currentTime = new Date()
        
        // 更新设备行数据
        row.value = data.value || 'N/A'
        row.lastUpdateTime = currentTime
        row.connectionStatus = 'online'
        row.updateCount++
        row.quality = data.quality || null
        row.source = data.source || null
        row.serverTimestamp = data.ts || null
        
        // 如果是首次收到数据，记录首次接收时间
        if (!row.hasData) {
          row.hasData = true
          row.timestamp = currentTime
        }
        
        console.log(`✅ 已更新设备 ${row.plc}${row.tag} 的数据: ${row.value}`)
      } else {
        // 如果找不到对应的设备行，输出警告（可能是配置文件中没有该设备）
        console.warn(`⚠️  收到未配置的设备数据 - PLC: ${extractedPlc}, Tag: ${extractedTag}`)
        console.warn(`完整服务器tag: ${data.tag}`)
      }
    } else {
      console.error('❌ 服务器返回的数据格式异常，缺少tag字段或格式不正确:', data)
    }
    
  } catch (error) {
    console.error('❌ 数据解析失败:', error)
    console.error('原始数据:', event.data)
  }
}

/**
 * WebSocket连接关闭处理
 */
const onSocketClose = (event) => {
  console.log('WebSocket连接已关闭:', event)
  connectionStatus.value = 'disconnected'
  stopDurationTimer()
  tableLoading.value = false
  
  ElNotification({
    title: '连接断开',
    message: 'WebSocket连接已断开',
    type: 'warning'
  })
}

/**
 * WebSocket错误处理
 */
const onSocketError = (error) => {
  console.error('WebSocket发生错误:', error)
  connectionStatus.value = 'disconnected'
  tableLoading.value = false
  
  ElMessage.error('WebSocket连接发生错误')
}

/**
 * 发送设备订阅请求（优化版）
 * 只发送服务器必需的字段，减少网络传输数据量
 */
const sendDeviceSubscription = (param) => {
  if (socket.value && socket.value.readyState === WebSocket.OPEN) {
    // 只提取服务器需要的字段进行订阅
    const subscriptionRequest = {
      id: param.id || "",
      type: param.type || "advise", 
      plc: param.plc,
      tag: param.tag
    }
    
    const message = JSON.stringify(subscriptionRequest)
    socket.value.send(message)
    console.log('发送设备订阅(优化版):', message)
  }
}

// ==================== 心跳保活机制 ====================
let heartbeatTimer = null

const startHeartbeat = () => {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
  }
  
  heartbeatTimer = setInterval(() => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      const heartbeatMsg = JSON.stringify({
        type: "info",
        info: "alive"
      })
      socket.value.send(heartbeatMsg)
      heartbeatCount.value++
      console.log('发送心跳保活信号:', heartbeatCount.value)
    } else {
      clearInterval(heartbeatTimer)
    }
  }, 2000) // 每2秒发送一次心跳
}

// ==================== 连接时长计时器 ====================
let durationTimer = null

const startDurationTimer = () => {
  if (durationTimer) {
    clearInterval(durationTimer)
  }
  
  durationTimer = setInterval(() => {
    if (connectionStartTime.value) {
      const duration = new Date() - connectionStartTime.value
      connectionDuration.value = formatDuration(duration)
    }
  }, 1000)
}

const stopDurationTimer = () => {
  if (durationTimer) {
    clearInterval(durationTimer)
    durationTimer = null
  }
  connectionDuration.value = '00:00:00'
}

// ==================== 数据看板计算 ====================

/**
 * Purple雪橇数量计算（数据值>5999时的雪橇数量之和）
 * 使用factor.e5进行计算
 */
const purpleSkidCount = computed(() => {
  return deviceData.value.reduce((total, row) => {
    // 只计算有数据且数据值>5999的记录
    if (row.hasData && row.value && row.factor) {
      const numValue = parseFloat(row.value)
      
      if (!isNaN(numValue) && numValue > 5999) {
        // 处理factor对象格式，使用factor.e5
        if (typeof row.factor === 'object' && row.factor.e5) {
          const factorE5 = parseFloat(row.factor.e5)
          if (!isNaN(factorE5)) {
            return total + (1 * factorE5)
          }
        } else {
          // 兼容旧格式：factor为数值
          const factorNum = parseFloat(row.factor)
          if (!isNaN(factorNum)) {
            return total + (1 * factorNum)
          }
        }
      }
    }
    return total
  }, 0)
})

/**
 * 常规雪橇数量计算（数据值<=5999时的雪橇数量之和）
 * 优化逻辑：使用factor.norm进行计算，当'数据值'<5999 且"weight"=1时，雪橇数量=1
 */
const normalSkidCount = computed(() => {
  return deviceData.value.reduce((total, row) => {
    // 只计算有数据且数据值<=5999的记录
    if (row.hasData && row.value) {
      const numValue = parseFloat(row.value)
      
      if (!isNaN(numValue) && numValue <= 5999 && numValue > 0) {
        // 优先级最高：当'数据值'<5999 且"weight"=1时，雪橇数量=1
        if (row.weight && parseFloat(row.weight) === 1) {
          return total + 1
        } else if (row.factor) {
          // 处理factor对象格式，使用factor.norm
          if (typeof row.factor === 'object' && row.factor.norm) {
            const factorNorm = parseFloat(row.factor.norm)
            if (!isNaN(factorNorm)) {
              return total + (1 * factorNorm)
            }
          } else {
            // 兼容旧格式：factor为数值
            const factorNum = parseFloat(row.factor)
            if (!isNaN(factorNum)) {
              return total + (1 * factorNum)
            }
          }
        }
      }
    }
    return total
  }, 0)
})

/**
 * 总雪橇数量计算
 */
const totalSkidCount = computed(() => {
  return purpleSkidCount.value + normalSkidCount.value
})

// ==================== 计算和颜色方法 ====================

/**
 * 计算雪橇数量 - 支持factor对象格式
 * @param {Object|string|number} factor - 系数值对象 {norm: "4", e5: "3"} 或数值
 * @param {string|number} value - 数据值
 * @param {string|number} weight - 权重值
 * @returns {number} 雪橇数量
 */
const calculateSkidCount = (factor, value, weight) => {
  const numValue = parseFloat(value)
  const weightNum = parseFloat(weight || 0)
  
  // 数据值无效时返回0
  if (isNaN(numValue) || numValue <= 0) {
    return 0
  }
  
  // 优先级最高：当'数据值'<5999 且"weight"=1时，雪橇数量=1
  if (numValue < 5999 && weightNum === 1) {
    return 1
  }
  
  // 处理factor对象格式
  if (factor && typeof factor === 'object') {
    if (numValue > 5999) {
      // 数据值>5999时，雪橇数量=1*Factor.e5
      const factorE5 = parseFloat(factor.e5 || 0)
      return isNaN(factorE5) ? 0 : 1 * factorE5
    } else {
      // 数据值<=5999时，雪橇数量=1*Factor.norm
      const factorNorm = parseFloat(factor.norm || 0)
      return isNaN(factorNorm) ? 0 : 1 * factorNorm
    }
  }
  
  // 兼容旧格式：factor为数值的情况
  const factorNum = parseFloat(factor)
  return isNaN(factorNum) ? 0 : 1 * factorNum
}

/**
 * 根据数据值获取颜色类型
 * @param {string|number} value - 数据值
 * @returns {string} Element Plus tag 类型
 */
const getValueColorType = (value) => {
  // 如果数据值为空、null、undefined 或 0，返回灰色
  if (!value || value === null || value === undefined || value === 0 || value === '0') {
    return 'info'  // 灰色
  }
  
  // 尝试将数据值转换为数字进行比较
  const numValue = parseFloat(value)
  
  // 如果不能转换为数字，返回灰色
  if (isNaN(numValue)) {
    return 'info'  // 灰色
  }
  
  // 根据数值大小判断颜色
  if (numValue > 5999) {
    return 'warning'  // 黄色
  } else {
    return 'primary'  // 蓝色
  }
}

// ==================== 工具方法 ====================

/**
 * 显示雪橇堆垛配置信息
 */
const showSkidConfigInfo = () => {
  ElMessageBox.alert(
    `常规雪橇堆垛配置：${normfactor.value}<br>Purple雪橇堆垛配置：${e5factor.value}<br>解跺机以满载计算`,
    
    '雪橇堆垛配置信息',
    {
      confirmButtonText: '确定',
      type: 'info',
      dangerouslyUseHTMLString: true,
      customStyle: {
        width: '400px'
      }
    }
  )
}

/**
 * 显示7区域示意图
 */
const showAreaDiagram = () => {
  showAreaDiagramDialog.value = true
  ElMessage.success('7区域布局示意图已打开')
}

/**
 * 图片加载成功处理
 */
const onImageLoad = () => {
  console.log('布局示意图加载成功')
}

/**
 * 图片加载失败处理
 */
const onImageError = () => {
  console.log('布局示意图加载失败')
  ElMessage.warning('布局示意图加载失败，请检查图片文件')
}

/**
 * 格式化时间显示
 */
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * 获取连接状态对应的标签类型
 */
const getStatusType = (status) => {
  switch (status) {
    case 'online':
      return 'success'
    case 'waiting':
      return 'warning'
    case 'offline':
      return 'danger'
    default:
      return 'info'
  }
}

/**
 * 获取连接状态显示文本
 */
const getStatusText = (status) => {
  switch (status) {
    case 'online':
      return '在线'
    case 'waiting':
      return '等待'
    case 'offline':
      return '离线'
    default:
      return '未知'
  }
}

/**
 * 获取数据质量对应的标签类型
 */
const getQualityType = (quality) => {
  if (quality === null || quality === undefined) {
    return 'info'
  }
  
  // 根据OPC质量值判断：192通常表示好质量，其他值可能表示问题
  switch (quality) {
    case 192:
      return 'success'  // 好质量
    case 0:
      return 'danger'   // 坏质量
    default:
      if (quality >= 128) {
        return 'success'  // 好质量范围
      } else if (quality >= 64) {
        return 'warning'  // 不确定质量
      } else {
        return 'danger'   // 坏质量
      }
  }
}

/**
 * 格式化连接时长
 */
const formatDuration = (milliseconds) => {
  const seconds = Math.floor(milliseconds / 1000)
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

/**
 * 清空数据表格
 * 重置所有设备行的数据状态，但保持表格结构和配置字段
 */
const clearData = () => {
  deviceData.value.forEach(row => {
    row.value = null
    row.connectionStatus = 'waiting'
    row.lastUpdateTime = null
    row.hasData = false
    row.updateCount = 0
    row.timestamp = null
    row.quality = null
    row.source = null
    row.serverTimestamp = null
    // 注意：不重置area和sequence，因为它们是配置字段，不是数据字段
  })
  messageCount.value = 0
  ElMessage.success('数据已清空，设备状态已重置')
}

/**
 * 刷新数据
 */
const refreshData = () => {
  if (socket.value && socket.value.readyState === WebSocket.OPEN) {
    // 重新发送订阅请求
    deviceParams.value.forEach((param, index) => {
      setTimeout(() => {
        sendDeviceSubscription(param)
      }, index * 50)
    })
    ElMessage.success('已重新发送订阅请求')
  } else {
    ElMessage.warning('请先连接WebSocket服务器')
  }
}

// ==================== 快捷键处理 ====================

/**
 * 处理快捷键事件
 * Ctrl+M: 同时切换控制面板和高级表格列的显示状态
 */
const handleKeydown = (event) => {
  if (event.ctrlKey && event.key.toLowerCase() === 'm') {
    event.preventDefault() // 阻止默认行为
    toggleUIVisibility()
  }
}

/**
 * 切换UI元素显示状态
 */
const toggleUIVisibility = () => {
  const prevPanel = showControlPanel.value
  
  showControlPanel.value = !showControlPanel.value
  // 保持高级列始终显示，不随面板切换而变化
  
  console.log(`🔄 UI切换完成:`)
  console.log(`  控制面板: ${prevPanel ? '显示' : '隐藏'} → ${showControlPanel.value ? '显示' : '隐藏'}`)
  console.log(`  高级列: 始终显示（保持完整数据）`)
  
  ElMessage.info(`UI切换: ${showControlPanel.value ? '显示' : '隐藏'}详细面板，数据列保持完整`)
}

// ==================== 生命周期钩子 ====================

onMounted(() => {
  console.log('WebSocket数据采集演示系统已加载')
  // 初始化设备数据表格
  initializeDeviceTable()
  
  // 初始化7区域数据分组
  groupDevicesByArea()
  
  // 添加全局快捷键监听
  document.addEventListener('keydown', handleKeydown)
  
  // 自动连接WebSocket服务器
  setTimeout(() => {
    console.log('正在自动连接WebSocket服务器...')
    connectWebSocket()
  }, 1000) // 延迟1秒后自动连接，确保页面完全加载
})

onUnmounted(() => {
  // 清理资源
  if (socket.value) {
    socket.value.close()
  }
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
  }
  if (durationTimer) {
    clearInterval(durationTimer)
  }
  
  // 移除快捷键监听
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.system-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  height: 80px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-buttons {
  display: flex;
  align-items: center;
  gap: 12px;
}

.config-info-container {
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.1);
}

.config-info-container:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.header-diagram-button {
  background: rgba(255, 255, 255, 0.15) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: white !important;
  transition: all 0.3s ease;
}

.header-diagram-button:hover {
  background: rgba(255, 255, 255, 0.25) !important;
  border-color: rgba(255, 255, 255, 0.5) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.config-info-item {
  margin: 2px 0;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
  white-space: nowrap;
}

.system-title {
  display: flex;
  align-items: center;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.title-icon {
  margin-right: 12px;
  font-size: 28px;
}

.connection-status {
  font-size: 14px;
}

.main-container {
  flex: 1;
  padding: 16px;
  gap: 16px;
}

.control-panel {
  background: transparent;
  transition: width 0.3s ease, opacity 0.3s ease;
  overflow: hidden;
}

.control-card {
  height: fit-content;
}

.data-card {
  height: calc(100vh - 100px); /* 调整卡片高度，为底部留出空间 */
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}

.data-card .el-card__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 3px 8px 20px 8px; /* 大幅增加底部内边距 */
  overflow: hidden;
  min-height: 0; /* 重要：允许flex收缩 */
}

.data-card .el-card__header {
  padding: 8px 12px; /* 减小头部内边距 */
  min-height: 35px;
  flex-shrink: 0; /* 防止头部被压缩 */
}

.card-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-header .el-icon {
  margin-right: 8px;
  color: #409EFF;
}

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.connection-config {
  margin-bottom: 24px;
}

.statistics {
  margin-top: 16px;
}

.data-display {
  padding: 0;
}

/* ==================== 数据看板样式 ==================== */
.data-dashboard {
  margin-bottom: 10px; /* 大幅减小底边距为表格腾出空间 */
  padding: 0 4px;
}

.dashboard-row {
  margin: 0 -10px;
}

.dashboard-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  border: none;
  height: 100px;
  cursor: pointer;
}

.dashboard-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.dashboard-item {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 8px;
}

.dashboard-icon {
  margin-right: 12px;
  padding: 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dashboard-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center; /* 垂直居中 */
  align-items: flex-start; /* 左对齐 */
  min-height: 0; /* 重要：允许flex收缩 */
}

.dashboard-label {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 1px 0; /* 最小边距 */
  font-weight: 500;
  line-height: 1.1;
  white-space: nowrap;
}

.dashboard-value {
  font-size: 32px;
  font-weight: bold;
  margin: 0 0 1px 0; /* 最小边距 */
  line-height: 1;
  color: inherit;
}

.dashboard-desc {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
  line-height: 1.1;
  white-space: nowrap;
}

/* Purple卡片样式 */
.purple-card {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.purple-card .dashboard-icon {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.purple-card .dashboard-label,
.purple-card .dashboard-desc {
  color: rgba(255, 255, 255, 0.9);
}

.purple-value {
  color: white;
}

/* 常规卡片样式 */
.normal-card {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
}

.normal-card .dashboard-icon {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.normal-card .dashboard-label,
.normal-card .dashboard-desc {
  color: rgba(255, 255, 255, 0.9);
}

.normal-value {
  color: white;
}

/* 总计卡片样式 */
.total-card {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.total-card .dashboard-icon {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.total-card .dashboard-label,
.total-card .dashboard-desc {
  color: rgba(255, 255, 255, 0.9);
}

.total-value {
  color: white;
}

/* 信息卡片样式 */
.info-card {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.info-card .dashboard-icon {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.info-card .dashboard-label,
.info-card .dashboard-desc {
  color: rgba(255, 255, 255, 0.9);
}

.info-value {
  color: white;
}

/* 设备状态指示样式（已移除动画效果） */

/* 数据更新高亮效果 */
.data-updated {
  background-color: #f0f9ff;
  transition: background-color 0.3s ease;
}

.recently-updated {
  background-color: #e8f5e8;
  animation: highlight-fade 3s ease-out;
}

@keyframes highlight-fade {
  0% { background-color: #c8e6c9; }
  100% { background-color: transparent; }
}

/* ==================== 表格字体增大样式 ==================== */

/* 表格字体增大2号 */
.larger-table-font {
  font-size: 16px !important; /* 基础字体从14px增大到16px */
}

.larger-table-font .el-table__header th {
  font-size: 18px !important; /* 表头字体增大 */
  font-weight: 600 !important;
  padding: 14px 8px !important; /* 增加表头内边距 */
}

.larger-table-font .el-table__body td {
  font-size: 16px !important; /* 表格内容字体增大 */
  padding: 14px 8px !important; /* 增加表格单元格内边距 */
}

.larger-table-font .el-tag {
  font-size: 15px !important; /* 标签字体增大 */
  padding: 0 12px !important;
  height: 30px !important;
  line-height: 30px !important;
}

.larger-table-font .el-table__row {
  height: 56px !important; /* 增加行高 */
}

/* 表格容器样式优化 */
.larger-table-font .el-table__body-wrapper {
  overflow-y: auto !important;
  max-height: calc(100vh - 360px) !important; /* 进一步减小高度，确保滚动空间 */
  padding-bottom: 0px !important; /* 移除内边距，避免干扰滚动 */
}

.larger-table-font .el-table__header-wrapper {
  flex-shrink: 0; /* 防止表头被压缩 */
}

/* 确保表格底部有足够的空间 */
.larger-table-font {
  margin-bottom: 20px; /* 增加表格底部边距 */
  border-bottom: none; /* 移除底部边框避免遮挡 */
}

/* 表格最后一行样式优化 */
.larger-table-font .el-table__body tr:last-child td {
  border-bottom: 1px solid #ebeef5; /* 确保最后一行有边框 */
  padding-bottom: 14px !important; /* 标准内边距 */
}

/* 表格底部额外空间 - 使用更可靠的方法 */
.larger-table-font .el-table__body {
  padding-bottom: 60px !important; /* 在表格体底部添加大量空间 */
}

/* 确保表格体有足够的空间 */
.larger-table-font .el-table__body table {
  margin-bottom: 40px !important; /* 在表格底部留出空间 */
}

/* 强制为最后一行留出空间 */
.larger-table-font .el-table__body-wrapper {
  box-sizing: border-box !important;
}

/* 在表格体内部添加空白行的效果 */
.larger-table-font .el-table__body tbody::after {
  content: "";
  display: table-row;
  height: 80px; /* 添加一个虚拟的空白行高度 */
}

/* 滚动条样式优化 */
.larger-table-font .el-table__body-wrapper::-webkit-scrollbar {
  width: 8px;
}

.larger-table-font .el-table__body-wrapper::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.larger-table-font .el-table__body-wrapper::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.larger-table-font .el-table__body-wrapper::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* ==================== 响应式设计 ==================== */

/* 基础响应式优化 */
.el-table {
  font-size: 12px;
  width: 100% !important;
}

/* 表格自动填满优化 */
.el-table__body-wrapper,
.el-table__header-wrapper {
  width: 100% !important;
}

.el-table th.el-table__cell,
.el-table td.el-table__cell {
  padding: 8px 6px;
  word-break: break-all;
}

/* 表格宽度自动调整 */
.el-table.el-table--fit {
  table-layout: auto !important;
}

/* 确保表格占满容器宽度 */
.el-table .el-table__body table,
.el-table .el-table__header table {
  width: 100% !important;
  table-layout: fixed;
}

/* 简化表格样式 - 当高级列隐藏时 */
.el-table.table-simplified {
  table-layout: auto !important;
}

.el-table.table-simplified .el-table__body table,
.el-table.table-simplified .el-table__header table {
  table-layout: auto !important;
}

/* 简化表格时，让关键列更好地利用空间 */
.el-table.table-simplified .el-table__cell {
  min-width: auto !important;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}

.el-table.table-simplified .cell {
  line-height: 1.4;
}

/* 表格列切换动画效果 */
.el-table .el-table__header th,
.el-table .el-table__body td {
  transition: all 0.3s ease;
}

/* 控制面板切换动画增强 */
.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: all 0.3s ease;
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  opacity: 0;
  transform: translateX(-100%);
}

/* 桌面设备 (>1024px) */
@media (min-width: 1025px) {
  .dashboard-row .el-col {
    margin-bottom: 0;
  }
  
  .data-dashboard {
    padding: 0 8px;
  }
}

/* 平板设备 (768px - 1024px) */
@media (max-width: 1024px) and (min-width: 769px) {
  .main-container {
    padding: 12px;
  }
  
  .control-panel {
    width: 280px !important;
  }
  
  .dashboard-row {
    margin: 0 -8px;
  }
  
  .dashboard-card {
    height: 90px;
  }
  
  .dashboard-value {
    font-size: 20px;
  }
  
  .system-title {
    font-size: 20px;
  }
  
  .el-table {
    font-size: 11px;
  }
}

/* 手机设备 (≤768px) */
@media (max-width: 768px) {
  .main-container {
    flex-direction: column;
    padding: 8px;
    gap: 12px;
  }
  
  .control-panel {
    width: 100% !important;
    position: fixed;
    top: 80px;
    left: 0;
    right: 0;
    z-index: 1000;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
    padding: 0 8px;
  }
  
  .system-title {
    font-size: 16px;
  }
  
  .title-icon {
    font-size: 20px;
    margin-right: 8px;
  }
  
  .header-content {
    flex-direction: row;
    justify-content: space-between;
    padding: 0 12px;
  }
  
  .header-buttons {
    gap: 8px;
  }
  
  .header-diagram-button {
    padding: 4px 8px !important;
    font-size: 11px !important;
  }
  
  .header-diagram-button .el-icon {
    font-size: 12px;
  }
  
  .connection-status {
    font-size: 12px;
  }
  
  /* 数据看板响应式 */
  .dashboard-row {
    margin: 0 -6px;
  }
  
  .dashboard-row .el-col {
    margin-bottom: 12px;
  }
  
  .dashboard-card {
    height: 80px;
  }
  
  .dashboard-item {
    padding: 6px;
  }
  
  .dashboard-icon {
    margin-right: 8px;
    padding: 6px;
  }
  
  .dashboard-label {
    font-size: 11px;
  }
  
  .dashboard-value {
    font-size: 18px;
  }
  
  .dashboard-desc {
    font-size: 10px;
  }
  
  /* 表格响应式 */
  .el-table {
    font-size: 10px;
  }
  
  .el-table .el-table__cell {
    padding: 8px 4px;
  }
  
  .data-display {
    margin-top: 120px; /* 为固定控制面板留出空间 */
  }
  
  /* 调整主要列的宽度分配 - 隐藏高级列时的优化 */
  .el-table-column--type-index {
    width: 40px !important;
  }
  
  /* 手机端表格列宽度自适应优化 */
  .el-table .el-table__cell {
    padding: 6px 3px !important;
  }
  
  /* 隐藏高级列时，主要列更好地填满空间 */
  .el-table th,
  .el-table td {
    text-align: center;
    vertical-align: middle;
  }
}

/* 小屏手机设备 (≤480px) */
@media (max-width: 480px) {
  .system-title {
    font-size: 14px;
  }
  
  .header-content {
    padding: 0 8px;
  }
  
  .header-buttons {
    gap: 6px;
  }
  
  .header-diagram-button {
    padding: 3px 6px !important;
    font-size: 10px !important;
  }
  
  .header-diagram-button .el-icon {
    font-size: 10px;
  }
  
  .config-info-container {
    padding: 6px 8px;
  }
  
  .config-info-item {
    font-size: 10px;
  }
  
  .dashboard-row .el-col {
    padding: 0 4px;
  }
  
  .dashboard-card {
    height: 70px;
  }
  
  .dashboard-value {
    font-size: 16px;
  }
  
  .dashboard-label {
    font-size: 10px;
  }
  
  .el-table {
    font-size: 9px;
  }
  
  .main-container {
    padding: 6px;
  }
}


/* ==================== 统一滚动容器样式 ==================== */

.unified-scroll-container {
  max-height: calc(100vh - 280px);
  overflow-y: auto;
  margin: 20px 0;
  border-radius: 8px;
  background: #fafafa;
  padding: 8px;
}

/* 统一滚动容器滚动条样式 */
.unified-scroll-container::-webkit-scrollbar {
  width: 8px;
}

.unified-scroll-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.unified-scroll-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.unified-scroll-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* ==================== 7区域数据表格布局样式 ==================== */

.areas-grid-layout {
  margin: 0 0 20px 0;
  padding: 0;
}


.areas-title {
  text-align: center;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  padding: 12px 0;
  border-bottom: 2px solid #409EFF;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 7区域网格布局 */
.areas-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  grid-template-rows: auto auto auto auto;
  gap: 16px;
  margin-bottom: 20px;
}

/* 第一行：area1, area2 */
.area1 { grid-column: 1; grid-row: 1; }
.area2 { grid-column: 2; grid-row: 1; }

/* 第二行：area3 居中 */
.area3 { 
  grid-column: 2; 
  grid-row: 2; 
}

/* 第三行：area4, area5, area6 */
.area4 { grid-column: 1; grid-row: 3; }
.area5 { grid-column: 2; grid-row: 3; }
.area6 { grid-column: 3; grid-row: 3; }

/* 第四行：area7 居中 */
.area7 { 
  grid-column: 2; 
  grid-row: 4; 
}

.area-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 16px;
  height: auto;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.area-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.area-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f0f0;
  flex-shrink: 0;
}

.area-header-left {
  display: flex;
  align-items: center;
  flex: 1;
}

.area-header-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.area-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.stats-label {
  color: #606266;
  font-weight: 500;
  font-size: 11px;
}

.purple-stats {
  background: linear-gradient(135deg, #f59e0b, #d97706) !important;
  border: none !important;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(245, 158, 11, 0.3);
}

.normal-stats {
  background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
  border: none !important;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.area-stats .el-tag {
  margin-left: 2px;
  font-size: 16px;
  padding: 2px 8px;
  border-radius: 20px;
  transition: all 0.3s ease;
  min-width: 40px;
  text-align: center;
}

.area-stats .el-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(182, 158, 158, 0.15);
}

.area-table-container {
  flex: 1;
  width: 100%;
}


/* ==================== 主数据表格优化 ==================== */

.main-data-table {
  min-height: 400px !important;
  border-radius: 8px;
  overflow: hidden;
}

.main-data-table .el-table__body-wrapper {
  min-height: 350px !important;
}

/* 统一容器内的主表格样式 */
.unified-scroll-container .main-data-table {
  margin-top: 20px;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.area-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.area-badge {
  background: #409EFF;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 8px;
  font-weight: 600;
}

.mini-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: visible;
  table-layout: auto;
}

.mini-table th {
  background: #f8f9fa;
  padding: 8px 6px;
  text-align: center;
  border: 1px solid #e9ecef;
  font-weight: 600;
  color: #495057;
  font-size: 11px;
}

.mini-table td {
  padding: 6px;
  text-align: center;
  border: 1px solid #e9ecef;
  color: #666;
  font-size: 11px;
}

.mini-table tr:nth-child(even) {
  background: #f8f9fa;
}

.mini-table tr:hover {
  background: #e8f4f8;
}

/* 数据点位列样式优化 */
.tag-cell {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}

.tag-cell:hover {
  overflow: visible;
  white-space: normal;
  word-break: break-all;
  background: #f0f8ff;
  position: relative;
  z-index: 10;
}

/* 设备连接状态行样式 */
.mini-table tr.online {
  background-color: #f0f9ff;
  border-left: 3px solid #10b981;
}

.mini-table tr.waiting {
  background-color: #fffbeb;
  border-left: 3px solid #f59e0b;
}

.mini-table tr.offline {
  background-color: #fef2f2;
  border-left: 3px solid #ef4444;
}

/* 无数据提示样式 */
.no-data {
  text-align: center;
  color: #6b7280;
  font-style: italic;
  padding: 16px 8px;
}

/* 状态指示器样式 */
.status-cell {
  text-align: center;
  padding: 4px !important;
}

.status-indicator {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  text-align: center;
  min-width: 32px;
}

.status-indicator.online {
  background-color: #dcfce7;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.status-indicator.waiting {
  background-color: #fef3c7;
  color: #d97706;
  border: 1px solid #fde68a;
}

.status-indicator.offline {
  background-color: #fecaca;
  color: #dc2626;
  border: 1px solid #fca5a5;
}

/* 7区域表格新增列样式 */
.data-value-cell {
  text-align: center;
  padding: 4px !important;
  min-width: 80px;
}

.data-value-cell .el-tag {
  font-size: 10px !important;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.skid-count-cell {
  text-align: center;
  padding: 4px !important;
  min-width: 60px;
}

.skid-count-cell .el-tag {
  font-size: 10px !important;
  font-weight: 600;
}

.update-time-cell {
  text-align: center;
  padding: 4px !important;
  min-width: 90px;
}

.update-time-cell .el-tag {
  font-size: 9px !important;
  max-width: 85px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 7区域表格整体优化 */
.mini-table {
  table-layout: fixed;
  width: 100%;
}

.mini-table th:nth-child(1) { width: 12%; }  /* PLC设备 */
.mini-table th:nth-child(2) { width: 15%; }  /* 滚床编号 */
.mini-table th:nth-child(3) { width: 25%; }  /* 数据点位 */
.mini-table th:nth-child(4) { width: 12%; }  /* 数据值 */
.mini-table th:nth-child(5) { width: 10%; }  /* 雪橇数量 */
.mini-table th:nth-child(6) { width: 8%; }   /* 状态 */
.mini-table th:nth-child(7) { width: 18%; }  /* 最后更新 */

/* 区域特色样式 */
.area1 .area-badge { background: #FF6B6B; }
.area2 .area-badge { background: #4ECDC4; }
.area3 .area-badge { background: #45B7D1; }
.area4 .area-badge { background: #96CEB4; }
.area5 .area-badge { background: #FFEAA7; color: #333; }
.area6 .area-badge { background: #DDA0DD; }
.area7 .area-badge { background: #98D8C8; }

/* 7区域响应式设计 */
@media (max-width: 1200px) {
  .areas-grid {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto auto auto auto;
  }
  
  /* 平板布局：2列排列 */
  .area1 { grid-column: 1; grid-row: 1; }
  .area2 { grid-column: 2; grid-row: 1; }
  .area3 { grid-column: 1; grid-row: 2; }
  .area4 { grid-column: 2; grid-row: 2; }
  .area5 { grid-column: 1; grid-row: 3; }
  .area6 { grid-column: 2; grid-row: 3; }
  .area7 { grid-column: 1 / 3; grid-row: 4; max-width: 50%; margin: 0 auto; }
}

@media (max-width: 900px) {
  .areas-grid {
    grid-template-columns: 1fr;
  }
  
  .area1, .area2, .area3, .area4, .area5, .area6, .area7 {
    grid-column: 1;
  }
  
  .area1 { grid-row: 1; }
  .area2 { grid-row: 2; }
  .area3 { grid-row: 3; }
  .area4 { grid-row: 4; }
  .area5 { grid-row: 5; }
  .area6 { grid-row: 6; }
  .area7 { grid-row: 7; }
}

@media (max-width: 768px) {
  .unified-scroll-container {
    max-height: calc(100vh - 200px);
    padding: 6px;
  }
  
  .areas-grid-layout {
    padding: 0 4px;
  }
  
  .areas-grid {
    gap: 12px;
  }
  
  .areas-title {
    font-size: 16px;
    margin-bottom: 16px;
  }
  
  .area-card {
    padding: 12px;
    min-height: auto;
  }
  
  .area-title {
    font-size: 14px;
  }
  
  /* 响应式统计信息样式 */
  .area-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .area-header-right {
    width: 100%;
    justify-content: flex-start;
  }
  
  .area-stats {
    gap: 4px;
    flex-wrap: wrap;
  }
  
  .stats-label {
    font-size: 10px;
  }
  
  .area-stats .el-tag {
    font-size: 12px;
    padding: 4px 10px;
    min-width: 50px;
  }
  
  .mini-table {
    font-size: 10px;
  }
  
  .mini-table th,
  .mini-table td {
    padding: 3px 2px;
  }
  
  /* 7区域表格移动端列宽调整 */
  .mini-table th:nth-child(1) { width: 10%; }  /* PLC设备 */
  .mini-table th:nth-child(2) { width: 12%; }  /* 滚床编号 */
  .mini-table th:nth-child(3) { width: 20%; }  /* 数据点位 */
  .mini-table th:nth-child(4) { width: 12%; }  /* 数据值 */
  .mini-table th:nth-child(5) { width: 10%; }  /* 雪橇数量 */
  .mini-table th:nth-child(6) { width: 8%; }   /* 状态 */
  .mini-table th:nth-child(7) { width: 28%; }  /* 最后更新 */
  
  .data-value-cell .el-tag,
  .skid-count-cell .el-tag,
  .update-time-cell .el-tag {
    font-size: 8px !important;
    padding: 1px 4px !important;
  }
  
  .status-indicator {
    font-size: 8px !important;
    padding: 1px 4px !important;
    min-width: 24px;
  }
}

@media (max-width: 480px) {
  .unified-scroll-container {
    max-height: calc(100vh - 150px);
    padding: 4px;
  }

  .areas-title {
    font-size: 14px;
    padding: 8px 0;
  }
  
  .area-card {
    padding: 8px;
    min-height: auto;
  }
  
  .area-title {
    font-size: 12px;
  }
  
  /* 手机端主表格优化 */
  .unified-scroll-container .main-data-table {
    margin-top: 15px;
  }
  
  .area-badge {
    font-size: 10px;
    padding: 2px 6px;
  }
  
  .mini-table {
    font-size: 10px;
  }
  
  .mini-table th,
  .mini-table td {
    padding: 3px;
  }
}

/* ==================== 7区域示意图对话框样式 ==================== */

.diagram-dialog-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
  font-size: 18px;
  font-weight: 600;
}

/* 醒目的红色关闭按钮样式 - 使用深度选择器和高优先级 */
:deep(.el-dialog__headerbtn) {
  background: #ff4757 !important;
  border: 2px solid #ff3742 !important;
  border-radius: 50% !important;
  width: 40px !important;
  height: 40px !important;
  top: 10px !important;
  right: 10px !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 2px 8px rgba(255, 71, 87, 0.3) !important;
}

:deep(.el-dialog__headerbtn:hover) {
  background: #ff3742 !important;
  border-color: #ff2837 !important;
  transform: scale(1.15) !important;
  box-shadow: 0 4px 16px rgba(255, 71, 87, 0.5) !important;
}

:deep(.el-dialog__headerbtn .el-dialog__close),
:deep(.el-dialog__headerbtn i) {
  color: white !important;
  font-size: 22px !important;
  font-weight: bold !important;
}

/* 备用方案 - 全局样式覆盖 */
.el-dialog .el-dialog__headerbtn,
.el-dialog__header .el-dialog__headerbtn,
.el-dialog__headerbtn {
  background: #ff4757 !important;
  border: 2px solid #ff3742 !important;
  border-radius: 50% !important;
  width: 40px !important;
  height: 40px !important;
  top: 10px !important;
  right: 10px !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 2px 8px rgba(255, 71, 87, 0.3) !important;
}

.el-dialog .el-dialog__headerbtn:hover,
.el-dialog__header .el-dialog__headerbtn:hover,
.el-dialog__headerbtn:hover {
  background: #ff3742 !important;
  border-color: #ff2837 !important;
  transform: scale(1.15) !important;
  box-shadow: 0 4px 16px rgba(255, 71, 87, 0.5) !important;
}

.el-dialog .el-dialog__headerbtn .el-dialog__close,
.el-dialog__header .el-dialog__headerbtn .el-dialog__close,
.el-dialog__headerbtn .el-dialog__close,
.el-dialog .el-dialog__headerbtn i,
.el-dialog__headerbtn i {
  color: white !important;
  font-size: 22px !important;
  font-weight: bold !important;
}

.area-diagram-container {
  padding: 16px;
  max-height: 80vh;
  overflow-y: auto;
}

.diagram-description {
  margin-bottom: 20px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
}

.diagram-description p {
  margin: 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.diagram-content {
  margin-bottom: 20px;
}

.diagram-layout {
  background: #ffffff;
  border-radius: 12px;
  padding: 0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  min-height: 500px;
  overflow: hidden;
}

.layout-diagram-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
  position: relative;
}

.background-image-container {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
}

.layout-background-image {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>
