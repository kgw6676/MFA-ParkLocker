import cv2
import numpy as np
import config
from config import NUM_BAYS, STABLE_FRAMES

# config.py에 해당 변수가 없으면 기본값 사용
USB_CAMERA_INDEX = getattr(config, 'USB_CAMERA_INDEX', 0)

# 1, 2, 3번 주차칸의 화면상 좌표 (x1, y1, x2, y2) -> 실제 하드웨어 조립 후 캘리브레이션 필요
BAY_ROIS = getattr(config, 'BAY_ROIS', {
    1: (50, 100, 200, 350),
    2: (230, 100, 380, 350),
    3: (410, 100, 560, 350),
})

class Camera:
    """USB 카메라 기반 주차칸 감지 인터페이스."""
    def __init__(self):
        self.observations = {i: False for i in range(1, NUM_BAYS + 1)}
        self.stable = self.observations.copy()
        self.counts = {i: 0 for i in self.observations}
        
        self.cap = cv2.VideoCapture(USB_CAMERA_INDEX)
        self.baseline = None       # 차가 없을 때의 기준 화면(Grayscale)
        self.diff_threshold = 35   # 픽셀 밝기 차이 임계값
        self.area_ratio = 0.25     # ROI 면적의 25% 이상 변화 시 주차된 것으로 판정

    def calibrate_empty(self):
        """빈 주차장 상태를 기준 이미지로 저장 (초기화 시 1회 호출)."""
        if not self.cap.isOpened():
            return False
        ret, frame = self.cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.baseline = cv2.GaussianBlur(gray, (21, 21), 0)
            return True
        return False

    def predict(self):
        # 카메라가 연결되지 않은 PC 환경 등에서는 기존 simulate() 값 유지
        if not self.cap.isOpened():
            return self.observations.copy()

        ret, frame = self.cap.read()
        if not ret:
            return self.observations.copy()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)

        # 첫 프레임을 빈 주차장 기준으로 자동 설정
        if self.baseline is None:
            self.baseline = blurred
            return self.observations.copy()

        frame_diff = cv2.absdiff(self.baseline, blurred)
        _, thresh = cv2.threshold(frame_diff, self.diff_threshold, 255, cv2.THRESH_BINARY)

        result = {}
        for bay_num, (x1, y1, x2, y2) in BAY_ROIS.items():
            roi = thresh[y1:y2, x1:x2]
            changed_pixels = cv2.countNonZero(roi)
            total_pixels = (x2 - x1) * (y2 - y1)
            occupied = (changed_pixels / total_pixels) > self.area_ratio
            result[bay_num] = bool(occupied)  # 반드시 파이썬 기본 bool로 변환

        self.observations = result
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

    def release(self):
        if self.cap.isOpened():
            self.cap.release()