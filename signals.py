from datetime import datetime

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta


def calculate_data(monthly_adjusted):
    fast = 12
    slow = 26
    fastma = monthly_adjusted.ewm(ignore_na=False, span=fast, min_periods=0, adjust=True).mean()
    slowma = monthly_adjusted.ewm(ignore_na=False, span=slow, min_periods=0, adjust=True).mean()
    algo = fastma.subtract(slowma)
    signal = algo.rolling(window=9).mean()
    diff = algo.subtract(signal).dropna()
    return algo, signal, diff


def find_false_positives(all_signals):
    # the difference between signals that lasted untill month end
    # and those who did not are the FP
    # the fp would be those that the "last" value in the column "start date" is different
    # from the index value (which is end of month)
    start_last_compare = all_signals.drop_duplicates().resample("BM").last().dropna(subset=["start_date"])
    false_positives_idx = start_last_compare[start_last_compare.index != start_last_compare.start_date].index

    # now that I have the FP i want to take to true start date
    # this is to take to first date in the month that got a signal
    signals_true_start = all_signals.drop_duplicates().resample("BM").first().dropna(subset=["start_date"])
    signals_true_start.at[false_positives_idx, 'FP'] = 1

    # to do
    # some signals cross over, than go back, than cross over again.. this is not handleled here
    # thought - maybe it is not relevant because we would have bought and waited for end of month
    return signals_true_start


def return_duration_strength(df):
    # TODO this is simple duration.. need to do duration from last valid signal
    df["T_strength"] = df.start_date - df.start_date.shift(1)

    return df


def get_end_dates(stock_signals_with_fp):
    # fp_idx = stock_signals_with_fp[stock_signals_with_fp.false_positive == 1].index
    # tp_idx = stock_signals_with_fp[stock_signals_with_fp.false_positive != 1].index
    #
    # # init the column
    # stock_signals_with_fp["end_date"] = 0
    # #     stock_signals_with_fp['end_date'] = pd.to_datetime(stock_signals_with_fp['end_date'])
    # # fix duration of FP to be end of month end date
    # offset = BMonthEnd()
    # stock_signals_with_fp.at[fp_idx, "end_date"] = pd.to_datetime(
    #     [offset.rollforward(start_date) for start_date in fp_idx])
    # #     pd.to_datetime([pd.to_datetime(str(pd.to_datetime(start_date).daysinmonth)+"-"+str(pd.to_datetime(start_date).month)+"-"+str(pd.to_datetime(start_date).year), dayfirst=True) for start_date in fp_idx], dayfirst=True)
    #
    # # set true positives end to be start of next true signal
    # tp_start_date_values = stock_signals_with_fp["start_date"].loc[tp_idx].shift(-1).values
    # tp_start_date_values = pd.to_datetime(tp_start_date_values, dayfirst=True)
    # stock_signals_with_fp.at[tp_idx, "end_date"] = tp_start_date_values
    #
    # # in order to add end date for last signal
    # current_position_end_date = datetime.datetime.today().date()
    # stock_signals_with_fp.at[tp_idx[-1], "end_date"] = pd.to_datetime(current_position_end_date)

    tp_idx = stock_signals_with_fp[stock_signals_with_fp.false_positive != 1].index
    stock_signals_with_fp["end_date"] = stock_signals_with_fp["start_date"].shift(-1)
    # in order to add end date for last signal
    current_position_end_date = datetime.today().date()
    stock_signals_with_fp.at[tp_idx[-1], "end_date"] = pd.to_datetime(current_position_end_date)
    return stock_signals_with_fp


def get_start_end_values(stock_signals, stock_data_df):
    start_values_idx = pd.to_datetime(stock_signals.start_date.values)
    start_values = stock_data_df["adj_close"].loc[start_values_idx]

    end_values_idx = pd.to_datetime(stock_signals.end_date.values)
    end_values = stock_data_df["adj_close"].loc[end_values_idx]

    stock_signals["start_values"] = start_values.values
    stock_signals["end_values"] = end_values.values

    # get current stock value for current position end value
    # fixing the last value of the true signal, not the false positive signal
    tp_idx = stock_signals[stock_signals.false_positive != 1].index
    # lats value in local data base
    most_current_value = stock_data_df["adj_close"].iloc[-1]
    stock_signals.at[tp_idx[-1], "end_values"] = most_current_value

    end_dates_nans_indx = stock_signals[stock_signals.end_values.isnull()].index
    if len(end_dates_nans_indx) != 0:
        end_dates_nans = [stock_signals.end_date.loc[indx] for indx in
                          stock_signals.end_values[stock_signals.end_values.isnull()].index]
        end_dates_nearest_values_indx = [stock_data_df.index.get_loc(indx, method='nearest') for indx in end_dates_nans]
        end_dates_nearest_values = stock_data_df.iloc[end_dates_nearest_values_indx]["adj_close"]
        print("Missing end value in {}".format(end_dates_nans_indx))
        stock_signals.loc[end_dates_nans_indx, "end_values"] = end_dates_nearest_values.values

    start_dates_nans_indx = stock_signals[stock_signals.start_values.isnull()].index
    if len(start_dates_nans_indx) != 0:
        start_dates_nans = [stock_signals.start_date.loc[indx] for indx in
                            stock_signals.start_values[stock_signals.start_values.isnull()].index]
        start_dates_nearest_values_indx = [stock_data_df.index.get_loc(indx, method='nearest') for indx in
                                           start_dates_nans]
        start_dates_nearest_values = stock_data_df.iloc[start_dates_nearest_values_indx]["adj_close"]
        print("Missing start value in {}".format(start_dates_nans_indx))
        stock_signals.loc[start_dates_nans_indx, "start_values"] = start_dates_nearest_values.values

    return stock_signals


def vectorized_signals(col):
    results_list = col
    results_list2 = results_list.shift(1)
    signals = (results_list * results_list2)
    df_signals = (signals[signals < 0] * results_list2).apply(np.sign).dropna().to_frame()
    df_signals.columns = ['type_sign']
    return df_signals['type_sign']


def vectorized_diff(col):
    fast = 12
    slow = 26
    fastma = col.ewm(ignore_na=False, span=fast, min_periods=0, adjust=True).mean()
    slowma = col.ewm(ignore_na=False, span=slow, min_periods=0, adjust=True).mean()
    algo = fastma.subtract(slowma)
    signal = algo.rolling(window=9).mean()
    diff = algo.subtract(signal).dropna()
    return diff


def calc_algo_signal(monthly_adjusted):
    fast = 12
    slow = 26
    fastma = monthly_adjusted.ewm(ignore_na=False, span=fast, min_periods=0, adjust=True).mean()
    slowma = monthly_adjusted.ewm(ignore_na=False, span=slow, min_periods=0, adjust=True).mean()
    algo = fastma.subtract(slowma)
    signal = algo.rolling(window=9).mean()
    # diff = algo.subtract(signal).dropna()
    # plot diff
    # plt.figure()
    # ax = diff.plot(figsize=(20,20))
    # ax.axhline(y=0, color='r', linestyle='--', lw=2)
    # plt.show()
    return algo, signal


#     plt.figure()
#     plt.title(monthly_adjusted.index[-1])
#     algo[-5::].plot(figsize=(5,5))
#     signal[-5::].plot()
#     plt.show()


def find_all_signals(df, plot_flag=None, start=None, end=None):
    # TODO check only month with real signals +- some window
    start = df.iloc[0].name + relativedelta(months=0)
    end = df.iloc[-1].name
    # end =start + relativedelta(months= 20)

    start = pd.to_datetime(start)
    end = pd.to_datetime(end)

    all_signals = pd.DataFrame(columns=["type_sign", "start_date", "false_positive", "break_away"])
    # TODO vectorized this
    for month in pd.date_range(start, end, freq="BM"):
        curr_year = month.year
        curr_month = month.month
        df_year = df[df.index.year == curr_year]
        df_month = df_year[df_year.index.month == curr_month]
        cols = df_month.transpose().columns
        # vals = df_month.transpose().values
        vals = df_month.transpose().iloc[0].values

        last_date = "1-" + str(curr_month) + "-" + str(curr_year)
        last_date = pd.to_datetime(last_date, dayfirst=True)
        curr_month_df = df[df.index < last_date]

        curr_month_df = curr_month_df["adj_close"].resample("BM").last()
        try:
            days_df = pd.concat([curr_month_df] * len(cols), axis=1)
        except ValueError:
            continue
        days_df.columns = cols
        days_df.loc[cols[-1]] = vals

        diff = days_df.apply(vectorized_diff, axis=0)
        all_month_signals = diff.apply(vectorized_signals, axis=0)
        all_month_signals = all_month_signals[
            (all_month_signals.index.year == curr_year) & (all_month_signals.index.month == curr_month)]

        if len(all_month_signals) == 0:
            continue
        else:
            a = all_month_signals.iloc[-1]
            a = np.sign(np.abs(a))
            a = a.reset_index(drop=True)
            a = a * (a.groupby((a != a.shift()).cumsum()).cumcount() + 1)

            BUY_RULE = 1
            if len(a.loc[a == BUY_RULE] != 0):  # because sometimes I want to but after X days of signals
                buying_index = a.loc[a == 1].index[0]
                tmp = all_month_signals.iloc[-1]
                start_date = pd.to_datetime(tmp.index[buying_index])
                type_sign = all_month_signals.iloc[-1][start_date]
                if all_month_signals.iloc[-1].last_valid_index() == all_month_signals.iloc[-1].name:
                    false_positive = 0
                    break_away = np.nan
                else:
                    false_positive = 1
                    break_away = np.nan
                all_signals.loc[start_date] = type_sign, start_date, false_positive, break_away

        if plot_flag:
            pass
            # plot_intra_month(curr_day_monthly_adjusted)

    return all_signals
