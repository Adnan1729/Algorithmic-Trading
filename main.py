import numpy as np 
import pandas as pd 
import requests 
import xlsxwriter 
import math 

# Read in a different csv file containing stock information
stocks = pd.read_csv('nasdaq_stocks.csv')

# Use a different API token
from secrets import ALTERNATE_API_TOKEN

# Initialize an empty DataFrame to store the final results
my_columns = ['Symbol', 'Current Price','Market Capitalization', 'Shares to Purchase']
final_dataframe = pd.DataFrame(columns = my_columns)

# Iterate through each symbol in the stocks DataFrame and retrieve data from the API
for symbol in stocks['Symbol']:
    api_url = f'https://alternateapi.com/stock/{symbol}/quote?token={ALTERNATE_API_TOKEN}'
    data = requests.get(api_url).json()
    
    # Append the new data to the final DataFrame
    final_dataframe = final_dataframe.append(
                                        pd.Series([symbol, 
                                                   data['currentPrice'], 
                                                   data['marketCap'], 
                                                   'N/A'], 
                                                  index = my_columns), 
                                        ignore_index = True)

# Split the symbols into chunks for batch API calls
def split_symbols(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

symbol_groups = list(split_symbols(stocks['Symbol'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))

# Make batch API calls and update the final DataFrame
for symbol_string in symbol_strings:
    batch_api_call_url = f'https://alternateapi.com/stock/market/batch/?types=quote&symbols={symbol_string}&token={ALTERNATE_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        final_dataframe.loc[final_dataframe['Symbol'] == symbol, 'Shares to Purchase'] = math.floor(position_size / final_dataframe.loc[final_dataframe['Symbol'] == symbol, 'Current Price'])

# Prompt the user for the portfolio size and calculate the position size
portfolio_size = input("Enter the value of your portfolio:")
try:
    val = float(portfolio_size)
except ValueError:
    print("That's not a number! \n Try again:")
    portfolio_size = input("Enter the value of your portfolio:")

position_size = float(portfolio_size) / len(final_dataframe.index)
for i in range(0, len(final_dataframe['Ticker'])-1):
    final_dataframe.loc[i, 'Number Of Shares to Buy'] = math.floor(position_size / final_dataframe['Price'][i])
final_dataframe

writer = pd.ExcelWriter('recommended_trades.xlsx', engine='xlsxwriter')
final_dataframe.to_excel(writer, sheet_name='Recommended Trades', index = False)

background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format(
        {
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

dollar_format = writer.book.add_format(
        {
            'num_format':'$0.00',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

integer_format = writer.book.add_format(
        {
            'num_format':'0',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

column_formats = { 
                    'A': ['Ticker', string_format],
                    'B': ['Price', dollar_format],
                    'C': ['Market Capitalization', dollar_format],
                    'D': ['Number of Shares to Buy', integer_format]
                    }

for column in column_formats.keys():
    writer.sheets['Recommended Trades'].set_column(f'{column}:{column}', 20, column_formats[column][1])
    writer.sheets['Recommended Trades'].write(f'{column}1', column_formats[column][0], string_format)

writer.save()
