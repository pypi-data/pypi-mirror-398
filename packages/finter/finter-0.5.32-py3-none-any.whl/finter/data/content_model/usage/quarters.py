"""
KRX Financial Loader - Quarters parameter usage documentation.
"""

QUARTERS_USAGE_TEXT = """
╔════════════════════════════════════════════════════════════════════════════╗
║                    Financial Calculator - Quick Guide                      ║
╚════════════════════════════════════════════════════════════════════════════╝

📖 Basic Usage:
   fc = cf.get_fc('item_name')
   result = fc.apply_rolling(4, 'sum').to_wide()

🔧 Polars Integration:
   fc.filter(pl.col("id") == 12170).sort("pit")  # Direct polars methods

📋 Operations:
   'sum'  : TTM (4-quarter sum)
   'mean' : 4-quarter average
   'diff' : YoY change (current - 4Q ago)
   'last' : Latest quarter (quarters=0)

💡 Common Patterns:

   # TTM Revenue
   cf.get_fc('revenue').apply_rolling(4, 'sum').to_wide()

   # Operating Margin (TTM)
   cf.get_fc({'revenue': 'revenue', 'oi': 'operating_income'})\\
     .apply_rolling(4, 'sum').apply_expression("oi / revenue").to_wide()

   # ROE (TTM income / latest equity)
   cf.get_fc({'income': 'net_income', 'equity': 'total_equity'})\\
     .apply_rolling(4, 'sum', variables=['income'])\\
     .apply_expression("income / equity").to_wide()

   # Working Capital
   cf.get_fc({'ca': 'current_assets', 'cl': 'current_liabilities'})\\
     .apply_expression("ca - cl").to_wide()

🎯 Advanced:
   - Multiple items: cf.get_fc({'a': 'item1', 'b': 'item2'})
   - Selective rolling: apply_rolling(4, 'sum', variables=['a'])
   - Expressions: apply_expression("a / b * 100")
   - Auto trading_days reindex (disable with trading_days=False)
"""
