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
        if count < 1:
            raise ValueError('주차칸은 최소 1개 필요합니다.')
        self.bays = {i: Bay(i) for i in range(1, count + 1)}

    def get_bay(self, number):
        if number not in self.bays:
            raise ValueError(f'{number}번 주차칸이 없습니다.')
        return self.bays[number]

    def detect(self, number, occupied):
        bay = self.get_bay(number)
        if type(occupied) is not bool:
            raise TypeError('차량 감지 결과는 bool이어야 합니다.')
        bay.occupied = occupied
        if occupied and bay.status == Status.EMPTY:
            bay.status = Status.WAITING
        elif not occupied and bay.status == Status.WAITING:
            bay.status = Status.EMPTY
        # REGISTERED: 인증 없이 차량이 사라지면 등록 정보를 보존하고 경고 대상으로 유지.
        # EXITING: 출차 확정은 controller에서 생체정보 삭제까지 처리한 후 수행.
        return bay.status

    def register(self, number):
        bay = self.get_bay(number)
        if bay.status != Status.WAITING or not bay.occupied:
            raise ValueError('등록 가능한 주차칸이 아닙니다.')
        bay.status = Status.REGISTERED

    def authorize_exit(self, number):
        bay = self.get_bay(number)
        if bay.status != Status.REGISTERED or not bay.occupied:
            raise ValueError('출차 인증 가능한 상태가 아닙니다.')
        bay.status = Status.EXITING

    def complete_exit(self, number):
        bay = self.get_bay(number)
        if bay.status != Status.EXITING or bay.occupied:
            raise ValueError('출차 완료를 확인할 수 없습니다.')
        bay.status = Status.EMPTY

    def cancel_exit(self, number):
        bay = self.get_bay(number)
        if bay.status == Status.EXITING:
            if not bay.occupied:
                raise ValueError('차량이 사라진 상태에서는 출차를 취소할 수 없습니다.')
            bay.status = Status.REGISTERED

    def is_full(self):
        return all(b.occupied for b in self.bays.values())

    def restore(self, data):
        # 저장된 상태는 재부팅 후 실제 카메라 감지 결과와 다를 수 있다.
        for number, bay in self.bays.items():
            saved = data.get(str(number))
            if not isinstance(saved, dict):
                continue
            try:
                status = Status(saved['status'])
                occupied = saved['occupied']
                if type(occupied) is not bool:
                    continue
                if status == Status.EMPTY and occupied:
                    continue
                if status == Status.WAITING and not occupied:
                    continue
                bay.status = status
                bay.occupied = occupied
            except (KeyError, ValueError, TypeError):
                continue
