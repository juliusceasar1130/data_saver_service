/**
 * 修改时间：2025年9月1日14点05分
 * 修改内容：创建Vue3应用主入口文件，配置Element Plus
 */
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './home/App.vue'
import './style.css'

// 创建Vue应用实例
const app = createApp(App)

// 配置Element Plus组件库
app.use(ElementPlus, {
  locale: zhCn, // 设置中文语言包
})

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 挂载应用到DOM
app.mount('#app')
