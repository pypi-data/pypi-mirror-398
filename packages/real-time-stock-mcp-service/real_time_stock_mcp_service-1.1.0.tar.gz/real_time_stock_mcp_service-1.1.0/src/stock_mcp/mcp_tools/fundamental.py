"""
基本面数据工具
src/mcp_tools/fundamental.py
提供基本面数据查询功能
"""
import logging
from mcp.server.fastmcp import FastMCP
from stock_mcp.data_source_interface import FinancialDataInterface
from stock_mcp.utils.markdown_formatter import format_list_to_markdown_table
from stock_mcp.utils.utils import format_large_number

logger = logging.getLogger(__name__)


def register_fundamental_tools(app: FastMCP, data_source: FinancialDataInterface):
    """
    注册基本面数据相关工具

    Args:
        app: FastMCP应用实例
        data_source: 数据源实例
    """

    @app.tool()
    def get_business_scope(stock_code: str) -> str:
        """
        获取主营业务范围


        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ

        Returns:
            主营业务范围文本

        Examples:
            - get_business_scope("300750.SZ")
        """
        try:
            logger.info(f"获取主营业务范围: {stock_code}")

            # 从数据源获取原始数据
            raw_data = data_source.get_business_scope(stock_code)

            if not raw_data:
                return f"未找到股票代码 '{stock_code}' 的主营业务范围数据"

            # 检查是否有错误信息
            if "error" in raw_data:
                error_msg = raw_data["error"]
                return f"获取主营业务范围数据失败: {error_msg}"

            # 提取BUSINESS_SCOPE内容
            business_scope = raw_data.get('BUSINESS_SCOPE', 'N/A')
            
            return business_scope

        except Exception as e:
            logger.error(f"获取主营业务范围时出错: {e}")
            return f"获取主营业务范围失败: {str(e)}"

    @app.tool()
    def get_main_business(stock_code: str) -> str:
        """
        获取主营构成分析

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ

        Returns:
            主营业务构成数据的Markdown表格

        Examples:
            - get_main_business("300059.SZ")
        """
        try:
            logger.info(f"获取主营业务构成: {stock_code}")

            # 获取最新的报告日期
            raw_report_dates = data_source.get_report_dates(stock_code)
            if not raw_report_dates or (isinstance(raw_report_dates, list) and len(raw_report_dates) == 0):
                return f"未找到股票代码 '{stock_code}' 的报告日期数据"

            # 检查是否有错误信息
            if isinstance(raw_report_dates, list) and len(raw_report_dates) > 0 and "error" in raw_report_dates[0]:
                error_msg = raw_report_dates[0]["error"]
                return f"获取报告日期数据失败: {error_msg}"

            # 只处理第一个数据（最近的报告日期）
            latest_report = raw_report_dates[0]
            report_date = latest_report.get('REPORT_DATE', 'N/A')
            # 只取日期部分，去除时间部分
            if report_date != 'N/A' and ' ' in report_date:
                report_date = report_date.split(' ')[0]

            # 从数据源获取原始数据
            raw_data = data_source.get_main_business(stock_code, report_date)

            if not raw_data:
                return f"未找到股票代码 '{stock_code}' 的主营业务构成数据"

            # 检查是否有错误信息
            if isinstance(raw_data, list) and len(raw_data) > 0 and "error" in raw_data[0]:
                error_msg = raw_data[0]["error"]
                return f"获取主营业务构成数据失败: {error_msg}"

            # 格式化数据
            formatted_data = []
            for item in raw_data:
                # 解析主营业务分类类型
                mainop_type = item.get('MAINOP_TYPE', 'N/A')
                type_mapping = {
                    '1': '按行业分类',
                    '2': '按产品分类',
                    '3': '按地区分类'
                }
                type_desc = type_mapping.get(mainop_type, f'未知分类({mainop_type})')
                
                # 使用 format_large_number 格式化大的数值
                main_income = item.get('MAIN_BUSINESS_INCOME')
                main_cost = item.get('MAIN_BUSINESS_COST')
                main_profit = item.get('MAIN_BUSINESS_RPOFIT')
                
                formatted_item = {
                    '报告日期': item.get('REPORT_DATE', 'N/A')[:10],  # 只取日期部分
                    '分类依据': type_desc,
                    '主营构成': item.get('ITEM_NAME', 'N/A'),
                    '主营业务收入': f"{format_large_number(main_income)}元" if main_income is not None else 'N/A',
                    '收入占比': f"{item.get('MBI_RATIO', 0) * 100:.2f}%" if item.get('MBI_RATIO') is not None else 'N/A',
                    '主营业务成本': f"{format_large_number(main_cost)}元" if main_cost is not None else 'N/A',
                    '成本占比': f"{item.get('MBC_RATIO', 0) * 100:.2f}%" if item.get('MBC_RATIO') is not None else 'N/A',
                    '主营业务利润': f"{format_large_number(main_profit)}元" if main_profit is not None else 'N/A',
                    '利润占比': f"{item.get('MBR_RATIO', 0) * 100:.2f}%" if item.get('MBR_RATIO') is not None else 'N/A',
                    '毛利率': f"{item.get('GROSS_RPOFIT_RATIO', 0) * 100:.2f}%" if item.get('GROSS_RPOFIT_RATIO') is not None else 'N/A',
                    '排序': item.get('RANK', 'N/A')
                }
                formatted_data.append(formatted_item)

            table = format_list_to_markdown_table(formatted_data)
            note = f"\n\n💡 显示 {len(formatted_data)} 条主营业务构成数据"
            
            if report_date:
                note += f"，报告期: {report_date}"
                
            return f"## {stock_code} 主营业务构成\n\n{table}{note}"

        except Exception as e:
            logger.error(f"获取主营业务构成时出错: {e}")
            return f"获取主营业务构成失败: {str(e)}"

    @app.tool()
    def get_business_review(stock_code: str) -> str:
        """
        获取经营评述

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ

        Returns:
            经营评述文本

        Examples:
            - get_business_review("688041.SH")
        """
        try:
            logger.info(f"获取经营评述: {stock_code}")

            # 从数据源获取原始数据
            raw_data = data_source.get_business_review(stock_code)

            if not raw_data:
                return f"未找到股票代码 '{stock_code}' 的经营评述数据"

            # 检查是否有错误信息
            if "error" in raw_data:
                error_msg = raw_data["error"]
                return f"获取经营评述数据失败: {error_msg}"

            # 提取BUSINESS_REVIEW内容
            business_review = raw_data.get('BUSINESS_REVIEW', 'N/A')

            # 返回经营评述内容，如果没有则返回提示信息
            if business_review and business_review != 'N/A':
                return business_review
            else:
                return f"股票代码 '{stock_code}' 无经营评述数据"

        except Exception as e:
            logger.error(f"获取经营评述时出错: {e}")
            return f"获取经营评述失败: {str(e)}"

    @app.tool()
    def get_main_financial_data(stock_code: str) -> str:
        """
        获取公司主要财务数据

        Args:
            stock_code: 股票代码，要在数字后加上交易所代码，格式如300750.SZ

        Returns:
            公司主要财务数据的Markdown表格

        Examples:
            - get_main_financial_data("300750.SZ")
        """
        try:
            logger.info(f"获取公司主要财务数据: {stock_code}")

            # 从数据源获取原始数据
            raw_data = data_source.get_main_financial_data(stock_code)

            if not raw_data:
                return f"未找到股票代码 '{stock_code}' 的主要财务数据"

            # 检查是否有错误信息
            if "error" in raw_data:
                error_msg = raw_data["error"]
                return f"获取公司主要数据失败: {error_msg}"

            # 字段映射和格式化
            field_mapping = {
                'f57': '股票代码',
                'f55': '收益',
                'f183': '总营收',
                'f184': '总营收同比',
                'f105': '净利润',
                'f185': '净利润同比',
                'f186': '毛利率',
                'f187': '净利率',
                'f173': 'ROE',
                'f188': '负债率',
                'f84': '总股本',
                'f116': '总市值',
                'f85': '流通股',
                'f117': '流通市值',
                'f92': '每股净资产',
                'f190': '每股未分配利润',
                'f189': '上市时间',
            }

            # 格式化数值数据
            formatted_data = []
            for key, name in field_mapping.items():
                value = raw_data.get(key, 'N/A')
                
                # 特殊处理数值字段
                if key in ['f55', 'f84', 'f85', 'f92', 'f105', 'f116', 'f117', 'f173', 'f183', 'f184', 'f185', 'f186', 'f187', 'f188', 'f190']:
                    if value != 'N/A' and value is not None:
                        # 百分比字段
                        if key in ['f173', 'f184', 'f185', 'f186', 'f187', 'f188']:
                            value = f"{float(value):.2f}%"
                        # 货币字段（转换为亿元或万元显示）
                        elif key in ['f84', 'f85', 'f105', 'f116', 'f117', 'f183']:
                            value_float = float(value)
                            if value_float >= 1e8:  # 大于1亿
                                value = f"{value_float/1e8:.2f} 亿元"
                            elif value_float >= 1e4:  # 大于1万
                                value = f"{value_float/1e4:.2f} 万元"
                            else:
                                value = f"{value_float:.2f} 元"
                        # 每股净资产和每股未分配利润
                        elif key in ['f92', 'f190']:
                            value = f"{float(value):.2f} 元"
                        # 收益
                        elif key == 'f55':
                            value = f"{float(value):.4f}"
                        else:
                            value = str(value)
                
                # 特殊处理上市时间
                if key == 'f189' and value != 'N/A':
                    # 将YYYYMMDD格式转换为YYYY-MM-DD
                    try:
                        date_str = str(value)
                        year = int(date_str[:4])
                        month = int(date_str[4:6])
                        day = int(date_str[6:8])
                        value = f"{year}-{month:02d}-{day:02d}"
                    except:
                        value = str(value)
                formatted_data.append({'指标': name, '数值': value})

            # 生成Markdown表格
            table = format_list_to_markdown_table(formatted_data)
            return f"## {stock_code} 公司主要财务数据\n\n{table}"

        except Exception as e:
            logger.error(f"获取公司主要财务数据时出错: {e}")
            return f"获取公司主要财务数据失败: {str(e)}"
