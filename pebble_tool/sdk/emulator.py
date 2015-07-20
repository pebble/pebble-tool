from __future__ import absolute_import
__author__ = 'katharine'

from six.moves import range

import errno
import json
import logging
import os
import os.path
import platform
import shutil
import signal
import socket
import subprocess
import tempfile
import time

from libpebble2.communication.transports.websocket import WebsocketTransport
from libpebble2.exceptions import ConnectionError

from pebble_tool.account import get_default_account
from pebble_tool.exceptions import MissingEmulatorError, ToolError
from pebble_tool.util.analytics import post_event
from . import sdk_path, get_sdk_persist_dir

logger = logging.getLogger("pebble_tool.sdk.emulator")
black_hole = open(os.devnull, 'w')

def get_emulator_info_path(platform):
    return os.path.join(tempfile.gettempdir(), 'pb-{}.json'.format(platform))

def get_emulator_info(platform):
    try:
        with open(get_emulator_info_path(platform)) as f:
            return json.load(f)
    except (OSError, IOError):
        return None


class ManagedEmulatorTransport(WebsocketTransport):
    def __init__(self, platform):
        self.platform = platform
        self._find_ports()
        super(ManagedEmulatorTransport, self).__init__('ws://localhost:{}/'.format(self.pypkjs_port))

    def connect(self):
        self._spawn_processes()
        for i in range(10):
            time.sleep(0.5)
            try:
                super(ManagedEmulatorTransport, self).connect()
            except ConnectionError:
                continue
            else:
                return
        super(ManagedEmulatorTransport, self).connect()

    def _find_ports(self):
        info = get_emulator_info(self.platform)
        qemu_running = False
        if info is not None:
            if self._is_pid_running(info['qemu']['pid']):
                qemu_running = True
                self.qemu_port = info['qemu']['port']
                self.qemu_serial_port = info['qemu']['serial']
                self.qemu_pid = info['qemu']['pid']
            else:
                self.qemu_pid = None

            if self._is_pid_running(info['pypkjs']['pid']):
                if qemu_running:
                    self.pypkjs_port = info['pypkjs']['port']
                    self.pypkjs_pid = info['pypkjs']['pid']
                else:
                    logger.info("pypkjs is alive, but qemu is not, so we're killing it.")
                    os.kill(info['pypkjs']['pid'], signal.SIGKILL)
                    self.pypkjs_pid = None
            else:
                self.pypkjs_pid = None
        else:
            self.qemu_pid = None
            self.pypkjs_pid = None

        if self.qemu_pid is None:
            self.qemu_port = self._choose_port()
            self.qemu_serial_port = self._choose_port()

        if self.pypkjs_pid is None:
            self.pypkjs_port = self._choose_port()

    def _spawn_processes(self):
        if self.qemu_pid is None:
            logger.info("Spawning QEMU.")
            self._spawn_qemu()
        else:
            logger.info("QEMU is already running.")

        if self.pypkjs_pid is None:
            logger.info("Spawning pypkjs.")
            self._spawn_pypkjs()
        else:
            logger.info("pypkjs is already running.")

        self._save_state()

    def _save_state(self):
        d = {
            'qemu': {
                'pid': self.qemu_pid,
                'port': self.qemu_port,
                'serial': self.qemu_serial_port,
            },
            'pypkjs': {
                'pid': self.pypkjs_pid,
                'port': self.pypkjs_port,
            }
        }
        with open(self._pid_filename, 'w') as f:
            json.dump(d, f, indent=4)


    def _spawn_qemu(self):
        qemu_bin = os.path.join(sdk_path(), 'Pebble', 'common', 'qemu',
                                'qemu-system-arm_{}_{}'.format(platform.system(), platform.machine()))
        qemu_micro_flash = os.path.join(sdk_path(), 'Pebble', self.platform, 'qemu', "qemu_micro_flash.bin")
        qemu_spi_flash = self._get_spi_path()

        for path in (qemu_bin, qemu_micro_flash, qemu_spi_flash):
            if not os.path.exists(path):
                raise MissingEmulatorError("Can't launch emulator: missing required file at {}".format(path))

        command = [
            qemu_bin,
            "-rtc", "base=localtime",
            "-serial", "null",
            "-serial", "tcp::{},server,nowait".format(self.qemu_port),
            "-serial", "tcp::{},server".format(self.qemu_serial_port),
            "-pflash", qemu_micro_flash,
        ]

        platform_args = {
            'basalt': [
                '-machine', 'pebble-snowy-bb',
                '-cpu', 'cortex-m4',
                '-pflash', qemu_spi_flash,
            ],
            'aplite': [
                '-machine', 'pebble-bb2',
                '-cpu', 'cortex-m3',
                '-mtdblock', qemu_spi_flash,
            ]
        }

        command.extend(platform_args[self.platform])
        logger.info("Qemu command: %s", subprocess.list2cmdline(command))
        process = subprocess.Popen(command, stdout=self._get_output(), stderr=self._get_output())
        time.sleep(0.2)
        if process.poll() is not None:
            try:
                subprocess.check_output(command, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                raise MissingEmulatorError("Couldn't launch emulator:\n{}".format(e.output.strip()))
        self.qemu_pid = process.pid
        self._wait_for_qemu()

    def _wait_for_qemu(self):
        logger.info("Waiting for the firmware to boot.")
        for i in range(20):
            time.sleep(0.2)
            try:
                s = socket.create_connection(('localhost', self.qemu_serial_port))
            except socket.error:
                logger.debug("QEMU not ready yet.")
                pass
            else:
                break
        else:
            post_event("qemu_launched", success=False, reason="qemu_launch_timeout")
            raise ToolError("Emulator launch timed out.")
        received = ''
        while True:
            received += s.recv(256)
            # PBL-21275: we'll add less hacky solutions for this to the firmware.
            if "<SDK Home>" in received or "<Launcher>" in received:
                break
        s.close()
        post_event("qemu_launched", success=True)
        logger.info("Firmware booted.")

    def _copy_spi_image(self, path):
        sdk_qemu_spi_flash = os.path.join(sdk_path(), 'Pebble', self.platform, 'qemu', 'qemu_spi_flash.bin')
        if not os.path.exists(sdk_qemu_spi_flash):
            raise MissingEmulatorError("Your SDK does not support the Pebble Emulator.")
        else:
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            shutil.copy(sdk_qemu_spi_flash, path)

    def _get_spi_path(self, platform=None):
        if platform is None:
            platform = self.platform
        path = os.path.join(get_sdk_persist_dir(platform), 'qemu_spi_flash.bin')
        if not os.path.exists(path):
            self._copy_spi_image(path)
        return path

    def _spawn_pypkjs(self):
        phonesim_bin = os.path.join(sdk_path(), 'Pebble', 'common', 'phonesim', 'phonesim.py')
        layout_file = os.path.join(sdk_path(), 'Pebble', self.platform, 'qemu', "layouts.json")

        command = [
            phonesim_bin,
            "--qemu", "localhost:{}".format(self.qemu_port),
            "--port", str(self.pypkjs_port),
            "--persist", get_sdk_persist_dir(self.platform),
            "--layout", layout_file,
            '--debug',
        ]

        account = get_default_account()
        if account.is_logged_in:
            command.extend(['--oauth', account.bearer_token])
        if logger.getEffectiveLevel() <= logging.DEBUG:
            command.append('--debug')
        logger.info("pypkjs command: %s", subprocess.list2cmdline(command))
        process = subprocess.Popen(command, stdout=self._get_output(), stderr=self._get_output())
        time.sleep(0.5)
        if process.poll() is not None:
            try:
                subprocess.check_output(command, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                raise MissingEmulatorError("Couldn't launch pypkjs:\n{}".format(e.output.strip()))
        self.pypkjs_pid = process.pid

    def _get_output(self):
        if logger.getEffectiveLevel() <= logging.DEBUG:
            return None
        else:
            return black_hole

    @property
    def _pid_filename(self):
        return get_emulator_info_path(self.platform)

    @classmethod
    def _choose_port(cls):
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    @classmethod
    def _is_pid_running(cls, pid):
        # PBL-21228: This isn't going to work on Windows.
        try:
            os.kill(pid, 0)
        except OSError as e:
            if e.errno == 3:
                return False
            else:
                raise
        return True

    @classmethod
    def is_platform_alive(cls, platform):
        info = get_emulator_info(platform)
        if info is None:
            return False
        return cls._is_pid_running(info['pypkjs']['pid']) and cls._is_pid_running(info['pypkjs']['pid'])
