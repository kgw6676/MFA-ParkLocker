import time
import serial
import adafruit_fingerprint
import config

FINGERPRINT_PORT = getattr(config, 'FINGERPRINT_PORT', '/dev/serial0')
FINGERPRINT_BAUD = getattr(config, 'FINGERPRINT_BAUD', 57600)

class FingerprintAuth:
    def __init__(self):
        self.uart = serial.Serial(FINGERPRINT_PORT, baudrate=FINGERPRINT_BAUD, timeout=1)
        self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)

    def _wait_for_finger(self, slot_buffer, timeout=10.0):
        """지정된 시간 내에 지문을 읽고 특징점 버퍼(1 또는 2)로 변환."""
        start = time.time()
        while time.time() - start < timeout:
            res = self.finger.get_image()
            if res == adafruit_fingerprint.OK:
                if self.finger.image_2_tz(slot_buffer) == adafruit_fingerprint.OK:
                    return True
                return False
            elif res == adafruit_fingerprint.NOFINGER:
                time.sleep(0.1)
            else:
                return False
        return False

    def enroll(self, number, timeout=15.0):
        """주차칸 번호(1~3)를 슬롯 ID로 사용하여 지문 2회 스캔 후 등록."""
        print(f'[{number}번 칸] 첫 번째 지문을 대주세요.')
        if not self._wait_for_finger(1, timeout):
            return False

        # 손가락을 뗄 때까지 대기
        time.sleep(1.0)
        start = time.time()
        while self.finger.get_image() != adafruit_fingerprint.NOFINGER:
            if time.time() - start > 5.0:
                break
            time.sleep(0.1)

        print(f'[{number}번 칸] 확인을 위해 한 번 더 지문을 대주세요.')
        if not self._wait_for_finger(2, timeout):
            return False

        if self.finger.create_model() != adafruit_fingerprint.OK:
            return False

        if self.finger.store_model(number) != adafruit_fingerprint.OK:
            return False

        print(f'[{number}번 칸] 지문 등록 완료')
        return True

    def verify(self, number, timeout=10.0):
        """지문을 스캔하여 해당 주차칸 번호(number)에 등록된 지문과 일치하는지 확인."""
        print(f'[{number}번 칸] 출차 인증용 지문을 대주세요.')
        if not self._wait_for_finger(1, timeout):
            return False

        if self.finger.finger_search() != adafruit_fingerprint.OK:
            return False

        # 검색된 지문 ID가 요청한 주차칸 번호와 일치하는지 확인
        if self.finger.finger_id == number and self.finger.confidence >= 50:
            print(f'[{number}번 칸] 지문 인증 성공 (신뢰도: {self.finger.confidence})')
            return True
        return False

    def delete(self, number):
        """출차 완료 후 해당 주차칸 슬롯의 지문 데이터 삭제."""
        res = self.finger.delete_model(number)
        return res == adafruit_fingerprint.OK