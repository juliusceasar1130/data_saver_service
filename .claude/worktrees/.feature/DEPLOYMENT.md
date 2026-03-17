# 部署配置说明

**修改时间：2025年9月1日14点05分**  
**修改内容：创建部署配置说明文档**

## 环境配置

### 可配置参数

项目中的主要配置参数都在 `src/App.vue` 中定义，您可以根据实际需要修改：

#### WebSocket连接配置
```javascript
// 默认WebSocket服务器地址
const wsUrl = ref('172.21.12.73/ws/emosweb')

// 心跳间隔（毫秒）
const heartbeatInterval = 2000

// 数据表格最大记录数
const maxDataRecords = 100
```

#### 设备点位配置
```javascript
// 在 deviceParams 数组中配置需要监控的设备点位
const deviceParams = ref([
  {"id":"21","type":"advise","plc":"L3FKT1","tag":".L3FKT1_1C_18AS_1C045RO_1C045ROFG1.ST[1].IL.SD.M1003_BodyID"},
  // ... 更多设备点位
])
```

### 快速启动

#### Windows系统
双击运行 `start.bat` 文件，或在命令行中执行：
```bash
start.bat
```

#### Linux/Mac系统
在终端中执行：
```bash
chmod +x start.sh
./start.sh
```

#### 手动启动
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 访问地址

项目启动后，可通过以下地址访问：
- 本地访问：http://localhost:3000
- 局域网访问：http://[您的IP地址]:3000

### 生产环境部署

#### 构建项目
```bash
npm run build
```

#### 部署文件
构建完成后，`dist` 目录中的文件可以部署到任何静态文件服务器，如：
- Nginx
- Apache
- 云服务（阿里云OSS、腾讯云COS等）

#### Nginx配置示例
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/your/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # WebSocket代理（如果需要）
    location /ws {
        proxy_pass http://your-websocket-server;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 常见问题

#### WebSocket连接失败
1. 检查服务器地址是否正确
2. 确认WebSocket服务器是否启动
3. 检查防火墙设置
4. 确认网络连接

#### 页面无法访问
1. 检查端口是否被占用
2. 确认防火墙允许3000端口
3. 尝试使用其他端口：`npm run dev -- --port 3001`

#### 依赖安装失败
1. 检查Node.js版本（建议16+）
2. 尝试使用国内镜像：`npm config set registry https://registry.npmmirror.com`
3. 清除缓存：`npm cache clean --force`

### 自定义配置

#### 修改默认端口
在 `vite.config.js` 中修改：
```javascript
export default defineConfig({
  server: {
    port: 8080, // 修改为您想要的端口
  }
})
```

#### 修改WebSocket地址
在 `src/App.vue` 中找到 `wsUrl` 并修改：
```javascript
const wsUrl = ref('your-websocket-server-address/ws/endpoint')
```

#### 添加新的设备点位
在 `src/App.vue` 的 `deviceParams` 数组中添加：
```javascript
deviceParams.value.push({
  "id": "新的ID",
  "type": "advise",
  "plc": "PLC设备名",
  "tag": "设备标签路径"
})
```

### 监控和日志

#### 浏览器控制台
项目包含详细的控制台日志，可通过浏览器开发者工具查看：
- F12 打开开发者工具
- 切换到 Console 标签页
- 查看连接状态、数据接收等日志

#### 生产环境监控
建议在生产环境中：
1. 关闭调试日志
2. 添加错误监控（如Sentry）
3. 配置性能监控
4. 设置告警机制

### 安全考虑

#### WebSocket连接安全
- 生产环境建议使用WSS（加密连接）
- 实现身份验证机制
- 限制连接频率和数据量

#### 网络安全
- 配置HTTPS
- 设置CORS策略
- 使用防火墙规则

### 技术支持

如遇到问题，请：
1. 查看浏览器控制台错误信息
2. 检查网络连接状态
3. 确认服务器端配置
4. 联系技术支持团队
