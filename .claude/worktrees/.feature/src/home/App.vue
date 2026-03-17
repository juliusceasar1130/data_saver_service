<!--
  修改时间：2025年10月10日15点30分
  修改内容：1. 【因子参数设置弹窗功能】在区域设置按钮下面添加"因子设置"按钮，用于修改全局e5factor和normfactor参数
           2. 实现现代化弹窗界面：数字输入框、实时预览、参数说明、响应式设计
           3. 参数保存逻辑：更新全局变量和所有设备配置，支持取消操作防止误修改
           4. 导入Setting图标，保持UI风格一致性，添加完整的用户反馈机制

  上次修改时间：2025年9月18日14点45分
  修改内容：1. 【缩略图与左侧区域比例优化】实现缩略图面板与左侧8区域的宽度比例为1:9
           2. 使用弹性布局(flex)实现比例分配：主内容区域flex: 9，缩略图面板flex: 1
           3. 设置缩略图面板最小宽度(165px)和最大宽度(200px)，确保内容正常显示
           4. 优化响应式设计：中小屏幕下缩略图面板宽度自动调整(150px-180px)
           
  上次修改时间：2025年9月18日14点40分  
  修改内容：1. 【禁用缩略图水平滚动条】添加overflow-x: hidden禁用水平滚动
           2. 保留垂直滚动条，确保内容可以垂直滚动查看
           3. 优化空间分配：调整max-height为calc(100vh - 200px)
           
  上次修改时间：2025年9月18日14点35分  
  修改内容：1. 【缩略图滚动区域空间优化】调整max-height从calc(100vh - 300px)到calc(100vh - 160px)
           2. 充分利用缩略图面板可用空间，减少底部空白区域
           3. 优化空间分配：为头部、底部按钮、边距预留最小必要空间
           
  上次修改时间：2025年9月18日14点30分  
  上次修改内容：1. 【右侧缩略图面板滚动条功能】为缩略图内容区域添加上下滚动条功能
           2. 设置thumbnail-content最大高度，启用overflow-y: auto
           3. 添加自定义滚动条样式：8px宽度，渐变色滑块，悬停效果
           4. 增加padding-right: 4px为滚动条预留空间
           
  上次修改时间：2025年9月18日14点20分  
  上次修改内容：1. 【8区域表格min-width完全移除优化】彻底移除所有min-width限制，实现完全响应式表格
           2. 移除Element Plus表格列的min-width属性，允许列宽自由调整
           3. 删除CSS中所有强制min-width规则，包括400px表格最小宽度和移动端列最小宽度
           4. 优化表格单元格样式：text-overflow ellipsis、防止不必要换行、优化内边距
           5. 改进响应式设计：表格完全自适应容器宽度，窗口变化时列宽自动调整
           6. 解决表格内容显示不全问题：滚床编号、数据值、雪橇数量列可完全压缩
           7. 【响应式PLC列隐藏功能】窗口宽度≤600px时自动隐藏PLC设备列
           8. 智能列宽重分配：PLC列隐藏后，剩余3列按35%-35%-30%重新分配
           9. 平滑过渡动画：添加CSS transition确保列隐藏/显示的流畅效果
           10. 小屏幕优化：进一步减小字体和内边距，提升空间利用率
           7. 【缩略图点击定位功能】实现点击缩略图area卡片自动定位到8区域对应区域功能
           2. 新增scrollToArea函数：平滑滚动、智能偏移、视觉反馈、错误处理一体化解决方案
           3. 缩略图交互优化：hover悬停效果、active点击反馈、区域高亮闪烁动画
           4. 智能用户引导：自动检测界面模式，提示用户切换到区域监控模式
           5. 跨容器滚动支持：优先使用统一滚动容器，备用原生scrollIntoView方案
           6. 视觉反馈完善：2秒高亮动画、成功提示消息、错误处理提示
           7. 【紫色主题高亮效果】将高亮动画主题色从蓝色改为紫色(#8B5CF6)
           8. 紫色主题一致性：桌面端、移动端、小屏设备高亮动画全部使用紫色主题
           9. 缩略图悬停优化：边框色改为紫色，背景渐变色调整为紫色系
           10. 移动端适配优化：触摸高亮色、点击反馈色均采用紫色主题
           11. 【按钮布局优化】将"配置说明"和"区域示意图"按钮从头部移动到缩略图面板底部
           12. 缩略图面板功能增强：在面板底部空白处添加功能按钮，提升空间利用率
           13. 界面布局优化：头部简化，功能按钮就近放置，提升操作便利性
           14. 【按钮居中最终方案】使用内联样式强制居中，固定宽度110px，确保完美居中显示
           15. 【8区域间隙优化】将区域间隙从12px缩小到6px，提升界面紧凑性和空间利用率
           7. 【8区域表格完整显示优化】彻底解决区域数据监控表格显示不完整问题
           2. 表格宽度自适应：移除固定宽度限制，表格可随窗口变化自动调整宽度
           3. 区域卡片优化：添加width:100%、min-width:0属性，确保充分利用网格空间
           4. 列宽智能分配：PLC设备(min-width:70px)、滚床编号(min-width:90px)、数据值(min-width:100px)、雪橇数量(min-width:70px)
           5. 表格容器优化：添加overflow处理和滚动条美化，防止内容溢出
           6. 网格布局强化：8区域网格添加width:100%和overflow:hidden，确保完整显示
           7. 移动端适配：按20%-30%-30%-20%比例分配列宽，确保各屏幕尺寸下表格完整可见
           4. 【8区域表格优化】取消状态列和最后更新列，表格更加紧凑简洁
           5. 【取消缩略图自动隐藏】取消屏幕尺寸自动隐藏功能，缩略图面板在所有屏幕尺寸下都保持可见
           5. 注释掉@media (max-width: 1200px)和@media (max-width: 768px)中的display: none规则
           6. 缩略图面板现在只能通过手动点击隐藏按钮来控制显示/隐藏状态
           7. 【缩略图面板动态数据接入】将右侧缩略图面板从静态随机数据改为真实动态数据
           2. 设备数量显示：使用getAreaDevices(areaNum).length获取各区域实际设备数量
           3. Purple/常规统计：使用getAreaSkidStats(areaNum)获取实时雪橇数量统计
           4. 实现缩略图面板与主数据同步更新，提供准确的区域概览信息
           5. 【缩略图隐藏按钮显示修复】重新设计隐藏按钮，确保在所有情况下都能正确显示
           2. 改用primary类型按钮，添加"隐藏"文字标签，提升按钮可识别性
           3. 增加thumbnail-header-right容器，优化按钮布局结构
           4. 强化CSS选择器优先级，使用具体的Element Plus卡片头部选择器
           5. 增大按钮尺寸(36x36px)和图标(20px)，确保在渐变背景下清晰可见
           6. 【缩略图隐藏按钮修复】增强隐藏按钮的可见性和交互效果
           2. 添加半透明背景和边框，确保按钮在渐变头部背景下清晰可见
           3. 增大按钮尺寸和图标，提升点击区域和视觉识别度
           4. 优化悬停效果：背景加深、边框高亮、轻微缩放，提供更好的交互反馈
           5. 【缩略图显示按钮优化】移除显示按钮的响应式隐藏设计，在所有屏幕尺寸下都保持可见
           2. 确保用户在任何设备上都能通过右侧垂直按钮重新显示隐藏的缩略图面板
           3. 提升移动端用户体验，避免按钮在小屏幕上消失导致无法恢复面板显示
           4. 【8区域缩略图面板重新添加】重新实现完整的8区域缩略图面板功能
           5. 右侧缩略图面板：220px宽度，显示8个区域的概览信息（Area标识、设备数量、Purple/常规统计）
           6. 隐藏/显示功能：面板头部隐藏按钮，隐藏时右侧显示垂直"区域概览"按钮
           7. 平滑动画效果：slide-thumbnail过渡动画，面板显示/隐藏流畅切换
           8. 自动空间填充：面板隐藏时主体内容自动占用全部宽度空间
           9. 响应式设计：大屏220px，中屏200px，小屏自动隐藏，移动端友好
           10. 视觉设计：区域特色颜色标识，Purple/常规渐变统计标签，悬停动画效果
           11. 紧凑布局：面板间距最小化(gap:2px)，左侧无边距贴合，最大化空间利用
           9. 【界面按钮样式统一】统一配置说明和区域示意图按钮的高度和样式，使用相同的el-button结构
           2. 移除旧的div样式，改为统一的.header-button样式类，确保高度32px、字体12px保持一致
           3. 添加DocumentAdd图标到配置说明按钮，与区域示意图按钮保持视觉平衡
           4. 更新响应式设计中的按钮样式：手机端28px、小屏设备24px，确保各种屏幕下的一致性
           5. 【表格显示完全修复】彻底解决"全部数据监控"表格滚动到底仍显示不全的问题
           2. 将table-wrapper从固定高度calc(100vh-285px)改为flex:1布局，自适应剩余空间
           3. 优化normal-mode-table-container使用flex布局，确保表格占用正确空间
           4. 重新设计表格内部flex结构：el-table__body-wrapper使用flex:1占用剩余空间
           5. 清理所有响应式设计中的固定高度计算，统一使用flex布局避免高度冲突
           6. 修复linter警告，清理空的CSS规则集，提高代码质量
           7. 【深度布局修复】解决flex容器内嵌套固定高度导致的布局计算冲突
           1. 【滚动区域优化】修复8区域数据监控底部空白过大问题，大幅提升空间利用率
           2. unified-scroll-container高度：280px→200px，外边距：20px→10px，节省90px显示空间
           3. 响应式优化：手机设备200px→160px，小屏设备150px→120px，areas-title边距优化
           4. areas-grid-layout底部边距：20px→8px，areas-title底部边距：20px→12px，内边距：12px→10px
           5. 【深度空间修复】发现并修复双重高度限制问题，彻底解决底部空白
           2. 修复data-card高度冲突：100px→75px，减少底部内边距：20px→8px
           3. 重新计算table-wrapper基准：基于实际布局而非视口高度，避免重复计算
           4. 桌面设备：250px→285px，平板：220px→260px，手机：180px→320px(含固定面板)，小屏：160px→280px
           5. 【底部空间优化】修复表格底部大量空间未利用问题，重新优化各设备的高度计算
           3. 【表格显示优化】修复全部数据监控表格内容显示不全问题，优化列宽度分配和表格布局
           2. 新增table-wrapper容器，提供更好的滚动控制和边框显示效果
           3. 启用水平滚动支持，确保所有列都能正常显示，设置合理的最小宽度(1400px)
           4. 优化表格固定列设置，序号列和PLC设备列固定在左侧，便于数据查看
           5. 重新调整所有列的宽度分配，确保内容完整显示：序号(55px)、PLC设备(85px)、滚床编号(105px)等
           6. 完善响应式设计，为平板(768px-1024px)和手机设备(≤768px)提供优化的表格显示
           7. 改进滚动条样式，提供更好的用户体验，支持水平和垂直双向滚动
           8. 移除过度复杂的底部空间处理逻辑，简化表格容器高度计算
           9. 【响应式布局深度优化】调整8区域网格断点1200px→900px，最大化保持area4、5、6同行显示范围
           2. 【重大优化】实施全量计算优化方案：防抖+缓存+一次遍历，替换原有computed属性
           2. 集成OptimizedFullStatsCalculator类，实现智能防抖、缓存机制和批量处理
           3. WebSocket消息处理集成统计计算器触发，实现高效的统计更新
           4. 优化区域统计函数，直接从计算器获取结果避免重复计算
           5. 添加性能监控和调试日志，便于现场环境性能分析
           6. 实现页面响应式布局优化，适配手机、平板、桌面设备
           7. 添加Ctrl+M快捷键控制连接控制面板和表格列的显示/隐藏
           8. 默认隐藏连接控制面板和部分表格列，优化界面简洁性
           9. 调整表格列宽度分配，优化数据看板响应式布局
           10. 在隐藏模式下同时隐藏数据卡片header，实现更简洁的界面显示
           11. 优化雪橇数量计算逻辑，支持factor对象格式{norm,e5}
           12. 数据值>5999时使用factor.e5，<=5999时使用factor.norm
           13. 优化Factor列显示格式，支持对象内容展示
           14. 优化WebSocket订阅请求，只发送必要字段(id,type,plc,tag)减少网络传输
           15. 添加雪橇堆垛配置信息点击提示功能，显示常规和Purple配置参数
           16. 调整配置说明按钮布局，实现左对齐显示
           17. 添加页面加载后自动连接WebSocket服务器功能，延迟1秒后自动连接
           18. 在高级列模式下增加区域列(area)和位置序号列(sequence)，提供更多设备信息展示
           19. 新增8区域网格布局，仅在隐藏模式下显示，插入到数据看板和完整表格之间
           20. 实现8区域数据显示功能：基于真实配置数据动态生成区域表格，按area分组按sequence排序
           21. 新增8区域示意图功能：在区域数据监控标题旁添加"8区域示意图"按钮
           22. 实现8区域布局示意图对话框基础框架，内容占位等待后续完善
           23. 将8区域示意图按钮移动到配置说明按钮旁边，统一放在系统头部
           24. 优化头部按钮布局和响应式设计，确保不同屏幕尺寸下的良好显示效果
           25. 完善8区域示意图对话框：添加draggable属性实现拖动功能
           26. 优化对话框关闭按钮样式，采用醒目的红色按钮设计和悬停效果（位置不变）
           27. 集成skid_layout.png背景图片到示意图中，实现响应式显示和错误处理
           28. 实现8区域表格统计信息功能：在每个区域表格右上角显示Purple和常规雪橇数量统计
           29. 添加高效的区域统计计算函数，复用现有计算逻辑确保性能优化
           30. 设计醒目的统计信息样式，采用渐变色背景和悬停效果
           31. 实现响应式统计信息布局，适配移动端显示
           32. 修复8区域统计计算逻辑错误，复用标准calculateSkidCount函数确保与数据看板计算一致
           33. 统一Purple雪橇颜色主题：数据看板卡片和8区域统计标签均采用黄色渐变背景
           34. 优化数据看板视觉效果：将所有统计数值文字颜色改为白色，提高可读性和一致性
           35. 优化8区域统计信息标签样式：改为椭圆形设计，字体增大3号，提升视觉效果
           36. 【界面模式重构】取消showAdvancedColumns高级列控制，所有表格始终显示完整列信息
           37. 【布局优化】重新设计界面模式：正常模式(数据看板+完整表格)，隐藏模式(数据看板+8区域)
           38. 简化Ctrl+M快捷键功能，专注于控制面板切换，移除表格列显示/隐藏控制
           39. 【雪橇算法优化】新增weight=2最高优先级规则：当weight字段等于2时，雪橇数量固定为1，不受factor和数据值影响
           40. 【表格组件升级】将8区域数据表格从原生HTML表格升级为Element Plus表格组件
           41. 实现完整的el-table结构：使用el-table-column定义列，保持原有数据逻辑和样式效果
           42. 优化表格样式和响应式设计：适配Element Plus表格的类名和结构，确保移动端显示正常
           43. 添加表格功能增强：stripe（斑马纹）、border（边框）、hover效果等Element Plus特性
           44. 完善连接状态行样式：适配Element Plus表格行class，保持原有的状态指示效果
           45. 【CSS最佳实践优化】移除大量!important声明，使用Vue深度选择器:deep()覆盖组件样式
           46. 采用更合理的CSS优先级策略：通过具体选择器和深度选择器替代!important强制覆盖
           47. 提高样式可维护性：清理CSS代码质量，遵循级联样式表的自然优先级规则
           48. 【8区域表格列优化】移除数据点位列，简化表格布局提升可读性和空间利用率
           49. 重新调整表格列宽分配：PLC设备(120)、滚床编号(130)、数据值(130)、雪橇数量(110)、状态(100)、最后更新(min-width:180)
           50. 更新移动端响应式列宽：优化6列布局的宽度分配，确保各种屏幕尺寸下的良好显示效果
           51. 【UI一致性优化】统一雪橇数量列与数据值列的显示格式，保持视觉一致性
           52. 雪橇数量列增加动态工具提示：显示系数和权重信息，方便理解计算依据
           53. 优化雪橇数量显示方式：从条件显示改为始终显示，空值时与数据值列显示"0"保持一致
           54. 【界面精简优化】8区域统计标签尺寸调整，从large改为small，更加紧凑美观
           55. 减小统计数值标签字体和尺寸：字体16px→13px，内边距更紧凑，圆角减少(20px→15px)
           56. 减小区域标题和标记尺寸：字体减小，内边距缩小，整体更加紧凑清晰
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
    <el-container class="main-container" style="display: flex; width: 100%;">
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
                  placeholder={{ wsUrl }}
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
      <el-main class="data-display" style="flex: 9; width: 90%;">
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

          <!-- 正常模式：全部数据监控表格 -->
          <div v-if="showControlPanel" class="normal-mode-table-container">
            <h3 class="areas-title">📊 全部数据监控</h3>
            <div class="table-wrapper">
              <el-table 
                :data="deviceData" 
                stripe 
                highlight-current-row
                style="width: 100%;"
                size="small"
                v-loading="tableLoading"
                element-loading-text="正在接收数据..."
                :fit="false"
                table-layout="auto"
                :class="{'larger-table-font': true, 'main-data-table': true}"
                :scroll-x="true"
              >
                  <el-table-column type="index" label="序号" width="55" align="center" fixed="left" />
                  <el-table-column 
                  prop="plc" 
                  label="PLC设备" 
                  width="85"
                  align="center"
                  fixed="left"
                >
                  <template #default="scope">
                    <el-tag size="small" type="primary">{{ scope.row.plc }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column 
                prop="RBindex" 
                label="滚床编号" 
                width="105"
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
                width="120"
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
                      {{ scope.row.value || '0' }}
                    </el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
              
                <el-table-column 
                prop="skidCount" 
                label="雪橇数量" 
                width="90"
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
                width="95"
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
                width="165"
                align="center"
              >
                <template #default="scope">
                  <el-tag 
                    size="small" 
                    :type="scope.row.lastUpdateTime ? 'success' : 'info'"
                  >
                    {{ scope.row.lastUpdateTime ? formatTime(scope.row.lastUpdateTime) : '0' }}
                  </el-tag>
                </template>
              </el-table-column>           

              
              <!-- 高级列 - 始终显示 -->
                <el-table-column prop="tag" label="数据点位标签" align="center" min-width="280" show-overflow-tooltip />
              
                <el-table-column prop="quality" label="数据质量" width="75" align="center">
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
              
                <el-table-column prop="updateCount" label="更新次数" width="75" align="center">
                <template #default="scope">
                  <el-tag size="small" type="info">{{ scope.row.updateCount }}</el-tag>
                </template>
              </el-table-column>
              
                <el-table-column prop="factor" label="Factor" width="140" align="center">
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
              
                <el-table-column prop="weight" label="Weight" width="75" align="center">
                <template #default="scope">
                  <el-tag size="small" type="info" v-if="scope.row.weight">
                    {{ scope.row.weight }}
                  </el-tag>
                  <span v-else class="text-gray-400">-</span>
                </template>
              </el-table-column>
              
                <el-table-column prop="type" label="消息类型" width="95" align="center">
                <template #default="scope">
                  <el-tag size="small" type="warning">{{ scope.row.type }}</el-tag>
                </template>
              </el-table-column>
              
                <el-table-column prop="area" label="区域" width="65" align="center">
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
              
                <el-table-column prop="sequence" label="位置序号" width="85" align="center">
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
          </div>

          <!-- 隐藏模式：8区域数据监控 -->
          <div v-if="!showControlPanel" class="unified-scroll-container">
            <!-- 8区域数据表格布局 -->
            <div class="areas-grid-layout">
              <h3 class="areas-title">📊 区域数据监控</h3>
              <div class="areas-grid">
                <!-- 动态生成8个区域的数据表格 -->
                <div 
                  v-for="areaNum in [0, 1, 2, 3, 4, 5, 6, 7]" 
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
                            size="small" 
                            type="danger" 
                            effect="dark"
                            class="purple-stats"
                          >
                            {{ getAreaSkidStats(areaNum).purple }}
                          </el-tag>
                          <el-tag 
                            size="small" 
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
                      <el-table 
                        :data="getAreaDevices(areaNum)" 
                        size="small"
                        stripe
                        border
                        style="width: 100%; table-layout: auto;"
                        :row-class-name="(data) => getAreaDeviceValue(areaNum, data.row)?.connectionStatus || 'waiting'"
                        class="area-mini-table"
                        :fit="true"
                        :flexible="true"
                      >
                        <!-- PLC设备列 - 自适应宽度 -->
                        <el-table-column prop="plc" label="PLC设备" align="center" :show-overflow-tooltip="true">
                          <template #default="scope">
                            <el-tag size="small" type="primary">{{ scope.row.plc }}</el-tag>
                          </template>
                        </el-table-column>
                        
                        <!-- 滚床编号列 - 弹性宽度 -->
                        <el-table-column prop="RBindex" label="滚床编号" align="center" :show-overflow-tooltip="true">
                          <template #default="scope">
                            <el-tag size="small" type="primary" v-if="scope.row.RBindex">
                              {{ scope.row.RBindex }}
                            </el-tag>
                            <span v-else class="text-gray-400">-</span>
                          </template>
                        </el-table-column>
                        
                        <!-- 数据值列 - 弹性宽度，最大权重 -->
                        <el-table-column prop="value" label="数据值" align="center" :show-overflow-tooltip="true">
                          <template #default="scope">
                            <el-tag 
                              size="small" 
                              :type="getAreaDeviceValue(areaNum, scope.row)?.hasData ? getValueColorType(getAreaDeviceValue(areaNum, scope.row)?.value) : 'info'"
                              :effect="getAreaDeviceValue(areaNum, scope.row)?.updateCount > 0 ? 'dark' : 'plain'"
                              :title="`服务器时间: ${getAreaDeviceValue(areaNum, scope.row)?.serverTimestamp || '未知'}\n数据源: ${getAreaDeviceValue(areaNum, scope.row)?.source || '未知'}`"
                            >
                              {{ getAreaDeviceValue(areaNum, scope.row)?.value || '0' }}
                            </el-tag>
                          </template>
                        </el-table-column>
                        
                        <!-- 雪橇数量列 - 自适应宽度 -->
                        <el-table-column prop="skidCount" label="雪橇数量" align="center" :show-overflow-tooltip="true">
                          <template #default="scope">
                            <el-tag 
                              size="small"
                              :type="getAreaDeviceValue(areaNum, scope.row)?.hasData ? getValueColorType(getAreaDeviceValue(areaNum, scope.row)?.value) : 'info'"
                              :effect="getAreaDeviceValue(areaNum, scope.row)?.updateCount > 0 ? 'dark' : 'plain'"
                              :title="`雪橇计算: ${scope.row.factor ? (typeof scope.row.factor === 'object' ? `norm:${scope.row.factor.norm}, e5:${scope.row.factor.e5}` : scope.row.factor) : '无系数'}, weight: ${scope.row.weight || '无权重'}`"
                            >
                              {{ (scope.row.factor && getAreaDeviceValue(areaNum, scope.row)?.value && parseFloat(getAreaDeviceValue(areaNum, scope.row)?.value) > 0) ? 
                                 calculateSkidCount(scope.row.factor, getAreaDeviceValue(areaNum, scope.row)?.value, scope.row.weight) : '0' }}
                            </el-tag>
                          </template>
                        </el-table-column>
                        
                        
                        
                        <!-- 空数据提示 -->
                        <template #empty>
                          <div class="no-data">暂无设备数据</div>
                        </template>
                      </el-table>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>

          <!-- 已移动到正常模式：全部数据监控表格 -->

        </el-card>
      </el-main>
      
      <!-- 8区域缩略图面板 -->
      <transition name="slide-thumbnail">
        <el-aside v-if="showThumbnailPanel" class="thumbnail-panel" style="flex: 1; width: 10%;">
          <el-card class="thumbnail-card-container" shadow="hover">
            <template #header>
              <div class="thumbnail-header">
                <div class="thumbnail-header-left">
                  <el-icon><Monitor /></el-icon>
                  <span>区域概览</span>
                </div>
                <div class="thumbnail-header-right">
                  <el-button 
                    type="primary" 
                    @click="toggleThumbnailPanel"
                    class="thumbnail-hide-btn"
                    title="隐藏缩略图面板"
                    size="small"
                    style="display: inline-flex !important; background: #409eff !important; color: white !important; border: 1px solid #409eff !important; z-index: 9999 !important; position: relative !important;"
                  >
                    <el-icon style="margin-right: 4px; color: white !important;"><ArrowRight /></el-icon>
                    隐藏
                  </el-button>
                </div>
              </div>
            </template>
          
            <div class="thumbnail-content">
              <!-- 8个区域缩略图 - 动态数据 -->
              <div 
                v-for="areaNum in [0, 1, 2, 3, 4, 5, 6, 7]" 
                :key="`thumbnail-area${areaNum}`"
                class="area-thumbnail-card"
                :class="`area-thumbnail-${areaNum}`"
                @click="scrollToArea(areaNum)"
                :title="`点击定位到Area${areaNum}区域`"
              >
                <div class="thumbnail-area-header">
                  <div class="thumbnail-area-badge">Area{{ areaNum }}</div>
                  <div class="thumbnail-device-count">{{ getAreaDevices(areaNum).length }}台设备</div>
                </div>
                <div class="thumbnail-stats">
                  <div class="thumbnail-stat-item purple-stat">
                    <span class="stat-label">Purple</span>
                    <span class="stat-value">{{ getAreaSkidStats(areaNum).purple }}</span>
                  </div>
                  <div class="thumbnail-stat-item normal-stat">
                    <span class="stat-label">常规</span>
                    <span class="stat-value">{{ getAreaSkidStats(areaNum).normal }}</span>
                  </div>
                </div>
              </div>
              
              <!-- 配置说明和区域示意图按钮 -->
              <div class="thumbnail-footer-buttons" style="display: flex; flex-direction: column; align-items: center; width: 100%; text-align: center;">
                <el-button
                  type="primary"
                  @click="showSkidConfigInfo"
                  class="thumbnail-footer-btn"
                  size="small"
                  title="点击查看详细配置信息"
                  style="width: 110px; margin: 0 auto; display: flex; align-items: center; justify-content: center;"
                >
                  <el-icon style="margin-right: 4px; font-size: 12px;"><DocumentAdd /></el-icon>
                  <span style="font-size: 12px;">配置说明</span>
                </el-button>
                <el-button
                  type="primary"
                  @click="showAreaDiagram"
                  class="thumbnail-footer-btn"
                  size="small"
                  style="width: 110px; margin: 0 auto; display: flex; align-items: center; justify-content: center;"
                >
                  <el-icon style="margin-right: 4px; font-size: 12px;"><Location /></el-icon>
                  <span style="font-size: 12px;">区域示意图</span>
                </el-button>
                <el-button
                  type="warning"
                  @click="showFactorSettings"
                  class="thumbnail-footer-btn"
                  size="small"
                  style="width: 110px; margin: 0 auto; display: flex; align-items: center; justify-content: center;"
                >
                  <el-icon style="margin-right: 4px; font-size: 12px;"><Setting /></el-icon>
                  <span style="font-size: 12px;">因子设置</span>
                </el-button>
              </div>
            </div>
          </el-card>
        </el-aside>
      </transition>
      
      <!-- 缩略图面板显示按钮（当面板隐藏时显示） -->
      <div v-if="!showThumbnailPanel" class="thumbnail-show-btn-container">
        <el-button 
          type="primary" 
          @click="toggleThumbnailPanel"
          class="thumbnail-show-btn"
          title="显示区域概览"
        >
          <el-icon><ArrowLeft /></el-icon>
          <span class="btn-text">区域概览</span>
        </el-button>
      </div>
    </el-container>
    
    <!-- 8区域示意图对话框 -->
    <el-dialog
      v-model="showAreaDiagramDialog"
      title="8区域实际布局示意图"
      :width="'90%'"
      :center="false"
      :close-on-click-modal="false"
      :destroy-on-close="true"
      draggable
    >
      <template #header>
        <div class="diagram-dialog-header">
          <el-icon><Location /></el-icon>
          <span>8区域实际布局示意图</span>
        </div>
      </template>
      
      <div class="area-diagram-container">     
        
        <!-- 示意图主体 -->
        <div class="diagram-content">
          <div class="diagram-layout">
            <div class="layout-diagram-container">
              <div class="background-image-container">
                <img 
                  src="@/assets/skid_layout.png" 
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

    <!-- 因子设置对话框 -->
    <el-dialog
      v-model="showFactorSettingsDialog"
      title="全局因子参数设置"
      width="500px"
      :center="true"
      :close-on-click-modal="false"
      :destroy-on-close="true"
      draggable
    >
      <template #header>
        <div class="factor-dialog-header">
          <el-icon><Setting /></el-icon>
          <span>全局因子参数设置</span>
        </div>
      </template>

      <div class="factor-settings-container">
        <el-form :model="factorSettings" label-width="120px" size="default">
          <el-form-item label="E5 因子" class="factor-form-item">
            <el-input-number
              v-model="factorSettings.e5"
              :min="1"
              :max="100"
              :precision="0"
              controls-position="right"
              style="width: 200px"
            />
            <div class="factor-description">
              用于计算E5系列设备的雪橇数量系数
            </div>
          </el-form-item>

          <el-form-item label="Norm 因子" class="factor-form-item">
            <el-input-number
              v-model="factorSettings.norm"
              :min="1"
              :max="100"
              :precision="0"
              controls-position="right"
              style="width: 200px"
            />
            <div class="factor-description">
              用于计算标准设备的雪橇数量系数
            </div>
          </el-form-item>
        </el-form>

        <div class="factor-preview">
          <h4>当前设置预览</h4>
          <div class="preview-item">
            <span>E5 因子: </span>
            <el-tag type="warning">{{ factorSettings.e5 }}</el-tag>
          </div>
          <div class="preview-item">
            <span>Norm 因子: </span>
            <el-tag type="primary">{{ factorSettings.norm }}</el-tag>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelFactorSettings">取消</el-button>
          <el-button type="primary" @click="saveFactorSettings">保存设置</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
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
  DocumentAdd,
  ArrowRight,
  ArrowLeft
} from '@element-plus/icons-vue'
import deviceConfig from '../config/deviceConfig.json'

// ==================== 全量统计计算器类 ====================

/**
 * 🚀 全量统计计算器 - 针对现场环境优化
 * 策略：防抖 + 缓存 + 一次遍历 + 智能更新
 * 修改时间：2025年9月17日14点05分
 * 修改内容：实现防抖+缓存+一次遍历的全量统计计算优化
 */
class OptimizedFullStatsCalculator {
  constructor() {
    // 📊 响应式统计结果
    this.stats = reactive({
      purple: 0,
      normal: 0, 
      total: 0,
      online: 0,
      areas: new Map() // 8区域统计
    })
    
    // 🚀 性能优化配置
    this.config = {
      debounceDelay: 500,        // 500ms防抖延迟
      cacheTimeout: 2000,        // 1秒缓存有效期
      batchUpdateThreshold: 5    // 3个设备变化后立即计算
    }
    
    // 🔄 计算控制状态
    this.calculationState = {
      isCalculating: false,      // 是否正在计算
      lastCalculation: 0,        // 上次计算时间
      pendingUpdates: new Set(), // 待更新设备列表
      debounceTimer: null        // 防抖定时器
    }
    
    // 📈 性能统计
    this.performanceStats = {
      totalCalculations: 0,
      totalTime: 0,
      avgTime: 0,
      lastCalculationTime: 0
    }
    
    // 初始化区域统计
    this.initializeAreaStats()
  }
  
  /**
   * 🎯 设备数据更新入口
   * 智能判断是否需要重新计算
   */
  onDeviceDataChange(deviceKey) {
    this.calculationState.pendingUpdates.add(deviceKey)
    
    // 🔥 批量更新策略：积累到一定数量立即计算
    if (this.calculationState.pendingUpdates.size >= this.config.batchUpdateThreshold) {
      console.log(`🚀 检测到批量设备更新(${this.calculationState.pendingUpdates.size}个)，立即执行全量计算`)
      this.triggerImmediateCalculation()
      return
    }
    
    // 🕐 防抖策略：延迟计算
    this.scheduleCalculation()
  }
  
  /**
   * ⏰ 调度计算（防抖机制）
   */
  scheduleCalculation() {
    // 清除现有定时器
    if (this.calculationState.debounceTimer) {
      clearTimeout(this.calculationState.debounceTimer)
    }
    
    // 设置防抖定时器
    this.calculationState.debounceTimer = setTimeout(() => {
      this.executeCalculation()
    }, this.config.debounceDelay)
    
    console.log(`⏰ 启动${this.config.debounceDelay}ms防抖定时器`)
  }
  
  /**
   * 🚀 立即触发计算
   */
  triggerImmediateCalculation() {
    if (this.calculationState.debounceTimer) {
      clearTimeout(this.calculationState.debounceTimer)
      this.calculationState.debounceTimer = null
    }
    this.executeCalculation()
  }
  
  /**
   * 💡 执行计算（核心优化算法）
   */
  async executeCalculation() {
    // 防止重复计算
    if (this.calculationState.isCalculating) {
      console.log('⚠️  计算进行中，跳过重复请求')
      return
    }
    
    // 检查缓存有效性
    const now = Date.now()
    if (now - this.calculationState.lastCalculation < this.config.cacheTimeout && 
        this.calculationState.pendingUpdates.size === 0) {
      console.log('📋 使用缓存结果，跳过计算')
      return this.stats
    }
    
    const startTime = performance.now()
    this.calculationState.isCalculating = true
    
    try {
      // 🔥 核心：一次遍历计算所有统计
      const results = this.calculateAllStatsInOnePass()
      
      // 更新响应式数据
      this.updateReactiveStats(results)
      
      // 清理状态
      this.calculationState.pendingUpdates.clear()
      this.calculationState.lastCalculation = now
      
      // 记录性能
      const endTime = performance.now()
      this.recordPerformance(endTime - startTime)
      
      console.log(`✅ 全量统计计算完成，耗时: ${(endTime - startTime).toFixed(2)}ms`)
      
      return this.stats
      
    } catch (error) {
      console.error('❌ 统计计算失败:', error)
      throw error
    } finally {
      this.calculationState.isCalculating = false
      this.calculationState.debounceTimer = null
    }
  }
  
  /**
   * 🎯 核心算法：一次遍历计算所有统计
   * 最大化性能，避免重复遍历
   */
  calculateAllStatsInOnePass() {
    console.log(`🔄 开始一次遍历全量计算 (${deviceData.value?.length || 0}个设备)...`)
    
    // 初始化结果对象
    const results = {
      purple: 0,
      normal: 0,
      total: 0,
      online: 0,
      areas: new Map()
    }
    
    // 初始化8个区域统计
    for (let areaNum = 0; areaNum <= 7; areaNum++) {
      results.areas.set(areaNum, {
        purple: 0,
        normal: 0,
        total: 0,
        online: 0,
        deviceCount: 0
      })
    }
    
    // 🚀 一次遍历计算所有统计
    deviceData.value?.forEach((device, index) => {
      if (!device || !deviceParams.value[index]) return
      
      const param = deviceParams.value[index]
      const area = param.area !== undefined ? param.area : 0
      const areaStats = results.areas.get(area)
      
      // 设备计数
      if (areaStats) {
        areaStats.deviceCount++
      }
      
      // 在线设备统计
      if (device.connectionStatus === 'online') {
        results.online++
        if (areaStats) {
          areaStats.online++
        }
      }
      
      // 雪橇数量统计
      if (device.hasData && device.value && param.factor) {
        const numValue = parseFloat(device.value)
        
        if (!isNaN(numValue) && numValue > 0) {
          // 🧮 使用现有的calculateSkidCount逻辑
          const skidCount = calculateSkidCount(param.factor, device.value, param.weight)
          
          if (skidCount > 0) {
            // 🔍 判断Purple/常规分类
            const isPurple = numValue > 5999
            
            // 全局统计累加
            if (isPurple) {
              results.purple += skidCount
            } else {
              results.normal += skidCount
            }
            results.total += skidCount
            
            // 区域统计累加
            if (areaStats) {
              if (isPurple) {
                areaStats.purple += skidCount
              } else {
                areaStats.normal += skidCount
              }
              areaStats.total += skidCount
            }
          }
        }
      }
    })
    
    // 📊 数值修正（避免浮点数精度问题）
    this.roundResults(results)
    
    return results
  }
  
  /**
   * 🔢 数值修正：避免JavaScript浮点数精度问题
   */
  roundResults(results) {
    results.purple = Math.round(results.purple)
    results.normal = Math.round(results.normal)
    results.total = Math.round(results.total)
    
    results.areas.forEach(areaStats => {
      areaStats.purple = Math.round(areaStats.purple)
      areaStats.normal = Math.round(areaStats.normal)
      areaStats.total = Math.round(areaStats.total)
    })
  }
  
  /**
   * 📡 更新响应式统计数据
   */
  updateReactiveStats(newResults) {
    // 更新全局统计
    this.stats.purple = newResults.purple
    this.stats.normal = newResults.normal
    this.stats.total = newResults.total
    this.stats.online = newResults.online
    
    // 更新区域统计
    newResults.areas.forEach((areaStats, areaNum) => {
      this.stats.areas.set(areaNum, { ...areaStats })
    })
  }
  
  /**
   * 📈 性能统计记录
   */
  recordPerformance(executionTime) {
    this.performanceStats.totalCalculations++
    this.performanceStats.totalTime += executionTime
    this.performanceStats.avgTime = this.performanceStats.totalTime / this.performanceStats.totalCalculations
    this.performanceStats.lastCalculationTime = executionTime
    
    // 性能警告
    if (executionTime > 50) {
      console.warn(`⚠️  计算耗时过长: ${executionTime.toFixed(2)}ms`)
    }
  }
  
  /**
   * 🏃‍♂️ 强制立即计算（用于特殊场景）
   */
  forceCalculation() {
    this.calculationState.lastCalculation = 0 // 重置缓存
    return this.executeCalculation()
  }
  
  /**
   * 📊 获取性能统计
   */
  getPerformanceStats() {
    return { ...this.performanceStats }
  }
  
  /**
   * 🔍 获取区域统计（对外接口）
   */
  getAreaStats(areaNumber) {
    return this.stats.areas.get(areaNumber) || {
      purple: 0, normal: 0, total: 0, online: 0, deviceCount: 0
    }
  }
  
  /**
   * 🎯 初始化区域统计
   */
  initializeAreaStats() {
    for (let i = 0; i <= 7; i++) {
      this.stats.areas.set(i, {
        purple: 0, normal: 0, total: 0, online: 0, deviceCount: 0
      })
    }
  }
}

// ==================== 响应式数据定义 ====================
const wsUrl = ref('localhost:8088/ws/emosweb') // 172.21.12.73/ws/emosweb
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
const showAreaDiagramDialog = ref(false) // 8区域示意图对话框显示状态
const showThumbnailPanel = ref(true) // 缩略图面板显示状态，默认显示
const showFactorSettingsDialog = ref(false) // 因子设置对话框显示状态

// 因子设置临时数据
const factorSettings = reactive({
  e5: deviceConfig.factor.e5,
  norm: deviceConfig.factor.norm
})

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

// 8区域数据分组
const areaGroupedData = ref({})

// ==================== 全量统计计算器实例 ====================
// 🚀 创建优化的统计计算器实例
const statsCalculator = new OptimizedFullStatsCalculator()

// 📊 统计数据绑定（替换原有的computed属性）
const purpleSkidCount = computed(() => statsCalculator.stats.purple)
const normalSkidCount = computed(() => statsCalculator.stats.normal)
const totalSkidCount = computed(() => statsCalculator.stats.total)

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
    const area = device.area !== undefined ? device.area : 1 // 默认为区域1，但允许area为0
    
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
 * 🚀 优化后的区域统计函数
 * 直接从统计计算器获取结果，避免重复计算
 * @param {number} areaNumber 区域编号(0-7)  
 * @returns {object} {purple: number, normal: number}
 */
const getAreaSkidStats = (areaNumber) => {
  return statsCalculator.getAreaStats(areaNumber)
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
        
        // 🚀 触发统计计算器更新（关键集成点）
        const deviceKey = `${extractedPlc}_${extractedTag}`
        statsCalculator.onDeviceDataChange(deviceKey)
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

// ==================== 原有computed属性已替换为统计计算器 ====================
// purpleSkidCount、normalSkidCount、totalSkidCount 现在通过 statsCalculator.stats 提供
// 详见上方的统计数据绑定部分

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
  
  // 优先级最高：当"weight"=2时，雪橇数量=1
  if (weightNum === 2) {
    return 1
  }
  
  // 优先级第二：当'数据值'<5999 且"weight"=1时，雪橇数量=1
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
 * 显示factor配置提示 - 页面加载时自动显示
 */
const showFactorConfigNotification = () => {
  ElMessageBox.alert(
    `配置文件中：<br>purple雪橇: ${e5factor.value}<br>普通雪橇: ${normfactor.value}<br><br>请从右下角因子设置按钮临时调整，页面刷新后失效`,

    '雪橇配置参数',
    {
      confirmButtonText: '确定',
      type: 'warning',
      dangerouslyUseHTMLString: true,
      customStyle: {
        width: '450px'
      }
    }
  )
}

/**
 * 显示8区域示意图
 */
const showAreaDiagram = () => {
  showAreaDiagramDialog.value = true
  ElMessage.success('8区域布局示意图已打开')
}

/**
 * 显示因子设置弹窗
 */
const showFactorSettings = () => {
  // 重置临时数据为当前值
  factorSettings.e5 = e5factor.value
  factorSettings.norm = normfactor.value
  showFactorSettingsDialog.value = true
  ElMessage.success('因子设置弹窗已打开')
}

/**
 * 保存因子设置
 */
const saveFactorSettings = () => {
  // 更新响应式变量
  e5factor.value = factorSettings.e5
  normfactor.value = factorSettings.norm

  // 更新deviceParams中所有设备的因子
  deviceParams.value.forEach(device => {
    if (device.factor && typeof device.factor === 'object') {
      device.factor.e5 = factorSettings.e5
      device.factor.norm = factorSettings.norm
    }
  })

  // 关闭弹窗
  showFactorSettingsDialog.value = false

  ElMessage.success('因子设置已保存并应用到所有设备')

  // 触发重新计算统计数据
  nextTick(() => {
    // 这里可以添加重新计算统计数据的逻辑
    console.log('因子已更新，新的计算因子:', {
      e5: e5factor.value,
      norm: normfactor.value
    })
  })
}

/**
 * 取消因子设置
 */
const cancelFactorSettings = () => {
  // 恢复临时数据为当前值
  factorSettings.e5 = e5factor.value
  factorSettings.norm = normfactor.value
  showFactorSettingsDialog.value = false
  ElMessage.info('已取消因子设置修改')
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
  
  // 🚀 触发统计重新计算
  statsCalculator.forceCalculation()
  
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
 * Ctrl+M: 切换控制面板的显示状态
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
  
  console.log(`🔄 UI切换完成:`)
  console.log(`  控制面板: ${prevPanel ? '显示' : '隐藏'} → ${showControlPanel.value ? '显示' : '隐藏'}`)
  
  ElMessage.info(`UI切换: ${showControlPanel.value ? '显示' : '隐藏'}详细面板`)
}

/**
 * 切换缩略图面板显示状态
 */
const toggleThumbnailPanel = () => {
  showThumbnailPanel.value = !showThumbnailPanel.value
  
  console.log(`🔄 缩略图面板切换: ${showThumbnailPanel.value ? '显示' : '隐藏'}`)
  ElMessage.info(`概览: ${showThumbnailPanel.value ? '显示' : '隐藏'}`)
}

/**
 * 🎯 缩略图点击定位功能 - 平滑滚动到对应区域
 * @param {number} areaNumber 区域编号(0-7)
 */
const scrollToArea = (areaNumber) => {
  console.log(`🎯 点击缩略图Area${areaNumber}，开始定位到对应区域`)
  
  // 智能模式检测和自动切换提示
  if (showControlPanel.value) {
    ElMessageBox.confirm(
      `当前处于详细面板模式，需要切换到区域监控模式才能查看Area${areaNumber}。\n是否立即切换？`,
      '切换到区域监控模式',
      {
        confirmButtonText: '立即切换',
        cancelButtonText: '取消',
        type: 'info',
        center: true
      }
    ).then(() => {
      // 用户确认切换模式
      toggleUIVisibility()
      
      // 等待界面切换完成后再定位
      nextTick(() => {
        setTimeout(() => {
          performAreaScroll(areaNumber)
        }, 300) // 等待切换动画完成
      })
    }).catch(() => {
      console.log('用户取消切换模式')
    })
    return
  }
  
  // 直接执行定位
  performAreaScroll(areaNumber)
}

/**
 * 🚀 执行区域定位滚动 - 核心滚动逻辑
 * @param {number} areaNumber 区域编号(0-7)
 */
const performAreaScroll = (areaNumber) => {
  try {
    // 查找目标区域元素
    const targetAreaSelector = `.area${areaNumber}`
    const targetElement = document.querySelector(targetAreaSelector)
    
    if (!targetElement) {
      console.warn(`⚠️ 未找到Area${areaNumber}对应的DOM元素`)
      ElMessage.warning(`未找到Area${areaNumber}区域，可能该区域暂无数据`)
      return
    }
    
    // 检查区域是否有设备数据
    const deviceCount = getAreaDevices(areaNumber).length
    if (deviceCount === 0) {
      ElMessage.info(`Area${areaNumber}区域暂无设备数据，已为您定位到该区域`)
    }
    
    // 添加临时高亮类，用于视觉反馈
    targetElement.classList.add('area-highlight-flash')
    
    // 查找滚动容器
    const scrollContainer = document.querySelector('.unified-scroll-container')
    
    if (scrollContainer) {
      // 计算目标元素在滚动容器中的位置
      const containerRect = scrollContainer.getBoundingClientRect()
      const targetRect = targetElement.getBoundingClientRect()
      
      // 智能计算滚动偏移量
      const scrollOffset = Math.min(80, containerRect.height * 0.1) // 动态偏移量，不超过容器高度的10%
      const scrollTop = targetRect.top - containerRect.top + scrollContainer.scrollTop - scrollOffset
      
      // 平滑滚动到目标位置
      scrollContainer.scrollTo({
        top: Math.max(0, scrollTop), // 确保不为负数
        behavior: 'smooth'
      })
      
      console.log(`✅ 成功定位到Area${areaNumber}，设备数量: ${deviceCount}，滚动偏移: ${scrollTop}px`)
      
      // 延迟显示成功消息，确保滚动开始后再提示
      setTimeout(() => {
        ElMessage.success(`📍 已定位到Area${areaNumber}区域 (${deviceCount}台设备)`)
      }, 100)
      
    } else {
      // 备用方案：使用原生scrollIntoView
      console.log('🔄 使用备用定位方案(scrollIntoView)')
      targetElement.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
        inline: 'nearest'
      })
      
      ElMessage.success(`📍 已定位到Area${areaNumber}区域 (${deviceCount}台设备)`)
    }
    
    // 2.5秒后移除高亮效果
    setTimeout(() => {
      if (targetElement.classList.contains('area-highlight-flash')) {
        targetElement.classList.remove('area-highlight-flash')
      }
    }, 2500)
    
    // 统计功能使用情况
    console.log(`📊 缩略图定位功能使用统计 - Area${areaNumber}, 设备数: ${deviceCount}, 时间: ${new Date().toLocaleTimeString()}`)
    
  } catch (error) {
    console.error(`❌ 定位Area${areaNumber}时发生错误:`, error)
    ElMessage.error(`定位失败，请检查页面状态后重试`)
  }
}

// 调试：检查按钮是否被正确挂载
onMounted(() => {
  nextTick(() => {
    const hideBtn = document.querySelector('.thumbnail-hide-btn')
    if (hideBtn) {
      console.log('✅ 隐藏按钮已找到:', hideBtn)
      console.log('按钮样式:', window.getComputedStyle(hideBtn))
    } else {
      console.log('❌ 隐藏按钮未找到')
    }
  })
})

// ==================== 生命周期钩子 ====================

onMounted(() => {
  console.log('WebSocket数据采集演示系统已加载')
  // 初始化设备数据表格
  initializeDeviceTable()

  // 初始化8区域数据分组
  groupDevicesByArea()

  // 🚀 初始化统计计算器（执行首次计算）
  console.log('🔄 初始化统计计算器...')
  statsCalculator.forceCalculation()

  // 添加全局快捷键监听
  document.addEventListener('keydown', handleKeydown)

  // 显示factor配置提示
  setTimeout(() => {
    showFactorConfigNotification()
  }, 500) // 延迟0.5秒后显示，确保页面完全加载

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
  height: 60px;
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

.header-button {
  background: rgba(255, 255, 255, 0.15) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: white !important;
  transition: all 0.3s ease;
  height: 32px !important;
  padding: 0 12px !important;
  font-size: 12px !important;
  font-weight: 500;
}

.header-button:hover {
  background: rgba(255, 255, 255, 0.25) !important;
  border-color: rgba(255, 255, 255, 0.5) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.header-button .el-icon {
  font-size: 14px;
  margin-right: 4px;
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
  padding: 5px;
  gap: 2px;
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
  height: calc(100vh - 75px); /* 优化卡片高度，充分利用空间 */
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}

.data-card .el-card__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 3px 8px 8px 8px; /* 优化底部内边距，减少空白 */
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
  transition: all 0.3s ease;
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

/* 新增表格容器包装器 - 使用flex布局 */
.table-wrapper {
  width: 100%;
  flex: 1; /* 占用剩余的flex空间 */
  min-height: 0; /* 重要：允许flex收缩 */
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  overflow: auto; /* 改为auto以显示滚动条 */
  background: white;
  position: relative; /* 添加定位以支持固定列 */
}

/* 表格字体增大2号 */
.larger-table-font {
  font-size: 16px !important; /* 基础字体从14px增大到16px */
  width: 100% !important;
  height: 100% !important;
}

.larger-table-font .el-table__header th {
  font-size: 18px !important; /* 表头字体增大 */
  font-weight: 600 !important;
  padding: 12px 6px !important; /* 优化表头内边距 */
  white-space: nowrap;
}

.larger-table-font .el-table__body td {
  font-size: 16px !important; /* 表格内容字体增大 */
  padding: 12px 6px !important; /* 优化表格单元格内边距 */
  white-space: nowrap;
}

.larger-table-font .el-tag {
  font-size: 14px !important; /* 适度调整标签字体 */
  padding: 0 8px !important;
  height: 28px !important;
  line-height: 28px !important;
}

.larger-table-font .el-table__row {
  height: 50px !important; /* 优化行高 */
}

/* 表格头部容器优化 */
.larger-table-font .el-table__header-wrapper {
  flex-shrink: 0; /* 防止表头被压缩 */
  overflow-x: hidden !important; /* 隐藏表头滚动，由容器控制 */
}

/* 确保表格在容器内正常滚动 */
.larger-table-font {
  width: 100% !important;
  height: 100% !important;
  min-width: 1450px; /* 确保最小宽度以显示所有列 */
  margin-bottom: 0; /* 移除底部边距避免重复 */
  border: none; /* 移除边框，由包装器处理 */
  display: flex; /* 使用flex布局 */
  flex-direction: column; /* 垂直排列 */
}

/* 表格内容区域优化 */
.larger-table-font .el-table__body-wrapper {
  flex: 1; /* 占用剩余空间 */
  overflow-y: auto !important;
  overflow-x: hidden !important; /* 隐藏body滚动，由容器控制 */
  min-height: 0; /* 允许收缩 */
}

/* 移除之前的复杂底部空间处理 */
.larger-table-font .el-table__body {
  padding-bottom: 20px !important; /* 简化底部空间 */
}

.larger-table-font .el-table__body table {
  margin-bottom: 0 !important; /* 移除底部边距 */
}

/* 移除虚拟空白行 */
.larger-table-font .el-table__body tbody::after {
  display: none;
}

/* 优化滚动条样式 - 主要由表格容器控制 */
.table-wrapper::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.table-wrapper::-webkit-scrollbar-track {
  background: #f5f7fa;
  border-radius: 6px;
}

.table-wrapper::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 6px;
  transition: background 0.3s;
}

.table-wrapper::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

.table-wrapper::-webkit-scrollbar-corner {
  background: #f5f7fa;
}

/* 确保表格本身的滚动条被禁用，统一由容器管理 */
.larger-table-font .el-table__body-wrapper::-webkit-scrollbar {
  width: 0px;
  height: 0px;
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
  table-layout: auto; /* 改为auto以支持水平滚动 */
  min-width: 1450px; /* 增加最小宽度确保所有列都能显示 */
}

/* 表格在包装容器内的宽度控制 */
.table-wrapper .el-table {
  width: 1450px; /* 设置固定宽度以确保水平滚动 */
  min-width: 1450px;
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
  
  /* 平板设备表格容器优化 - 使用flex布局 */
  /* .table-wrapper 样式已移至全局定义，无需平板专用样式 */
  
  .larger-table-font .el-table__header th {
    font-size: 16px !important;
    padding: 10px 4px !important;
  }
  
  .larger-table-font .el-table__body td {
    font-size: 14px !important;
    padding: 10px 4px !important;
  }
  
  .larger-table-font .el-tag {
    font-size: 12px !important;
    height: 24px !important;
    line-height: 24px !important;
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
  
  .header-button {
    height: 28px !important;
    padding: 0 10px !important;
    font-size: 11px !important;
  }
  
  .header-button .el-icon {
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
    transform: scale(0.6); /* 缩小图标 */
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
    padding: 6px 3px;
  }
  
  .data-display {
    margin-top: 120px; /* 为固定控制面板留出空间 */
  }
  
  /* 手机设备表格容器优化 - 使用flex布局 */
  .table-wrapper {
    border: none;
    border-radius: 6px;
  }
  
  /* 在较小的手机屏幕上隐藏图标并优化布局 */
  @media (max-width: 900px) {
    .dashboard-icon {
      display: none; /* 完全隐藏图标 */
    }
    
    .dashboard-content {
      text-align: center;
      align-items: center; /* 内容居中对齐 */
      padding: 0 4px; /* 减少内边距 */
    }
    
    .dashboard-card {
      height: 75px; /* 减小卡片高度 */
    }
    
    .dashboard-label {
      margin-bottom: 4px; /* 减少标签下方间距 */
    }
    
    .dashboard-value {
      margin: 2px 0; /* 减少数值上下间距 */
    }
    
    .dashboard-desc {
      margin-top: 2px; /* 减少描述上方间距 */
    }
  }
  
  .larger-table-font .el-table__header th {
    font-size: 12px !important;
    padding: 8px 2px !important;
  }
  
  .larger-table-font .el-table__body td {
    font-size: 11px !important;
    padding: 8px 2px !important;
  }
  
  .larger-table-font .el-tag {
    font-size: 10px !important;
    height: 20px !important;
    line-height: 20px !important;
    padding: 0 4px !important;
  }
  
  .larger-table-font .el-table__row {
    height: 40px !important;
  }
  
  /* 手机端表格最小宽度调整 */
  .el-table .el-table__body table,
  .el-table .el-table__header table {
    min-width: 1200px; /* 在手机端减少最小宽度 */
  }
  
  /* 手机端表格列宽度自适应优化 */
  .el-table .el-table__cell {
    padding: 6px 2px !important;
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
  
  .header-button {
    height: 24px !important;
    padding: 0 8px !important;
    font-size: 10px !important;
  }
  
  .header-button .el-icon {
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
  
  /* 小屏设备表格容器优化 - 使用flex布局 */
  .table-wrapper {
    border: none;
    border-radius: 4px;
  }
  
  .larger-table-font .el-table__header th {
    font-size: 10px !important;
    padding: 6px 1px !important;
  }
  
  .larger-table-font .el-table__body td {
    font-size: 9px !important;
    padding: 6px 1px !important;
  }
  
  .larger-table-font .el-tag {
    font-size: 8px !important;
    height: 18px !important;
    line-height: 18px !important;
    padding: 0 3px !important;
  }
  
  .larger-table-font .el-table__row {
    height: 35px !important;
  }
  
  /* 小屏设备表格最小宽度进一步调整 */
  .el-table .el-table__body table,
  .el-table .el-table__header table {
    min-width: 1000px; /* 在小屏设备上进一步减少最小宽度 */
  }
}


/* ==================== 统一滚动容器样式 ==================== */

.unified-scroll-container {
  max-height: calc(100vh - 200px); /* 大幅减少高度扣减，充分利用空间 */
  overflow-y: auto;
  margin: 10px 0; /* 减少外边距 */
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
  margin: 0 0 8px 0; /* 大幅减少底部边距 */
  padding: 0;
}


.areas-title {
  text-align: center;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 12px; /* 减少底部边距 */
  padding: 10px 0; /* 减少内边距 */
  border-bottom: 2px solid #409EFF;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 8区域网格布局 */
.areas-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  grid-template-rows: auto auto auto auto auto;
  gap: 4px;
  margin-bottom: 20px;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
}

/* 第一行：area0 居中 */
.area0 { 
  grid-column: 2; 
  grid-row: 1; 
  width: 100%;
  min-width: 0;
}

/* 第二行：area1, area2 */
.area1 { 
  grid-column: 1; 
  grid-row: 2; 
  width: 100%;
  min-width: 0;
}
.area2 { 
  grid-column: 2; 
  grid-row: 2; 
  width: 100%;
  min-width: 0;
}

/* 第三行：area3 居中 */
.area3 { 
  grid-column: 2; 
  grid-row: 3; 
  width: 100%;
  min-width: 0;
}

/* 第四行：area4, area5, area6 */
.area4 { 
  grid-column: 1; 
  grid-row: 4; 
  width: 100%;
  min-width: 0;
}
.area5 { 
  grid-column: 2; 
  grid-row: 4; 
  width: 100%;
  min-width: 0;
}
.area6 { 
  grid-column: 3; 
  grid-row: 4; 
  width: 100%;
  min-width: 0;
}

/* 第五行：area7 居中 */
.area7 { 
  grid-column: 2; 
  grid-row: 5; 
  width: 100%;
  min-width: 0;
}

.area-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 12px;
  height: auto;
  width: 100%;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  min-width: 0; /* 重要：允许flex收缩 */
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
  font-size: 13px;
  padding: 1px 6px;
  border-radius: 15px;
  transition: all 0.3s ease;
  min-width: 32px;
  text-align: center;
}

.area-stats .el-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(182, 158, 158, 0.15);
}

.area-table-container {
  flex: 1;
  width: 100%;
  min-width: 0; /* 重要：允许flex收缩 */
  overflow: hidden; /* 防止溢出 */
}


/* ==================== 正常模式表格容器样式 ==================== */

.normal-mode-table-container {
  flex: 1; /* 占用剩余的flex空间 */
  display: flex;
  flex-direction: column;
  margin: 10px 0 0 0; /* 减少边距 */
  min-height: 0; /* 重要：允许flex收缩 */
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.normal-mode-table-container .areas-title {
  margin: 0 0 8px 0; /* 减少底部边距 */
  padding: 12px 16px 0 16px; /* 减少内边距 */
  background: white;
  border-radius: 8px 8px 0 0;
  flex-shrink: 0; /* 防止标题被压缩 */
}

.normal-mode-table-container .el-table {
  margin: 0;
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

/* 统一容器样式优化（只包含7区域） */

.area-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.area-badge {
  background: #409EFF;
  color: white;
  padding: 3px 7px;
  border-radius: 4px;
  font-size: 11px;
  margin-right: 8px;
  font-weight: 600;
}

/* Element Plus 表格样式 - 使用深度选择器和具体选择器 */
.area-mini-table {
  font-size: 12px;
  border-radius: 6px;
  overflow: hidden;
}

/* 使用深度选择器覆盖Element Plus默认样式 */
.area-mini-table :deep(.el-table__header th.el-table__cell) {
  background: #f8f9fa;
  color: #495057;
  font-size: 11px;
  font-weight: 600;
  padding: 8px 6px;
}

.area-mini-table :deep(.el-table__body td.el-table__cell) {
  font-size: 11px;
  padding: 6px;
  color: #666;
}

.area-mini-table :deep(.el-table__row:hover) {
  background: #e8f4f8;
}

.area-mini-table :deep(.el-table__row--striped) {
  background: #f8f9fa;
}

.area-mini-table :deep(.el-table__row--striped:hover) {
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

/* 设备连接状态行样式 - 使用深度选择器和高优先级选择器 */
.area-mini-table :deep(.el-table__body .el-table__row.online) {
  background-color: #f0f9ff;
  border-left: 3px solid #10b981;
}

.area-mini-table :deep(.el-table__body .el-table__row.waiting) {
  background-color: #fffbeb;
  border-left: 3px solid #f59e0b;
}

.area-mini-table :deep(.el-table__body .el-table__row.offline) {
  background-color: #fef2f2;
  border-left: 3px solid #ef4444;
}

.area-mini-table :deep(.el-table__body .el-table__row.online:hover) {
  background-color: #dbeafe;
}

.area-mini-table :deep(.el-table__body .el-table__row.waiting:hover) {
  background-color: #fef3c7;
}

.area-mini-table :deep(.el-table__body .el-table__row.offline:hover) {
  background-color: #fecaca;
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

/* 8区域Element Plus表格整体优化 */
.area-mini-table {
  width: 100% !important;
  max-width: 100% !important;
  table-layout: auto !important;
  overflow: hidden;
}

.area-mini-table :deep(.el-table__cell) {
  text-align: center;
  vertical-align: middle;
  word-break: break-word;
  overflow-wrap: break-word;
  padding: 8px 4px !important;
}

/* 8区域表格自适应列宽优化 - 完全响应式设计 */
.area-mini-table :deep(.el-table) {
  width: 100% !important;
  max-width: 100% !important;
  table-layout: auto !important;
  border-collapse: separate;
  border-spacing: 0;
  overflow: hidden; /* 防止内容溢出 */
}

.area-mini-table :deep(.el-table__header),
.area-mini-table :deep(.el-table__body) {
  width: 100% !important;
}

/* 8区域表格列宽自适应分配 - 完全移除min-width限制 */
.area-mini-table :deep(.el-table colgroup col) {
  width: auto !important;
}

/* 8区域表格单元格响应式优化 */
.area-mini-table :deep(.el-table__cell) {
  padding: 6px 4px !important;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  word-break: keep-all; /* 防止不必要的换行 */
  transition: all 0.3s ease; /* 添加过渡动画 */
}

/* 确保弹性列能够均匀分配剩余空间 */
.area-mini-table :deep(.el-table__body-wrapper),
.area-mini-table :deep(.el-table__header-wrapper) {
  width: 100% !important;
  overflow-x: auto;
  overflow-y: auto;
}

/* 表格容器滚动优化 */
.area-mini-table :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  height: 6px;
}

.area-mini-table :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.area-mini-table :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.area-mini-table :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 区域特色样式 */
.area0 .area-badge { background: #6C5CE7; }
.area1 .area-badge { background: #FF6B6B; }
.area2 .area-badge { background: #4ECDC4; }
.area3 .area-badge { background: #45B7D1; }
.area4 .area-badge { background: #96CEB4; }
.area5 .area-badge { background: #FFEAA7; color: #333; }
.area6 .area-badge { background: #DDA0DD; }
.area7 .area-badge { background: #98D8C8; }

/* ==================== 缩略图点击定位高亮效果 ==================== */

/* 目标区域高亮闪烁动画 */
.area-highlight-flash {
  animation: area-flash-highlight 2s ease-in-out;
  position: relative;
  z-index: 10;
}

@keyframes area-flash-highlight {
  0% {
    box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.8);
    transform: scale(1);
    background-color: inherit;
  }
  15% {
    box-shadow: 0 0 0 5px rgba(139, 92, 246, 0.4), 0 0 20px 5px rgba(139, 92, 246, 0.3);
    transform: scale(1.02);
    background-color: rgba(139, 92, 246, 0.05);
  }
  30% {
    box-shadow: 0 0 0 8px rgba(139, 92, 246, 0.2), 0 0 30px 10px rgba(139, 92, 246, 0.2);
    transform: scale(1.01);
    background-color: rgba(139, 92, 246, 0.03);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(139, 92, 246, 0.1), 0 0 40px 15px rgba(139, 92, 246, 0.1);
    transform: scale(1);
    background-color: rgba(139, 92, 246, 0.02);
  }
  75% {
    box-shadow: 0 0 0 5px rgba(139, 92, 246, 0.05), 0 0 20px 8px rgba(139, 92, 246, 0.05);
    transform: scale(1);
    background-color: rgba(139, 92, 246, 0.01);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(139, 92, 246, 0);
    transform: scale(1);
    background-color: inherit;
  }
}

/* 缩略图卡片点击反馈动画 */
.area-thumbnail-card:active {
  transform: translateY(-1px) scale(0.98);
  transition: all 0.15s ease;
}

.area-thumbnail-card:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
  border-color: #8B5CF6;
  background: linear-gradient(135deg, #f8f9fa 0%, #f3f0ff 100%);
}

/* 缩略图点击定位功能响应式优化 */
@media (max-width: 768px) {
  /* 移动端高亮动画适配 */
  .area-highlight-flash {
    animation: area-flash-highlight-mobile 1.5s ease-in-out;
  }
  
  @keyframes area-flash-highlight-mobile {
    0% {
      box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.8);
      transform: scale(1);
      background-color: inherit;
    }
    20% {
      box-shadow: 0 0 0 5px rgba(139, 92, 246, 0.5), 0 0 15px 3px rgba(139, 92, 246, 0.4);
      transform: scale(1.01);
      background-color: rgba(139, 92, 246, 0.08);
    }
    40% {
      box-shadow: 0 0 0 8px rgba(139, 92, 246, 0.3), 0 0 20px 5px rgba(139, 92, 246, 0.25);
      transform: scale(1.005);
      background-color: rgba(139, 92, 246, 0.05);
    }
    60% {
      box-shadow: 0 0 0 6px rgba(139, 92, 246, 0.2), 0 0 15px 4px rgba(139, 92, 246, 0.15);
      transform: scale(1);
      background-color: rgba(139, 92, 246, 0.03);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(139, 92, 246, 0);
      transform: scale(1);
      background-color: inherit;
    }
  }
  
  /* 移动端缩略图点击区域适配 */
  .area-thumbnail-card {
    min-height: 70px;
    padding: 12px;
    cursor: pointer;
    -webkit-tap-highlight-color: rgba(139, 92, 246, 0.1);
  }
  
  .area-thumbnail-card:active {
    transform: translateY(0) scale(0.96);
    background-color: rgba(139, 92, 246, 0.1);
  }
}

@media (max-width: 480px) {
  /* 小屏幕设备高亮效果进一步优化 */
  @keyframes area-flash-highlight-mobile {
    0% {
      box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.8);
      background-color: inherit;
    }
    25% {
      box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.6), 0 0 10px 2px rgba(139, 92, 246, 0.5);
      background-color: rgba(139, 92, 246, 0.1);
    }
    50% {
      box-shadow: 0 0 0 5px rgba(139, 92, 246, 0.4), 0 0 15px 3px rgba(139, 92, 246, 0.3);
      background-color: rgba(139, 92, 246, 0.06);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(139, 92, 246, 0);
      background-color: inherit;
    }
  }
  
  .area-thumbnail-card {
    min-height: 65px;
    padding: 10px;
  }
}

/* 8区域响应式设计 - 进一步缩小断点，确保更多设备保持area4、5、6同行 */
@media (max-width: 900px) {
  .areas-grid {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto auto auto auto auto;
  }
  
  /* 平板布局：2列排列 */
  .area0 { grid-column: 1 / 3; grid-row: 1; max-width: 50%; margin: 0 auto; }
  .area1 { grid-column: 1; grid-row: 2; }
  .area2 { grid-column: 2; grid-row: 2; }
  .area3 { grid-column: 1; grid-row: 3; }
  .area4 { grid-column: 2; grid-row: 3; }
  .area5 { grid-column: 1; grid-row: 4; }
  .area6 { grid-column: 2; grid-row: 4; }
  .area7 { grid-column: 1 / 3; grid-row: 5; max-width: 50%; margin: 0 auto; }
}

@media (max-width: 768px) {
  .areas-grid {
    grid-template-columns: 1fr;
  }
  
  .area0, .area1, .area2, .area3, .area4, .area5, .area6, .area7 {
    grid-column: 1;
  }
  
  .area0 { grid-row: 1; }
  .area1 { grid-row: 2; }
  .area2 { grid-row: 3; }
  .area3 { grid-row: 4; }
  .area4 { grid-row: 5; }
  .area5 { grid-row: 6; }
  .area6 { grid-row: 7; }
  .area7 { grid-row: 8; }
}

@media (max-width: 768px) {
  .unified-scroll-container {
    max-height: calc(100vh - 160px); /* 手机设备进一步减少空白 */
    padding: 6px;
    margin: 8px 0; /* 减少外边距 */
  }
  
  .areas-grid-layout {
    padding: 0 4px;
  }
  
  .areas-grid {
    gap: 4px;
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
    font-size: 11px;
    padding: 2px 8px;
    min-width: 30px;
  }
  
  .area-mini-table {
    font-size: 10px;
  }
  
  .area-mini-table :deep(.el-table__header th.el-table__cell),
  .area-mini-table :deep(.el-table__body td.el-table__cell) {
    padding: 3px 2px;
    font-size: 10px;
  }
  
  /* 8区域表格移动端自适应布局优化 - 4列弹性布局 */
  .area-mini-table {
    table-layout: auto !important;
  }
  
  
  /* 移动端表格优化：确保表格宽度充分利用容器空间 */
  .area-mini-table :deep(.el-table) {
    width: 100% !important;
  }
  
  /* 移动端列宽自适应分配 */
  .area-mini-table :deep(.el-table__header th),
  .area-mini-table :deep(.el-table__body td) { 
    padding: 6px 3px !important;
    font-size: 10px !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  /* 移动端列宽比例分配 - 取消min-width限制，实现完全响应式 */
  .area-mini-table :deep(.el-table__header th:nth-child(1)),
  .area-mini-table :deep(.el-table__body td:nth-child(1)) { 
    width: 20% !important; 
  }  /* PLC设备 */
  
  .area-mini-table :deep(.el-table__header th:nth-child(2)), 
  .area-mini-table :deep(.el-table__body td:nth-child(2)) { 
    width: 30% !important;
  }  /* 滚床编号 */
  
  .area-mini-table :deep(.el-table__header th:nth-child(3)),
  .area-mini-table :deep(.el-table__body td:nth-child(3)) { 
    width: 30% !important;
  }  /* 数据值 */
  
  .area-mini-table :deep(.el-table__header th:nth-child(4)),
  .area-mini-table :deep(.el-table__body td:nth-child(4)) { 
    width: 20% !important; 
  }  /* 雪橇数量 */
  
  .data-value-cell .el-tag,
  .skid-count-cell .el-tag,
  .update-time-cell .el-tag {
    font-size: 8px;
    padding: 1px 4px;
  }
  
  .status-indicator {
    font-size: 8px;
    padding: 1px 4px;
    min-width: 24px;
  }
}

/* ==================== 窗口过小时隐藏PLC设备列 ==================== */

/* 当窗口宽度 ≤ 600px 时隐藏PLC设备列，重新分配剩余3列宽度 */
@media (max-width: 900px) {
  /* 隐藏PLC设备列（第1列） */
  .area-mini-table :deep(.el-table__header th:nth-child(1)),
  .area-mini-table :deep(.el-table__body td:nth-child(1)) {
    display: none !important;
  }
  
  /* 重新分配剩余3列宽度：滚床编号(35%) + 数据值(35%) + 雪橇数量(30%) */
  .area-mini-table :deep(.el-table__header th:nth-child(2)), 
  .area-mini-table :deep(.el-table__body td:nth-child(2)) { 
    width: 35% !important;
  }  /* 滚床编号 */
  
  .area-mini-table :deep(.el-table__header th:nth-child(3)),
  .area-mini-table :deep(.el-table__body td:nth-child(3)) { 
    width: 35% !important;
  }  /* 数据值 */
  
  .area-mini-table :deep(.el-table__header th:nth-child(4)),
  .area-mini-table :deep(.el-table__body td:nth-child(4)) { 
    width: 30% !important; 
  }  /* 雪橇数量 */
  
  /* 优化表格在小屏幕下的显示效果 */
  .area-mini-table :deep(.el-table__cell) {
    padding: 4px 2px !important;
    font-size: 10px !important;
  }
  
  .area-mini-table :deep(.el-tag) {
    font-size: 9px !important;
    padding: 1px 3px !important;
  }
}

@media (max-width: 480px) {
  .unified-scroll-container {
    max-height: calc(100vh - 120px); /* 小屏设备最大化空间利用 */
    padding: 4px;
    margin: 6px 0; /* 减少外边距 */
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
  
  .area-mini-table {
    font-size: 10px;
  }
  
  .area-mini-table :deep(.el-table__header th.el-table__cell),
  .area-mini-table :deep(.el-table__body td.el-table__cell) {
    padding: 3px;
    font-size: 10px;
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

/* ==================== 8区域缩略图面板样式 ==================== */

.thumbnail-panel {
  background: transparent;
  padding: 0px 5px 5px 0px;
  transition: all 0.3s ease;
  min-width: 100px; /* 最小宽度保证内容正常显示 */
  max-width: 200px; /* 最大宽度限制，避免在大屏幕上过宽 */
}

.thumbnail-card-container {
  /* height: calc(100vh - 75px); */
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
  border-radius: 2px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  background: white;
}

.thumbnail-card-container .el-card__header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px 10px 0 0;
  color: white;
  font-weight: 600;
  padding: 12px 16px;
  border-bottom: none;
}

.thumbnail-card-container .el-card__body {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  min-height: 0;
}

.thumbnail-header {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  width: 100% !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  color: white !important;
  position: relative !important;
  z-index: 1 !important;
}

.thumbnail-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.thumbnail-header-left .el-icon {
  font-size: 18px;
}

.thumbnail-header-right {
  display: flex !important;
  align-items: center !important;
  flex-shrink: 0 !important;
  position: relative !important;
  z-index: 100 !important;
}

.thumbnail-hide-btn {
  color: white !important;
  padding: 8px 12px !important;
  min-height: 32px !important;
  border-radius: 6px !important;
  transition: all 0.3s ease !important;
  background: rgba(255, 255, 255, 0.15) !important;
  border: 2px solid rgba(255, 255, 255, 0.3) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  opacity: 1 !important;
  visibility: visible !important;
  position: relative !important;
  z-index: 10 !important;
}

.thumbnail-hide-btn:hover {
  background: rgba(255, 255, 255, 0.25) !important;
  color: white !important;
  border-color: rgba(255, 255, 255, 0.4) !important;
  transform: scale(1.05) !important;
}

.thumbnail-hide-btn .el-icon {
  font-size: 18px !important;
  margin: 0 !important;
  color: white !important;
  display: block !important;
}

/* 确保按钮在Element Plus卡片头部中可见 - 使用最高优先级 */
.thumbnail-panel .thumbnail-card-container .el-card__header .thumbnail-header .thumbnail-header-right .thumbnail-hide-btn {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  background: #409eff !important;
  color: white !important;
  border: 1px solid #409eff !important;
  border-radius: 4px !important;
  padding: 5px 11px !important;
  font-size: 12px !important;
  line-height: 1 !important;
  height: auto !important;
  min-height: 28px !important;
  opacity: 1 !important;
  visibility: visible !important;
  position: relative !important;
  z-index: 1000 !important;
  cursor: pointer !important;
  margin: 0 !important;
  white-space: nowrap !important;
  text-align: center !important;
  box-sizing: border-box !important;
  outline: none !important;
  transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1) !important;
}

.thumbnail-panel .thumbnail-card-container .el-card__header .thumbnail-header .thumbnail-header-right .thumbnail-hide-btn:hover {
  background: #66b1ff !important;
  border-color: #66b1ff !important;
  color: white !important;
}

.thumbnail-panel .thumbnail-card-container .el-card__header .thumbnail-header .thumbnail-header-right .thumbnail-hide-btn .el-icon {
  font-size: 12px !important;
  margin-right: 4px !important;
  color: white !important;
  vertical-align: middle !important;
}

.thumbnail-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  max-height: calc(100vh - 200px); /* 充分利用空间，为头部、底部按钮、边距预留最小必要空间 */
  overflow-y: auto; /* 启用垂直滚动条 */
  overflow-x: hidden; /* 禁用水平滚动条 */
  padding-right: 4px; /* 为滚动条预留空间 */
}

/* 缩略图底部按钮容器 */
.thumbnail-footer-buttons {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e4e7ed;
  text-align: center;
  width: 100%;
}

/* 按钮包装器 */
.button-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

/* 缩略图底部按钮样式 */
.thumbnail-footer-btn {
  width: 120px !important;
  height: 32px !important;
  font-size: 12px !important;
  padding: 6px 12px !important;
  border-radius: 6px !important;
  transition: all 0.3s ease !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center !important;
  margin: 0 auto !important;
}

.thumbnail-footer-btn .el-icon {
  margin-right: 4px !important;
  font-size: 12px !important;
  display: inline-flex !important;
  align-items: center !important;
}

.thumbnail-footer-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

/* 缩略图卡片样式 */
.area-thumbnail-card {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 10px;
  transition: all 0.3s ease;
  cursor: pointer;
  min-height: 65px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.area-thumbnail-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  border-color: #409eff;
  background: #f8f9fa;
}

.thumbnail-area-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.thumbnail-area-badge {
  background: #409EFF;
  color: white;
  padding: 3px 6px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  min-width: 40px;
  text-align: center;
}

.thumbnail-device-count {
  font-size: 10px;
  color: #64748b;
  font-weight: 500;
}

.thumbnail-stats {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: space-between;
}

.thumbnail-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px 6px;
  border-radius: 8px;
  min-width: 35px;
  transition: all 0.3s ease;
}

.thumbnail-stat-item .stat-label {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  margin-bottom: 1px;
}

.thumbnail-stat-item .stat-value {
  font-size: 12px;
  font-weight: bold;
  color: white;
}

.purple-stat {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  box-shadow: 0 2px 6px rgba(245, 158, 11, 0.3);
}

.purple-stat:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
}

.normal-stat {
  background: linear-gradient(135deg, #3B82F6, #2563EB);
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);
}

.normal-stat:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

/* 不同区域的特色颜色 */
.area-thumbnail-0 .thumbnail-area-badge { background: #6C5CE7; }
.area-thumbnail-1 .thumbnail-area-badge { background: #FF6B6B; }
.area-thumbnail-2 .thumbnail-area-badge { background: #4ECDC4; }
.area-thumbnail-3 .thumbnail-area-badge { background: #45B7D1; }
.area-thumbnail-4 .thumbnail-area-badge { background: #96CEB4; }
.area-thumbnail-5 .thumbnail-area-badge { background: #FFEAA7; color: #333; }
.area-thumbnail-6 .thumbnail-area-badge { background: #DDA0DD; }
.area-thumbnail-7 .thumbnail-area-badge { background: #98D8C8; }

/* 缩略图面板滚动条样式 */
.thumbnail-card-container .el-card__body::-webkit-scrollbar {
  width: 6px;
}

.thumbnail-card-container .el-card__body::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.thumbnail-card-container .el-card__body::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
  transition: background 0.3s;
}

.thumbnail-card-container .el-card__body::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 缩略图内容区域滚动条样式 */
.thumbnail-content::-webkit-scrollbar {
  width: 8px;
}

.thumbnail-content::-webkit-scrollbar-track {
  background: #f5f7fa;
  border-radius: 4px;
  margin: 2px;
}

.thumbnail-content::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #409eff 0%, #6c5ce7 100%);
  border-radius: 4px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.2);
}

.thumbnail-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #66b1ff 0%, #8a7cff 100%);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.4);
}

/* 缩略图面板响应式设计 */
@media (max-width: 1400px) {
  .thumbnail-panel {
    min-width: 150px !important;
    max-width: 180px !important;
  }
  
  .area-thumbnail-card {
    padding: 8px;
    min-height: 60px;
  }
  
  .thumbnail-area-badge {
    font-size: 10px;
    padding: 2px 5px;
    min-width: 35px;
  }
  
  .thumbnail-device-count {
    font-size: 9px;
  }
  
  .thumbnail-stat-item {
    padding: 3px 5px;
    min-width: 30px;
  }
  
  .thumbnail-stat-item .stat-value {
    font-size: 11px;
  }
  
  .thumbnail-stat-item .stat-label {
    font-size: 8px;
  }
}

/* 【已取消】屏幕尺寸自动隐藏功能 - 缩略图面板在所有屏幕尺寸下都保持可见 */
/* 原来的@media (max-width: 1200px)和@media (max-width: 768px)自动隐藏规则已被移除 */
/* 现在缩略图面板只能通过手动点击隐藏按钮来控制显示/隐藏状态 */

/*
已注释的原始规则：
@media (max-width: 1200px) {
  .thumbnail-panel {
    display: none;
  }
}

@media (max-width: 768px) {
  .thumbnail-panel {
    display: none !important;
  }
}
*/

/* ==================== 缩略图面板切换动画和显示按钮样式 ==================== */

/* 缩略图面板滑动动画 - 减少过渡时间一半 */
.slide-thumbnail-enter-active,
.slide-thumbnail-leave-active {
  transition: all  ease;
}

.slide-thumbnail-enter-from,
.slide-thumbnail-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

/* 缩略图显示按钮容器 */
.thumbnail-show-btn-container {
  position: fixed;
  top: 50%;
  right: 10px;
  transform: translateY(-50%);
  z-index: 1000;
  transition: all 0.3s ease;
}

/* 缩略图显示按钮样式 */
.thumbnail-show-btn {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  padding: 12px 8px !important;
  min-height: 80px !important;
  border-radius: 8px 0 0 8px !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  color: white !important;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.15) !important;
  transition: all 0.3s ease !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 4px !important;
}

.thumbnail-show-btn:hover {
  background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
  transform: translateX(-3px);
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.2) !important;
}

.thumbnail-show-btn .el-icon {
  font-size: 16px;
  margin-bottom: 4px;
}

.thumbnail-show-btn .btn-text {
  font-size: 12px;
  font-weight: 500;
  writing-mode: vertical-rl;
  text-orientation: upright;
  letter-spacing: 2px;
}

/* 显示按钮在所有屏幕尺寸下都保持可见 */

/* 因子设置弹窗样式 */
.factor-dialog-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
  font-weight: bold;
}

.factor-settings-container {
  padding: 20px 0;
}

.factor-form-item {
  margin-bottom: 24px;
}

.factor-description {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
  line-height: 1.4;
}

.factor-preview {
  margin-top: 24px;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.factor-preview h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
  font-weight: 600;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.preview-item:last-child {
  margin-bottom: 0;
}

.preview-item span {
  font-size: 13px;
  color: #606266;
  min-width: 80px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .factor-settings-container {
    padding: 16px 0;
  }

  .factor-form-item {
    margin-bottom: 20px;
  }

  .factor-preview {
    margin-top: 20px;
    padding: 12px;
  }

  .preview-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .preview-item span {
    min-width: auto;
  }
}

</style>
