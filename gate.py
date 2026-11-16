import time
from gpiozero import AngularServo
import config

GATE_PINS = getattr(config, 'GATE_PINS', {
    '입차': 17,   # GPIO 17 (물리 핀 11번)
    '출차': 27,   # GPIO 27 (물리 핀 13번)
})

class Gate:
    def __init__(self, name, pin=None, open_angle=90, close_angle=0):
        self.name = name
        self.is_open = False
        self.open_angle = open_angle
        self.close_angle = close_angle

        target_pin = pin if pin is not None else GATE_PINS.get(name, 17)
        # SG-90 표준 펄스 폭 (0.5ms ~ 2.5ms) 설정
        self.servo = AngularServo(
            target_pin,
            min_angle=0,
            max_angle=180,
            min_pulse_width=0.0005,
            max_pulse_width=0.0025
        )
        self.close()

    def _move(self, angle):
        self.servo.angle = angle
        time.sleep(0.5)          # 차단기 암이 회전할 시간 확보
        self.servo.value = None  # 떨림(Jitter) 및 발열 방지를 위해 PWM 신호 차단

    def open(self):
        if not self.is_open:
            self._move(self.open_angle)
            self.is_open = True
            print(f'{self.name} 차단기 열림')

    def close(self):
        self._move(self.close_angle)
        self.is_open = False
        print(f'{self.name} 차단기 닫힘')