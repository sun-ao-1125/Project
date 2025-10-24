# 高德地图MCP客户端调用示例

这是一个演示如何通过程序调用高德地图API的示例项目。

## 功能特性

本项目实现了以下高德地图API功能:

1. **IP定位** - 根据IP地址自动获取当前位置
2. **天气查询** - 查询实时天气和天气预报
3. **地理编码** - 将地址转换为经纬度坐标
4. **逆地理编码** - 将经纬度坐标转换为地址
5. **POI搜索** - 搜索兴趣点(餐厅、商店等)
6. **距离测量** - 计算两点间的距离
7. **🤖 AI路线规划** - 使用DeepSeek AI模型理解自然语言输入,智能规划路线

## 快速开始

### 1. 获取高德地图API Key

1. 访问 [高德开放平台](https://lbs.amap.com/)
2. 注册/登录账号
3. 进入控制台创建应用
4. 选择"Web服务API"类型
5. 获取API Key

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件,填入你的API Key
# AMAP_API_KEY=your_amap_api_key_here
```

### 3. 安装依赖

```bash
npm install
```

### 4. 运行示例

```bash
# 运行基础功能示例
npm start

# 运行AI智能路线规划
npm run navigate  # 输入自然语言指令,如: "从北京到上海的路线"
```

## 项目结构

```
.
├── src/
│   ├── amapClient.js    # 高德地图API客户端封装
│   ├── aiService.js     # DeepSeek AI服务封装
│   ├── index.js         # 基础功能示例代码
│   └── aiRouteDemo.js   # AI智能路线规划示例
├── .env.example         # 环境变量模板
├── .gitignore
├── package.json
└── README.md
```

## API使用示例

### IP定位

```javascript
import AmapClient from './amapClient.js';

const client = new AmapClient('your_api_key');

// 自动获取当前位置
const result = await client.getLocationByIp();
console.log(result.city); // "北京市"
console.log(result.adcode); // "110000"
```

### 天气查询

```javascript
// 查询实时天气
const weather = await client.getWeather('北京', 'base');
console.log(weather.weather); // "晴"
console.log(weather.temperature); // "25"

// 查询天气预报
const forecast = await client.getWeather('北京', 'all');
console.log(forecast.casts); // 未来3-4天的天气预报
```

### 地理编码

```javascript
// 地址转坐标
const result = await client.geocode('北京市朝阳区阜通东大街6号', '北京');
console.log(result.location); // "116.481488,39.990464"
```

### 逆地理编码

```javascript
// 坐标转地址
const result = await client.regeocode('116.481488,39.990464');
console.log(result.formatted_address);
```

### POI搜索

```javascript
// 搜索咖啡厅
const result = await client.searchPoi('咖啡厅', '北京', 10);
console.log(result.pois);
```

### 距离测量

```javascript
// 计算两点间距离
const result = await client.distance(
  '116.481488,39.990464',  // 起点
  '121.472644,31.231706',  // 终点
  1  // 1=直线距离, 3=驾车距离
);
console.log(result.distance); // 单位:米
```

### 路线规划

```javascript
// 驾车路线规划
const result = await client.drivingRoute(
  '116.481488,39.990464',  // 起点坐标
  '121.472644,31.231706',  // 终点坐标
  '4'  // 策略: 0-速度优先, 1-费用优先, 2-距离优先, 3-不走高速, 4-躲避拥堵
);
console.log(result.distance); // 总距离(米)
console.log(result.duration); // 预计时间(秒)
console.log(result.tolls); // 通行费(元)
console.log(result.steps); // 详细导航步骤
```

# 🤖 AI智能路线规划系统

基于高德地图API与DeepSeek大模型，实现自然语言驱动的智能出行解决方案。

## 核心功能

### 🗺️ 智能路线规划
- **自然语言理解**：使用<mcsymbol name="AIService.parseLocationInput" filename="aiService.js" path="src/aiService.js" startline="10" type="function"></mcsymbol>解析用户输入
- **自动定位**：集成<mcsymbol name="AmapClient.getCurrentLocation" filename="amapClient.js" path="src/amapClient.js" startline="346" type="function"></mcsymbol>实现IP定位
- **多策略导航**：支持躲避拥堵/最短路径等驾驶策略

### 🚀 主要特性
1. **智能地址解析**
   - 自动补全省市信息（"西湖" → "杭州西湖风景名胜区"）
   - 支持模糊查询（"那个陆家嘴的高楼" → "上海东方明珠"）
   
2. **全流程自动化**
   ```mermaid
   graph TD
   A[自然语言输入] --> B(AI解析地址)
   B --> C(地理编码)
   C --> D(路线规划)
   D --> E(AI摘要生成)
   E --> F(自动打开地图)
   ```

### 配置DeepSeek API Key

1. 访问 [DeepSeek开放平台](https://platform.deepseek.com/)
2. 注册/登录账号
3. 创建API Key
4. 在 `.env` 文件中添加:
   ```
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   ```

### 使用方法

```bash
npm run ai-route
```

然后输入自然语言描述,例如:
- "我要从北京天安门去上海东方明珠"
- "从杭州西湖到苏州拙政园"
- "帮我规划从广州塔到深圳世界之窗的路线"

### AI路线规划示例代码

```javascript
import AmapClient from './amapClient.js';
import AIService from './aiService.js';

const amapClient = new AmapClient('your_amap_key');
const aiService = new AIService('your_deepseek_key');

// 1. AI解析自然语言输入
const parseResult = await aiService.parseLocationInput(
  "我要从北京天安门去上海东方明珠"
);
console.log(parseResult.origin);      // "北京天安门"
console.log(parseResult.destination); // "上海东方明珠"

// 2. 地理编码
const originGeo = await amapClient.geocode(parseResult.origin);
const destGeo = await amapClient.geocode(parseResult.destination);

// 3. 路线规划
const route = await amapClient.drivingRoute(
  originGeo.location,
  destGeo.location,
  '4' // 躲避拥堵
);

// 4. AI生成路线摘要
const summary = await aiService.generateRouteSummary(
  route,
  originGeo.formatted_address,
  destGeo.formatted_address
);
console.log(summary.summary);
```

## 集成到Claude Code MCP

如果你想将此客户端集成到Claude Code作为MCP服务器,可以参考以下配置:

### Claude Code MCP配置示例

在 Claude Code 的配置文件中添加:

```json
{
  "mcpServers": {
    "amap": {
      "command": "node",
      "args": ["src/index.js"],
      "env": {
        "AMAP_API_KEY": "your_amap_api_key"
      }
    }
  }
}
```

## 注意事项

1. **API Key安全**: 不要将API Key提交到代码仓库
2. **配额限制**: 高德地图API有每日调用次数限制,请注意配额
3. **错误处理**: 所有API调用都包含错误处理,请检查返回结果的 `success` 字段

## 参考文档

- [高德地图Web服务API文档](https://lbs.amap.com/api/webservice/summary)
- [IP定位API](https://lbs.amap.com/api/webservice/guide/api/ipconfig)
- [天气查询API](https://lbs.amap.com/api/webservice/guide/api/weatherinfo)
- [地理编码API](https://lbs.amap.com/api/webservice/guide/api/georecode)
- [POI搜索API](https://lbs.amap.com/api/webservice/guide/api/search)

## License

MIT
