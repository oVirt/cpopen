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


SUPPORTS_RESTORE_SIGPIPE = (
    'restore_sigpipe' in inspect.getargspec(Popen.__init__).args
)


class CPopen(Popen):

    def __init__(self, args, close_fds=False, cwd=None, env=None,
                 deathSignal=0, childUmask=None,
                 stdin=PIPE, stdout=PIPE, stderr=PIPE,
                 restore_sigpipe=False):
        if not isinstance(args, list):
            args = list(args)

        self._childUmask = childUmask
        self._deathSignal = int(deathSignal)

        if SUPPORTS_RESTORE_SIGPIPE:
            kw = {'restore_sigpipe': restore_sigpipe}
        else:
            kw = {}

        Popen.__init__(self, args,
                       close_fds=close_fds, cwd=cwd, env=env,
                       stdin=stdin, stdout=stdout,
                       stderr=stderr,
                       **kw)

    def _execute_child_v276(
            self, args, executable, preexec_fn, close_fds,
            cwd, env, universal_newlines,
            startupinfo, creationflags, shell, to_close,
            p2cread, p2cwrite,
            c2pread, c2pwrite,
            errread, errwrite,
            restore_sigpipe=False
    ):

        return self._execute_child_v275(
            args, executable, preexec_fn,
            close_fds, cwd, env, universal_newlines,
            startupinfo, creationflags, shell,
            p2cread, p2cwrite,
            c2pread, c2pwrite,
            errread, errwrite,
            restore_sigpipe=restore_sigpipe,
            _to_close=to_close
        )

    def _execute_child_v275(
            self, args, executable, preexec_fn, close_fds,
            cwd, env, universal_newlines,
            startupinfo, creationflags, shell,
            p2cread, p2cwrite,
            c2pread, c2pwrite,
            errread, errwrite,
            restore_sigpipe=False,
            _to_close=None
    ):

        if env is not None and not isinstance(env, list):
            env = list(("=".join(item) for item in env.iteritems()))

        if _to_close is None:
            _to_close = self._fds_to_close(p2cread, p2cwrite,
                                           c2pread, c2pwrite,
                                           errread, errwrite)

        def close_fd(fd):
            _to_close.remove(fd)
            os.close(fd)

        try:
            pid, stdin, stdout, stderr = createProcess(
                args, close_fds,
                p2cread or -1, p2cwrite or -1,
                c2pread or -1, c2pwrite or -1,
                errread or -1, errwrite or -1,
                cwd, env,
                self._deathSignal,
                self._childUmask,
                restore_sigpipe
            )

            self.pid = pid
        except:
            # Keep the original exception and reraise it after all fds are
            # closed, ignoring error during close. This is needed only for
            # Python 2.6, as Python 2.7 already does this when _execute_child
            # raises.
            t, v, tb = sys.exc_info()
            for fd in list(_to_close):
                try:
                    close_fd(fd)
                except OSError:
                    pass
            raise t, v, tb

        # If child was started, close the unused fds on the parent side. Note
        # that we don't want to hide exceptions here.
        for fd in (p2cread, c2pwrite, errwrite):
            if fd in _to_close:
                close_fd(fd)

    def _fds_to_close(self, p2cread, p2cwrite,
                      c2pread, c2pwrite,
                      errread, errwrite):
        """
        Return a set of fds owned by us and may be closed for version of Python
        that do not provide the to_close argument in _execute_child.

        When calling Popen with PIPE, we create new pipe, and both sides of the
        pipe may be closed.

        When calling Popen with existing file descriptor or file like object,
        one side of the pipe will be None, and we may not close the other
        side, since it belongs to the caller.
        """
        to_close = set()

        for fdpair in ((p2cread, p2cwrite),
                       (c2pread, c2pwrite),
                       (errread, errwrite)):
            if None not in fdpair:
                to_close.update(fdpair)

        return to_close

    if 'to_close' in inspect.getargspec(Popen._execute_child).args:
        _execute_child = _execute_child_v276
    else:
        _execute_child = _execute_child_v275
