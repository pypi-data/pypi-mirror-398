class UIAutomation:
    def __init__(self):
        self.automation = None

    def __enter__(self):
        from FlaUI.UIA3 import UIA3Automation
        self.automation = UIA3Automation()
        return self.automation
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self.automation:
            self.automation.Dispose()
            self.automation = None