from __future__ import absolute_import, print_function, division
__author__ = 'katharine'

from six import iteritems

import os
import signal
import subprocess

from pebble_tool.commands.base import PebbleCommand
from pebble_tool.sdk import sdk_manager
from pebble_tool.sdk.emulator import ManagedEmulatorTransport
from pebble_tool.exceptions import ToolError


class GdbCommand(PebbleCommand):
    """Connects a debugger to the current app. Only works in the emulator."""
    command = 'gdb'
    valid_connections = {'emulator'}

    @classmethod
    def _find_app_load_offset(cls, fw_elf, kind):
        elf_sections = subprocess.check_output(["arm-none-eabi-readelf", "-W", "-s", fw_elf])

        # Figure out where we load the app into firmware memory
        for line in elf_sections.split(b'\n'):
            if b'__{}_flash_load_start__'.format(kind) in line:
                return int(line.split()[1], 16)
        else:
            raise ToolError("Couldn't find the {} address offset.".format(kind))

    @classmethod
    def _find_real_app_section_offsets(cls, base_addr, app_elf_path):
        offsets = {}
        for line in subprocess.check_output(["arm-none-eabi-objdump", "-h", app_elf_path]).decode('utf-8').split('\n'):
            cols = line.split()
            if len(cols) < 4:
                continue

            if cols[1] in ('.text', '.data', '.bss'):
                offsets[cols[1][1:]] = int(cols[3], 16) + base_addr
        return offsets

    def _get_symbol_command(self, elf, kind):
        base_address = self._find_app_load_offset(self._fw_elf, kind)
        offsets = self._find_real_app_section_offsets(base_address, elf)

        add_symbol_file = 'add-symbol-file "{elf}" {text} '.format(elf=elf, **offsets)
        del offsets['text']
        add_symbol_file += ' '.join('-s .{} {}'.format(k, v) for k, v in iteritems(offsets))

        return add_symbol_file

    def __call__(self, args):
        super(GdbCommand, self).__call__(args)
        # We poke around in the ManagedEmulatorTransport, so it's important that we actually have one.
        # Just asserting is okay because this should already be enforced by valid_connections.
        assert isinstance(self.pebble.transport, ManagedEmulatorTransport)

        platform = self.pebble.transport.platform
        sdk_version = self.pebble.transport.version
        gdb_port = self.pebble.transport.qemu_gdb_port
        if gdb_port is None:
            raise ToolError("The emulator does not have gdb support. Try killing and re-running it.")

        sdk_root = sdk_manager.path_for_sdk(sdk_version)
        self._fw_elf = os.path.join(sdk_root, 'pebble', platform, 'qemu', '{}_sdk_debug.elf'.format(platform))

        if not os.path.exists(self._fw_elf):
            raise ToolError("SDK {} does not support app debugging. You need at least SDK 3.10.".format(sdk_version))

        app_elf_path = os.path.join(os.getcwd(), 'build', platform, 'pebble-app.elf')
        if not os.path.exists(app_elf_path):
            raise ToolError("No app debugging information available. "
                            "You must be in a project directory and have built the app.")

        gdb_commands = [
            "set charset US-ASCII",  # Avoid a bug in the ancient version of libiconv apple ships.
            "target remote :{}".format(gdb_port),
            "set confirm off",
            self._get_symbol_command(app_elf_path, 'app')
        ]

        # Optionally add the worker symbols, if any exist.
        worker_elf_path = os.path.join(os.getcwd(), 'build', platform, 'pebble-worker.elf')
        if os.path.exists(worker_elf_path):
            gdb_commands.append(self._get_symbol_command(worker_elf_path, 'worker'))

        gdb_commands.extend([
            "set confirm on",
            "break app_crashed",  # app crashes (as of FW 3.10) go through this symbol for our convenience.
            'echo \nPress ctrl-D or type \'quit\' to exit.\n',
            'echo Try `pebble gdb --help` for a short cheat sheet.\n',
        ])

        gdb_args = ['arm-none-eabi-gdb', self._fw_elf, '-q'] + ['--ex={}'.format(x) for x in gdb_commands]

        # Ignore SIGINT, or we'll die every time the user tries to pause execution.
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        subprocess.call(gdb_args)

    epilog = """
gdb cheat sheet:
  ctrl-C                Pause app execution.
  ctrl-D, quit          Quit gdb.
  continue, c           Continue app execution.
  break, b              Set a breakpoint. This can be either a symbol or a
                        position:
                         - `b show_train_info` to break when entering a
                            function.
                         - `b stop_info.c:45` to break on line 45 of stop_info.c.
  step, s               Step forward one line.
  next, n               Step *over* the current line, avoiding stopping for
                        any functions it calls into.
  finish                Run forward until exiting the current stack frame.
  backtrace, bt         Print out the current call stack.
  p [expression]        Print the result of evaluating the given expression.
  set var x = foo       Set the value of the variable x to foo.
  info args             Show the values of arguments to the current function.
  info locals           Show local variables in the current frame.
  bt full               Show all local variables in all stack frames.
  info break            List break points (#1 is <app_crashed>, and is
                        inserted by the pebble tool).
  delete [n]            Delete breakpoint #n.
"""
