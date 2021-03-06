#
# Copyright 2012-2014 Red Hat, Inc.
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
import errno
import fcntl
import os
import platform
import shutil
import signal
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time

from unittest import TestCase
from nose.plugins.skip import SkipTest


def distutils_dir_name(dname):
    """Returns the name of a distutils build directory"""
    f = "{dirname}.{platform}-{machine}-{version[0]}.{version[1]}"
    return f.format(dirname=dname,
                    platform=platform.system().lower(),
                    machine=platform.machine(),
                    version=sys.version_info)


TESTS_DIR = os.path.dirname(__file__)
BUILD_DIR = os.path.join(TESTS_DIR, "..", "build", distutils_dir_name("lib"))
sys.path = [BUILD_DIR] + sys.path

import cpopen
from cpopen import CPopen, PIPE

EXT_ECHO = "/bin/echo"


class TestCPopen(TestCase):
    def testEcho(self):
        data = "Hello"
        p = CPopen([EXT_ECHO, "-n", data])
        out, err = p.communicate()
        self.assertTrue(p.returncode == 0,
                        "Process failed: %s" % os.strerror(p.returncode))
        self.assertEquals(out, data)

    def testCat(self):
        path = "/etc/passwd"
        p = CPopen(["cat", path])
        out, err = p.communicate()
        self.assertTrue(p.returncode == 0,
                        "Process failed: %s" % os.strerror(p.returncode))
        with open(path, "r") as f:
            self.assertEquals(out, f.read())

    def testCloseFDs(self):
        with open("/dev/zero") as f:
            p = CPopen(["sleep", "1"], close_fds=True)
            try:
                child_fds = set(os.listdir("/proc/%s/fd" % p.pid))
            finally:
                p.kill()
                p.wait()
            self.assertEqual(child_fds, set(["0", "1", "2"]))

    def testNoCloseFds(self):
        with open("/dev/zero") as f:
            p = CPopen(["sleep", "1"], close_fds=False)
            try:
                child_fds = set(os.listdir("/proc/%s/fd" % p.pid))
            finally:
                p.kill()
                p.wait()
            # We cannot know which fds will be inherited in the child since the
            # test framework may open some fds.
            self.assertTrue(str(f.fileno()) in child_fds)

    def testEnv(self):
        p = CPopen(["printenv"], env={"key": "value"})
        out, err = p.communicate()
        self.assertEqual(out, "key=value\n")

    def testEnvUnicodeKey(self):
        p = CPopen(["printenv"], env={u"\u05d0": "value"})
        out, err = p.communicate()
        self.assertEqual(out, "\xd7\x90=value\n")

    def testEnvUnicodeValue(self):
        p = CPopen(["printenv"], env={"key": u"\u05d0"})
        out, err = p.communicate()
        self.assertEqual(out, "key=\xd7\x90\n")

    def testCwd(self):
        cwd = "/proc"
        p = CPopen(["python", "-c", "import os; print os.getcwd()"],
                   cwd=cwd)
        out, err = p.communicate()
        self.assertTrue(p.returncode == 0,
                        "Process failed: %s" % os.strerror(p.returncode))
        self.assertEquals(out.strip(), cwd)

    def testRunNonExecutable(self):
        self.assertRaises(OSError, CPopen, ["/tmp"])

    def testBadCwd(self):
        self.assertRaises(OSError, CPopen, ["echo", "hello"],
                          cwd="/~~~~~dasdas~~~~")

    def testUnicodeArg(self):
        data = u'hello'
        cmd = [EXT_ECHO, "-n", data]

        p = CPopen(cmd)
        out, err = p.communicate()
        p2 = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out2, err2 = p2.communicate()
        self.assertEquals(out, out2)

    def testNonASCIIUnicodeArg(self):
        data = u'\u05e9\u05dc\u05d5\u05dd'
        # If the default encoding is not utf-8 the test *should* fail as non
        # ascii conversion shouldn't work
        if sys.getfilesystemencoding() != "UTF-8":
            raise SkipTest("The default encoding isn't unicode")

        cmd = [EXT_ECHO, "-n", data]

        p = CPopen(cmd)
        out, err = p.communicate()
        p2 = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out2, err2 = p2.communicate()
        self.assertEquals(out, out2)

    def testStdin(self):
        data = "Hello World"
        p = CPopen(["cat"])
        out, err = p.communicate(data)
        self.assertTrue(p.returncode == 0,
                        "Process failed: %s" % os.strerror(p.returncode))

        self.assertEquals(out, data)

    def testStdinEpoll(self):
        import select

        data = "Hello World"
        p = CPopen(["cat"])
        ep = select.epoll()
        ep.register(p.stdin, select.EPOLLOUT)
        fd, ev = ep.poll(1)[0]
        ep.close()
        os.write(fd, data)
        p.stdin.close()
        p.wait()
        self.assertTrue(p.returncode == 0,
                        "Process failed: %s" % os.strerror(p.returncode))

        self.assertEquals(p.stdout.read(), data)

    def testDeathSignal(self):
        # This is done because assignment in python doesn't cross scopes
        procPtr = [None]

        def spawn():
            procPtr[0] = CPopen(["sleep", "1"],
                                deathSignal=signal.SIGKILL)

        t = threading.Thread(target=spawn)
        t.start()
        t.join()
        self.assertEqual(procPtr[0].wait(), -signal.SIGKILL)

    def testUmaskChange(self):
        p = CPopen(['sh', '-c', 'umask'], childUmask=0o007)
        out, err = p.communicate()
        self.assertEquals(out.splitlines()[0].strip(), '0007')

    def testUmaskTmpfile(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            name = os.path.join(tmp_dir, "file.txt")
            p = CPopen(['touch', name], childUmask=0o007)
            p.wait()
            data = os.stat(name)
            self.assertTrue(data.st_mode & stat.S_IROTH == 0,
                            "%s is world-readable" % name)
            self.assertTrue(data.st_mode & stat.S_IWOTH == 0,
                            "%s is world-writeable" % name)
            self.assertTrue(data.st_mode & stat.S_IXOTH == 0,
                            "%s is world-executable" % name)
        finally:
            shutil.rmtree(tmp_dir)

    def testNoEnt(self):
        try:
            CPopen(['there-is-no-executable-with-this/funny/name'])
        except OSError as ose:
            self.assertEquals(ose.errno, errno.ENOENT)
        else:
            self.fail('OSError not raised')

    def testNoStreams(self):
        p = CPopen(['true'], stdin=None, stdout=None, stderr=None)
        self.assertEqual(p.stdin, None)
        self.assertEqual(p.stdout, None)
        self.assertEqual(p.stderr, None)
        p.wait()
        self.assertEquals(p.returncode, 0)

    def testInheritParentFds(self):
        # From Python docs: With the default settings of None, no redirection
        # will occur; the child's file handles will be inherited from the
        # parent.
        with open("/dev/zero") as f:
            p = CPopen(["sleep", "1"], stdin=None, stdout=None, stderr=None,
                       close_fds=False)
            try:
                child_fds = set(os.listdir("/proc/%s/fd" % p.pid))
            finally:
                p.kill()
                p.wait()
            expected_fds = set(["0", "1", "2", str(f.fileno())])
        self.assertEqual(child_fds, expected_fds)

    def testInheritParentFdsCloseFds(self):
        # From Python docs: If close_fds is true, all file descriptors except
        # 0, 1 and 2 will be closed before the child process is executed.
        with open("/dev/zero") as f:
            p = CPopen(["sleep", "1"], stdin=None, stdout=None, stderr=None,
                       close_fds=True)
            try:
                child_fds = set(os.listdir("/proc/%s/fd" % p.pid))
            finally:
                p.kill()
                p.wait()
        self.assertEqual(child_fds, set(["0", "1", "2"]))

    def testCloseOnExecStdin(self):
        # Unset close-on-exec on stdin fd
        data = "data"
        with tempfile.NamedTemporaryFile() as f:
            f.write(data)
            f.flush()
            set_close_on_exec(f.fileno())
            p = CPopen(["cat", f.name], stdin=f.fileno(), stdout=PIPE)
            out, err = p.communicate()
            self.assertEqual(out, data)

    def testCloseOnExecStdout(self):
        # Unset close-on-exec on stdout fd
        with tempfile.NamedTemporaryFile() as f:
            set_close_on_exec(f.fileno())
            p = CPopen(["sh", "-c", "echo -n data >&1"], stdout=f.fileno())
            p.wait()
            f.seek(0)
            self.assertEqual(f.read(), "data")

    def testCloseOnExecStderr(self):
        # Unset close-on-exec on stderr fd
        with tempfile.NamedTemporaryFile() as f:
            set_close_on_exec(f.fileno())
            p = CPopen(["sh", "-c", "echo -n data >&2"], stderr=f.fileno())
            p.wait()
            f.seek(0)
            self.assertEqual(f.read(), "data")

    # references about pipe/SIGPIPE tests:
    # https://bugzilla.redhat.com/show_bug.cgi?id=1117751#c4
    # http://bugs.python.org/issue1652
    def testBrokenPipe(self):
        p = CPopen(["sleep", "1"])
        try:
            p.send_signal(signal.SIGPIPE)
        finally:
            p.kill()
        p.wait()
        self.assertEqual(p.returncode, -signal.SIGKILL)

    def testBrokenPipeSIGPIPERestored(self):
        if not cpopen.SUPPORTS_RESTORE_SIGPIPE:
            raise SkipTest("subprocess module does not support restore_sigpipe")
        p = CPopen(["sleep", "1"], restore_sigpipe=True)
        try:
            p.send_signal(signal.SIGPIPE)
        finally:
            p.kill()
        p.wait()
        self.assertEqual(p.returncode, -signal.SIGPIPE)

    def testUserFd(self):
        data = "it works!"
        with tempfile.TemporaryFile() as f:
            p = CPopen(["echo", "-n", data], stdout=f.fileno())
            p.wait()
            f.seek(0)
            self.assertEqual(data, f.read())

    def testUserFdNoClose(self):
        with tempfile.TemporaryFile() as f:
            self.assertRaises(OSError, CPopen, ["echo", "fail"],
                              stdout=f.fileno(), cwd="/nodir")
            self.assertEqual("", f.read())

    def testUserFile(self):
        data = "it works!"
        with tempfile.TemporaryFile() as f:
            p = CPopen(["echo", "-n", data], stdout=f)
            p.wait()
            f.seek(0)
            self.assertEqual(data, f.read())

    def testUserFileNoClose(self):
        with tempfile.TemporaryFile() as f:
            self.assertRaises(OSError, CPopen, ["echo", "fail"], stdout=f,
                              cwd="/nodir")
            self.assertEqual("", f.read())

    def testUserFileWithRedirect(self):
        data = "it works!"
        with tempfile.TemporaryFile() as f:
            p = CPopen(["echo", "-n", data], stdout=f, stderr=f)
            p.wait()
            f.seek(0)
            self.assertEqual(data, f.read())

    def testPipeline(self):
        # echo -n 'it works!' | cat
        data = "it works!"
        p2 = CPopen(["cat"], stdin=PIPE, stdout=PIPE)
        try:
            p1 = CPopen(["echo", "-n", data], stdin=PIPE, stdout=p2.stdin)
            p1.wait()
        finally:
            out, err = p2.communicate()
        self.assertEqual(data, out)


def set_close_on_exec(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    flags |= fcntl.FD_CLOEXEC
    return fcntl.fcntl(fd, fcntl.F_SETFD, flags)
