"""Raspberry Pi CSI camera face enrollment/verification.

SIMULATION=True: in-memory enrollment, for end-to-end UI tests only.
Real mode: Picamera2 + OpenCV contrib LBPH; experimental classroom prototype,
NOT a secure biometric authentication system.
"""
from pathlib import Path
import time

from config import SIMULATION


class FaceAuth:
    def __init__(self, simulation=None, data_dir='face_data', camera_factory=None):
        self.simulation = SIMULATION if simulation is None else simulation
        self.data_dir = Path(data_dir)
        self._sim_registered = set()
        self.camera_factory = camera_factory
        self.samples = 12
        self.timeout = 20
        self.threshold = 65.0  # Tune with real test data; lower is stricter for LBPH.

    def _dependencies(self):
        try:
            import cv2
            import numpy as np
            if not hasattr(cv2, 'face') or not hasattr(cv2.face, 'LBPHFaceRecognizer_create'):
                raise RuntimeError('opencv-contrib의 cv2.face.LBPHFaceRecognizer_create가 필요합니다.')
            if self.camera_factory is None:
                from picamera2 import Picamera2
                factory = Picamera2
            else:
                factory = self.camera_factory
            return cv2, np, factory
        except ImportError as e:
            raise RuntimeError('Picamera2, numpy, opencv-contrib 설치가 필요합니다.') from e

    def _capture(self, cv2, factory, needed):
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        detector = cv2.CascadeClassifier(cascade_path)
        if detector.empty():
            raise RuntimeError('얼굴 검출 모델을 불러올 수 없습니다.')
        camera = factory()
        faces = []
        try:
            camera.configure(camera.create_preview_configuration(main={'size': (640, 480), 'format': 'RGB888'}))
            camera.start()
            deadline = time.monotonic() + self.timeout
            while time.monotonic() < deadline and len(faces) < needed:
                frame = camera.capture_array()
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                boxes = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(75, 75))
                # Avoid accepting ambiguous frames with multiple faces.
                if len(boxes) == 1:
                    x, y, w, h = boxes[0]
                    cropped = cv2.resize(gray[y:y+h, x:x+w], (160, 160))
                    faces.append(cropped)
                time.sleep(0.18)
        finally:
            try:
                camera.stop()
            finally:
                camera.close()
        return faces

    def _path(self, number):
        number = int(number)
        if number < 1 or number > 3:
            raise ValueError('잘못된 주차칸 번호입니다.')
        return self.data_dir / f'slot_{number}.yml'

    def enroll(self, number):
        path = self._path(number)
        if self.simulation:
            self._sim_registered.add(int(number))
            return True
        cv2, np, factory = self._dependencies()
        faces = self._capture(cv2, factory, self.samples)
        if len(faces) < self.samples:
            return False
        model = cv2.face.LBPHFaceRecognizer_create()
        model.train(faces, np.full(len(faces), int(number), dtype=np.int32))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix('.tmp.yml')
        try:
            model.write(str(temp))
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)
        return True

    def verify(self, number):
        path = self._path(number)
        if self.simulation:
            return int(number) in self._sim_registered
        if not path.exists():
            return False
        cv2, np, factory = self._dependencies()
        model = cv2.face.LBPHFaceRecognizer_create()
        model.read(str(path))
        faces = self._capture(cv2, factory, 5)
        if len(faces) < 3:
            return False
        matches = 0
        for face in faces:
            label, confidence = model.predict(face)
            if label == int(number) and confidence <= self.threshold:
                matches += 1
        return matches >= 3

    def delete(self, number):
        path = self._path(number)
        if self.simulation:
            self._sim_registered.discard(int(number))
            return True
        path.unlink(missing_ok=True)
        return True
