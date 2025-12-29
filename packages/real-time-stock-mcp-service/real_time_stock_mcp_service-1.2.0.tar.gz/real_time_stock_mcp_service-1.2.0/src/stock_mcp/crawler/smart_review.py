from stock_mcp.crawler.base_crawler import EastMoneyBaseSpider

import requests
from typing import Optional, Dict, Any, List


class SmartReviewCrawler(EastMoneyBaseSpider):
    """
    智能点评数据爬虫类

    用于获取股票的智能分析点评信息
    """
    
    SMART_REVIEW_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
    EXPERT_REVIEW_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
    SMART_SCORE_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    MAIN_FORCE_CONTROL_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    PARTICIPATION_WISH_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"

    def __init__(
            self,
            session: Optional[requests.Session] = None,
            timeout: int = 10,
    ):
        """
        初始化智能点评数据爬虫
        
        :param session: requests.Session 实例
        :param timeout: 请求超时时间
        """
        super().__init__(session, timeout)

    def get_participation_wish(self, stock_code: str) -> Optional[List[Dict[Any, Any]]]:
        """
        获取市场参与意愿数据
        
        :param stock_code: 股票代码
        :return: 市场参与意愿数据列表
        """
        # 如果股票代码包含交易所后缀，则移除后缀只保留纯数字部分
        if '.' in stock_code:
            stock_code = stock_code.split('.')[0]
        
        # 生成 callback 参数
        callback = self._generate_callback()
        
        params = {
            "callback": callback,
            "filter": f"(SECURITY_CODE=\"{stock_code}\")",
            "columns": "ALL",
            "source": "WEB",
            "client": "WEB",
            "reportName": "RPT_STOCK_PARTICIPATION",
            "sortColumns": "TRADE_DATE",
            "sortTypes": "1",
            "pageSize": "30"
        }
        
        try:
            response = self._get_jsonp(self.PARTICIPATION_WISH_URL, params)
            
            # 检查响应是否成功
            if response and response.get("code") == 0 and response.get("success") is True:
                data = response.get("result", {}).get("data", [])
                return data if data else []
            else:
                # 如果不成功，返回错误信息
                message = response.get("message", "未知错误") if response else "未知错误"
                return [{"error": message}]
        except Exception as e:
            return [{"error": str(e)}]

    def get_main_force_control(self, stock_code: str) -> Optional[List[Dict[Any, Any]]]:
        """
        获取主力控盘数据
        
        :param stock_code: 股票代码
        :return: 主力控盘数据列表
        """
        # 如果股票代码包含交易所后缀，则移除后缀只保留纯数字部分
        if '.' in stock_code:
            stock_code = stock_code.split('.')[0]
        
        # 生成 callback 参数
        callback = self._generate_callback()
        
        params = {
            "callback": callback,
            "reportName": "RPT_DMSK_TS_STOCKEVALUATE",
            "filter": f"(SECURITY_CODE=\"{stock_code}\")",
            "columns": "ALL",
            "source": "WEB",
            "client": "WEB",
            "sortColumns": "TRADE_DATE",
            "sortTypes": "1"
        }
        
        try:
            response = self._get_jsonp(self.MAIN_FORCE_CONTROL_URL, params)
            
            # 检查响应是否成功
            if response and response.get("code") == 0 and response.get("success") is True:
                data = response.get("result", {}).get("data", [])
                return data if data else []
            else:
                # 如果不成功，返回错误信息
                message = response.get("message", "未知错误") if response else "未知错误"
                return [{"error": message}]
        except Exception as e:
            return [{"error": str(e)}]

    def get_smart_score(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        """
        获取股票智能评分数据
        
        :param stock_code: 股票代码
        :return: 智能评分数据字典
        """
        # 如果股票代码包含交易所后缀，则移除后缀只保留纯数字部分
        if '.' in stock_code:
            stock_code = stock_code.split('.')[0]
        
        # 生成 callback 参数
        callback = self._generate_callback()
        
        params = {
            "callback": callback,
            "filter": f"(SECURITY_CODE=\"{stock_code}\")",
            "columns": "ALL",
            "source": "WEB",
            "client": "WEB",
            "reportName": "RPT_CUSTOM_STOCK_PK"
        }
        
        additional_params = {
            "callback": callback,
            "filter": f"(SECURITY_CODE=\"{stock_code}\")",
            "columns": "ALL",
            "source": "WEB",
            "client": "WEB",
            "reportName": "RPT_STOCK_CHANGERATE",
            "pageSize": "1"
        }
        
        try:
            response = self._get_jsonp(self.SMART_SCORE_URL, params)
            additional_response = self._get_jsonp(self.SMART_SCORE_URL, additional_params)
            
            # 检查响应是否成功
            if response and response.get("code") == 0 and response.get("success") is True:
                data = response.get("result", {}).get("data", [])
                result = data[0] if data else {}
                
                # 添加额外的数据
                if additional_response and additional_response.get("code") == 0 and additional_response.get("success") is True:
                    additional_data = additional_response.get("result", {}).get("data", [])
                    if additional_data:
                        additional_info = additional_data[0]
                        result.update({
                            "SECURITY_NAME_ABBR":  additional_info.get("SECURITY_NAME_ABBR"),
                            "RISE_1_PROBABILITY": additional_info.get("RISE_1_PROBABILITY"),
                            "AVERAGE_1_INCREASE": additional_info.get("AVERAGE_1_INCREASE"),
                            "RISE_5_PROBABILITY": additional_info.get("RISE_5_PROBABILITY"),
                            "AVERAGE_5_INCREASE": additional_info.get("AVERAGE_5_INCREASE")
                        })
                
                return result if result else None
            else:
                # 如果不成功，返回错误信息
                message = response.get("message", "未知错误") if response else "未知错误"
                return {"error": message}
        except Exception as e:
            return {"error": str(e)}

    def get_smart_score_rank(self, stock_code: str) -> Optional[Dict[Any, Any]]:
        """
        获取个股智能评分排名数据
        
        :param stock_code: 股票代码
        :return: 智能评分排名数据字典
        """
        # 如果股票代码包含交易所后缀，则移除后缀只保留纯数字部分
        if '.' in stock_code:
            stock_code = stock_code.split('.')[0]
        
        # 生成 callback 参数
        callback = self._generate_callback()
        
        params = {
            "callback": callback,
            "filter": f"(SECURITY_CODE=\"{stock_code}\")",
            "columns": "ALL",
            "source": "WEB",
            "client": "WEB",
            "reportName": "RPT_STOCK_PK_RANK"
        }
        
        try:
            response = self._get_jsonp(self.SMART_SCORE_URL, params)
            
            # 检查响应是否成功
            if response and response.get("code") == 0 and response.get("success") is True:
                data = response.get("result", {}).get("data", [])
                return data[0] if data else None
            else:
                # 如果不成功，返回错误信息
                message = response.get("message", "未知错误") if response else "未知错误"
                return {"error": message}
        except Exception as e:
            return {"error": str(e)}

    def get_top_rated_stocks(self, page_size: int = 10) -> Optional[List[Dict[Any, Any]]]:
        """
        获取全市场高评分个股
        
        :param page_size: 返回数据条数，默认为10条
        :return: 高评分个股数据列表
        """
        # 生成 callback 参数
        callback = self._generate_callback()
        
        params = {
            "callback": callback,
            "filter": "",
            "columns": "ALL",
            "source": "WEB",
            "client": "WEB",
            "reportName": "RPT_STOCK_PK_RANK",
            "sortColumns": "COMPRE_SCORE",
            "sortTypes": "-1",
            "pageSize": str(page_size)
        }
        
        try:
            response = self._get_jsonp(self.SMART_SCORE_URL, params)
            
            # 检查响应是否成功
            if response and response.get("code") == 0 and response.get("success") is True:
                data = response.get("result", {}).get("data", [])
                return data if data else []
            else:
                # 如果不成功，返回错误信息
                message = response.get("message", "未知错误") if response else "未知错误"
                return [{"error": message}]
        except Exception as e:
            return [{"error": str(e)}]