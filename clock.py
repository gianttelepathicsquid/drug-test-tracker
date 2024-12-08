from apscheduler.schedulers.blocking import BlockingScheduler
from app import send_notifications

scheduler = BlockingScheduler()
scheduler.add_job(func=send_notifications, trigger="cron", hour=9)  # Run daily at 9 AM

scheduler.start()

---
