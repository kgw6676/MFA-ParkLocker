import time
import config

class Buzzer:
    def __init__(self, pin=None):
        self.buzzer = None
        if not config.SIMULATION:
            from gpiozero import Buzzer as GPIOBuzzer
            self.buzzer = GPIOBuzzer(pin if pin is not None else config.BUZZER_GPIO)

    def alert(self, repeat=3):
        print('부저 경고음' + (' (시뮬레이션)' if self.buzzer is None else ''))
        if self.buzzer is None:
            return
        try:
            for _ in range(repeat):
                self.buzzer.on()
                time.sleep(0.15)
                self.buzzer.off()
                time.sleep(0.1)
        finally:
            self.buzzer.off()

    def release(self):
        if self.buzzer is not None:
            self.buzzer.close()
