import os
import sys
import schedule
import time
import threading
from django.conf import settings
from .services import GlobalSystemLogAdd

app_scheduler = schedule.Scheduler()

def run_scheduler():
    while True:
        app_scheduler.run_pending()
        time.sleep(1)

def start_scheduler():
    if (not 'manage.py' in sys.argv[0] and not settings.DEBUG) or ('runserver' in sys.argv and os.environ.get('RUN_MAIN')):
        app_scheduler.clear()

        app_scheduler.every().hour.do(GlobalSystemLogAdd.clear_hourly)
        app_scheduler.every(1).minutes.do(GlobalSystemLogAdd.clear_every_minute)

        scheduler_thread = threading.Thread(target=run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()