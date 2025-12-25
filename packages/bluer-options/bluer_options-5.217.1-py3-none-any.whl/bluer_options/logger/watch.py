import time

from bluer_options.env import bluer_ai_log_filename


def watch(seconds: int = 1) -> bool:
    try:
        with open(bluer_ai_log_filename, "r") as f:
            f.seek(0, 2)  # jump to end of file
            while True:
                line = f.readline()
                if not line:
                    time.sleep(seconds)
                    continue
                print(line, end="")
    except KeyboardInterrupt:
        print("\n^C received.")

    return True
