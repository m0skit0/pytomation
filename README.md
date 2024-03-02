# Pytomation

Python modules for Android and Charles proxy automation, mainly oriented for testing automation.

## Android module:

- Runs in any OS with `adb` and Python support.
- Locking/unlocking Android devices.
- Installing/uninstalling apps.
- Stopping/lauching any app.
- Clearing app data.
- Accessing data folder filesystem for debug apps.
- Home, back and overview button tapping.
- Tapping, long tapping, swiping views by resource id, content description, text or absolute coordinates.
- Full keyboard simulation.
- Current screen view hierarchy as Python dictionary with full view details (resource id, coordinates, etc...).
- Current app and activity name.
- Switching between apps in overview.
- Screenshots (saved in host computer, not in device).
- OCR recognition through Pytesseract library, returning coordinates of recognized character (for tapping/swiping, etc...).
- Waiting for activity, app or view with specified conditions (text, resource id, name...) to appear. Includes timeout to not block forever.
- Permission dialogs "wait and accept".
- Full logcat access (including clearing it).
- Detecting Android version and API level.

`android.py` is the Android automation module. It expects `adb` to be in the environment PATH.

`pytesseract_helper.py` is a helper module for the Pytesseract OCR library. Can be used to do OCR on a screenshot captured by the `android` module and return coordinates of specified text. Useful when testing WebViews or games where no actual Android views are present.

## Charles module:

- Stopping/launching Charles (only in MacOS and Linux).
- Loading Charles XML configuration (this loads mappings, rewrites and other Charles configurations).
- Enabling/disabling local mappings, rewrites and throttling.
- Accessing current session.
- Checking entries in current session, including host, path and body of requests as dictionaries.

`charles.py` is the Charles automation module. Currently only works in MacOS and Linux.

## Examples

- Example of automating the process of setting the Charles proxy in Pixel devices using the Android module:

```
import time

from pytomation import android

# Works for Pixel devices, can be adjusted for other devices

def set_proxy():
    print('>> Setting up proxy')
    android.stop('com.android.settings')
    android.launch('com.android.settings')
    android.tap_view_by_text('Network & internet')
    android.tap_view_by_text('AndroidWifi')
    android.tap_view_by_text('AndroidWifi')
    android.tap_view_by_content_description('Modify')
    android.tap_view_by_text('Advanced options')
    if android.find_view_by_text('Manual'):
        print('>> Proxy looks to be set, skipping')
        android.home()
        return
    android.tap_view_by_text('None')
    android.tap_view_by_text('Manual')
    android.tap_view_by_id('proxy_hostname')
    android.text('192.168.1.61')
    android.back()
    android.tap_view_by_id('proxy_port')
    android.text('8888')
    android.back()
    time.sleep(1)
    android.tap_view_by_text('Save')
    time.sleep(1)


def download_certificate():
    print('>> Downloading Charles CA certificate')
    android.stop('com.android.chrome')
    android.launch('com.android.chrome')
    web_address = android.find_view_by_text('web address')
    if web_address is None:
        print('>> Chrome not initialized, initialing')
        # Changes depending on Android version
        api_level = android.api_level()
        if api_level >= 34:
            print('>> Chrome for Android 14+ initialization')
            android.tap_view_by_text('without')
            android.tap_view_by_text('No thanks')
        else:
            print('>> Chrome for Android < 14 initialization')
            android.tap_view_by_text('Accept & continue')
            android.tap_view_by_text('No thanks')
        web_address = android.find_view_by_text('web address')
    else:
        print('>> Chrome already initialized, skipping initial steps')
    assert web_address is not None
    android.tap_view(web_address)
    time.sleep(1)
    android.text('http://chls.pro/ssl')
    time.sleep(1)
    android.enter()
    print('>> Waiting for CA certificate to download')
    time.sleep(5)


def install_certificate():
    print('>> Installing CA certificate from settings')
    android.stop('com.android.settings')
    android.launch('com.android.settings')
    android.tap_view_by_text('Search')
    time.sleep(2)
    android.text('certificate')
    time.sleep(1)
    android.tap_view_by_text('CA')
    android.tap_view_by_text('CA')
    android.tap_view_by_text('ANYWAY')
    android.tap_view_by_text('charles-proxy')
    time.sleep(1)
    android.stop('com.android.settings')


android.home()
set_proxy()
download_certificate()
install_certificate()
android.home()
print(">> Done!")
```
