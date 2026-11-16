import config

class Camera:
    def __init__(self):
        self.observations = {n: False for n in range(1, config.NUM_BAYS + 1)}
        self.stable = self.observations.copy()
        self.counts = {n: 0 for n in self.observations}
        self.baseline = None
        self.cap = None
        if not config.SIMULATION:
            import cv2
            self.cv2 = cv2
            self.cap = cv2.VideoCapture(config.USB_CAMERA_INDEX)
            if not self.cap.isOpened():
                raise RuntimeError('USB 카메라를 열 수 없습니다.')

    def calibrate_empty(self):
        """Call ONLY after visually confirming all parking bays are empty."""
        if config.SIMULATION:
            return True
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError('빈 주차장 기준 영상 촬영 실패')
        gray = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2GRAY)
        self.baseline = self.cv2.GaussianBlur(gray, (21, 21), 0)
        return True

    def predict(self):
        if config.SIMULATION:
            return self.observations.copy()
        if self.baseline is None:
            raise RuntimeError('빈 주차장 기준 영상이 없습니다. 빈 주차장 확인 후 calibrate_empty()를 실행하세요.')
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError('USB 카메라 프레임 읽기 실패')
        cv2 = self.cv2
        gray = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (21, 21), 0)
        if gray.shape != self.baseline.shape:
            raise RuntimeError('카메라 해상도가 기준 영상과 다릅니다.')
        diff = cv2.absdiff(self.baseline, gray)
        _, mask = cv2.threshold(diff, getattr(config, 'CAMERA_DIFF_THRESHOLD', 35), 255, cv2.THRESH_BINARY)
        height, width = mask.shape
        rois = getattr(config, 'BAY_ROIS', {1:(50,100,200,350),2:(230,100,380,350),3:(410,100,560,350)})
        if set(rois) != set(self.observations):
            raise ValueError('BAY_ROIS는 모든 주차칸을 포함해야 합니다.')
        result = {}
        for number, (x1,y1,x2,y2) in rois.items():
            if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
                raise ValueError(f'{number}번 칸 ROI가 영상 범위를 벗어났습니다.')
            changed = cv2.countNonZero(mask[y1:y2,x1:x2])
            result[number] = bool(changed / ((x2-x1)*(y2-y1)) > getattr(config, 'CAMERA_AREA_RATIO', 0.25))
        return result

    def get_occupancy(self):
        current = self.predict()
        if set(current) != set(self.stable) or any(type(v) is not bool for v in current.values()):
            raise ValueError('카메라 결과는 각 주차칸의 bool 점유 상태여야 합니다.')
        for number, value in current.items():
            if value == self.stable[number]:
                self.counts[number] = 0
            else:
                self.counts[number] += 1
                if self.counts[number] >= config.STABLE_FRAMES:
                    self.stable[number] = value
                    self.counts[number] = 0
        return self.stable.copy()

    def simulate(self, number, occupied):
        if not config.SIMULATION:
            raise RuntimeError('실제 카메라 모드에서는 simulate()를 사용할 수 없습니다.')
        if number not in self.observations:
            raise ValueError('없는 주차칸입니다.')
        self.observations[number] = bool(occupied)

    def release(self):
        if self.cap is not None:
            self.cap.release()
