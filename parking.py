from dataclasses import dataclass
from enum import Enum

class Status(str, Enum):
    EMPTY = 'EMPTY'
    WAITING = 'WAITING'
    REGISTERED = 'REGISTERED'
    EXITING = 'EXITING'

@dataclass
class Bay:
    number: int
    status: Status = Status.EMPTY
    occupied: bool = False

class Parking:
    def __init__(self, count=3):
        self.bays = {i: Bay(i) for i in range(1, count + 1)}

    def detect(self, number, occupied):
        bay = self.bays[number]
        bay.occupied = occupied
        if occupied and bay.status == Status.EMPTY:
            bay.status = Status.WAITING
        elif not occupied and bay.status == Status.WAITING:
            bay.status = Status.EMPTY
        return bay.status

    def register(self, number):
        bay = self.bays[number]
        if bay.status != Status.WAITING or not bay.occupied:
            raise ValueError('등록 가능한 주차칸이 아닙니다.')
        bay.status = Status.REGISTERED

    def authorize_exit(self, number):
        bay = self.bays[number]
        if bay.status != Status.REGISTERED:
            raise ValueError('출차 인증 가능한 상태가 아닙니다.')
        bay.status = Status.EXITING

    def complete_exit(self, number):
        bay = self.bays[number]
        if bay.status != Status.EXITING or bay.occupied:
            raise ValueError('출차 완료를 확인할 수 없습니다.')
        bay.status = Status.EMPTY

    def cancel_exit(self, number):
        bay = self.bays[number]
        if bay.status == Status.EXITING:
            bay.status = Status.REGISTERED

    def is_full(self):
        return all(b.occupied for b in self.bays.values())
