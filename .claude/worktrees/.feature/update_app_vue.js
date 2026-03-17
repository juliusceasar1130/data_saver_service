// 修改时间：2025年9月1日14点05分
// 修改内容：更新App.vue中的deviceParams数组

const fs = require('fs');

try {
  // 读取App.vue文件
  const appVueContent = fs.readFileSync('src/App.vue', 'utf8');
  
  // 读取提取的设备参数
  const deviceParamsContent = fs.readFileSync('vue_device_params.txt', 'utf8');
  
  // 构建新的deviceParams数组字符串
  const newDeviceParams = `// 设备参数配置 - 根据测试需求配置的设备点位
const deviceParams = ref([
${deviceParamsContent}
])`;

  // 找到原来的deviceParams数组位置并替换
  const deviceParamsPattern = /\/\/ 设备参数配置[\s\S]*?const deviceParams = ref\(\[[\s\S]*?\]\)/;
  
  const updatedContent = appVueContent.replace(deviceParamsPattern, newDeviceParams);
  
  // 检查是否成功替换
  if (updatedContent === appVueContent) {
    console.log('未找到deviceParams数组，尝试其他匹配方式...');
    
    // 尝试更简单的匹配方式
    const simplePattern = /const deviceParams = ref\(\[[\s\S]*?\]\)/;
    const updatedContent2 = appVueContent.replace(simplePattern, `const deviceParams = ref([
${deviceParamsContent}
])`);
    
    if (updatedContent2 !== appVueContent) {
      fs.writeFileSync('src/App.vue', updatedContent2);
      console.log('✅ 成功更新App.vue中的deviceParams数组');
      console.log('更新后的数组包含了2146个完整的工业设备点位');
    } else {
      console.log('❌ 无法找到deviceParams数组进行替换');
    }
  } else {
    // 写入更新后的文件
    fs.writeFileSync('src/App.vue', updatedContent);
    console.log('✅ 成功更新App.vue中的deviceParams数组');
    console.log('更新后的数组包含了2146个完整的工业设备点位');
  }
  
} catch (error) {
  console.error('更新过程中出现错误:', error.message);
}
