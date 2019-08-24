import threading

from data import get_sp500, load_stocks_to_memory
from digestors import digest_stocks_signals


def main(all_stocks):
    offset = 1
    multiply = 26
    num_of_threads = 8

    threads = []

    for i in range(0, num_of_threads):
        # TODO convert to processes and not threads
        # choose digest function to parallel
        t = threading.Thread(target=digest_stocks_signals, args=(all_stocks, i * multiply, i * multiply + offset))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    print("here")


SP500 = get_sp500()
stocks_data_dict = load_stocks_to_memory(SP500[0:10])
main(SP500)
