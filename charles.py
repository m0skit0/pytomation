import os
import re
import subprocess
import time

import requests
import json

MAIN_URL = 'http://control.charles'
SESSION_JSON_URL = 'http://control.charles/session/export-json'
CLEAR_SESSION_URL = 'http://control.charles/session/clear'
ENABLE_LOCAL_MAPPING_URL = 'http://control.charles/tools/map-local/enable'
DISABLE_LOCAL_MAPPING_URL = 'http://control.charles/tools/map-local/disable'
ENABLE_THROTTLING_URL = 'http://control.charles/throttling/activate?preset='
DISABLE_THROTTLING_URL = 'http://control.charles/throttling/deactivate?'
DISABLE_REWRITE_URL = 'http://control.charles/tools/rewrite/disable'

CHARLES_APP_PATH = '/Applications/Charles.app/Contents/MacOS/Charles'

proxies = {
    'http': 'http://localhost:8888'
}

throttling_presets = {
    '512': 'http://control.charles/throttling/activate?preset=512+kbps+ISDN%2FDSL',
    '256': 'http://control.charles/throttling/activate?preset=256+kbps+ISDN%2FDSL',
}


def launch(path=CHARLES_APP_PATH, config=None):
    """
    Launches Charles, killing it first if it was already running.
    Also disables local mapping, throttling and rewrites for a clean state startup.
    :param path: Charles app path.
    :param config: Charles config XML path to load. This is where several options are set up, e.g. mappings.
    (see Charles documentation: https://www.charlesproxy.com/documentation/using-charles/command-line-options/)
    :return: Nothing.
    """
    kill()
    if config is None:
        process = subprocess.Popen(path)
    else:
        process = subprocess.Popen([path, '--config', config])
    time.sleep(10)  # Wait for Charles to boot
    disable_local_mapping()
    time.sleep(1)
    disable_throttling()
    time.sleep(1)
    disable_rewrite()
    time.sleep(1)
    return process


def _get_url(url):
    response = requests.get(url, proxies=proxies)
    return response.content


def _call_url(url):
    response = requests.get(url, proxies=proxies)
    assert response.status_code == 200


def clear_session():
    """
    Clears current session
    :return: Nothing.
    """
    _call_url(CLEAR_SESSION_URL)


def _get_session_json():
    return _get_url(SESSION_JSON_URL)


def get_session():
    """
    Returns current session as a dictionary.
    :return: Current Charles session as a dictionary.
    """
    return json.loads(_get_session_json())


def get_request_body(session_entry):
    """
    Returns request body of a session entry.
    :param session_entry: Charles session entry.
    :return: Body request of the session entry.
    """
    return json.loads(session_entry['request']['body']['text'])


def enable_local_mapping():
    """
    Turns on local mapping as defined by the loaded configuration.
    :return: Nothing.
    """
    _call_url(ENABLE_LOCAL_MAPPING_URL)


def disable_local_mapping():
    """
    Disables local mapping.
    :return: Nothing.
    """
    _call_url(DISABLE_LOCAL_MAPPING_URL)


def kill():
    """
    Shuts down Charles.
    :return: Nothing.
    """
    os.system('killall -9 Charles')


def get_first_entry(session, path, assertion=True):
    """
    Get first entry in session with the specified path.
    :param session: Charles session to use.
    :param path: Path to look for.
    :param assertion: If True will assert an entry was found.
    :return: Session entry with the specified path.
    """
    entry = next((entry for entry in session if entry['path'] == path), None)
    if assertion:
        assert entry is not None
    return entry


def get_first_entry_in_session(path, desc=False, assertion=True):
    """
    Get first entry in current session with the specified path.
    :param path: Path to look for.
    :param desc: If True look in descending order, if False current order.
    :param assertion: If True will assert an entry was found.
    :return: Session entry with the specified path.
    """
    session = get_session()
    if desc:
        session.reverse()
    return get_first_entry(session, path, assertion)


def check_no_request(path):
    """
    Check no request was made to the specified path in current session.
    :param path: Path to look for.
    :return: Nothing.
    """
    for entry in get_session():
        if entry is not None:
            assert path not in entry['path']


def _update_config_body_files_qa(file, new_root):
    with open(file, 'r') as f1:
        with open('tmp', 'w') as f2:
            for line in f1.readlines():
                result = re.search(r'(.*?)<dest>(.*?/body_files_qa)/(.*?)</dest>', line)
                if result is not None:
                    line = f'{result.group(1)}<dest>{new_root}/{result.group(3)}</dest>\n'
                f2.write(line)
    os.system(f'mv -f tmp {file}')


# TODO Remove this on public API as it is a very specific local use-case
def update_all_config(base, new_root):
    """
    Updates Charles configuration with new paths.
    :param base: Base path to look for.
    :param new_root: New base path to insert.
    :return: Nothing.
    """
    files = os.listdir(base)
    for file in files:
        _update_config_body_files_qa(f'{base}/{file}', new_root)


def disable_throttling():
    """
    Disables throttling.
    :return: Nothing.
    """
    _call_url(DISABLE_THROTTLING_URL)


def disable_rewrite():
    """
    Disables all configured rewrites.
    :return: Nothing.
    """
    _call_url(DISABLE_REWRITE_URL)


def check_no_request_host(host):
    """
    Checks if no request have been made to the specified host.
    :param host: Host to check.
    :return: True if no requests have been made to the specified host, False otherwise.
    """
    return all(entry for entry in get_session() if entry and entry['host'] != host)


def enable_throttling(preset=None):
    """
    Enables throttling with the specified preset.
    :param preset: Preset to be enabled. If None turn on whatever preset has been set before.
    :return: Nothing.
    """
    if preset:
        _call_url(throttling_presets[preset])
    else:
        _call_url(ENABLE_THROTTLING_URL)

