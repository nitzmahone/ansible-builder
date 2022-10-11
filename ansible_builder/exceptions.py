import sys


class DefinitionError(RuntimeError):
    # Eliminate the output of traceback before our custom error message prints out
    sys.tracebacklimit = 0

    def __init__(self, msg, path=None):
        super(DefinitionError, self).__init__("%s" % msg)
        self.msg = msg
        self.path = path
