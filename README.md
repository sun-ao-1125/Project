# 高德地图MCP客户端调用示例

这是一个演示如何通过程序调用高德地图API的示例项目。

## 功能特性

本项目实现了以下高德地图API功能:

1. **地理编码** - 将地址转换为经纬度坐标
2. **逆地理编码** - 将经纬度坐标转换为地址
3. **POI搜索** - 搜索兴趣点(餐厅、商店等)
4. **距离测量** - 计算两点间的距离

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
npm start
```

## 项目结构

```
.
├── src/
│   ├── amapClient.js    # 高德地图API客户端封装
│   └── index.js         # 示例代码
├── .env.example         # 环境变量模板
├── .gitignore
├── package.json
└── README.md
```

## API使用示例

### 地理编码

```javascript
import AmapClient from './amapClient.js';

const client = new AmapClient('your_api_key');

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
- [地理编码API](https://lbs.amap.com/api/webservice/guide/api/georecode)
- [POI搜索API](https://lbs.amap.com/api/webservice/guide/api/search)

## License

MIT
