import datetime
import logging

import transaction
from pyramid_celery import celery_app

from caerp.celery.conf import get_request
from caerp.models.notification import NotificationEvent
from caerp.utils.notification import clean_notifications, publish_event

logger = logging.getLogger(__name__)


@celery_app.task
def publish_pending_notifications_task():
    try:
        request = get_request()
        now = datetime.datetime.now()
        events = NotificationEvent.query().filter(
            NotificationEvent.due_datetime <= now,
            NotificationEvent.published == False,  # noqa:E712
        )
        for event in events:
            if event.is_valid(request):
                publish_event(request, event)
            else:
                request.dbsession.delete(event)
        transaction.commit()
    except Exception:
        logger.exception("Erreur dans publish_pending_notifications_task")
        transaction.abort()


@celery_app.task
def clean_notifications_task():
    """
    Clean notifications in case

    - Notification Event is outdated, conditions are not met anymore
    (e.g : contractor has left)

    - All Notifications have been read
    """
    try:
        request = get_request()
        clean_notifications(request)
        transaction.commit()
    except Exception:
        logger.exception("Erreur dans clean_notification_task")
        transaction.abort()
