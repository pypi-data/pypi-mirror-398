# **fdnpy**

Complete Python SDK for [FinancialData.Net](https://financialdata.net/) API

## **Installation**

```
pip install fdnpy
```
## **Usage Example**

```python
from fdnpy import FinancialDataClient

# Replace 'YOUR_API_KEY' with your actual key  
client = FinancialDataClient(api_key='YOUR_API_KEY')

# Get stock prices for Microsoft  
prices = client.get_stock_prices(identifier='MSFT')  
print(prices[0], end='\n\n')

# Get Microsoft's balance sheet  
balance_sheet = client.get_balance_sheet_statements(identifier='MSFT', period='year')  
print(balance_sheet[0])  
```