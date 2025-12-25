from typing import Dict, Any
from fastmcp import FastMCP, Context
from pydantic import Field
from config import config

def register_home_statistic_tools(mcp: FastMCP) -> FastMCP:
    """注册首页统计相关的工具"""

    @mcp.tool()
    def get_home_statistic(
        ctx: Context,
        ab_id: int = Field(description="帐套ID"),
        accounting_period: str = Field(description="会计期间，格式：YYYY-MM")
    ) -> Dict[str, Any]:
        """
        获取首页统计指标数据
        
        根据不同的会计准则统计首页指标，包括：
        - 资产总额
        - 负债总额  
        - 本月营业收入
        - 本月净利润
        - 财务能力分析（偿债能力、盈利能力、运营能力、现金流状况）
        
        调用示例：
        {
            "accounting_period": "2025-10",
            "ab_id": 81
        }

        Returns:
            Dict[str, Any]: 返回首页统计指标数据，结构如下：
            {
                "total_assets": {
                    "current": "当期资产总额，Decimal类型，保留2位小数",
                    "yoy": "同比变化百分比，Decimal类型，如10.50表示10.50%",
                    "mom": "环比变化百分比，Decimal类型",
                    "previous_year": "去年同期资产总额",
                    "previous_month": "上个月资产总额",
                    "raw_data": {
                        "current_period_value": "当前期间原始值",
                        "previous_year_value": "去年同期原始值", 
                        "previous_month_value": "上个月原始值"
                    }
                },
                "total_liabilities": {
                    "current": "当期负债总额，Decimal类型，保留2位小数",
                    "yoy": "同比变化百分比",
                    "mom": "环比变化百分比", 
                    "previous_year": "去年同期负债总额",
                    "previous_month": "上个月负债总额",
                    "raw_data": {...}  # 同total_assets结构
                },
                "monthly_revenue": {
                    "current": "本月营业收入",
                    "yoy": "营业收入同比变化百分比",
                    "mom": "营业收入环比变化百分比",
                    "previous_year": "去年同期营业收入",
                    "previous_month": "上个月营业收入", 
                    "raw_data": {...}  # 同total_assets结构
                },
                "monthly_net_profit": {
                    "current": "本月净利润",
                    "yoy": "净利润同比变化百分比", 
                    "mom": "净利润环比变化百分比",
                    "previous_year": "去年同期净利润",
                    "previous_month": "上个月净利润",
                    "raw_data": {...}  # 同total_assets结构
                },
                "financial_analysis": {
                    "solvency": {
                        "current_ratio": "流动比率(%) = 流动资产/流动负债×100%",
                        "asset_liability_ratio": "资产负债率(%) = 总负债/总资产×100%", 
                        "raw_data": {
                            "current_assets": "流动资产",
                            "current_liabilities": "流动负债",
                            "total_assets": "总资产",
                            "total_liabilities": "总负债"
                        }
                    },
                    "profitability": {
                        "gross_profit_margin": "毛利率(%) = (营业收入-营业成本)/营业收入×100%",
                        "net_profit_margin": "销售净利率(%) = 净利润/营业收入×100%", 
                        "roe": "净资产收益率(%) = 净利润/净资产×100%",
                        "raw_data": {
                            "gross_profit": "毛利润 = 营业收入-营业成本",
                            "revenue": "营业收入",
                            "net_profit": "净利润", 
                            "equity": "净资产 = 总资产-总负债"
                        }
                    },
                    "operational": {
                        "receivables_turnover_ratio": "应收账款周转率 = 营业收入/平均应收账款余额",
                        "receivables_turnover_days": "应收账款周转天数 = 365/应收账款周转率",
                        "inventory_turnover_ratio": "存货周转率 = 营业成本/平均存货余额", 
                        "inventory_turnover_days": "存货周转天数 = 365/存货周转率",
                        "raw_data": {
                            "revenue": "营业收入",
                            "average_receivables": "平均应收账款 = (期初+期末)/2",
                            "cost_of_goods_sold": "营业成本",
                            "average_inventory": "平均存货 = (期初+期末)/2"
                        }
                    },
                    "cash_flow": {
                        "sales_cash_ratio": "销售收入现金比率(%) = 经营活动现金流量净额/营业收入×100%",
                        "operating_cash_flow_ratio": "营业现金流量比率(%) = 经营活动现金流量净额/流动负债×100%", 
                        "raw_data": {
                            "operating_cash_flow": "经营活动现金流量净额",
                            "revenue": "营业收入", 
                            "current_liabilities": "流动负债"
                        }
                    }
                }
            }
            
        注意：
        1. 所有数值均为Decimal类型，保留2位小数
        2. 增长率使用百分比形式（如10.50表示10.50%）
        3. 不同会计准则返回的financial_analysis内容可能不同，部分会计准则可能缺少某些分析指标
        4. 如果数据获取失败，相关字段会返回默认值0.00
        """
        # 构建请求数据
        request_data = {
            "ab_id": ab_id,
            "accounting_period": accounting_period
        }

        # 调用通用API处理函数
        response_data = config.handle_api_request(
            ctx,
            f"{config.backend_base_url}/api/financial_reports/home_statistic/",
            request_data
        )

        return response_data

    return mcp