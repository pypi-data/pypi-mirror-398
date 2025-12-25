import sys
import time

import servicemanager as sm
import win32event
import win32service
import win32serviceutil as win32su


class GenXAIService(win32su.ServiceFramework):
    _svc_name_ = "GenXAIService"
    _svc_display_name_ = "GenX AI Service"
    _svc_description_ = "AI for industry"

    def __init__(self, args):
        win32su.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        sm.LogMsg(
            sm.EVENTLOG_INFORMATION_TYPE, sm.PYS_SERVICE_STARTED, (self._svc_name_, "")
        )
        while self.running:
            # Your main service code
            self.main()
            time.sleep(60)
        sm.LogMsg(
            sm.EVENTLOG_INFORMATION_TYPE, sm.PYS_SERVICE_STOPPED, (self._svc_name_, "")
        )

    def main(self):
        print("GenX AI Service is running...")

        from genx_ai.listener import Listener

        listener = Listener()
        try:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            listener.listen()
        except KeyboardInterrupt:
            listener.stop()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sm.Initialize()
        sm.PrepareToHostSingle(GenXAIService)
        sm.StartServiceCtrlDispatcher()
    else:
        win32su.HandleCommandLine(GenXAIService)
