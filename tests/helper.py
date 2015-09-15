import sys
import os

cmd = sys.argv[1]
if cmd == "fds":
    try:
        os.close(int(sys.argv[2]))
        print "False"
    except:
        print "True"

elif cmd == "nofds":
    try:
        os.close(int(sys.argv[2]))
        print "True"
    except:
        print "False"
