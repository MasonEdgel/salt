# -*- coding: utf-8 -*-
'''
Check Host & Service status from Nagios via JSON RPC.

.. versionadded:: Beryllium

'''

# Import python libs
from __future__ import absolute_import
import logging
import httplib

# Import 3rd-party libs
# pylint: disable=import-error,no-name-in-module,redefined-builtin
from salt.ext.six.moves.urllib.parse import urljoin as _urljoin
# pylint: enable=import-error,no-name-in-module

try:
    import requests
    from requests.exceptions import ConnectionError
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only load if requests is successfully imported
    '''
    if REQUESTS_AVAILABLE:
        return 'nagios_rpc'
    log.debug('Unable to initialize "nagios_rpc": library "requests" is not installed.')

    return False


def _config():
    '''
    Get configuration items for URL, Username and Password
    '''
    return {
        'url': __salt__['config.get']('nagios:url', ''),
        'username': __salt__['config.get']('nagios:username', ''),
        'password': __salt__['config.get']('nagios:password', ''),
    }


def _status_query(query, method='GET', **kwargs):
    '''
    Send query along to Nagios
    '''
    headers = {}
    parameters = {}
    data = {}

    nagios_url = kwargs.get('nagios_url')
    nagios_username = kwargs.get('nagios_username')
    nagios_password = kwargs.get('nagios_password')

    query_params = {
        'service': [
            'hostname',
            'servicedescription',
        ],
        'host': [
            'hostname',
        ],
    }
    parameters['query'] = query
    for param in query_params[query]:
        parameters[param] = kwargs[param]

    if not nagios_url.endswith('/'):
        nagios_url = nagios_url + '/'

    if 'cgi-bin' in nagios_url:
        url = _urljoin(nagios_url, 'statusjson.cgi')
    else:
        url = _urljoin(nagios_url, 'cgi-bin/statusjson.cgi')

    try:
        if username and password:
            auth = (username, password,)
        else:
            auth = None
        result = requests.request(method=method,
                                  url=url,
                                  params=req_params,
                                  data=data,
                                  verify=True,
                                  auth=auth)
        if result.status_code == httplib.OK:
            data = result.json()
        elif result.status_code == httplib.UNAUTHORIZED:
        elif result.status_code == httplib.NOT_FOUND:
        else:
            log.info('Results: {0}'.format(result.text))
    except ConnectionError as conn_err:
        log.error('Error {0}'.format(conn_err))

    return data


def service_status(hostname, service_description):
    '''
    Check the status in Nagios for a particular
    service on a particular host

    :param hostname:                The hostname to check the status of the service in Nagios.
    :param service_description:     The service to check the status of in Nagios.
    :return: Boolean                True is the status is 'OK' or 'Warning', False if 'Critical'

    CLI Example:

    .. code-block:: bash

        salt '*' nagios_json.service_status hostname=webserver.domain.com service_description='HTTP'

    '''

    config = _config()

    if not config['nagios_url']:
        log.error('Missing nagios_url')
        return False

    results = _status_query(query='service',
                            nagios_url=config['nagios_url'],
                            nagios_username=config['nagios_username'],
                            nagios_password=config['nagios_password'],
                            hostname=hostname,
                            servicedescription=service_description)

    data = results.get('data', '')
    if data:
        status = data.get('service', '').get('status', '')
        if status and status == 0:
            return False
        elif status and status > 0:
            return True
        else:
            return False
    else:
        return False


