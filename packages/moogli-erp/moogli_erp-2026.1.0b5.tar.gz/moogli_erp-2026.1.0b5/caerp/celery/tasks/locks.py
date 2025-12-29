from caerp.celery.locks import release_lock
from caerp.celery.tasks import utils
from caerp.celery.transactional_task import task_tm

logger = utils.get_logger(__name__)


@task_tm
def release_lock_after_commit(lockname):
    """Delay the release of a lock after a commited transaction (used for numbering)"""
    logger.debug("Releasing lock {}".format(lockname))
    release_lock(lockname)
