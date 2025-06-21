import mss


class Grabber:
    _sct = mss.mss()

    def screenshot(self, output="screenshot.png"):
        monitor = self._sct.monitors[1]  # [0] — all, [1] — основной монитор
        screenshot = self._sct.grab(monitor)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=output)
        return output



