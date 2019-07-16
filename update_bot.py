from reestr_data import reestr_update
import schedule
import time


if __name__ == "__main__":
    schedule.every().monday.at("18:20").do(reestr_update)
    while True:
        schedule.run_pending()
        time.sleep(60)
    # reestr_update()
    