import datetime

from sqlalchemy import delete

from caerp.celery.conf import get_request
from caerp.celery.transactional_task import task_tm
from caerp.models.user.login import UserConnections


@task_tm
def clean_old_user_connections_task():
    now = datetime.datetime.now()
    purge_datetime = now - datetime.timedelta(days=365)
    query = delete(UserConnections).where(
        UserConnections.month_last_connection < purge_datetime,
    )
    request = get_request()
    request.dbsession.execute(query)
