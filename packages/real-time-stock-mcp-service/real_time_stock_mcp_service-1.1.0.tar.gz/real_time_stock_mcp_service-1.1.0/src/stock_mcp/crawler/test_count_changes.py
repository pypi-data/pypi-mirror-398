import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.stock_mcp.crawler.market import MarketSpider

def main():
    # 创建爬虫实例
    spider = MarketSpider()

    result = spider.get_current_count_changes()

    # 打印结果
    if result:
        print(f"成功获取到 {len(result)} 条数据:")
        print(result)
    else:
        print("未能获取到数据")

if __name__ == "__main__":
    main()