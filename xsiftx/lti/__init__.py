"""
This is a simple LTI interface application/blueprint
for flask that allows user's to run a sifter from
inside their courseware (if authorized)
"""
# pylint: disable=C0103
import os
import shlex
import time

from celery import Celery
from flask import (
    Blueprint,
    render_template,
    session,
    request,
    jsonify,
    make_response,
)

from .decorators import lti_authentication, lti_staff_required
from .util import (
    InvalidAPIUsage,
    LTIException,
    LTIRoleException,
    get_allowed_sifters
)
from xsiftx.config import settings, get_consumer, VENV, EDX_PLATFORM
from xsiftx.util import (
    XsiftxException,
    SifterException,
    run_sifter
)


API_VERSION = 'v0.1'

JOB_CLEAR_STATUSES = ['SUCCESS', 'FAILURE', 'REVOKED', 'SIFTER_FAILURE', ]


# Define our app as a blueprint
xsiftx_lti = Blueprint(
    'xsiftx_lti',
    __name__,
    template_folder='templates/lti',
    static_folder='static/lti',
)


celery = Celery(
    'xsiftx_lti',
    broker=settings.get(
        'CELERY_BROKER_URL',
        'amqp://guest:guest@127.0.0.1:5672/'
    ),
    backend=settings.get(
        'CELERY_RESULT_BACKEND', 'amqp'
    )
)
celery.conf.update(settings)


@xsiftx_lti.route('/', methods=['GET', 'POST'])
@lti_authentication
@lti_staff_required
def index():
    """
    Show the xsift interface page
    """
    consumer = get_consumer(session['oauth_consumer_key'])
    sifters = get_allowed_sifters(consumer)

    return render_template(
        'index.html',
        sifters=sifters,
    )


@xsiftx_lti.route('/api/{0}/run'.format(API_VERSION), methods=['POST'])
@lti_authentication
def run():
    """
    Runs a given sifter for the course in the LTI component.
    """
    sifter_name = request.form.get('sifter', None)
    if not sifter_name:
        raise InvalidAPIUsage(
            'This api call requires the parameter "sifter".'
        )
    consumer = get_consumer(session['oauth_consumer_key'])
    sifters = get_allowed_sifters(consumer, True)
    sifter = sifters.get(sifter_name, None)
    if not sifter:
        raise InvalidAPIUsage(
            'You have specified an invalid sifter.',
            400,
            {'available_sifters': sifters}
        )

    course = session['context_id']
    extra_args = shlex.split(request.form.get('extra_args', ''))
    task = web_run_sifter.apply_async((
        sifter,
        course,
        extra_args
    ))
    managed_tasks = list(session.get('managed_tasks', []))
    task_dict = {
        'sifter': sifter_name,
        'task_id': task.task_id,
        'time': time.strftime('%Y-%m-%d %H:%M:%SZ', time.localtime()),
        'extra_args': extra_args,
        'course': course,
    }
    managed_tasks.append(task_dict)
    session['managed_tasks'] = managed_tasks
    return get_task_status()


@xsiftx_lti.route(
    '/api/{0}/update_task_status'.format(API_VERSION),
    methods=['PUT']
)
@lti_authentication
def get_task_status():
    """
    Grabs a status of all the tasks that are stored in the session
    """
    managed_tasks = session.get('managed_tasks', [])
    for task in managed_tasks:
        result = celery.AsyncResult(task['task_id'])  # pylint: disable=e1121
        task['status'] = result.status
        if result.state == 'SUCCESS':
            task['results'] = result.result
            if not task['results']['success']:
                task['status'] = 'SIFTER_FAILURE'
    session['managed_tasks'] = managed_tasks
    return jsonify({'tasks': managed_tasks})


@xsiftx_lti.route(
    '/api/{0}/clear_complete_tasks'.format(API_VERSION),
    methods=['DELETE'])
@lti_authentication
def clear_complete_tasks():
    """
    Nukes completed tasks from the session store
    """
    # Update list
    get_task_status()
    managed_tasks = session.get('managed_tasks', [])
    managed_tasks[:] = [
        task for task in managed_tasks
        if not task['status'] in JOB_CLEAR_STATUSES
    ]
    return jsonify({'tasks': managed_tasks})


@celery.task(name='xsiftx.run_sifter')
def web_run_sifter(sifter, course, extra_args):
    """
    Run the given sifter and handle errors from the internal call
    """
    error = u''
    success = True
    try:
        run_sifter(
            sifter,
            course,
            settings[VENV[0]],
            settings[EDX_PLATFORM[0]],
            extra_args
        )
    except XsiftxException as err:
        error = unicode(err)
        success = False
    except SifterException as err:
        error = unicode(err)
        success = False

    return {
        'success': success,
        'sifter': os.path.basename(sifter),
        'error': error,
    }


@xsiftx_lti.errorhandler(InvalidAPIUsage)
def handle_invalid_api_usage(error):
    """Return jsonified error message"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@xsiftx_lti.errorhandler(LTIException)
@xsiftx_lti.errorhandler(LTIRoleException)
def handle_lti_error(error):
    """Return LTI error"""
    # Return json if this is from an API call or html
    # if not.
    if '/api/{0}'.format(API_VERSION) in request.url:
        response = jsonify({'message': unicode(error)})
    else:
        response = make_response(render_template(
            'lti_error.html',
            message=unicode(error)
        ))
    response.status_code = 401
    return response
