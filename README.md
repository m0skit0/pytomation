# Pytomation

Python modules for Android and Charles proxy automation, mainly oriented for testing automation.

`android.py` is the Android automation module. It expects `adb` to be in the environment PATH.

`pytesseract_helper.py` is a helper module for the Pytesseract OCR library. Can be used to do OCR on a screenshot captured by the `android` module and return coordinates of specified text. Useful when testing WebViews or games where no actual Android views are present.

`charles.py` is the Charles automation module. Currently only works in MacOS and Linux.

Example of automating the process of setting the Charles proxy in Pixel devices using the Android module:

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
