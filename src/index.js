import AmapClient from './amapClient.js';
import * as dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, '../.env') });

/**
 * 高德地图MCP客户端调用示例
 */
async function main() {
  const apiKey = process.env.AMAP_API_KEY;
  
  if (!apiKey || apiKey === 'your_amap_api_key_here') {
    console.error('错误: 请先在 .env 文件中设置 AMAP_API_KEY');
    console.error('1. 复制 .env.example 为 .env');
    console.error('2. 在 https://lbs.amap.com/ 注册并获取API Key');
    console.error('3. 将API Key填入 .env 文件');
    process.exit(1);
  }

  const client = new AmapClient(apiKey);

  console.log('===== 高德地图API调用示例 =====\n');

  // 示例1: 地理编码 - 地址转坐标
  console.log('1. 地理编码 - 地址转坐标');
  const geocodeResult = await client.geocode('北京市朝阳区阜通东大街6号', '北京');
  console.log('输入地址: 北京市朝阳区阜通东大街6号');
  if (geocodeResult.success) {
    console.log('经纬度:', geocodeResult.location);
    console.log('格式化地址:', geocodeResult.formatted_address);
    console.log('级别:', geocodeResult.level);
  } else {
    console.log('错误:', geocodeResult.error);
  }
  console.log('');

  // 示例2: 逆地理编码 - 坐标转地址
  console.log('2. 逆地理编码 - 坐标转地址');
  const regeocodeResult = await client.regeocode('116.481488,39.990464');
  console.log('输入坐标: 116.481488,39.990464');
  if (regeocodeResult.success) {
    console.log('格式化地址:', regeocodeResult.formatted_address);
    console.log('省份:', regeocodeResult.addressComponent.province);
    console.log('城市:', regeocodeResult.addressComponent.city);
    console.log('区域:', regeocodeResult.addressComponent.district);
  } else {
    console.log('错误:', regeocodeResult.error);
  }
  console.log('');

  // 示例3: POI搜索
  console.log('3. POI搜索 - 搜索咖啡厅');
  const poiResult = await client.searchPoi('咖啡厅', '北京', 5);
  console.log('搜索关键词: 咖啡厅 (北京)');
  if (poiResult.success) {
    console.log(`找到 ${poiResult.count} 个结果，显示前 ${poiResult.pois.length} 个:`);
    poiResult.pois.forEach((poi, index) => {
      console.log(`  ${index + 1}. ${poi.name}`);
      console.log(`     地址: ${poi.address}`);
      console.log(`     坐标: ${poi.location}`);
      if (poi.tel) console.log(`     电话: ${poi.tel}`);
    });
  } else {
    console.log('错误:', poiResult.error);
  }
  console.log('');

  // 示例4: 距离测量
  console.log('4. 距离测量 - 两点间直线距离');
  const distanceResult = await client.distance(
    '116.481488,39.990464',  // 北京
    '121.472644,31.231706',  // 上海
    1  // 直线距离
  );
  console.log('起点: 116.481488,39.990464 (北京)');
  console.log('终点: 121.472644,31.231706 (上海)');
  if (distanceResult.success) {
    console.log('直线距离:', (distanceResult.distance / 1000).toFixed(2), '公里');
  } else {
    console.log('错误:', distanceResult.error);
  }
  console.log('');

  console.log('===== 示例执行完成 =====');
}

main().catch(console.error);
