from src.stock_mcp.crawler.technical_data import KlineSpider

kline_spider = KlineSpider()
intraday_changes = kline_spider.get_intraday_changes("300274.SZ")
print(intraday_changes)