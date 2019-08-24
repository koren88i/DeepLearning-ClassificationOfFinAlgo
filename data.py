from datetime import datetime

import pandas as pd


def get_sp500():
    return list(
        pd.read_excel("C:\\Users\\koren\\Documents\\Google Drive Update Folder\\Stocks\\geometric2month\\spy.xls",
                      skiprows=3)["Identifier"].values)

def get_russel3000():
    return list(
        pd.read_csv("C:\\Users\\koren\\Documents\\Google Drive Update Folder\\Stocks\\geometric2month\\russel3000.csv")["Ticker"].values)


def load_stocks_to_memory(stocks):
    path = "C:\\Users\\koren\\Documents\\Google Drive Update Folder\\Stocks\\stock data base\\updated1\\"
    print(datetime.now())
    stocks_data = {}
    for curr_stock in stocks:
        try:
            print(f"{curr_stock}")
            curr_stock_df = pd.read_csv(path + str(curr_stock) + ".csv", index_col="date")
            curr_stock_df.index = pd.to_datetime(curr_stock_df.index)
            stocks_data[curr_stock] = curr_stock_df
        except IOError:
            # # could not find stock in local data, fetching from intrinio
            # # and saving in local data
            print("{0} - Not in local - check your updater".format(curr_stock))
            continue
        except UnicodeDecodeError as e:
            print("{0} - unicode error".format(curr_stock))
            print(str(e))
    print(datetime.now())
    return stocks_data
