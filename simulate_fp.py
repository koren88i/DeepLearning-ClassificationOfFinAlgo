import calendar

import matplotlib.pyplot as plt
import pandas as pd

from data import load_stocks_to_memory
from signals import find_all_signals, find_false_positives, calc_algo_signal


def simulate_false_positives(stock, compute_stock_signals_with_fp=True, compue_all_signals=True):
    stock_data_df = load_stocks_to_memory([stock])[stock]

    if compue_all_signals:
        all_signals = find_all_signals(stock_data_df, plot_flag=None)

    if compute_stock_signals_with_fp:
        stock_signals_with_fp = find_false_positives(all_signals)
    else:
        dict_of_stocks_fp = pd.read_csv("signals.csv", index_col=0, parse_dates=['start_date'])
        stock_signals_with_fp = dict_of_stocks_fp[dict_of_stocks_fp.symbol == stock]

    fp_months = stock_signals_with_fp[stock_signals_with_fp.false_positive == 1].index
    for fp in fp_months:
        fp = pd.to_datetime(fp)
        # extracting the month and year of each false positive
        year = fp.year
        month = fp.month
        start_day = 1
        # craeting the range of all days in that signal month
        num_days = calendar.monthrange(year, month)[1]
        end_day = start_day + num_days - 1
        # need to take only business days
        start_date = pd.to_datetime({'year': [fp.year], 'month': [fp.month], 'day': [start_day]})[0]
        end_date = pd.to_datetime({'year': [fp.year], 'month': [fp.month], 'day': [end_day]})[0]
        days = pd.date_range(start_date, end_date, freq='B')

        # grid for plots
        # %matplotlib inline
        fig = plt.figure()
        fig.subplots_adjust(hspace=0.4, wspace=0.4)
        print("False Positive in month {0}".format(fp))
        for idx, day in enumerate(days):
            day = pd.to_datetime(day)
            curr_day_data = stock_data_df[stock_data_df.index <= day]
            # this was an attempt to make function faster.. but created a lot of false data
            # curr_day_data = curr_day_data[curr_day_data.index >= (day - timedelta(365*2+90))]

            # creating monthly data for signal calculations
            curr_day_monthly_adjusted = curr_day_data["adj_close"].resample("BM").last()

            # changing end of month for current day to actual current day
            end_of_month = curr_day_monthly_adjusted.index[-1]
            curr_day_monthly_adjusted = curr_day_monthly_adjusted.rename({end_of_month: day})

            # plot intra month values to validate false positives
            fig.add_subplot(4, 6, idx + 1)
            algo, signal = calc_algo_signal(curr_day_monthly_adjusted)
            plt.title(day.date())
            algo[-5::].plot(figsize=(40, 40))
            signal[-5::].plot(figsize=(40, 40))
            plt.xlabel('')
        fig.savefig(str(fp)[0:10] + '.png')
        fig.clf()
        fig.clear()
        plt.close("all")
        # fig.show()


simulate_false_positives("MSFT", False, False)
