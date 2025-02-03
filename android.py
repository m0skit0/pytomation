from datetime import datetime
import subprocess
import time
import xmltodict
import re
import traceback


def _time_prefix():
    return datetime.now().strftime("%H:%M:%S")


# TODO Maybe keep a shell process open to speed this up instead of having to call adb shell every time
def _run_adb_shell(command, assertion=True):
    ret = subprocess.run(['adb', 'shell', command], capture_output=True)
    if assertion:
        assert ret.returncode == 0
    time.sleep(0.3)


def _run_command(command, assertion=True):
    ret = subprocess.run(command, capture_output=False)
    if assertion:
        assert ret.returncode == 0
    time.sleep(0.3)


def _check_output(command):
    return subprocess.check_output(command, shell=True, text=True).strip()


# TODO Maybe keep a shell process open to speed this up instead of having to call adb shell every time
def _adb_shell_check_output(command):
    return _check_output(f'adb shell {command}')


def _view_hierarchy_xml():
    _run_adb_shell('uiautomator dump')
    return _adb_shell_check_output('cat /sdcard/window_dump.xml')


def view_hierarchy():
    """
    Returns current screen view hierarchy.
    :return: Dictionary representing the current screen view hierarchy.
    """
    xml = _view_hierarchy_xml()
    return xmltodict.parse(xml)


def _print_stack_trace():
    for frame in traceback.extract_stack():
        print(frame)


def _find_view_by_key(key, value, view):
    while True:
        if isinstance(view, dict):
            if key in view:
                if value in view[key]:
                    return view
            if 'node' in view:
                view = view['node']
                continue
            else:
                return None
        elif isinstance(view, list):
            if not len(view):
                return None
            else:
                for node in view:
                    found = _find_view_by_key(key, value, node)
                    if found is not None:
                        return found
        return None


def find_view_by_id(res_id, view=None, debug=False):
    """
    Returns first view (as dictionary) which id contains res_id in current screen
    If second parameter is not None, it will only search inside that view.
    :param res_id: Resource id to look for.
    :param view: View hierarchy dictionary to look under, or None to get current screen view hierarchy.
    :param debug: Prints the view hierarchy on STDOUT.
    :return: View as a dictionary if found, None otherwise.
    """
    if view is None:
        view = view_hierarchy()
    if debug:
        print(view)
    return _find_view_by_key('@resource-id', res_id, view['hierarchy'])


def find_view_by_content_desc(content_desc, view=None):
    """
    Returns first view (as dictionary) by id.
    :param content_desc: Content description to look for.
    :param view: View hierarchy dictionary to look under, or None to get current screen view hierarchy.
    :return: View as a dictionary if found, None otherwise.
    """
    if view is None:
        view = view_hierarchy()
    return _find_view_by_key('@content-desc', content_desc, view['hierarchy'])


def find_view_by_text(_text, view=None):
    """
    Returns first view (as dictionary) by contained text.
    :param _text: View text to look for.
    :param view: View hierarchy dictionary to look under, or None to get current screen view hierarchy.
    :return: View as a dictionary if found, None otherwise.
    """
    if view is None:
        view = view_hierarchy()
    return _find_view_by_key('@text', _text, view['hierarchy'])


def _tap_coordinates_for_view(view):
    if view is None:
        return None
    elif '@bounds' in view:
        p = re.search(r'\[(\d+),(\d+)]\[(\d+),(\d+)]', view['@bounds'])
        x1 = int(p.group(1))
        y1 = int(p.group(2))
        x2 = int(p.group(3))
        y2 = int(p.group(4))
        return int(x1 + ((x2 - x1) / 2)), int(y1 + ((y2 - y1) / 2))
    else:
        return None


def tap_view_by_id(res_id, view=None, debug=False):
    """
    Taps first view by id.
    :param res_id: Resource id to look for.
    :param view: View hierarchy dictionary to look under, or None to get current screen view hierarchy.
    :param debug: If True, prints the view hierarchy on STDOUT.
    :return: True if view found, False otherwise.
    """
    if view is None:
        view = view_hierarchy()
    view = find_view_by_id(res_id, view=view, debug=debug)
    if view is None:
        return False
    return tap_view(view)


def tap_view_by_text(_text, view=None):
    """
    Taps first view by text.
    :param _text: Text to look for.
    :param view: View hierarchy dictionary to look under, or None to get current screen view hierarchy.
    :return: True if view found, False otherwise.
    """
    if view is None:
        view = view_hierarchy()
    view = find_view_by_text(_text, view)
    if view is None:
        return False
    return tap_view(view)


def tap_view_by_content_description(content_description, view=None):
    """
    Taps first view by content description.
    :param content_description: Content description to look for.
    :param view: View hierarchy dictionary to look under, or None to get current screen view hierarchy.
    :return: True if view found, False otherwise.
    """
    if view is None:
        view = view_hierarchy()
    view = find_view_by_content_desc(content_description, view)
    if view is None:
        return False
    return tap_view(view)


def tap_view(view):
    """
    Taps a view.
    :param view: The view to tap.
    :return: True if view coordinates found, False otherwise.
    """
    click_coord = _tap_coordinates_for_view(view)
    if click_coord is None:
        return False
    _adb_tap(click_coord[0], click_coord[1])
    return True


def tap(x=None, y=None):
    """
    Taps a view by coordinates.
    :param x: X coordinate of the view to tap.
    :param y: Y coordinate of the view to tap.
    :return: True if view found, False otherwise.
    """
    if x is not None and y is not None:
        click_coord = x, y
    else:
        click_coord = _center_coordinates()
    if click_coord is None:
        return False
    _adb_tap(click_coord[0], click_coord[1])
    return True


def _adb_tap(x, y):
    _run_adb_shell(f'input tap {x} {y}')


def screen_size():
    """
    Returns current screen size in pixels.
    :return: Tuple of (height, width) in pixels.
    """
    output = _adb_shell_check_output('wm size')
    p = re.search(r'.*: (\d+)x(\d+)', output)
    return int(p.group(1)), int(p.group(2))


# TODO Maybe allow tag as well for logcat
def log(message):
    """
    Logs a message in the logcat with "android.py" as tag.
    :param message: Message to log.
    :return: Nothing.
    """
    print(f'{_time_prefix()} >> {message}')
    _run_adb_shell(f'log -t android.py "{message}"')


def power():
    """
    Simulates a power button press.
    Note that this might fail to work in some devices.
    :return: Nothing.
    """
    _run_adb_shell("input keyevent 26")


# TODO Find a way to only press the power button when the device is not locked already.
def lock():
    """
    Simulates a power button press.
    Note that this might fail to work in some devices.
    :return: Nothing.
    """
    power()


def unlock():
    """
    Simulates a power button press and swipes up (unlocks a device with no security login set up).
    Note that this might fail to work in some devices.
    :return: Nothing.
    """
    power()
    time.sleep(0.3)
    swipe_up()
    time.sleep(0.3)


def _dumpsys_activity():
    return _check_output("adb shell dumpsys activity top | grep 'ACTIVITY' | tail -n 1")


def current_app_name():
    """
    Returns current foreground app name.
    :return: App package name.
    """
    return re.search(r'ACTIVITY (.*)/.*', _dumpsys_activity()).group(1).strip()


def current_activity_name():
    """
    Returns foreground activity (not canonical) class name.
    :return: Activity class name.
    """
    activity_name = re.search(r'ACTIVITY .*/(.*?) .*', _dumpsys_activity()).group(1).strip()
    if activity_name.startswith('.'):
        return activity_name.lstrip('.')
    else:
        return activity_name


def clear(app_package):
    """
    Clears data for an app.
    Note that this will kill the app if it's executing.
    :param app_package: App package name.
    :return: Nothing.
    """
    _run_adb_shell(f'pm clear {app_package}')
    time.sleep(0.5)


def launch(app_package, activity_name=None):
    """
    Launches the specified app.
    :param app_package: App package name to launch.
    :param activity_name: Activity name to launch, or main activity as defined in manifest if None.
    :return: Nothing.
    """
    if activity_name is None:
        _run_adb_shell(f'monkey -p {app_package} -c android.intent.category.LAUNCHER 1')
    else:
        _run_adb_shell(f'am start {app_package}/{activity_name}')
    time.sleep(0.5)


def stop(app_package):
    """
    Stops app.
    :param app_package: App package name to stop.
    :return: Nothing.
    """
    _run_adb_shell(f'am force-stop {app_package}')


def overview():
    """
    Opens the app overview screen.
    :return: Nothing
    """
    _run_adb_shell(f'input keyevent KEYCODE_APP_SWITCH')
    time.sleep(0.5)


def latest_app_in_overview():
    """
    Taps the latest app in overview.
    Note that some devices automatically select the previous app if an app is already open.
    :return: Nothing
    """
    overview()
    size = screen_size()
    _run_adb_shell(f'input tap {size[0] / 2} {size[1] / 2}')
    time.sleep(0.5)


def _center_coordinates(res_id=None):
    if res_id is None:
        size = screen_size()
        x1 = size[0] / 2
        y1 = size[1] / 2
    else:
        view = find_view_by_id(res_id)
        coord = _tap_coordinates_for_view(view)
        x1 = coord[0]
        y1 = coord[0]
    return x1, y1


def _swipe_delta_vertical():
    return int(screen_size()[1] / 3)


def _swipe_delta_horizontal():
    return int(screen_size()[0] / 2)


def swipe_up(res_id=None, delta=None):
    """
    Swipes up starting on a specific view with the specified resource id.
    :param res_id: Resource id for the view to start swiping up on, or None for the center of the screen.
    :param delta: How many pixels to move while swiping, or 1/3 of the screen size on that direction if None.
    :return: Nothing.
    """
    coord = _center_coordinates(res_id)
    x1 = coord[0]
    y1 = coord[1]
    if delta is None:
        delta = _swipe_delta_vertical()
    y2 = y1 - delta
    _adb_swipe(x1, y1, x1, y2)


def swipe_down(res_id=None, delta=None):
    """
    Swipes down starting on a specific view with the specified resource id.
    :param res_id: Resource id for the view to start swiping up on, or None for the center of the screen.
    :param delta: How many pixels to move while swiping, or 1/3 of the screen size on that direction if None.
    :return: Nothing.
    """
    coord = _center_coordinates(res_id)
    x1 = coord[0]
    y1 = coord[1]
    if delta is None:
        delta = _swipe_delta_vertical()
    y2 = y1 + delta
    _adb_swipe(x1, y1, x1, y2)


def swipe_left(res_id=None, delta=None):
    """
    Swipes left starting on a specific view with the specified resource id.
    :param res_id: Resource id for the view to start swiping up on, or None for the center of the screen.
    :param delta: How many pixels to move while swiping, or 1/3 of the screen size on that direction if None.
    :return: Nothing.
    """
    coord = _center_coordinates(res_id)
    x1 = coord[0]
    y1 = coord[1]
    if delta is None:
        delta = _swipe_delta_horizontal()
    x2 = x1 - delta
    _adb_swipe(x1, y1, x2, y1)


def swipe_right(res_id=None, delta=None):
    """
    Swipes right starting on a specific view with the specified resource id.
    :param res_id: Resource id for the view to start swiping up on, or None for the center of the screen.
    :param delta: How many pixels to move while swiping, or 1/3 of the screen size on that direction if None.
    :return: Nothing.
    """
    coord = _center_coordinates(res_id)
    x1 = coord[0]
    y1 = coord[1]
    if delta is None:
        delta = _swipe_delta_horizontal()
    x2 = x1 + delta
    _adb_swipe(x1, y1, x2, y1)


def _adb_swipe(x1, y1, x2, y2):
    _run_adb_shell(f'input touchscreen swipe {x1} {y1} {x2} {y2} 200')
    time.sleep(0.2)


def back():
    """
    Simulates a "back" button press.
    :return: Nothing.
    """
    _run_adb_shell('input keyevent KEYCODE_BACK')
    time.sleep(0.2)


def home():
    """
    Simulates a "home" button press.
    :return: Nothing.
    """
    _run_adb_shell('input keyevent KEYCODE_HOME')
    time.sleep(0.2)


def enter():
    """
    Simulates an "enter" button press on the keyboard.
    Note that this will work even if the keyboard is not open.
    :return: Nothing.
    """
    _run_adb_shell('input keyevent 66')


def text(value):
    """
    Simulates the typing of the specified text.
    Note that this will work even if the keyboard is not open.
    :param value: The text to be simulated typing.
    :return: Nothing.
    """
    _run_adb_shell(f'input text "{value}"')


def accept_permission(timeout=5):
    """
    Waits and accepts current permission popup.
    If the permission popup does not show, this function will throw an assertion error.
    :param timeout: Timeout in seconds.
    :return: Nothing.
    """
    assert wait_for_res("permission_allow_button", timeout=timeout)
    assert tap_view_by_id("permission_allow_button")


def get_text_from_view(res_id):
    """
    Returns text on specified view id.
    :param res_id: Resource id of the view to look for.
    :return: Text on the view, or None if no view found with that id.
    """
    node = find_view_by_id(res_id)
    if node:
        if '@text' in node:
            return node['@text']
    return None


def wait_for_activity(activity, timeout=5):
    """
    Wait for an activity by class name to become the foreground activity.
    :param activity: Class name of the activity.
    :param timeout: Timeout in seconds.
    :return:
    """
    for i in range(timeout):
        if activity in current_activity_name():
            return True
        else:
            time.sleep(0.5)
    return False


def wait_for_res(res_id, timeout=5, debug=False):
    """
    Wait for view by id to appear.
    :param res_id: Resource id of the view
    :param timeout: Timeout in seconds.
    :param debug: If True prints the view on STDOUT.
    :return: True if the view was found before the timeout, False otherwise.
    """
    for i in range(timeout):
        if find_view_by_id(res_id, debug=debug) is not None:
            return True
    return False


def wait_for_text(res_id, _text, timeout=5):
    """
    Wait for text in specified view to appear.
    :param res_id: Resource id of the view.
    :param _text: Text to look for in the view.
    :param timeout: Timeout in seconds.
    :return: True if the view was found before the timeout, False otherwise.
    """
    for i in range(timeout):
        if _text in get_text_from_view(res_id):
            return True
        time.sleep(1)
    return False


# TODO Return True/False if installation was successful or not
def install(apk_path):
    """
    Installs apk.
    :param apk_path: Path of the APK to install
    :return: Nothing.
    """
    _run_command(['adb', 'install', apk_path])


# TODO Return True/False if uninstall was successful or not
def uninstall(package):
    """
    Uninstalls an app.
    :param package: App package name to uninstall.
    :return: Nothing.
    """
    _run_command(['adb', 'uninstall', package], assertion=False)


def long_press_view(view):
    """
    Long presses a view.
    :param view: View to long-press as dictionary.
    :return: True if view coordinates were found, False otherwise.
    """
    click_coord = _tap_coordinates_for_view(view)
    if click_coord is None:
        return False
    x = click_coord[0]
    y = click_coord[1]
    _adb_swipe(x, y, x, y)
    return True


# TODO Add filtering by tag or something.
def logcat():
    """
    Returns logcat.
    :return: Full logcat text.
    """
    return _check_output('adb logcat -d')


def clear_logcat():
    """
    Clears logcat.
    :return: Nothing.
    """
    _run_command(['adb', 'logcat', '-c'])


def screenshot(file_name='../screenshot.png'):
    """
    Saves a screenshot in the host (not in the device itself).
    :param file_name: File name where to store the screenshot.
    :return: Nothing.
    """
    file = open(file_name, "w")
    subprocess.Popen(['adb', 'shell', 'screencap', '-p'], stdout=file).wait()


def display_height():
    """
    Returns device display height.
    :return: Display height in pixels.
    """
    output = _check_output('adb shell dumpsys window')
    return int(re.search(r'displayHeight=(\d+)', output).group(1))


# IMPORTANT: This only works for debug APK!
def ls(package_name, path):
    """
    Returns list of files and folders in the specified app data folder.
    NOTE: This only works for debug APKs.
    :param package_name: App package name.
    :param path: Path inside the app data folder.
    :return: List of file and folder names.
    """
    _ls = _check_output(f'adb exec-out run-as {package_name} ls -a /data/data/{package_name}/{path}')
    _ls = _ls.split('\n')
    _ls = list(map(lambda x: x.split(' '), _ls))
    result = []
    for x in _ls:
        result.extend(x)
    result = list(filter(lambda x: x and not all(c == '.' for c in x), result))
    return result


def wait_for_view_with_text(_text, timeout=5):
    """
    Waits for a view with the specific text to appear.
    :param _text: Text in the view.
    :param timeout: Timeout in seconds.
    :return: True if the view appeared before the timeout, False otherwise.
    """
    for i in range(timeout):
        if find_view_by_text(_text) is not None:
            return True
    return False


def api_level():
    """
    Returns device API level (aka Android version)
    :return: API level as integer.
    """
    return int(_check_output('adb shell getprop ro.build.version.sdk'))

def airplane_mode(is_enabled = None):
    """
    Turns Airplane mode on/off
    :param is_enabled: True for Airplane mode on, False for Airplane mode off, None for switching
    """
    if is_enabled is None:
        output = _check_output('adb shell cmd connectivity airplane-mode')
        if output == 'enabled':
            is_enabled = False
        else:
            is_enabled = True
    if is_enabled:
        param = 'enable'
    else:
        param = 'disable'
    _run_command(['adb', 'shell', 'cmd', 'connectivity', 'airplane-mode', param])

def launch_deeplink(url, expected_activity = None):
    """
    Launch a deep link intent with the specified URL.
    :param url: Deep link URL
    :param expected_activity: Activity the deep link is expected to land into.
    :return:
    """
    _run_adb_shell(f'am start -a android.intent.action.VIEW -d "{url}"')
    if expected_activity is None:
        return True
    else:
        return wait_for_activity(expected_activity)

