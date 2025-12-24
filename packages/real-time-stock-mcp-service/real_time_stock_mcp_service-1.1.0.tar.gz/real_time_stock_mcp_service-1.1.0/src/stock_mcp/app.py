"""
股票数据 MCP Server（托管友好入口）

为什么这样改：
1) 托管平台更喜欢 “python -m 包名” 这种稳定入口
2) 避免依赖工作目录（cwd）导致 import src.* 失败
3) 将 “构建应用/注册工具” 与 “初始化/运行/清理” 解耦，方便测试与排障
"""

import logging
import os
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from stock_mcp.data_source_interface import FinancialDataInterface
from stock_mcp.stock_data_source import WebCrawlerDataSource
from stock_mcp.utils.utils import setup_logging

from stock_mcp.mcp_tools.search import register_search_tools
from stock_mcp.mcp_tools.kline_data import register_kline_tools
from stock_mcp.mcp_tools.real_time_data import register_real_time_data_tools
from stock_mcp.mcp_tools.fundamental import register_fundamental_tools
from stock_mcp.mcp_tools.valuation import register_valuation_tools
from stock_mcp.mcp_tools.financial_analysis import register_financial_analysis_tools
from stock_mcp.mcp_tools.market import register_market_tools
from stock_mcp.mcp_tools.smart_review import register_smart_review_tools


def build_app(active_data_source: FinancialDataInterface) -> FastMCP:
    """
    构建 FastMCP app（只做“创建 + 注册工具”）
    - 不在这里 initialize 数据源
    - 不在这里 run
    这样托管失败时更好定位：是构建期失败还是运行期失败
    """
    current_date = datetime.now().strftime("%Y-%m-%d")

    app = FastMCP(
        name="real-time-stock-mcp-service",
        instructions=f"""📊 一个获取实时股票数据服务和分析的MCP服务器

**今天日期**: {current_date}

📈 主要功能:
- 查找股票名称，代码
- 实时股票数据
- K线数据（日线、周线、月线）
- 计算技术指标
- 基本面数据（主营构成、经营范围、经营评述等）
- 估值分析数据（市盈率、市净率等）
- 板块行情数据
- 智能点评和评分
""",
    )

    # ✅ 注册所有工具（建议：register_* 内不要做网络请求/阻塞初始化）
    register_search_tools(app, active_data_source)
    register_real_time_data_tools(app, active_data_source)
    register_kline_tools(app, active_data_source)
    register_fundamental_tools(app, active_data_source)
    register_valuation_tools(app, active_data_source)
    register_financial_analysis_tools(app, active_data_source)
    register_market_tools(app, active_data_source)
    register_smart_review_tools(app, active_data_source)

    return app


def main() -> None:
    """
    程序主入口：
    1) 配日志
    2) 创建数据源（依赖注入）
    3) 构建 app + 注册工具
    4) 初始化数据源
    5) app.run() 启动（stdio）
    6) finally 清理资源
    """
    # ✅ 托管环境常用环境变量控制日志级别，方便排障
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    setup_logging(level=getattr(logging, log_level, logging.INFO))
    logger = logging.getLogger(__name__)

    # 1) 依赖注入：后续切换数据源只改这里（符合你项目的 DI 设计）  :contentReference[oaicite:3]{index=3}
    active_data_source: FinancialDataInterface = WebCrawlerDataSource()
    logger.info("数据源: %s", active_data_source.__class__.__name__)

    # 2) 构建 app（注册工具）
    app = build_app(active_data_source)
    logger.info("工具模块注册完成")

    # 3) 初始化数据源（失败不一定要退出，看你业务需求）
    try:
        if active_data_source.initialize():
            logger.info("✅ 数据源初始化成功")
        else:
            logger.warning("⚠️ 数据源初始化失败，某些功能可能不可用")
    except Exception:
        logger.exception("💥 数据源初始化异常：将继续启动（功能可能受限）")

    # 4) 运行服务（托管通常走 stdio，保持默认）
    try:
        logger.info("🚀 启动 MCP Server（stdio）")
        app.run()
    except KeyboardInterrupt:
        logger.info("🛑 服务被中断")
    except Exception:
        logger.exception("💥 服务运行出错")
        # ✅ 托管环境：抛出异常让平台判定启动失败并保留日志
        raise
    finally:
        # 5) 清理资源
        try:
            active_data_source.cleanup()
            logger.info("🧹 资源清理完成")
        except Exception:
            logger.exception("💥 资源清理异常")


if __name__ == "__main__":
    # 允许开发阶段直接 python app.py 运行
    main()
