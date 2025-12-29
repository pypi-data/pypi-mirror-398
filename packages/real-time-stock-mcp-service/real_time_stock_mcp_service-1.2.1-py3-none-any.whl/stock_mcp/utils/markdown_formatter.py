"""
Markdown格式化工具
src/utils/markdown_formatter.py
提供通用的Markdown格式化功能
"""


def format_list_to_markdown_table(data_list):
    """
    将列表数据格式化为Markdown表格
    
    Args:
        data_list: 已经格式化好的字典列表
        
    Returns:
        str: Markdown格式的表格字符串
    """
    if not data_list:
        return ""
    
    # 从字典键中自动提取列标题
    columns = list(data_list[0].keys()) if data_list else []
    
    if not columns:
        return ""
    
    # 表头
    header = "| " + " | ".join(columns) + " |"
    
    # 分隔符行
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    
    # 数据行
    rows = []
    for item in data_list:
        row_data = [str(item.get(col, "")) for col in columns]
        row = "| " + " | ".join(row_data) + " |"
        rows.append(row)
        
    return "\n".join([header, separator] + rows)