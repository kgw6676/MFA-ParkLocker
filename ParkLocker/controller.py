from parking import Parking, Status
from camera import Camera
from face import FaceAuth
from fingerprint import FingerprintAuth
from gate import Gate
from buzzer import Buzzer
from storage import Storage
from config import AUTO_CLOSE_EXIT_GATE

class Controller:
    def __init__(self):
        self.parking = Parking()
        self.camera = Camera()
        self.face = FaceAuth()
        self.fingerprint = FingerprintAuth()
        self.entry = Gate('입구')
        self.exit = Gate('출구')
        self.buzzer = Buzzer()
        self.storage = Storage()
        self.sync_entry()

    def sync_entry(self):
        if self.parking.is_full():
            self.entry.close()
        else:
            self.entry.open()

    def update_camera(self):
        for number, occupied in self.camera.get_occupancy().items():
            self.parking.detect(number, occupied)
        self.sync_entry()
        self.storage.save(self.parking)

    def register(self, number):
        if self.parking.bays[number].status != Status.WAITING:
            return False
        # 두 등록 모두 성공한 후에만 상태 변경
        if self.face.enroll(number) and self.fingerprint.enroll(number):
            self.parking.register(number)
            self.storage.save(self.parking)
            return True
        return False

    def authenticate(self, number):
        if self.parking.bays[number].status != Status.REGISTERED:
            return False
        if self.face.verify(number) and self.fingerprint.verify(number):
            self.parking.authorize_exit(number)
            self.exit.open()
            self.storage.save(self.parking)
            return True
        self.buzzer.alert()
        return False

    def finish_exit(self, number):
        # 카메라로 주차칸이 비었는지 확인한 뒤 호출; 통과 여부는 확인 불가
        # 비었는지 확인 후 몇 초 기다리고 닫을까 고민 중
        self.parking.complete_exit(number)
        self.face.delete(number)
        self.fingerprint.delete(number)
        if AUTO_CLOSE_EXIT_GATE:
            self.exit.close()
        self.sync_entry()
        self.storage.save(self.parking)
