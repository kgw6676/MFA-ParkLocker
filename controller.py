import logging

from parking import Parking, Status
from camera import Camera
from face import FaceAuth
from fingerprint import FingerprintAuth
from gate import Gate
from buzzer import Buzzer
from storage import Storage
from config import NUM_BAYS, AUTO_CLOSE_EXIT_GATE

logger = logging.getLogger(__name__)


class Controller:
    def __init__(self, camera=None, face=None, fingerprint=None,
                 entry=None, exit_gate=None, buzzer=None, storage=None):
        self.parking = Parking(NUM_BAYS)
        self.camera = camera if camera is not None else Camera()
        self.face = face if face is not None else FaceAuth()
        self.fingerprint = fingerprint if fingerprint is not None else FingerprintAuth()
        self.entry = entry if entry is not None else Gate('입구')
        self.exit = exit_gate if exit_gate is not None else Gate('출구')
        self.buzzer = buzzer if buzzer is not None else Buzzer()
        self.storage = storage if storage is not None else Storage()
        self.last_error = None
        self._exit_opened = False

        try:
            self.parking.restore(self.storage.load())
        except (OSError, ValueError, TypeError) as e:
            self.last_error = f'저장 정보 복구 실패: {e}'
            logger.exception(self.last_error)
        # 재부팅 후에도 출구 차단기가 열려 있어야 하는지는 별도 안전장치로 판단.
        # EXITING 상태는 유지하고 자동 폐쇄하지 않는다.
        self.sync_entry()

    def _save(self):
        try:
            self.storage.save(self.parking)
            return True
        except (OSError, ValueError, TypeError) as e:
            self.last_error = f'상태 저장 실패: {e}'
            logger.exception(self.last_error)
            return False

    def sync_entry(self):
        try:
            if self.parking.is_full():
                self.entry.close()
            else:
                self.entry.open()
            return True
        except Exception as e:
            self.last_error = f'입구 차단기 제어 실패: {e}'
            logger.exception(self.last_error)
            return False

    def update_camera(self):
        self.last_error = None
        try:
            detected = self.camera.get_occupancy()
            if not isinstance(detected, dict) or set(detected) != set(self.parking.bays):
                raise ValueError('카메라 결과의 주차칸 번호가 올바르지 않습니다.')
            if any(type(v) is not bool for v in detected.values()):
                raise TypeError('카메라 결과는 bool이어야 합니다.')
            for number, occupied in detected.items():
                self.parking.detect(number, occupied)
            self.sync_entry()
            # 출차 승인된 차량이 사라졌을 때만 자동 완료.
            for number, bay in self.parking.bays.items():
                if bay.status == Status.EXITING and not bay.occupied:
                    self.finish_exit(number)
            self._save()
            return True
        except Exception as e:
            self.last_error = f'카메라 처리 실패: {e}'
            logger.exception(self.last_error)
            return False

    def _cleanup_registration(self, number):
        success = True
        for device in (self.face, self.fingerprint):
            try:
                if device.delete(number) is False:
                    success = False
            except Exception:
                success = False
                logger.exception('등록 취소 중 정보 삭제 실패: %s', number)
        return success

    def register(self, number):
        self.last_error = None
        try:
            bay = self.parking.get_bay(number)
            if bay.status != Status.WAITING or not bay.occupied:
                self.last_error = '등록 가능한 주차칸이 아닙니다.'
                return False
            if self.face.enroll(number) is not True:
                self.last_error = '얼굴 등록에 실패했습니다.'
                self._cleanup_registration(number)
                return False
            if self.fingerprint.enroll(number) is not True:
                self.last_error = '지문 등록에 실패했습니다.'
                self._cleanup_registration(number)
                return False
            self.parking.register(number)
            return self._save()
        except Exception as e:
            self.last_error = f'등록 처리 오류: {e}'
            logger.exception(self.last_error)
            self._cleanup_registration(number)
            return False

    def authenticate(self, number):
        self.last_error = None
        try:
            bay = self.parking.get_bay(number)
            if bay.status != Status.REGISTERED or not bay.occupied:
                self.last_error = '출차 인증 가능한 상태가 아닙니다.'
                return False
            if self.face.verify(number) is not True or self.fingerprint.verify(number) is not True:
                self.last_error = '얼굴 또는 지문이 일치하지 않습니다.'
                self.buzzer.alert()
                return False
            # 차단기를 먼저 열고, 성공한 경우에만 출차 승인 상태로 전환.
            self.exit.open()
            self._exit_opened = True
            self.parking.authorize_exit(number)
            return self._save()
        except Exception as e:
            self.last_error = f'인증 또는 출구 차단기 오류: {e}'
            logger.exception(self.last_error)
            return False

    def finish_exit(self, number):
        self.last_error = None
        try:
            bay = self.parking.get_bay(number)
            if bay.status != Status.EXITING or bay.occupied:
                self.last_error = '출차 완료 조건을 충족하지 않았습니다.'
                return False
            # 삭제가 실패하면 상태를 유지하고 다음 감지 주기에 재시도한다.
            # 두 삭제를 모두 호출하므로 delete()는 반복 호출해도 안전해야 한다.
            deleted = True
            for device in (self.face, self.fingerprint):
                try:
                    if device.delete(number) is False:
                        deleted = False
                except Exception:
                    deleted = False
                    logger.exception('출차 후 생체정보 삭제 실패: %s', number)
            if not deleted:
                self.last_error = '생체정보 삭제 실패: 재시도 필요'
                return False
            self.parking.complete_exit(number)
            self._save()
            self.sync_entry()
            # 주차칸이 비었다는 사실만으로 차량의 출구 통과는 보장되지 않음.
            if AUTO_CLOSE_EXIT_GATE:
                logger.warning('출구 자동 닫힘은 별도 통과 안전 센서 없이 사용하면 안 됩니다.')
                # 실제 하드웨어에서 안전 확인이 없으므로 자동 닫기는 수행하지 않음.
            return True
        except Exception as e:
            self.last_error = f'출차 완료 처리 오류: {e}'
            logger.exception(self.last_error)
            return False

    def cancel_exit(self, number):
        try:
            self.parking.cancel_exit(number)
            return self._save()
        except (ValueError, OSError) as e:
            self.last_error = str(e)
            return False
