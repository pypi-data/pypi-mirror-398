import time


class print_time:
    def __init__(self, obj=None, enter_msg=None, exit_msg=None):
        self.enter_msg = enter_msg if obj is None else "Starting to {}".format(obj)
        self.exit_msg = exit_msg if obj is None else "Successfully {}!".format(obj)

    def __enter__(self):
        print("\n" + self.enter_msg, flush=True)
        self.time = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        tot = time.time() - self.time
        if tot >= 60:
            res = '{} minutes and {} seconds'.format(int(int(tot) / 60), int(tot) % 60)
        else:
            res = '{} seconds'.format(int(tot))
        print(self.exit_msg, res + "\n", flush=True)
