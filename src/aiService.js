import axios from 'axios';

class AIService {
  constructor(apiKey, baseUrl = 'https://api.deepseek.com/v1') {
    if (!apiKey) {
      throw new Error('需要提供DeepSeek API密钥');
    }
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async parseLocationInput(userInput) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/chat/completions`,
        {
          model: 'deepseek-chat',
          messages: [
            {
              role: 'system',
              content: `你是一个地理位置解析助手。用户会输入起点和终点的描述,你需要提取出起点和终点的地址信息。
请以JSON格式返回结果,格式如下:
{
  "origin": "起点地址",
  "destination": "终点地址"
}

注意:
1. 只返回JSON对象,不要有其他文字
2. 地址要尽可能完整和准确
3. 如果用户只提到一个地点,将其作为终点,起点设为"当前位置"
4. 如果用户没有明确提到起点或终点,请根据上下文合理推断`
            },
            {
              role: 'user',
              content: userInput
            }
          ],
          temperature: 0.3,
          max_tokens: 200
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data && response.data.choices && response.data.choices.length > 0) {
        const content = response.data.choices[0].message.content.trim();
        
        const jsonMatch = content.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[0]);
          return {
            success: true,
            origin: parsed.origin,
            destination: parsed.destination,
            rawResponse: content
          };
        } else {
          return {
            success: false,
            error: '无法解析AI返回的结果',
            rawResponse: content
          };
        }
      } else {
        return {
          success: false,
          error: 'AI未返回有效响应'
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        details: error.response?.data
      };
    }
  }

  async generateRouteSummary(routeInfo, origin, destination) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/chat/completions`,
        {
          model: 'deepseek-chat',
          messages: [
            {
              role: 'system',
              content: '你是一个友好的导航助手。根据提供的路线信息,生成简洁友好的路线摘要,包括总距离、预计时间、通行费等关键信息。'
            },
            {
              role: 'user',
              content: `请为以下路线生成摘要:
起点: ${origin}
终点: ${destination}
总距离: ${routeInfo.distance}米
预计时间: ${routeInfo.duration}秒
通行费: ${routeInfo.tolls}元
收费路段: ${routeInfo.toll_distance}米
红绿灯数量: ${routeInfo.traffic_lights}个

请用简洁友好的语言描述这条路线,包括距离换算成公里、时间换算成分钟或小时等。`
            }
          ],
          temperature: 0.7,
          max_tokens: 300
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data && response.data.choices && response.data.choices.length > 0) {
        return {
          success: true,
          summary: response.data.choices[0].message.content.trim()
        };
      } else {
        return {
          success: false,
          error: 'AI未返回有效响应'
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}

export default AIService;
