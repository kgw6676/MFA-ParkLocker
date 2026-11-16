import time
import config

class Gate:
    def __init__(self, name, pin=None, open_angle=90, close_angle=0):
        if name not in ('입구', '출구'):
            raise ValueError('차단기 이름은 입구 또는 출구여야 합니다.')
        self.name = name
        self.is_open = False
        self.open_angle = open_angle
        self.close_angle = close_angle
        self.servo = None
        self.pin = pin if pin is not None else (config.ENTRY_SERVO_GPIO if name == '입구' else config.EXIT_SERVO_GPIO)
        if not config.SIMULATION:
            from gpiozero import AngularServo
            self.servo = AngularServo(self.pin, min_angle=0, max_angle=180,
                                      min_pulse_width=0.0005, max_pulse_width=0.0025,
                                      initial_angle=None)

    def _move(self, angle):
        if self.servo is not None:
            self.servo.angle = angle
            time.sleep(0.5)
            self.servo.value = None

    def open(self):
        if not self.is_open:
            self._move(self.open_angle)
            self.is_open = True
            print(f'{self.name} 차단기 열림' + (' (시뮬레이션)' if self.servo is None else ''))

    def close(self):
        if self.is_open or self.servo is not None:
            self._move(self.close_angle)
        self.is_open = False
        print(f'{self.name} 차단기 닫힘' + (' (시뮬레이션)' if self.servo is None else ''))

    def release(self):
        if self.servo is not None:
            self.servo.close()
