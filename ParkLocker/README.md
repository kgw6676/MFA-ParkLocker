# ParkLocker

라즈베리파이 기반 3칸 주차장, 얼굴·지문 이중 인증 프로젝트의 초기 뼈대입니다.

## 실행

Python 3 및 tkinter가 설치된 환경에서 `python main.py`.
현재는 UI와 상태 관리 구조를 확인하는 단계입니다. 영상 인식, 얼굴/지문 센서, GPIO 차단기 제어는 TODO이며 실제 인증이 동작하지 않습니다.

## 상태

- EMPTY: 빈 칸
- WAITING: 차량 감지, 등록 대기
- REGISTERED: 등록 완료
- EXITING: 인증 성공, 출차 대기

## 인터페이스

- `Camera.get_occupancy()` -> `{1: bool, 2: bool, 3: bool}`
- `FaceAuth.enroll/verify/delete(number)` -> 성공 여부(bool), 삭제는 성공 확인 필요
- `FingerprintAuth.enroll/verify/delete(number)` -> 성공 여부(bool), 삭제는 성공 확인 필요
- `Gate.open/close()` -> 차단기 구동
- `Buzzer.alert()` -> 실패 알림
- `Controller.update_camera/register/authenticate/finish_exit()` -> 전체 흐름

## 구현 전 필수 과제

1. `main.py`에서 주기적으로 카메라 감지 결과를 읽도록 연결
2. 주차 감지 안정화(연속 프레임 확인) 및 영상 모델 적용
3. 얼굴/지문 등록 실패 시 롤백과 등록 데이터 삭제 구현
4. 출구 통과 감지 센서 및 끼임 방지 인터록 구현
5. 실제 GPIO 핀과 서보/릴레이 구동, 안전한 기본 상태 정의
6. 재시작 시 상태 복구 및 비정상 종료 처리
7. 인증 시도 제한, 생체 템플릿 보호 및 출차 후 삭제
8. UI 등록·인증 페이지 구현 (현재 버튼은 안내만 표시)

**주의:** 현재 `finish_exit()`는 출차 센서 확인 없이 호출하면 안 됩니다. 실물 차단기 연결 전에 안전 인터록을 별도로 구현하세요.

## 확정된 하드웨어 사양 (2026-11-12)

- 주차 점유 판별: USB 웹캠 (OpenCV + 팀 자체 영상 모델)
- 얼굴 등록/검증: Raspberry Pi CSI 카메라 (Picamera2 기반, 팀 자체 얼굴 인증)
- 지문 등록/검증: UART 지문 센서 (`/dev/serial0`, 통신 속도는 모델별 확인)
- 입구/출구 차단기: 서보모터 2개 (실제 PWM 구동은 하드웨어 확인 후 구현)
- 경고: GPIO 부저
- 화면: Raspberry Pi용 4인치 터치스크린 (현재 UI 480x320, 실제 해상도 확인)

### 구현 규약 및 안전 사항

1. `camera.py`의 `predict()`는 `{1: bool, 2: bool, 3: bool}`을 반환한다. 기본 구현은 **시뮬레이션**이며 실제 웹캠 영상을 읽지 않는다. 4회 연속 같은 결과가 나와야 상태가 바뀐다.
2. `face.py`는 CSI 카메라 전용. `fingerprint.py`는 UART 센서 전용. **현재 둘 다 미구현**이며 실제 인증을 수행하지 않는다.
3. `gate.py`와 `buzzer.py`는 시뮬레이션. 핀 번호는 예시값이며 하드웨어 회로도 검토 전 실제 모터를 연결하지 않는다. 서보는 별도 전원 및 공통 접지, PWM 드라이버 검토가 필요하다.
4. `controller.py`는 `EXITING` 상태에서 주차칸이 비었다는 영상 결과가 확인된 경우에만 `finish_exit()`를 호출하도록 상위 흐름을 작성해야 한다. **현재 자동 호출은 없다.**
5. 카메라는 차량이 주차칸을 떠났다는 것만 확인한다. 출구 통과와 끼임 방지는 감지할 수 없으므로 `AUTO_CLOSE_EXIT_GATE=False`로 유지한다. 실제 운영에는 통과 감지 센서, 안전 인터록 및 수동 정지 장치가 필수다.
6. 인증 템플릿은 외부 공개 저장소에 올리지 말고, 실패 횟수 제한·암호화·출차 후 안전 삭제 정책을 추가한다. 미등록/미인증 차량은 자동 출차 허용 금지.
7. 카메라 프레임 처리 및 생체 인증은 UI 스레드를 막지 않도록 작업 스레드/프로세스로 분리한다. 현재 `ui.py`의 주기 폴링은 가벼운 모의 결과에만 적합하다.
8. Git 브랜치 추천: `feature/parking-camera`, `feature/face-auth`, `feature/fingerprint`, `feature/gates`, `feature/ui`. 각 담당자는 공통 인터페이스를 유지한다.

### 데모

`python main.py`로 화면 확인 가능. 시뮬레이션 상태 변경은 `controller.camera.simulate(1, True)` 후 4회 폴링하면 반영된다. 실물 차량 인식/생체 등록은 아직 동작하지 않는다.
