import threading

from pandas.tseries.offsets import BDay, BMonthEnd, Week

from data import get_sp500, load_stocks_to_memory, get_russel3000
from features import *
from signals import calculate_data, return_duration_strength, find_all_signals

pd.options.display.float_format = '{:.2f}'.format
pd.options.mode.chained_assignment = 'raise'
pd.options.display.max_rows = 999
pd.set_option('display.max_columns', None)
lock = threading.Lock()


def do_features(df, curr_signal_start_date, all_signals, stock, signal_index, signal_label):
    end_of_month = df.index[-1]
    # changing end of month for current day to actual current day

    curr_signal_month_data = df.rename({end_of_month: curr_signal_start_date})
    # TODO understand why signals have different length...
    # calculating the algorithm for current signal
    algo, signal, diff = calculate_data(curr_signal_month_data)
    # crafting the features
    curr_signal_only, curr_signal_features = create_signal_feature(algo, signal, diff, all_signals, stock,
                                                                   curr_signal_start_date, signal_index,
                                                                   signal_label)

    curr_signal_features.insert(0, 'raw_data', curr_signal_month_data)
    curr_signal_features = curr_signal_features.round(5)
    # curr_signal_features, NAlist = reduce_mem_usage(curr_signal_features)
    # print("_________________")
    # print("")
    # print("Warning: the following columns have missing values filled with 'df['column_name'].min() -1': ")
    # print("_________________")
    # print("")
    # print(NAlist)

    return curr_signal_only, curr_signal_features


def digest_stocks_features(stock_lst, start_index, finish_index):
    for stock in stock_lst[start_index:finish_index + 1]:
        print("working on {}".format(stock))

        stock_data_df = stocks_data_dict[stock]
        all_signals = dict_of_stocks_fp[dict_of_stocks_fp.symbol == stock]
        # TODO add counter and progress bar or percentage ( curr / len of signals) # TODO per stock per all stocks
        curr_stock_signals_features = pd.DataFrame()
        for signal_index, row in enumerate(all_signals.iterrows()):
            curr_signal_start_date = pd.to_datetime(row[1].start_date)
            signal_label = row[1].false_positive

            curr_signal_month_data = stock_data_df["adj_close"][stock_data_df.index <= curr_signal_start_date].resample(
                "BM").last().interpolate()
            curr_signal_month_data = curr_signal_month_data[
                curr_signal_month_data.index >= curr_signal_start_date - BMonthEnd(100)]

            curr_signal_week_data = stock_data_df["adj_close"][stock_data_df.index <= curr_signal_start_date].resample(
                "W").last().interpolate()
            curr_signal_week_data = curr_signal_week_data[
                curr_signal_week_data.index >= curr_signal_start_date - Week(100)]

            curr_signal_day_data = stock_data_df["adj_close"][stock_data_df.index <= curr_signal_start_date].resample(
                "B").last().interpolate()
            curr_signal_day_data = curr_signal_day_data[
                curr_signal_day_data.index >= curr_signal_start_date - BDay(100)]

            curr_signal_only, curr_signal_features_month = do_features(curr_signal_month_data, curr_signal_start_date,
                                                                       all_signals, stock, signal_index, signal_label
                                                                       )
            curr_signal_only, curr_signal_features_week = do_features(curr_signal_week_data, curr_signal_start_date,
                                                                      all_signals, stock, signal_index, signal_label
                                                                      )
            curr_signal_only, curr_signal_features_day = do_features(curr_signal_day_data, curr_signal_start_date,
                                                                     all_signals, stock, signal_index, signal_label
                                                                     )

            timestamps_features_month[str(stock) + "_" + str(signal_index)] = curr_signal_features_month
            timestamps_features_week[str(stock) + "_" + str(signal_index)] = curr_signal_features_week
            timestamps_features_day[str(stock) + "_" + str(signal_index)] = curr_signal_features_day

            # adding to df of current stock
            curr_stock_signals_features = pd.concat([curr_stock_signals_features, curr_signal_only])

        # disregard the date index
        # still saving it for train/test separations (e.g. learn until 2010 and test afterwards)
        curr_stock_signals_features = curr_stock_signals_features.reset_index()

        with lock:
            # add to the list of all signals of all stocks
            print("finished {}".format(stock))
            all_stocks_signals_features[stock] = curr_stock_signals_features

    print("finished stocks features")


def digest_stocks_signals(stock_lst, start_index, finish_index):
    for stock in stock_lst[start_index:finish_index + 1]:
        print("working on {}".format(stock))
        stock_data_df = stocks_data_dict[stock]

        all_signals = find_all_signals(stock_data_df[["adj_close"]], plot_flag=None, start=None, end=None)
        if len(all_signals) == 0:
            print("No signals for {}".format(stock))
            continue

        all_signals["symbol"] = stock
        all_signals['type_str'] = all_signals.type_sign.apply(lambda x: 'Long' if x == 1 else 'Short')
        if len(all_signals) == 1:
            all_signals["T_strength"] = 0
        else:
            all_signals = return_duration_strength(all_signals)

        dict_of_stocks_fp[stock] = all_signals

    print("finished stocks signals")


def dict_to_dataframe(dict, output_name, cols=None):
    if cols is None:
        cols = next(iter(dict.values())).columns
    frames = []
    for stock in dict:
        df = dict[stock][cols]
        frames.append(df)
    final = pd.concat(frames)
    final.to_csv(output_name + ".csv")


do_signals_flag = 0
do_features_flag = 1

STOCKS_TO_DO = 40  # more than that I get memory error

SP500 = get_sp500()
russel3000 = get_russel3000()

stocks_data_dict = load_stocks_to_memory(russel3000[0:])  # limit this if you want to check something
keys = list(stocks_data_dict.keys())

if do_signals_flag == 1:
    dict_of_stocks_fp = {}
    digest_stocks_signals(keys, 0, len(keys))
    signals_cols = ["symbol", 'type_sign', 'type_str', 'false_positive', 'break_away', 'start_date', 'T_strength']
    dict_to_dataframe(dict_of_stocks_fp, "signals", cols=signals_cols)

for i in range(0, 100):  # TODO needs to be 100
    if do_features_flag == 1:
        timestamps_features_month = {}
        timestamps_features_week = {}
        timestamps_features_day = {}

        all_stocks_signals_features = {}
        dict_of_stocks_fp = pd.read_csv("signals.csv", index_col=0, parse_dates=['start_date'])
        digest_stocks_features(keys, i * STOCKS_TO_DO, (i + 1) * STOCKS_TO_DO)
        dict_to_dataframe(timestamps_features_month, "timestamps_features_month" + str(i))
        dict_to_dataframe(timestamps_features_week, "timestamps_features_week" + str(i))
        dict_to_dataframe(timestamps_features_day, "timestamps_features_day" + str(i))

        # dict_to_dataframe(all_signals_features, "features")
