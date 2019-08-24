import calendar

import matplotlib.pyplot as plt
import pandas as pd

from data import load_stocks_to_memory
from signals import find_all_signals, find_false_positives, calc_algo_signal


def simulate_false_positives(stock, stock_signals_with_fp=None, all_signals=None):
    stock_data_df = load_stocks_to_memory([stock])[stock]

    if all_signals is None:
        all_signals = find_all_signals(stock_data_df, plot_flag=None)

    if stock_signals_with_fp is None:
        stock_signals_with_fp = find_false_positives(all_signals)

    fp_months = stock_signals_with_fp[stock_signals_with_fp.FP == 1].index
    for fp in fp_months:

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
        fig = plt.figure(figsize=(40, 40))
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
            ax = fig.add_subplot(8, 4, idx + 1)
            algo, signal = calc_algo_signal(curr_day_monthly_adjusted)
            # plt.title(curr_day_monthly_adjusted.index[-1])
            algo[-5::].plot(figsize=(20, 40))
            signal[-5::].plot()
            # plt.xlabel('')

        fig.show()


simulate_false_positives("MSFT")
