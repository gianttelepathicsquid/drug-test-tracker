from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from drug_test_tracker import DrugTestTracker, create_zapier_payload
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def send_notifications():
    tracker = DrugTestTracker('data/drug_tests_2024.csv')
    notifications = tracker.get_notifications()
    payload = create_zapier_payload(notifications)
    
    webhook_url = os.getenv('ZAPIER_WEBHOOK_URL')
    if webhook_url:
        requests.post(webhook_url, json=payload)

scheduler = BackgroundScheduler()
scheduler.add_job(func=send_notifications, trigger="cron", hour=9)  # Run daily at 9 AM
scheduler.start()

@app.route('/')
def home():
    return 'Drug Test Tracker is running!'

if __name__ == '__main__':
    app.run()

---
