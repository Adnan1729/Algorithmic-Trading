import numpy as np
import pandas as pd
import requests
import xlsxwriter
import math
from secrets import ALTERNATE_API_TOKEN

# Read in a different csv file containing stock information
stocks = pd.read_csv('nasdaq_stocks.csv')

# Split the symbols into chunks for batch API calls
def split_symbols(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

symbol_groups = list(split_symbols(stocks['Symbol'], 100))
symbol_strings = [','.join(group) for group in symbol_groups]

# Initialize an empty DataFrame to store the final results
my_columns = ['Symbol', 'Current Price', 'Market Capitalization', 'Shares to Purchase']
final_dataframe = pd.DataFrame(columns=my_columns)

# Make batch API calls and update the final DataFrame
for symbol_string in symbol_strings:
    batch_api_call_url = f'https://alternateapi.com/stock/market/batch/?types=quote&symbols={symbol_string}&token={ALTERNATE_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    
    for symbol in symbol_string.split(','):
        final_dataframe = final_dataframe.append(
            pd.Series(
                [
                    symbol,
                    data[symbol]['quote']['currentPrice'],
                    data[symbol]['quote']['marketCap'],
                    'N/A'
                ],
                index=my_columns
            ),
            ignore_index=True
        )

# Prompt the user for the portfolio size and calculate the position size
portfolio_size = input("Enter the value of your portfolio:")

try:
    val = float(portfolio_size)
except ValueError:
    print("That's not a number! \n Try again:")
    portfolio_size = input("Enter the value of your portfolio:")

position_size = float(portfolio_size) / len(final_dataframe.index)
final_dataframe['Shares to Purchase'] = (position_size / final_dataframe['Current Price']).apply(math.floor)

# Save the final DataFrame to an Excel file
writer = pd.ExcelWriter('recommended_trades.xlsx', engine='xlsxwriter')
final_dataframe.to_excel(writer, sheet_name='Recommended Trades', index=False)

background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format({'font_color': font_color, 'bg_color': background_color, 'border': 1})
dollar_format = writer.book.add_format({'num_format': '$0.00', 'font_color': font_color, 'bg_color': background_color, 'border': 1})
integer_format = writer.book.add_format({'num_format': '0', 'font_color': font_color, 'bg_color': background_color, 'border': 1})

column_formats = {
    'A': ['Symbol', string_format],
    'B': ['Current Price', dollar_format],
    'C': ['Market Capitalization', dollar_format],
    'D': ['Shares to Purchase', integer_format]
}

for column, (header, cell_format) in column_formats.items():
    writer.sheets['Recommended Trades'].set_column(f'{column}:{column}', 20, cell_format)
    writer.sheets['Recommended Trades'].write(f'{column}1', header, string_format)

writer.save()
