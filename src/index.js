import AmapClient from './amapClient.js';
import dotenv from 'dotenv';
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

  // 示例1: IP定位 - 获取当前位置
  console.log('1. IP定位 - 获取当前位置');
  const ipLocationResult = await client.getLocationByIp();
  if (ipLocationResult.success) {
    console.log('当前位置:');
    console.log('  省份:', ipLocationResult.province);
    console.log('  城市:', ipLocationResult.city);
    console.log('  城市编码:', ipLocationResult.adcode);
    
    // 使用获取到的城市查询天气
    console.log('\n2. 天气查询 - 当前城市实况天气');
    const weatherResult = await client.getWeather(ipLocationResult.adcode, 'base');
    if (weatherResult.success) {
      console.log('天气信息:');
      console.log('  城市:', weatherResult.city);
      console.log('  天气:', weatherResult.weather);
      console.log('  温度:', weatherResult.temperature, '°C');
      console.log('  风向:', weatherResult.winddirection);
      console.log('  风力:', weatherResult.windpower, '级');
      console.log('  湿度:', weatherResult.humidity, '%');
      console.log('  数据更新时间:', weatherResult.reporttime);
    } else {
      console.log('天气查询失败:', weatherResult.error);
    }

    // 查询未来几天的天气预报
    console.log('\n3. 天气预报 - 未来3天天气');
    const forecastResult = await client.getWeather(ipLocationResult.adcode, 'all');
    if (forecastResult.success) {
      console.log('天气预报:');
      forecastResult.casts.forEach((cast, index) => {
        console.log(`  ${cast.date} (${cast.week}):`);
        console.log(`    白天: ${cast.dayweather}, ${cast.daytemp}°C, ${cast.daywind}风 ${cast.daypower}级`);
        console.log(`    夜间: ${cast.nightweather}, ${cast.nighttemp}°C, ${cast.nightwind}风 ${cast.nightpower}级`);
      });
    } else {
      console.log('天气预报查询失败:', forecastResult.error);
    }
  } else {
    console.log('IP定位失败:', ipLocationResult.error);
    console.log('将使用默认城市(北京)进行演示...\n');
    
    // 如果IP定位失败,使用北京作为示例
    const weatherResult = await client.getWeather('北京', 'base');
    if (weatherResult.success) {
      console.log('北京天气:');
      console.log('  天气:', weatherResult.weather);
      console.log('  温度:', weatherResult.temperature, '°C');
      console.log('  风向:', weatherResult.winddirection);
      console.log('  风力:', weatherResult.windpower, '级');
    }
  }

  console.log('\n===== 其他功能示例 =====\n');

  // 示例4: 地理编码 - 地址转坐标
  console.log('4. 地理编码 - 地址转坐标');
  const geocodeResult = await client.geocode('北京市朝阳区阜通东大街6号', '北京');
  console.log('输入地址: 北京市朝阳区阜通东大街6号');
  if (geocodeResult.success) {
    console.log('经纬度:', geocodeResult.location);
    console.log('格式化地址:', geocodeResult.formatted_address);
  } else {
    console.log('错误:', geocodeResult.error);
  }
  console.log('');

  // 示例5: 逆地理编码 - 坐标转地址
  console.log('5. 逆地理编码 - 坐标转地址');
  const regeocodeResult = await client.regeocode('116.481488,39.990464');
  console.log('输入坐标: 116.481488,39.990464');
  if (regeocodeResult.success) {
    console.log('格式化地址:', regeocodeResult.formatted_address);
    console.log('省份:', regeocodeResult.addressComponent.province);
    console.log('城市:', regeocodeResult.addressComponent.city);
  } else {
    console.log('错误:', regeocodeResult.error);
  }
  console.log('');

  // 示例6: POI搜索
  console.log('6. POI搜索 - 搜索咖啡厅');
  const poiResult = await client.searchPoi('咖啡厅', '北京', 3);
  console.log('搜索关键词: 咖啡厅 (北京)');
  if (poiResult.success) {
    console.log(`找到 ${poiResult.count} 个结果，显示前 ${poiResult.pois.length} 个:`);
    poiResult.pois.forEach((poi, index) => {
      console.log(`  ${index + 1}. ${poi.name}`);
      console.log(`     地址: ${poi.address}`);
      console.log(`     坐标: ${poi.location}`);
    });
  } else {
    console.log('错误:', poiResult.error);
  }
  console.log('');

  console.log('===== 示例执行完成 =====');
}

main().catch(console.error);
