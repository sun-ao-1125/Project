import axios from 'axios';

/**
 * 高德地图API客户端
 */
class AmapClient {
  constructor(apiKey) {
    if (!apiKey) {
      throw new Error('需要提供高德地图API密钥');
    }
    this.apiKey = apiKey;
    this.baseUrl = 'https://restapi.amap.com/v3';
  }

  /**
   * 地理编码 - 将地址转换为经纬度坐标
   * @param {string} address - 地址
   * @param {string} city - 城市(可选)
   * @returns {Promise<Object>} 地理编码结果
   */
  async geocode(address, city = '') {
    try {
      const response = await axios.get(`${this.baseUrl}/geocode/geo`, {
        params: {
          key: this.apiKey,
          address: address,
          city: city
        }
      });

      if (response.data.status === '1' && response.data.geocodes.length > 0) {
        const result = response.data.geocodes[0];
        return {
          success: true,
          location: result.location,
          formatted_address: result.formatted_address,
          province: result.province,
          city: result.city,
          district: result.district,
          level: result.level
        };
      } else {
        return {
          success: false,
          error: '地理编码失败',
          info: response.data.info
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * 逆地理编码 - 将经纬度坐标转换为地址
   * @param {string} location - 经纬度坐标 (格式: "经度,纬度")
   * @returns {Promise<Object>} 逆地理编码结果
   */
  async regeocode(location) {
    try {
      const response = await axios.get(`${this.baseUrl}/geocode/regeo`, {
        params: {
          key: this.apiKey,
          location: location
        }
      });

      if (response.data.status === '1') {
        const result = response.data.regeocode;
        return {
          success: true,
          formatted_address: result.formatted_address,
          addressComponent: result.addressComponent,
          pois: result.pois
        };
      } else {
        return {
          success: false,
          error: '逆地理编码失败',
          info: response.data.info
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * POI搜索 - 搜索兴趣点
   * @param {string} keywords - 搜索关键词
   * @param {string} city - 城市
   * @param {number} offset - 每页记录数(最大50)
   * @returns {Promise<Object>} POI搜索结果
   */
  async searchPoi(keywords, city = '', offset = 10) {
    try {
      const response = await axios.get(`${this.baseUrl}/place/text`, {
        params: {
          key: this.apiKey,
          keywords: keywords,
          city: city,
          offset: offset
        }
      });

      if (response.data.status === '1') {
        return {
          success: true,
          count: response.data.count,
          pois: response.data.pois.map(poi => ({
            name: poi.name,
            type: poi.type,
            address: poi.address,
            location: poi.location,
            tel: poi.tel
          }))
        };
      } else {
        return {
          success: false,
          error: 'POI搜索失败',
          info: response.data.info
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * 距离测量 - 计算两点间的距离
   * @param {string} origin - 起点坐标 (格式: "经度,纬度")
   * @param {string} destination - 终点坐标 (格式: "经度,纬度")
   * @param {number} type - 路径类型: 1-直线距离, 3-驾车距离
   * @returns {Promise<Object>} 距离测量结果
   */
  async distance(origin, destination, type = 1) {
    try {
      const response = await axios.get(`${this.baseUrl}/distance`, {
        params: {
          key: this.apiKey,
          origins: origin,
          destination: destination,
          type: type
        }
      });

      if (response.data.status === '1') {
        return {
          success: true,
          distance: response.data.results[0].distance,
          duration: response.data.results[0].duration
        };
      } else {
        return {
          success: false,
          error: '距离测量失败',
          info: response.data.info
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * IP定位 - 根据IP地址获取位置信息
   * @param {string} ip - IP地址(可选,不传则自动识别)
   * @returns {Promise<Object>} IP定位结果
   */
  async getLocationByIp(ip = '') {
    try {
      const response = await axios.get(`${this.baseUrl}/ip`, {
        params: {
          key: this.apiKey,
          ip: ip
        }
      });

      if (response.data.status === '1') {
        return {
          success: true,
          province: response.data.province,
          city: response.data.city,
          adcode: response.data.adcode,
          rectangle: response.data.rectangle
        };
      } else {
        return {
          success: false,
          error: 'IP定位失败',
          info: response.data.info
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * 天气查询 - 查询指定城市的天气信息
   * @param {string} city - 城市名称或城市编码(adcode)
   * @param {string} extensions - base:返回实况天气, all:返回预报天气
   * @returns {Promise<Object>} 天气查询结果
   */
  async getWeather(city, extensions = 'base') {
    try {
      const response = await axios.get(`${this.baseUrl}/weather/weatherInfo`, {
        params: {
          key: this.apiKey,
          city: city,
          extensions: extensions
        }
      });

      if (response.data.status === '1') {
        if (extensions === 'base' && response.data.lives && response.data.lives.length > 0) {
          const live = response.data.lives[0];
          return {
            success: true,
            type: 'live',
            province: live.province,
            city: live.city,
            weather: live.weather,
            temperature: live.temperature,
            winddirection: live.winddirection,
            windpower: live.windpower,
            humidity: live.humidity,
            reporttime: live.reporttime
          };
        } else if (extensions === 'all' && response.data.forecasts && response.data.forecasts.length > 0) {
          const forecast = response.data.forecasts[0];
          return {
            success: true,
            type: 'forecast',
            province: forecast.province,
            city: forecast.city,
            casts: forecast.casts
          };
        } else {
          return {
            success: false,
            error: '天气数据为空'
          };
        }
      } else {
        return {
          success: false,
          error: '天气查询失败',
          info: response.data.info
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

export default AmapClient;
