import time

import requests
from typing import Dict, Any, Optional, List
from stock_mcp.crawler.base_crawler import EastMoneyBaseSpider


class RealTimeDataSpider(EastMoneyBaseSpider):
    """
    东方财富实时股票数据爬虫

    用于获取股票的实时行情数据
    """

    MARKET_INDEX_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    REAL_TIME_DATA_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"


    def __init__(
            self,
            session: Optional[requests.Session] = None,
            timeout: int = None,
    ):
        super().__init__(session, timeout)


    def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票实时数据

        :param symbol: 股票代码，包含交易所代码，格式例如 SZ300750
        :return: 实时股票数据
        """
        # 将股票代码转换为东方财富的secid格式
        secid = self.format_secid(symbol)
        
        params = {
            "cb": self._generate_callback(),
            "secid": secid,
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "end": "20500101",
            "lmt": "1",
            "_": str(int(time.time() * 1000))
        }
        
        response = self._get_jsonp(self.REAL_TIME_DATA_URL, params)
        
        if response is None:
            raise Exception("获取实时数据失败: 无法解析响应")
        
        rc = response.get("rc", -1)
        if rc != 0:
            raise Exception(f"获取实时数据失败: rc={rc}")
            
        data = response.get("data", {})
        return data

    def get_real_time_market_indices(self) -> List[Dict]:
        """
        获取实时大盘指数数据
        
        :return: 实时大盘指数数据列表
        """
        params = {
            "ut": "13697a1cc677c8bfa9a496437bfef419",
            "fields": "f1,f2,f3,f4,f12,f13,f14",
            "secids": "1.000001,1.000016,1.000300,1.000003,1.000688,0.399001,0.399006,0.399106,0.399003",
            "_": str(int(time.time() * 1000))
        }
        
        response = self._get_json(self.MARKET_INDEX_URL, params)
        rc = response.get("rc", -1)
        
        if rc != 0:
            raise Exception(f"获取大盘指数数据失败: rc={rc}")
            
        data = response.get("data", {})
        diff = data.get("diff", [])
        
        return diff


if __name__ == '__main__':
    # 创建爬虫实例
    spider = RealTimeDataSpider()
    # 获取宁德时代的实时数据
    data = spider.get_real_time_data("SZ300750")
    print(data)