# -*- coding: UTF-8 -*-
import logging
from pprint import pformat

from apscheduler.events import EVENT_JOB_MAX_INSTANCES, EVENT_JOB_REMOVED

EVENT_MAP = {EVENT_JOB_MAX_INSTANCES: 'EVENT_JOB_MAX_INSTANCES', EVENT_JOB_REMOVED: 'EVENT_JOB_REMOVED'}


def my_listener(event):
    msg = "=== ISO 调度 %s: \n%s\n" % (EVENT_MAP[event.code], pformat(vars(event), indent=4))
    if event.jobstore != 'default':
        logging.getLogger('apscheduler').info(msg)
    else:
        logging.getLogger('apscheduler').warning(msg)
