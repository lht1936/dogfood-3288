import akshare as ak

print("=== 测试获取 ETF 基金列表 ===")
try:
    df = ak.fund_etf_category_sina(symbol="ETF基金")
    print(df.head(50))
    print("\n列名:", df.columns.tolist())
except Exception as e:
    print(f"错误: {e}")
