from __future__ import absolute_import
__author__ = 'katharine'

from six import iteritems

import collections
import json
import logging
import os.path
import platform
import socket
import uuid

import requests

from pebble_tool.account import get_default_account
from pebble_tool.sdk.project import PebbleProject
from pebble_tool.exceptions import PebbleProjectException
from pebble_tool.sdk import sdk_version, get_persist_dir

logger = logging.getLogger("pebble_tool.util.analytics")


class PebbleAnalytics(object):
    TD_SERVER = "https://td.getpebble.com/td.pebble.sdk_events"

    def __init__(self):
        self.should_track = self._should_track()

    @classmethod
    def _flatten(cls, d, parent_key=''):
        items = []
        for k, v in iteritems(d):
            new_key = parent_key + '_0_' + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(iteritems(cls._flatten(v, new_key)))
            else:
                items.append((new_key, v))
        return dict(items)

    def submit_event(self, event, **data):
        if not self.should_track:
            return

        analytics = {
            'event': event,
            'identity': self._get_identity(),
            'platform': 'native_sdk',
            'sdk': {
                'host': self._get_host_info(),
                'version': sdk_version()
            },
            'data': data.copy()
        }
        try:
            analytics['sdk']['project'] = self._get_project_info()
        except PebbleProjectException:
            pass


        td_obj = self._flatten(analytics)

        fields = {
            'json': json.dumps(td_obj)
        }
        logger.debug("Posting analytics data: {}".format(analytics))
        requests.post(self.TD_SERVER, data=fields)

    def _should_track(self):
        # Should we track analytics?
        sdk_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        dnt_file = os.path.join(sdk_path, "NO_TRACKING")
        if os.path.exists(dnt_file):
            return False

        # Don't track if internet connection is down
        try:
            # NOTE: This is the IP address of www.google.com. On certain
            # flavors of linux (Ubuntu 13.04 and others), the timeout argument
            # is ignored during the DNS lookup portion so we test connectivity
            # using an IP address only.
            requests.head("http://209.118.208.39", timeout=0.75)
        except (requests.RequestException, socket.error):
            logger.debug("Analytics collection disabled due to lack of internet connectivity")
            return False
        return True

    def _get_identity(self):
        account = get_default_account()
        identity = {
            'sdk_client_id': self._get_machine_identifier()
        }
        if account.is_logged_in:
            identity['user'] = account.id
        return identity

    def _get_machine_identifier(self):
        # Get installation info. If we detect a new install, post an appropriate event
        settings_dir = get_persist_dir()
        client_id_file = os.path.join(settings_dir, "client_id")

        # Get (and create if necessary) the client id
        try:
            with open(client_id_file) as f:
                return f.read()
        except IOError:
            client_id = str(uuid.uuid4())
            with open(client_id_file, 'w') as f:
                f.write(client_id)
            return client_id

    def _get_project_info(self):
        project = PebbleProject()
        return {
            'uuid': str(project.uuid),
            'app_name': project.long_name,
            'is_watchface': project.is_watchface,
            'type': 'native',
            'sdk': project.sdk_version,
        }

    def _get_host_info(self):
        return {
            'platform': platform.platform(),
            'is_vm': self._is_running_in_vm(),
            'python_version': platform.python_version(),
        }

    _shared_analytics = None
    @classmethod
    def get_shared(cls, *args, **kwargs):
        if cls._shared_analytics is None:
            cls._shared_analytics = cls()
        return cls._shared_analytics

    @staticmethod
    def _is_running_in_vm():
        """ Return true if we are running in a VM """

        try:
            drv_name = "/proc/scsi/scsi"
            if os.path.exists(drv_name):
                contents = open(drv_name).read()
                if "VBOX" in contents or "VMware" in contents:
                    return True
        except (OSError, IOError):
            pass

        return False


# Convenience method.
def post_event(event, **data):
    PebbleAnalytics.get_shared().submit_event(event, **data)
