from live_inspect.uiautomation import UIAutomation
from live_inspect.config import BIN_PATH
from threading import Thread,Event
from time import sleep
import pythonnet
pythonnet.load()
import clr

class WatchCursor:
    def __init__(self):
        self.is_running = Event()
        self.cursor_watch_thread:Thread = None
        self.setup_dotnet()
    
    def setup_dotnet(self):
        paths=BIN_PATH.glob('*.dll')
        clr.AddReference("System")
        for path in paths:
            clr.AddReference(path.as_posix())

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def register_focus_changed(self,automation):
        from FlaUI.Core.AutomationElements import AutomationElement
        from System import Action
        focus_delegate = Action[AutomationElement](lambda _: None)
        return automation.RegisterFocusChangedEvent(focus_delegate)

    def unregister_focus_changed(self,automation,focus_handler):
        automation.UnregisterFocusChangedEvent(focus_handler)

    def focus_changed_func(self):
        from FlaUI.Core.Input import Mouse
        with UIAutomation() as automation:
            focus_handler = self.register_focus_changed(automation)
            try:
                while self.is_running.is_set():
                    point = Mouse.Position
                    try:
                        automation.FromPoint(point)
                    except Exception:
                        # Ignore permissions errors when inspecting specific windows
                        pass
                    sleep(1.0)
            finally:
                self.unregister_focus_changed(automation,focus_handler)
        self.is_running.clear()
    
    def get_mouse_position(self):
        from FlaUI.Core.Input import Mouse
        point=Mouse.Position
        return f'({point.X},{point.Y})'

    def start(self):
        self.cursor_watch_thread = Thread(name='watch_cursor_thread',target=self.focus_changed_func)
        self.is_running.set()
        self.cursor_watch_thread.start()

    def stop(self):
        self.is_running.clear()
        if self.cursor_watch_thread and self.cursor_watch_thread.is_alive():
            self.cursor_watch_thread.join(timeout=2.0)