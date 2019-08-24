from math import atan2, degrees
from math import sqrt

import numpy as np
import pandas as pd


def get_angle_of_line_between_to_points(p1_y, p2_y):
    xDiff = 2 - 1
    yDiff = p2_y - p1_y
    return degrees(atan2(yDiff, xDiff))


def create_distance_and_growth(df_orig):
    df = df_orig[['prev_algo', 'algo', 'prev_signal', 'signal']].copy().reset_index()
    df.dropna(inplace=True)
    df.set_index('date', inplace=True)
    # changing names for semantic understanding
    df = df.rename(columns={'prev_algo': 'line1_y1', 'algo': 'line1_y2', 'prev_signal': 'line2_y1', 'signal': 'line2_y2'})    #     redundant columns for later use in apply func
    df['line1_x2'] = 2
    df['line2_x2'] = 2

    # calc the initial distance between the points in the original lines
    dist_points_line1 = df[['line1_y1', 'line1_x2', 'line1_y2']].apply(lambda x: get_dist1(*x), axis=1)
    dist_points_line2 = df[['line2_y1', 'line2_x2', 'line2_y2']].apply(lambda x: get_dist1(*x), axis=1)

    # calc intersection points between the two lines
    intersection_point = df[['line1_y1', 'line1_y2', 'line2_y1', 'line2_y2']].apply(lambda x: get_intersect(*x),
                                                                                    axis=1)
    # splitting the tuple into two different columns
    df[['inter_point_x', 'inter_point_y']] = intersection_point.apply(pd.Series)

    # calc distance from the point to each line
    dist_from_line1 = df[['line1_y2', 'inter_point_x', 'inter_point_y']].apply(lambda x: get_dist2(*x), axis=1)
    dist_from_line2 = df[['line2_y2', 'inter_point_x', 'inter_point_y']].apply(lambda x: get_dist2(*x), axis=1)

    df.insert(len(df.columns), 'dist_from_line1', dist_from_line1.values)
    df.insert(len(df.columns), 'dist_from_line2', dist_from_line2.values)

    # calculating how much does a line need to grow inorder to "hit" the intersection point
    df['line1_growth'] = dist_from_line1 / dist_points_line1
    df['line2_growth'] = dist_from_line2 / dist_points_line2

    df['dist_points_line1'] = dist_points_line1
    df['dist_points_line2'] = dist_points_line2

    # visual is for debugging, learning is for the ML model
    visual_cols = ['line1_y1', 'line1_y2', 'line2_y1,' 'line2_y2', 'inter_point_x',
                   'inter_point_y', 'dist_from_line1', 'dist_from_line2', 'line1_growth']
    learning_cols = ['dist_from_line1', 'dist_from_line2', 'line1_growth']
    # return df1[learning_cols]

    return df[["dist_from_line1", 'dist_from_line2', 'line1_growth']]


def create_up_or_down(diff, stock):
    df = pd.DataFrame(diff)

    df.columns = ['diff']

    # subsequence of asc dec numbers and some threshold
    previous = df['diff'].shift(1)
    df.insert(0, 'previous', previous)
    df.insert(0, 'symbol', stock)

    df["diff_sign"] = df['diff'].apply(np.sign)
    # dfdf=dfdf.dropna()
    df['delta_previous'] = df['diff'] - df['previous']
    df['up_or_down'] = df['delta_previous'].apply(np.sign)
    # TODO
    # think if i need to go to zero once there is a signal (change in sign of diff...)
    # or continue the count as usual (still momentum is momentum)
    y = df.up_or_down
    y = y * (y.groupby((y != y.shift()).cumsum()).cumcount() + 1)

    return y


def create_signals(algo, signal):
    df = pd.DataFrame()
    df['diff'] = algo - signal
    results_list = df['diff']
    results_list2 = results_list.shift(1)
    signals = (results_list * results_list2)
    signals = (signals[signals < 0] * results_list2).apply(np.sign)
    return signals


def create_signal_feature(algo, signal, diff, stock_signals_with_fp, stock, curr_signal_date, signal_index,
                          signal_label):
    df = pd.DataFrame(diff)

    df['num_of_ups_downs'] = create_up_or_down(diff, stock)

    df.insert(len(df.columns), 'algo', algo)
    prev_algo = df['algo'].shift(1)
    df.insert(len(df.columns) - 1, 'prev_algo', prev_algo)
    df['signal'] = signal
    prev_signal = df['signal'].shift(1)
    df.insert(len(df.columns) - 1, 'prev_signal', prev_signal)

    # df['signals'] = create_signals(algo, signal)

    df['algo_slope'] = (df['algo'] - df['prev_algo']) / (2 - 1)
    df['algo_b'] = -1 * df['algo_slope'] + df['algo']
    df['signal_slope'] = (df['signal'] - df['prev_signal']) / (2 - 1)
    df['signal_b'] = -1 * df['signal_slope'] + df['signal']

    df['distance'] = abs(df['algo'] - df['signal'])

    # get angle of the two lines
    # *(-1) to get the direction right
    df['angle_algo'] = df[['prev_algo', 'algo']].apply(lambda x: get_angle_of_line_between_to_points(*x), axis=1) * (-1)
    df['angle_signal'] = df[['prev_signal', 'signal']].apply(lambda x: get_angle_of_line_between_to_points(*x),
                                                             axis=1) * (-1)
    df['symbol'] = stock + "_" + str(signal_index)
    df['angle_between'] = df['angle_algo'] - df['angle_signal']
    df['label'] = signal_label
    # deal with nan values
    df = df.fillna(value=0)
    # make both types of signals as "1" result
    # df.signals.replace(to_replace=-1, value=1.00, inplace=True)

    features = ['algo', 'signal', 'algo_slope', 'algo_b', 'signal_slope', 'signal_b', 'symbol', "angle_between",
                'distance', 'num_of_ups_downs', 'label']
    curr_signal_features = df[features]

    # TODO check those features
    intersection_features = create_distance_and_growth(df)
    curr_signal_features = curr_signal_features.join([intersection_features], how='outer', sort=True)

    curr_signal_only = curr_signal_features.iloc[-1::].copy()

    # TODO think about those features, are they relevant?
    fp_value = stock_signals_with_fp[stock_signals_with_fp.start_date == curr_signal_date].false_positive
    t_strength_value = stock_signals_with_fp[stock_signals_with_fp.start_date == curr_signal_date].T_strength
    curr_signal_only["fp"] = fp_value[0]
    curr_signal_only["t_strength"] = t_strength_value[0]

    return curr_signal_only, curr_signal_features


def get_intersect(a1, a2, b1, b2):
    # parse my data to fit this function
    a1 = [1, a1]
    a2 = [2, a2]
    b1 = [1, b1]
    b2 = [2, b2]
    """ 
    Returns the point of intersection of the lines passing through a2,a1 and b2,b1.
    a1: [x, y] a point on the first line
    a2: [x, y] another point on the first line
    b1: [x, y] a point on the second line
    b2: [x, y] another point on the second line
    """
    s = np.vstack([a1, a2, b1, b2])  # s for stacked
    h = np.hstack((s, np.ones((4, 1))))  # h for homogeneous
    l1 = np.cross(h[0], h[1])  # get first line
    l2 = np.cross(h[2], h[3])  # get second line
    x, y, z = np.cross(l1, l2)  # point of intersection
    if z == 0:  # lines are parallel
        return (float('inf'), float('inf'))
    return (x / z, y / z)


# if __name__ == "__main__":
#     print get_intersect((0, 1), (0, 2), (1, 10), (1, 9))  # parallel  lines
#     print get_intersect((0, 1), (0, 2), (1, 10), (2, 10)) # vertical and horizontal lines
#     print get_intersect((1, -3.69), (2, -2.78), (1, -1.95), (2, -1.54))  # another line for fun


def get_dist2(y1, x2, y2):
    x1 = 2
    dist = sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return dist


def get_dist1(y1, x2, y2):
    x1 = 1
    dist = sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return dist
