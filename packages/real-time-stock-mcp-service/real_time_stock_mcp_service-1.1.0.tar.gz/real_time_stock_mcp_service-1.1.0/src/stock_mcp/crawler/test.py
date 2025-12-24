from src.stock_mcp.crawler.real_time_data import RealTimeDataSpider
from src.stock_mcp.crawler.fundamental_data import FundamentalDataCrawler

real_time_spider = RealTimeDataSpider()
real_time_data = real_time_spider.get_real_time_data("688041.SH")
print(real_time_data)

mark_indices = real_time_spider.get_real_time_market_indices()
print(mark_indices)

print("获取股票代码300750.SZ的 main_business")
fundamental_spider = FundamentalDataCrawler()
main_business = fundamental_spider.get_main_business("300750.SZ")
print(main_business)