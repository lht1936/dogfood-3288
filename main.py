import akshare as ak
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="纳斯达克指数基金查询服务",
    description="使用 akshare 获取纳斯达克指数基金数据的 FastAPI 服务",
    version="1.0.0"
)


class FundInfo(BaseModel):
    代码: str
    名称: str
    最新价: Optional[str] = None
    涨跌幅: Optional[str] = None


@app.get("/")
def root():
    return {"message": "纳斯达克指数基金查询服务", "docs": "/docs"}


NASDAQ_KEYWORDS = ["纳指", "纳斯达克", "QQQ", "NAS"]


def filter_nasdaq_funds(df):
    if df is None or df.empty:
        return df
    
    mask = df["名称"].apply(lambda x: any(kw in str(x) for kw in NASDAQ_KEYWORDS))
    return df[mask]


@app.get("/api/funds/nasdaq", response_model=List[FundInfo])
def get_nasdaq_funds():
    try:
        logger.info("开始获取纳斯达克指数基金数据...")
        df = ak.fund_etf_category_sina(symbol="ETF基金")
        
        if df is None or df.empty:
            logger.warning("未获取到 ETF 数据")
            return []
        
        nasdaq_df = filter_nasdaq_funds(df)
        
        if nasdaq_df is None or nasdaq_df.empty:
            logger.warning("未筛选到纳斯达克相关基金")
            return []
        
        records = nasdaq_df.to_dict(orient="records")
        funds = []
        for record in records:
            fund = FundInfo(
                代码=str(record.get("代码", "")),
                名称=str(record.get("名称", "")),
                最新价=str(record.get("最新价", "")) if record.get("最新价") is not None else None,
                涨跌幅=str(record.get("涨跌幅", "")) if record.get("涨跌幅") is not None else None
            )
            funds.append(fund)
        
        logger.info(f"成功获取 {len(funds)} 条纳斯达克指数基金数据")
        return funds
    except Exception as e:
        logger.error(f"获取纳斯达克指数基金数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@app.get("/api/funds/nasdaq/search")
def search_nasdaq_funds(keyword: str):
    try:
        funds = get_nasdaq_funds()
        
        if not keyword:
            return funds
        
        keyword = keyword.lower()
        filtered = [
            fund for fund in funds
            if keyword in fund.代码.lower() or keyword in fund.名称.lower()
        ]
        
        return filtered
    except Exception as e:
        logger.error(f"搜索基金失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@app.get("/api/funds/nasdaq/{fund_code}")
def get_fund_by_code(fund_code: str):
    try:
        funds = get_nasdaq_funds()
        
        for fund in funds:
            if fund.代码 == fund_code:
                return fund
        
        raise HTTPException(status_code=404, detail=f"未找到代码为 {fund_code} 的基金")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基金详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取基金详情失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
