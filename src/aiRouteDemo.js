import AmapClient from './amapClient.js';
import AIService from './aiService.js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import readline from 'readline';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, '../.env') });

async function getUserInput(prompt) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    rl.question(prompt, (answer) => {
      rl.close();
      resolve(answer);
    });
  });
}

async function main() {
  const amapApiKey = process.env.AMAP_API_KEY;
  const deepseekApiKey = process.env.DEEPSEEK_API_KEY;

  if (!amapApiKey || amapApiKey === 'your_amap_api_key_here') {
    console.error('错误: 请先在 .env 文件中设置 AMAP_API_KEY');
    process.exit(1);
  }

  if (!deepseekApiKey || deepseekApiKey === 'your_deepseek_api_key_here') {
    console.error('错误: 请先在 .env 文件中设置 DEEPSEEK_API_KEY');
    console.error('请访问 https://platform.deepseek.com/ 注册并获取API Key');
    process.exit(1);
  }

  const amapClient = new AmapClient(amapApiKey);
  const aiService = new AIService(deepseekApiKey);

  console.log('===== 🤖 AI驱动的智能路线规划 =====\n');
  console.log('💡 提示: 你可以用自然语言描述你的行程\n');
  console.log('示例输入:');
  console.log('  - "去上海东方明珠"');
  console.log('  - "到杭州西湖的路线"');
  console.log('  - "从公司出发到北京站"');

  // 获取用户输入后自动处理定位
  const userInput = await getUserInput('请输入你的行程描述（例：去九寨沟）: ');

  if (!userInput.trim()) {
    console.log('输入为空,程序退出');
    process.exit(0);
  }

  console.log('\n🔍 正在使用AI解析你的需求...');
  const parseResult = await aiService.parseLocationInput(userInput);
  
  // 新增：自动处理当前位置
  if (parseResult.origin === '当前位置') {
    console.log('\n📍 正在获取当前位置...');
    const currentLocation = await amapClient.getCurrentLocation();
    if (currentLocation.success) {
      parseResult.origin = currentLocation.formatted_address;
      console.log(`✅ 已使用当前位置: ${parseResult.origin}`);
    } else {
      console.log('⚠️ 自动定位失败，请手动输入起点');
      parseResult.origin = await getUserInput('请输入详细起点地址: ');
    }
  }
  
  if (!parseResult.success) {
    console.error('❌ AI解析失败:', parseResult.error);
    process.exit(1);
  }

  console.log('✅ AI解析结果:');
  console.log('  起点:', parseResult.origin);
  console.log('  终点:', parseResult.destination);

  console.log('\n📍 正在将地址转换为坐标...');
  
  const originGeocode = await amapClient.geocode(parseResult.origin);
  if (!originGeocode.success) {
    console.error('❌ 起点地理编码失败:', originGeocode.error);
    process.exit(1);
  }

  const destGeocode = await amapClient.geocode(parseResult.destination);
  if (!destGeocode.success) {
    console.error('❌ 终点地理编码失败:', destGeocode.error);
    process.exit(1);
  }

  console.log('  起点坐标:', originGeocode.location);
  console.log('  起点地址:', originGeocode.formatted_address);
  console.log('  终点坐标:', destGeocode.location);
  console.log('  终点地址:', destGeocode.formatted_address);

  console.log('\n🗺️  正在规划最佳路线...');
  
  const routeResult = await amapClient.drivingRoute(
    originGeocode.location,
    destGeocode.location,
    '4'
  );

  if (!routeResult.success) {
    console.error('❌ 路线规划失败:', routeResult.error);
    process.exit(1);
  }

  console.log('✅ 路线规划成功!\n');

  const distanceKm = (parseInt(routeResult.distance) / 1000).toFixed(2);
  const durationMin = (parseInt(routeResult.duration) / 60).toFixed(0);
  const durationHour = (parseInt(routeResult.duration) / 3600).toFixed(1);

  console.log('📊 路线信息:');
  console.log('  总距离:', distanceKm, 'km');
  console.log('  预计时间:', durationMin > 60 ? `${durationHour} 小时` : `${durationMin} 分钟`);
  console.log('  通行费:', routeResult.tolls, '元');
  console.log('  收费路段:', (parseInt(routeResult.toll_distance) / 1000).toFixed(2), 'km');
  console.log('  红绿灯:', routeResult.traffic_lights, '个');

  console.log('\n🤖 正在生成AI路线摘要...');
  
  const summaryResult = await aiService.generateRouteSummary(
    routeResult,
    originGeocode.formatted_address,
    destGeocode.formatted_address
  );

  if (summaryResult.success) {
    console.log('\n💬 AI路线摘要:');
    console.log('━'.repeat(60));
    console.log(summaryResult.summary);
    console.log('━'.repeat(60));
  }

  // 修改后的自动打开地图逻辑
  try {
    const [originLng, originLat] = originGeocode.location.split(',');
    const [destLng, destLat] = destGeocode.location.split(',');

    console.log('\n🌐 正在打开高德地图展示路线...');
    await amapClient.openMap('amap-web', {
      lat: destLat,
      lng: destLng,
      address: destGeocode.formatted_address,
      origin: `${originLng},${originLat}`,
      originAddress: originGeocode.formatted_address,
      strategy: '4'
    });
    console.log('✅ 地图已打开，正在展示最佳路线');
  } catch (e) {
    console.warn('⚠️ 地图打开失败:', e.message);
  }

  console.log('\n🛣️  详细导航指引:');
  console.log('━'.repeat(60));
  routeResult.steps.slice(0, 10).forEach((step, index) => {
    console.log(`${index + 1}. ${step.instruction}`);
    console.log(`   道路: ${step.road || '未知'}`);
    console.log(`   距离: ${(parseInt(step.distance) / 1000).toFixed(2)} km`);
    console.log('');
  });

  if (routeResult.steps.length > 10) {
    console.log(`... 还有 ${routeResult.steps.length - 10} 个导航步骤\n`);
  }

  // 修改main函数末尾部分
  console.log('━'.repeat(60));
  console.log('✨ 祝你旅途愉快! ✨');

  // 删除以下用户确认环节代码
  process.exit(0);
}

// 确保只执行主函数
main().catch(console.error);

