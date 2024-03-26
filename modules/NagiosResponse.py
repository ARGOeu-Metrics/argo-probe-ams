class NagiosResponse(object):
    _msgBagWarning = []
    _msgBagCritical = []
    _msgBagOk = []
    _msgBagUnknown = []
    _okMsg = ""
    _code = None

    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3

    def __init__(self, ok_msg=""):
        self._code = self.OK
        self._okMsg = ok_msg

    def writeWarningMessage(self, msg):
        self._msgBagWarning.append(msg)

    def writeOkMessage(self, msg):
        self._msgBagOk.append(msg)

    def writeCriticalMessage(self, msg):
        self._msgBagCritical.append(msg)

    def writeUnknownMessage(self, msg):
        self._msgBagUnknown.append(msg)

    def setCode(self, code):
        self._code = code

    def getCode(self):
        return self._code

    def getMsg(self):
        if self._code == self.WARNING:
            return "WARNING - " + self._toString(self._msgBagWarning)
        elif self._code == self.CRITICAL:
            return "CRITICAL - " + self._toString(self._msgBagCritical)
        elif self._code == self.OK:
            msg = self._okMsg if self._okMsg else self._toString(self._msgBagOk)
            return "OK - " + msg
        elif self._code == self.UNKNOWN:
            msg = self._toString(self._msgBagUnknown)
            return "UNKNOWN - " + msg

    def _toString(self, msgArray):
        return ' / '.join(msgArray)
