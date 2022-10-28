from __future__ import absolute_import, print_function
__author__ = 'katharine'

from contextlib import closing
from distutils.util import strtobool
import errno
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
from pebble_tool.sdk.requirements import Requirements
from pebble_tool.util import get_persist_dir
from pebble_tool.util.config import config
from pebble_tool.util.npm import invoke_npm
from pebble_tool.util.versions import version_to_key

pebble_platforms = ('aplite', 'basalt', 'chalk', 'diorite', 'emery')


class SDKManager(object):
    DOWNLOAD_SERVER = "https://sdk.getpebble.com"

    def __init__(self, sdk_dir=None):
        self.sdk_dir = os.path.normpath(sdk_dir or os.path.join(get_persist_dir(), "SDKs"))
        if not os.path.exists(self.sdk_dir):
            os.makedirs(self.sdk_dir)

    def list_local_sdks(self):
        sdks = []
        try:
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
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
            return []

        return sdks

    def list_local_sdk_versions(self):
        return {x['version'] for x in self.list_local_sdks()}

    def list_remote_sdks(self):
        sdks = self.request("/v1/files/sdk-core?channel={}".format(self.get_channel())).json()
        return sdks['files']

    def uninstall_sdk(self, version):
        current_sdk = self.get_current_sdk()
        shutil.rmtree(self.root_path_for_sdk(version))
        if current_sdk == version:
            current_sdks = sorted(self.list_local_sdk_versions(), reverse=True, key=version_to_key)
            if len(current_sdks) > 0:
                self.set_current_sdk(current_sdks[0])
            else:
                os.unlink(self._current_path)

    def install_from_url(self, url):
        print("Downloading...")
        bar = ProgressBar(widgets=[Percentage(), Bar(marker='=', left='[', right=']'), ' ', FileTransferSpeed(), ' ',
                                   Timer(format='%s')])
        bar.start()
        response = requests.get(url, stream=True)
        response.raise_for_status()
        bar.maxval = int(response.headers['Content-Length'])
        with tempfile.TemporaryFile() as f:
            for content in response.iter_content(512):
                bar.update(bar.currval + len(content))
                f.write(content)
            bar.finish()
            f.flush()
            f.seek(0)
            self._install_from_handle(f)

    def install_from_path(self, path):
        with open(path) as f:
            self._install_from_handle(f)

    def _install_from_handle(self, f):
        path = None
        try:
            print("Extracting...")
            with tarfile.open(fileobj=f, mode="r:*") as t:
                with closing(t.extractfile('sdk-core/manifest.json')) as f_manifest:
                    sdk_info = json.load(f_manifest)
                path = os.path.normpath(os.path.join(self.sdk_dir, sdk_info['version']))
                if os.path.exists(path):
                    raise SDKInstallError("SDK {} is already installed.".format(sdk_info['version']))
                contents = t.getnames()
                for filename in contents:
                    if filename.startswith('/') or '..' in filename:
                        raise SDKInstallError("SDK contained a questionable file: {}".format(filename))
                if not path.startswith(self.sdk_dir):
                    raise SDKInstallError("Suspicious version number: {}".format(sdk_info['version']))
                Requirements(sdk_info['requirements']).ensure_satisfied()
                os.mkdir(os.path.join(self.sdk_dir, sdk_info['version']))
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(t, path)
            virtualenv_path = os.path.join(path, ".env")
            print("Preparing virtualenv... (this may take a while)")
            subprocess.check_call([sys.executable, "-m", "virtualenv", virtualenv_path, "--no-site-packages"])
            print("Installing dependencies...")
            subprocess.check_call([os.path.join(virtualenv_path, "bin", "python"), "-m", "pip", "install", "-r",
                                   os.path.join(path, "sdk-core", "requirements.txt")],
                                  env={'PYTHONHOME': virtualenv_path})
            package_json = os.path.join(path, "sdk-core", "package.json")
            if os.path.exists(package_json):
                print("Installing JS dependencies... (this may take a while)")
                node_modules_folder = os.path.join(path, "node_modules")
                os.mkdir(node_modules_folder)
                shutil.copy2(package_json, os.path.join(path, "package.json"))
                invoke_npm(["install", "--silent"], cwd=path)

            self.set_current_sdk(sdk_info['version'])
            print("Done.")
        except Exception:
            print("Failed.")
            try:
                if path is not None and os.path.exists(path):
                    print("Cleaning up failed install...")
                    shutil.rmtree(path)
                    print("Done.")
            except OSError:
                print("Cleanup failed.")
            raise

    def install_remote_sdk(self, version):
        sdk_info = self.request("/v1/files/sdk-core/{}?channel={}".format(version, self.get_channel())).json()
        if 'version' not in sdk_info:
            raise SDKInstallError("SDK {} could not be downloaded.".format(version))
        path = os.path.normpath(os.path.join(self.sdk_dir, sdk_info['version']))
        if os.path.exists(path):
            raise SDKInstallError("SDK {} is already installed.".format(sdk_info['version']))
        # For now, we ignore this field aside from bailing if it has content.
        Requirements(sdk_info['requirements']).ensure_satisfied()
        self._license_prompt()
        self.install_from_url(sdk_info['url'])

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
        if not os.path.exists(path):
            raise SDKInstallError("SDK version {} is not currently installed.".format(version))
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

    @classmethod
    def set_channel(cls, channel):
        config.set('sdk-channel', channel)

    @classmethod
    def get_channel(cls):
        return config.get('sdk-channel', '')

    def make_tintin_sdk(self, path):
        path = os.path.realpath(os.path.expanduser(path))
        dest_path = os.path.join(self.sdk_dir, 'tintin')
        if not os.path.exists(os.path.join(path, 'wscript')):
            raise SDKInstallError("No tintin found at {}".format(path))
        if os.path.exists(dest_path):
            raise SDKInstallError("tintin SDK already set up. uninstall before making changes.")
        build_path = os.path.join(path, 'build')
        sdk_path = os.path.join(build_path, 'sdk')
        os.mkdir(dest_path)
        env_path = os.path.join(dest_path, '.env')
        if os.path.exists(os.path.join(sdk_path, 'package.json')):
            shutil.copy2(os.path.join(sdk_path, 'package.json'), os.path.join(dest_path, 'package.json'))
            node_modules_path = os.path.join(dest_path, 'node_modules')
            os.mkdir(node_modules_path)
        dest_path = os.path.join(dest_path, 'sdk-core')
        os.mkdir(os.path.join(dest_path))
        pebble_path = os.path.join(dest_path, 'pebble')
        os.mkdir(pebble_path)

        # A symlink doesn't work for some reason; instead write a python script that invokes waf using whatever
        # interpreter we used to invoke it.
        with open(os.path.join(pebble_path, 'waf'), 'w') as f:
            f.write("""#!/usr/bin/env python
import subprocess
import sys
subprocess.call([sys.executable, {}] + sys.argv[1:])
""".format(repr(os.path.join(sdk_path, 'waf'))))
            os.chmod(os.path.join(pebble_path, 'waf'), 0o755)
        for platform in pebble_platforms:
            os.mkdir(os.path.join(pebble_path, platform))
            os.symlink(os.path.join(sdk_path, platform, 'include'), os.path.join(pebble_path, platform, 'include'))
            os.symlink(os.path.join(sdk_path, platform, 'lib'), os.path.join(pebble_path, platform, 'lib'))
            os.mkdir(os.path.join(pebble_path, platform, 'qemu'))
            os.symlink(os.path.join(build_path, 'qemu_micro_flash.bin'),
                       os.path.join(pebble_path, platform, 'qemu', 'qemu_micro_flash.bin'))
            os.symlink(os.path.join(build_path, 'qemu_spi_flash.bin'),
                       os.path.join(pebble_path, platform, 'qemu', 'qemu_spi_flash.bin'))

        os.symlink(os.path.join(sdk_path, 'common/'), 
                   os.path.join(pebble_path, 'common'))

        with open(os.path.join(dest_path, 'manifest.json'), 'w') as f:
            json.dump({
                'requirements': [],
                'version': 'tintin',
                'type': 'sdk-core',
                'channel': '',
            }, f)

        print("Preparing virtualenv... (this may take a while)")
        subprocess.check_call([sys.executable, "-m", "virtualenv", env_path, "--no-site-packages"])
        print("Installing dependencies...")
        print("This may fail installing Pillow==2.0.0. In that case, question why we still force 2.0.0 anyway.")
        if sys.platform.startswith('darwin'):
            platform = 'osx'
        elif sys.platform.startswith('linux'):
            platform = 'linux'
        else:
            raise SDKInstallError("Couldn't figure out what requirements to install.")
        subprocess.check_call([os.path.join(env_path, "bin", "python"), "-m", "pip", "install", "-r",
                               os.path.join(path, "requirements-{}.txt".format(platform))],
                              env={'PYTHONHOME': env_path, 'PATH': os.environ['PATH']})
        if os.path.exists(os.path.join(dest_path, '..', 'node_modules')):
            print("Installing JS dependencies... (this may take a while)")
            invoke_npm(["install", "--silent"], cwd=os.path.join(dest_path, '..'))

        self.set_current_sdk('tintin')
        print("Generated an SDK linked to {}.".format(path))

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
