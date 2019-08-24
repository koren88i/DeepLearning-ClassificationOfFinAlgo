# buy_flag = 0
#
# if len(a.loc[a == 2] != 0):
#     buy_flag = 1
#     buying_index = a.loc[a == 2].index[0]
#     tmp = allmonth_signals.iloc[-1]
#     start_date = tmp.index[buying_index]
#     type_sign = allmonth_signals.iloc[-1][start_date]
#     if allmonth_signals.iloc[-1].last_valid_index() == allmonth_signals.iloc[-1].name:
#         false_positive = 0
#         break_away = np.nan
#     else:
#         false_positive = 1
#         break_away = np.nan
#     all_signals.loc[start_date] = type_sign, start_date, false_positive, break_away
#
#     b = b[buying_index + 1:]
#     if len(b.loc[b == -1] != 0):
#         buy_flag = 0
#         selling_index = b.loc[b == -1].index[0]
#         tmp = allmonth_signals.iloc[-1]
#         sell_date = tmp.index[selling_index]
#         type_sign = allmonth_signals.iloc[-1][start_date] * (-1)
#         if allmonth_signals.iloc[-1].last_valid_index() == allmonth_signals.iloc[-1].name:
#             false_positive = 3
#             break_away = 0
#         else:
#             false_positive = 2
#             break_away = 1
#         all_signals.loc[sell_date] = type_sign, sell_date, false_positive, break_away
#
# if (allmonth_signals.iloc[-1].last_valid_index() == allmonth_signals.iloc[-1].name) & (buy_flag == 0):
#     start_date = allmonth_signals.iloc[-1].last_valid_index()
#     false_positive = 0
#     break_away = np.nan
#     type_sign = allmonth_signals.iloc[-1][start_date]
#     all_signals.loc[allmonth_signals.iloc[-1].name] = type_sign, start_date, false_positive, break_away




