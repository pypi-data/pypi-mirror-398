from datetime import date, timedelta

from celery import shared_task
from wbcore.workers import Queue

from wbnews.models import News


@shared_task(queue=Queue.BACKGROUND.value)
def handle_daily_news_duplicates(
    task_date: date | None = None,
    day_interval: int = 7,
):
    if not task_date:
        task_date = date.today()

    News.handle_duplicates(task_date - timedelta(days=day_interval), task_date + timedelta(days=day_interval))
