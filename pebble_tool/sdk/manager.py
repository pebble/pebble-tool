from __future__ import absolute_import, print_function
__author__ = 'katharine'

from distutils.util import strtobool
import json
import os
from progressbar import ProgressBar, Percentage, Bar, FileTransferSpeed, Timer
import requests
import shutil
import subprocess
import sys
import tempfile
import tarfile

from pebble_tool.exceptions import SDKInstallError, MissingSDK
from pebble_tool.util import get_persist_dir


class SDKManager(object):
    DOWNLOAD_SERVER = "https://pebble-sdk-server-staging.herokuapp.com"
    def __init__(self, sdk_dir=None):
        self.sdk_dir = os.path.normpath(sdk_dir or os.path.join(get_persist_dir(), "SDKs"))
        if not os.path.exists(self.sdk_dir):
            os.makedirs(self.sdk_dir)

    def list_local_sdks(self):
        sdks = []
        for dir in os.listdir(self.sdk_dir):
            dir = os.path.join(self.sdk_dir, dir)
            if os.path.islink(dir):
                continue
            manifest_path = os.path.join(dir, 'sdk-core', 'manifest.json')
            if not os.path.exists(manifest_path):
                continue
            with open(manifest_path) as f:
                try:
                    sdks.append(json.load(f))
                except ValueError:
                    pass

        return sdks

    def list_local_sdk_versions(self):
        return {x['version'] for x in self.list_local_sdks()}

    def list_remote_sdks(self):
        sdks = self.request("/v1/files/sdk-core").json()
        return sdks['files']

    def uninstall_sdk(self, version):
        current_sdk = self.get_current_sdk()
        shutil.rmtree(self.root_path_for_sdk(version))
        if current_sdk == version:
            # TODO: This is going to make odd choices if we get past x.9.
            current_sdks = sorted(self.list_local_sdk_versions(), reverse=True)
            if len(current_sdks) > 0:
                self.set_current_sdk(current_sdks[0])
            else:
                os.unlink(self._current_path)

    def install_remote_sdk(self, version):
        sdk_info = self.request("/v1/files/sdk-core/{}".format(version)).json()
        path = os.path.normpath(os.path.join(self.sdk_dir, sdk_info['version']))
        if os.path.exists(path):
            raise SDKInstallError("SDK {} is already installed.".format(sdk_info['version']))
        self._license_prompt()
        print("Downloading...")
        bar = ProgressBar(widgets=[Percentage(), Bar(marker='=', left='[', right=']'), ' ', FileTransferSpeed(), ' ',
                                   Timer(format='%s')])
        bar.start()
        response = requests.get(sdk_info['url'], stream=True)
        response.raise_for_status()
        bar.maxval = int(response.headers['Content-Length'])
        with tempfile.TemporaryFile() as f:
            for content in response.iter_content(512):
                bar.update(bar.currval + len(content))
                f.write(content)
            bar.finish()
            f.flush()
            f.seek(0)
            print("Extracting...")
            with tarfile.open(fileobj=f, mode="r:*") as t:
                contents = t.getnames()
                for filename in contents:
                    if filename.startswith('/') or '..' in filename:
                        raise SDKInstallError("SDK contained a questionable file: {}".format(filename))
                if not path.startswith(self.sdk_dir):
                    raise SDKInstallError("Suspicious version number: {}".format(sdk_info['version']))
                os.mkdir(os.path.join(self.sdk_dir, sdk_info['version']))
                t.extractall(path)
        virtualenv_path = os.path.join(path, ".env")
        print("Preparing virtualenv... (this may take a while)")
        subprocess.check_call([sys.executable, "-m", "virtualenv", virtualenv_path, "--no-site-packages"])
        print("Installing dependencies...")
        subprocess.check_call([os.path.join(virtualenv_path, "bin", "python"), "-m", "pip", "install", "-r",
                               os.path.join(path, "sdk-core", "requirements.txt")])
        print("Done.")

        self.set_current_sdk(sdk_info['version'])

    def _license_prompt(self):
        prompt = """To use the Pebble SDK, you must agree to the following:

PEBBLE TERMS OF USE
https://developer.getpebble.com/legal/terms-of-use

PEBBLE DEVELOPER LICENSE
https://developer.getpebble.com/legal/sdk-license
"""
        print(prompt)
        result = False
        while True:
            try:
                result = strtobool(raw_input("Do you accept the Pebble Terms of Use and the "
                                             "Pebble Developer License? (y/n) "))
            except ValueError:
                pass
            else:
                break
        if not result:
            raise SDKInstallError("You must accept the Terms of Use and Developer License to install an SDK.")

    def set_current_sdk(self, version):
        path = os.path.join(self.sdk_dir, version)
        # PBL-24516: This isn't going to play nice on Windows.
        try:
            os.unlink(self._current_path)
        except (OSError, TypeError):
            pass
        os.symlink(path, self._current_path)

    def get_current_sdk(self):
        if self.current_path is None:
            return None
        manifest_path = os.path.join(self.current_path, "manifest.json")
        if not os.path.exists(manifest_path):
            return None
        with open(manifest_path) as f:
            return json.load(f)['version']

    @property
    def current_path(self):
        path = self._current_path
        if not os.path.exists(path):
            return None
        return os.path.join(path, 'sdk-core')

    @property
    def _current_path(self):
        return os.path.join(self.sdk_dir, "current")

    def request(self, path, *args):
        return requests.get("{}{}".format(self.DOWNLOAD_SERVER, path), *args)

    def root_path_for_sdk(self, version):
        path = os.path.join(self.sdk_dir, version)
        if not os.path.exists(path):
            raise MissingSDK("SDK {} is not installed.".format(version))
        return path

    def path_for_sdk(self, version):
        path = os.path.join(self.root_path_for_sdk(version), 'sdk-core')
        if not os.path.exists(path):
            raise MissingSDK("SDK {} is not installed.".format(version))
        return path


    @staticmethod
    def parse_version(version_string):
        return tuple(map(int, version_string.split('-', 1)[0].split('.', 2)) + [0, 0])[:3]