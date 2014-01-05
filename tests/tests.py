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
import os
import sys
import stat
import subprocess
from nose.plugins.skip import SkipTest
import signal
import threading
import time
import tempfile
import posix
import sysconfig

from unittest import TestCase


def distutils_dir_name(dname):
    """Returns the name of a distutils build directory"""
    f = "{dirname}.{platform}-{version[0]}.{version[1]}"
    return f.format(dirname=dname,
                    platform=sysconfig.get_platform(),
                    version=sys.version_info)


BUILD_DIR = os.path.join("..", "build", distutils_dir_name("lib"))
sys.path = [BUILD_DIR] + sys.path

from cpopen import CPopen

EXT_ECHO = "/bin/echo"
EXT_HELPER = os.path.join(os.path.dirname(__file__), 'helper.py')


class TestCPopen(TestCase):
    def testEcho(self):
        data = "Hello"
        p = CPopen([EXT_ECHO, "-n", data])
        p.wait()
        self.assertTrue(p.returncode == 0,
                        "Process failed: %s" % os.strerror(p.returncode))
        self.assertEquals(p.stdout.read(), data)

    def testCat(self):
        path = "/etc/passwd"
        p = CPopen(["cat", path])
        p.wait()
        self.assertTrue(p.returncode == 0,
                        "Process failed: %s" % os.strerror(p.returncode))
        with open(path, "r") as f:
            self.assertEquals(p.stdout.read(), f.read())

    def _subTest(self, name, params, *args, **kwargs):
        p = CPopen(["python", EXT_HELPER, name] + params,
                   *args, **kwargs)
        p.wait()
        self.assertTrue(p.returncode == 0,
                        "Process failed: %s" % os.strerror(p.returncode))
        self.assertEquals(p.stdout.read().strip(), "True")

    def testCloseFDs(self):
        fds = os.pipe()
        try:
            self._subTest("fds", [str(fds[1])], close_fds=True)
        finally:
            os.close(fds[0])
            os.close(fds[1])

    def testNoCloseFds(self):
        fds = os.pipe()
        try:
            self._subTest("nofds", [str(fds[1])], close_fds=False)
        finally:
            os.close(fds[0])
            os.close(fds[1])

    def testEnv(self):
        env = os.environ.copy()
        env["TEST"] = "True"
        self._subTest("env", [], env=env)

    def testCwd(self):
        cwd = "/proc"
        p = CPopen(["python", "-c", "import os; print os.getcwd()"],
                   cwd=cwd)
        p.wait()
        self.assertTrue(p.returncode == 0,
                        "Process failed: %s" % os.strerror(p.returncode))
        self.assertEquals(p.stdout.read().strip(), cwd)

    def testRunNonExecutable(self):
        self.assertRaises(OSError, CPopen, ["/tmp"])

    def testBadCwd(self):
        self.assertRaises(OSError, CPopen, ["echo", "hello"],
                          cwd="/~~~~~dasdas~~~~")

    def testUnicodeArg(self):
        data = u'hello'
        cmd = [EXT_ECHO, "-n", data]

        p = CPopen(cmd)
        p.wait()
        p2 = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p2.wait()
        self.assertEquals(p.stdout.read(), p2.stdout.read())

    def testNonASCIIUnicodeArg(self):
        data = u'\u05e9\u05dc\u05d5\u05dd'
        # If the default encoding is not utf-8 the test *should* fail as non
        # ascii conversion shouldn't work
        if sys.getfilesystemencoding() != "UTF-8":
            raise SkipTest("The default encoding isn't unicode")

        cmd = [EXT_ECHO, "-n", data]

        p = CPopen(cmd)
        p.wait()
        p2 = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p2.wait()
        self.assertEquals(p.stdout.read(), p2.stdout.read())

    def testStdin(self):
        data = "Hello World"
        p = CPopen(["cat"])
        p.stdin.write(data)
        p.stdin.flush()
        p.stdin.close()
        p.wait()
        self.assertTrue(p.returncode == 0,
                        "Process failed: %s" % os.strerror(p.returncode))

        self.assertEquals(p.stdout.read(), data)

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
            procPtr[0] = CPopen(["sleep", "10"],
                                deathSignal=signal.SIGKILL)

        t = threading.Thread(target=spawn)
        t.start()
        t.join()
        start = time.time()
        procPtr[0].wait()
        self.assertTrue(time.time() - start < 1)

    def testUmaskChange(self):
        p = CPopen(['umask'], childUmask=0o007)
        p.wait()
        out = p.stdout.readlines()
        self.assertEquals(out[0].strip(), '0007')

    def testUmaskTmpfile(self):
        tmp_dir = tempfile.mkdtemp()
        name = os.path.join(tmp_dir, "file.txt")
        p = CPopen(['touch', name], childUmask=0o007)
        p.wait()
        data = os.stat(name)
        os.unlink(name)
        self.assertTrue(data.st_mode & stat.S_IROTH == 0,
                        "%s is world-readable" % name)
        self.assertTrue(data.st_mode & stat.S_IWOTH == 0,
                        "%s is world-writeable" % name)
        self.assertTrue(data.st_mode & stat.S_IXOTH == 0,
                        "%s is world-executable" % name)
        posix.rmdir(tmp_dir)

    def testNoEnt(self):
        try:
            CPopen(['there-is-no-executable-with-this/funny/name'])
        except OSError as ose:
            self.assertEquals(ose.errno, errno.ENOENT)
        else:
            self.fail('OSError not raised')
