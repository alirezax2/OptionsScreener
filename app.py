import pandas as pd
import numpy as np
import os
import io
from datetime import datetime
from datetime import timedelta

import hvplot as hv
import holoviews as hvs
import panel as pn
import hvplot.pandas

import yfinance as yf

from datasets import load_dataset

pn.extension('bokeh', template='bootstrap')

def _extract_raw_data(ticker):
  df = yf.Ticker(ticker)
  return df.history(period="6mo", interval="1d").reset_index()

def _transform_data(raw_data: pd.DataFrame):
  data = raw_data[["Date", "Open", "High", "Low", "Close", "Volume"]].copy(deep=True).rename(columns={
      "Date": "time",
      "Open": "open",
      "High": "high",
      "Low": "low",
      "Close": "close",
      "Volume": "volume",
  })
  t_delta = timedelta(hours=1)
  data['time_start'] = data.time - 9*t_delta # rectangles start
  data['time_end'] = data.time + 9*t_delta    # rectangles end
  data['positive'] = ((data.close - data.open)>0).astype(int)
  return data

def make_candle_stick(ticker):
    raw_data = _extract_raw_data(ticker = ticker)
    data = _transform_data(raw_data=raw_data)
    _delta = np.median(np.diff(data.time))
    candlestick = hvs.Segments(data, kdims=['time', 'low', 'time', 'high']) * hvs.Rectangles(data, kdims=['time_start','open', 'time_end', 'close'], vdims=['positive'])
    candlestick = candlestick.redim.label(Low='Values')
    candlechart = pn.Column(candlestick.opts(hvs.opts.Rectangles(color='positive', cmap=['red', 'green'], responsive=True), hvs.opts.Segments(color='black', height=400, responsive=True , show_grid=True)) , 
                     data.hvplot(x="time", y="volume", kind="line", responsive=True, height=200).opts( show_grid=True) )
                    #  data.hvplot(y="volume", kind="bar", responsive=True, height=200) )
    return candlechart

# Function to convert DataFrame to CSV
def get_csv(df):
    sio = io.StringIO()
    df.to_csv(sio, index=False)
    sio.seek(0)
    return sio

# Function to convert the 'Ticker' column to a comma-separated string in a text file
def get_text(df):
    tickers = df['Ticker'].tolist()
    tickers_str = ','.join(tickers)
    sio = io.StringIO()
    sio.write(tickers_str)
    sio.seek(0)
    return sio

dataset = load_dataset('AmirTrader/optioncharts.io', data_files='DFtickerTotal.csv')
df = dataset['train'].to_pandas()

#widget
ticker = pn.widgets.AutocompleteInput(name='Ticker', options=list(df.Ticker) , placeholder='Write Ticker here همین جا',value='ALL', restrict=False)
Industry = pn.widgets.CheckBoxGroup( name='Select Industry', value=list(set(df.Industry)), options=list(set(df.Industry)), inline=True)
Sector = pn.widgets.CheckBoxGroup( name='Select Sector', value=list(set(df.Sector)), options=list(set(df.Sector)), inline=False)
MarketCap = pn.widgets.FloatSlider(name='Market Capital (B$)', start=0, end=4000, step=1, value=1)


def get_DF(DF,ticker, Sector,MarketCap):
  if ticker and ticker!="ALL":
    table1 = pn.widgets.Tabulator(DF.query("Ticker == @ticker"), height=200, widths=200, show_index=False)
    chart1 = make_candle_stick(ticker)
    return pn.Column(table1,chart1)
  else:
    # return pn.widgets.Tabulator( DF.query(" Sector in @Sector & MarketCap>@MarketCap"), height=800, widths=200, show_index=False)
    return pn.widgets.Tabulator( DF, height=800, widths=200, show_index=False)

pn.extension('tabulator')
bound_plot = pn.bind(get_DF, DF=df,ticker=ticker, Sector=Sector ,MarketCap=MarketCap)

pn.Column(pn.Row(pn.Column(ticker, MarketCap, Sector),bound_plot)).servable(title="Option Volatility View")

