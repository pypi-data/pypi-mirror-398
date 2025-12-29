import time

import transaction
from celery.utils.log import get_task_logger
from pyramid.security import forget, remember
from sqlalchemy.orm.exc import NoResultFound

JOB_RETRIEVE_ERROR = "We can't retrieve the job {jobid}, the task will not \
be run"
TASK_RETRIEVE_ERROR = "We can't retrieve the task {}, the task will not \
be run"


def get_logger(name=""):
    return get_task_logger("celery." + name)


logger = get_logger(__name__)


# we wait max TIMEOUT seconds before considering there was an error while
# inserting job in the database on main process side
TIMEOUT = 20
# Interval of "try again"
INTERVAL = 2


def get_job(celery_request, job_model, job_id):
    """
    Return the current executed job (in caerp's sens)

    :param obj celery_request: The current celery request object
    :param obj job_model: The Job model
    :param int job_id: The id of the job

    :returns: The current job
    :raises sqlalchemy.orm.exc.NoResultFound: If the job could not be found
    """
    logger.debug("Retrieving a job with id : {0}".format(job_id))
    from caerp.models.base import DBSESSION

    # We try to get tje job back, waiting for the current request to be
    # finished : since we use a transaction manager, the delay call launched in
    # a view is done before the job  element is commited to the bdd (at the end
    # of the request) if we query for the job too early, the session will not
    # be able to retrieve the newly created job
    current_time = 0
    job = None
    while current_time <= TIMEOUT and job is None:
        try:
            job = DBSESSION().query(job_model).filter(job_model.id == job_id).one()
            job.jobid = celery_request.id
            if job.status not in ("planned"):
                logger.error("Job has already been launched")
                job = None
        except NoResultFound:
            transaction.abort()
            transaction.begin()
            logger.debug(" -- No job found")
            logger.exception(JOB_RETRIEVE_ERROR.format(jobid=job_id))

        if job is None:
            time.sleep(INTERVAL)
            current_time += INTERVAL

    return job


def get_task(task_id: int) -> "Task":
    """
    Retrieve a task

    :param obj celery_request: The current celery request object
    :param int task_id: The id of the Task object

    :returns: The current Task
    :raises sqlalchemy.orm.exc.NoResultFound: If the Task could not be found
    """
    logger.debug("Retrieving a task with id : {0}".format(task_id))
    from caerp.models.base import DBSESSION
    from caerp.models.task import CancelInvoice, Invoice, Task

    # We retrieve a task back, we try several times waiting for it to be available
    # with its official_number (It should not be necessary anymore with task_tm that is
    # fired after the current web request and its underlying transaction are finished)
    current_time = 0
    task = None
    while current_time <= TIMEOUT and task is None:
        try:
            task = DBSESSION().query(Task).get(task_id)
            if task is not None and isinstance(task, (Invoice, CancelInvoice)):
                if task.official_number is None:
                    logger.error("Task has no number yet")
                    task = None
                    raise NoResultFound
        except NoResultFound:
            DBSESSION().close()
            transaction.abort()
            transaction.begin()
            logger.debug(" -- No Valid Task found")
            logger.exception(TASK_RETRIEVE_ERROR.format(task_id))

        if task is None:
            time.sleep(INTERVAL)
            current_time += INTERVAL
    logger.debug("Task {}".format(task))

    return task


def _record_running(job):
    """
    Record that a job is running
    """
    job.status = "running"
    from caerp.models.base import DBSESSION

    DBSESSION().merge(job)


def start_job(celery_request, job_model, job_id) -> None:
    """
    Entry point to launch when starting a job

    :param obj celery_request: The current celery request object
    :param obj job_model: The Job model
    :param int job_id: The id of the job

    :returns: The current job or None
    """
    logger.info(" Starting job %s %s" % (job_model, job_id))
    transaction.begin()
    try:
        job = get_job(celery_request, job_model, job_id)
        if job is not None:
            _record_running(job)
        else:
            raise Exception("No job found")
        transaction.commit()
    except:
        transaction.abort()
        raise Exception("Error while launching start_job")

    logger.info("Task marked as RUNNING")


def _record_job_status(job_model, job_id, status_str):
    """
    Record a status and return the job object
    """
    # We fetch the job again since we're in a new transaction
    from caerp.models.base import DBSESSION

    job = DBSESSION().query(job_model).filter(job_model.id == job_id).first()
    job.status = status_str
    return job


def record_failure(job_model, job_id, e=None, **kwargs):
    """
    Record a job's failure
    """
    transaction.begin()
    job = _record_job_status(job_model, job_id, "failed")
    # We append an error
    if hasattr(job, "error_messages") and e:
        job.error_messages = e

    for key, value in list(kwargs.items()):
        setattr(job, key, value)

    transaction.commit()
    logger.info("* Task marked as FAILED")


def record_completed(job_model, job_id, **kwargs):
    """
    Record job's completion and set additionnal arguments
    """
    transaction.begin()
    job = _record_job_status(job_model, job_id, "completed")
    for key, value in list(kwargs.items()):
        setattr(job, key, value)
    transaction.commit()
    logger.info("* Task marked as COMPLETED")


def check_alive():
    """
    Check the redis service is available
    """
    from pyramid_celery import celery_app
    from redis.exceptions import ConnectionError

    return_code = True
    return_msg = ""
    try:
        from celery.app.control import Inspect

        insp = Inspect(app=celery_app)

        stats = insp.stats()
        if not stats:
            return_code = False
            return_msg = (
                "Le service backend ne répond pas " "(Celery service not available)."
            )
    except (Exception, ConnectionError) as e:
        return_code = False
        return_msg = "Erreur de connextion au service backend (%s)." % e

    if return_code is False:
        return_msg += " Veuillez contacter un administrateur"

    return return_code, return_msg


def set_current_user(pyramid_request, user_id):
    """
    set a user on the current request
    """
    # De telle façon qu'on ait un request.identity
    from caerp.models.user import User

    forget(pyramid_request)
    login = User.get(user_id).login.login
    remember(pyramid_request, login)
