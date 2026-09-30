import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.tasks import check_and_send_expiring_alerts

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        # Run every day at 10:00 AM
        scheduler.add_job(
            check_and_send_expiring_alerts,
            CronTrigger(hour=10, minute=0),
            id='daily_expiry_alerts',
            replace_existing=True
        )
        # Also run it once immediately on startup for testing/demo purposes
        scheduler.add_job(check_and_send_expiring_alerts, 'date')
        
        scheduler.start()
        logger.info("✅ Background scheduler started")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Background scheduler stopped")
