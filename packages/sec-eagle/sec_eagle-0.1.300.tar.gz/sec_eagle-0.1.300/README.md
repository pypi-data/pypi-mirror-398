# sec_eagle

**sec_eagle** is a Python package for fetching and parsing SEC (Securities and Exchange Commission) filings. It leverages web scraping and XML parsing to help analysts and developers extract structured financial data.

## 🔍 Features

- Fetch SEC filing data using Requests
- Export data to Pandas DataFrames
- Utilities for identifying key financial metrics
- Any Inline Fact with a tag is scrapable

## 🚀 Installation

```bash
-- pip install sec_eagle


## 📦 Example Usage

from sec_eagle import FileGather, SecCompany
import pandas as pd

# Initialize FileGather to search for filings
email = "your.email@example.com"
filings = FileGather(email=email, return_type="df")

# Specify the tickers and filing types
tickers = ["AAPL", "AMZN", "NFLX"]
filing_types = ["10-K", "10-Q", "20-F", "40-F"]
urls = filings.company_file(filing_types, tickers, "ticker")

# Tags to extract from XML filings
data_tags = ["dei:EntityCommonStockSharesOutstanding","dei:SecurityExchangeName"]  # example tags
data = []

# Loop through filings and collect parsed data
for url in urls:
    company = SecCompany(url=url, email=email, return_type="df")
    xml_data = company.xml_parser(data_tags)
    data.append(xml_data)

# Combine all company data into a single DataFrame
df = pd.concat(data).reset_index(drop=True)
```
