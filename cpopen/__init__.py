#
# Copyright 2012 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#

"""
Python's implementation of Popen forks back to python before execing.
Forking a python proc is a very complex and volatile process.

This is a simpler method of execing that doesn't go back to python after
forking. This allows for faster safer exec.
"""

import inspect
import os
import sys
from subprocess import Popen, PIPE

from cpopen import createProcess


class CPopen(Popen):
    def __init__(self, args, close_fds=False, cwd=None, env=None,
                 deathSignal=0, childUmask=None,
                 stdin=PIPE, stdout=PIPE, stderr=PIPE):
        if not isinstance(args, list):
            args = list(args)

        if env is not None and not isinstance(env, list):
            env = list(("=".join(item) for item in env.iteritems()))

        self._childUmask = childUmask
        self._deathSignal = int(deathSignal)
        Popen.__init__(self, args,
                       close_fds=close_fds, cwd=cwd, env=env,
                       stdin=stdin, stdout=stdout,
                       stderr=stderr)

    def _execute_child_v276(
            self, args, executable, preexec_fn, close_fds,
            cwd, env, universal_newlines,
            startupinfo, creationflags, shell, to_close,
            p2cread, p2cwrite,
            c2pread, c2pwrite,
            errread, errwrite,
    ):

        return self._execute_child_v275(
            args, executable, preexec_fn,
            close_fds, cwd, env, universal_newlines,
            startupinfo, creationflags, shell,
            p2cread, p2cwrite,
            c2pread, c2pwrite,
            errread, errwrite,
        )

    def _execute_child_v275(
            self, args, executable, preexec_fn, close_fds,
            cwd, env, universal_newlines,
            startupinfo, creationflags, shell,
            p2cread, p2cwrite,
            c2pread, c2pwrite,
            errread, errwrite,
    ):

        try:
            pid, stdin, stdout, stderr = createProcess(
                args, close_fds,
                p2cread or -1, p2cwrite or -1,
                c2pread or -1, c2pwrite or -1,
                errread or -1, errwrite or -1,
                cwd, env,
                self._deathSignal,
                self._childUmask,
            )

            self.pid = pid
        except:
            # Keep the original exception and reraise it after all fds are
            # closed, ignoring error during close. This is needed only for
            # Python 2.6, as Python 2.7 already does this when _execute_child
            # raises.
            t, v, tb = sys.exc_info()
            for fd in (
                p2cread, p2cwrite,
                c2pread, c2pwrite,
                errread, errwrite,
            ):
                try:
                    if fd:
                        os.close(fd)
                except OSError:
                    pass
            raise t, v, tb

        # If child was started, close the unused fds on the parent side. Note
        # that we don't want to hide exceptions here.
        for fd in (
            p2cread,
            errwrite,
            c2pwrite
        ):
            if fd:
                os.close(fd)

    if 'to_close' in inspect.getargspec(Popen._execute_child).args:
        _execute_child = _execute_child_v276
    else:
        _execute_child = _execute_child_v275
