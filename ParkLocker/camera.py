from config import NUM_BAYS, STABLE_FRAMES

class Camera:
    """USB 카메라 기반 주차칸 감지 인터페이스. 실제 모델은 predict()에 연결."""
    def __init__(self):
        self.observations = {i: False for i in range(1, NUM_BAYS + 1)}
        self.stable = self.observations.copy()
        self.counts = {i: 0 for i in self.observations}

    def predict(self):
        # TODO: cv2.VideoCapture(USB_CAMERA_INDEX) 프레임을 영상 모델에 입력
        # 모델은 각 칸의 점유 여부를 bool로 반환해야 함
        return self.observations.copy()

    def get_occupancy(self):
        current = self.predict()
        if set(current) != set(self.stable):
            raise ValueError('카메라 결과는 1~3번 모든 주차칸을 포함해야 합니다.')
        for n, val in current.items():
            if type(val) is not bool:
                raise TypeError('주차칸 점유 결과는 bool이어야 합니다.')
            if val == self.stable[n]:
                self.counts[n] = 0
            else:
                self.counts[n] += 1
                if self.counts[n] >= STABLE_FRAMES:
                    self.stable[n] = val
                    self.counts[n] = 0
        return self.stable.copy()

    def simulate(self, number, occupied):
        if number not in self.observations:
            raise ValueError('없는 주차칸입니다.')
        self.observations[number] = bool(occupied)
