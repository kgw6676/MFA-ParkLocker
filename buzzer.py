import time
from gpiozero import Buzzer as GPIOBuzzer
import config

BUZZER_PIN = getattr(config, 'BUZZER_PIN', 22)  # GPIO 22 (물리 핀 15번)

class Buzzer:
    def __init__(self, pin=None):
        target_pin = pin if pin is not None else BUZZER_PIN
        self.buzzer = GPIOBuzzer(target_pin)

    def alert(self, repeat=3):
        """인증 실패 시 짧은 경고음 3회 출력."""
        print('부저 경고음 발생!')
        for _ in range(repeat):
            self.buzzer.on()
            time.sleep(0.15)
            self.buzzer.off()
            time.sleep(0.1)