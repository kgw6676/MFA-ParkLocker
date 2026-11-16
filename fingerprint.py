import time
import config

class FingerprintAuth:
    def __init__(self):
        self.uart = None
        self.finger = None
        self.simulated = set()
        if not config.SIMULATION:
            import serial
            import adafruit_fingerprint
            self.api = adafruit_fingerprint
            self.uart = serial.Serial(config.FINGERPRINT_PORT,
                                      baudrate=getattr(config, 'FINGERPRINT_BAUDRATE', 57600),
                                      timeout=1)
            self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)

    def _wait_for_finger(self, buffer_id, timeout=10):
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            result = self.finger.get_image()
            if result == self.api.OK:
                return self.finger.image_2_tz(buffer_id) == self.api.OK
            if result != self.api.NOFINGER:
                return False
            time.sleep(0.1)
        return False

    def _wait_for_release(self, timeout=5):
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            result = self.finger.get_image()
            if result == self.api.NOFINGER:
                return True
            if result != self.api.OK:
                return False
            time.sleep(0.1)
        return False

    def enroll(self, number, timeout=15):
        if number not in range(1, config.NUM_BAYS + 1):
            return False
        if config.SIMULATION:
            self.simulated.add(number)
            return True
        print(f'{number}번 칸: 지문을 대주세요.')
        if not self._wait_for_finger(1, timeout):
            return False
        if not self._wait_for_release():
            return False
        print('손가락을 다시 대주세요.')
        if not self._wait_for_finger(2, timeout):
            return False
        if self.finger.create_model() != self.api.OK:
            return False
        return self.finger.store_model(number) == self.api.OK

    def verify(self, number, timeout=10):
        if config.SIMULATION:
            return number in self.simulated
        if not self._wait_for_finger(1, timeout):
            return False
        if self.finger.finger_search() != self.api.OK:
            return False
        minimum = getattr(config, 'FINGERPRINT_MIN_CONFIDENCE', 50)
        return self.finger.finger_id == number and self.finger.confidence >= minimum

    def delete(self, number):
        if config.SIMULATION:
            self.simulated.discard(number)
            return True
        return self.finger.delete_model(number) == self.api.OK

    def release(self):
        if self.uart is not None:
            self.uart.close()
