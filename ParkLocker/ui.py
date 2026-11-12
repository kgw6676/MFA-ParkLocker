import tkinter as tk
from parking import Status

class ParkingUI:
    def __init__(self, root, controller):
        self.root = root
        self.ctrl = controller
        root.title('ParkLocker')
        root.geometry('480x320')
        self.message = tk.StringVar(value='주차칸을 선택하세요')
        self.buttons = []
        tk.Label(root, text='ParkLocker 주차 현황', font=('Arial', 17, 'bold')).pack(pady=10)
        frame = tk.Frame(root)
        frame.pack(fill='both', expand=True)
        for i in range(1, 4):
            b = tk.Button(frame, command=lambda n=i: self.select(n), font=('Arial', 12))
            b.pack(side='left', fill='both', expand=True, padx=4, pady=8)
            self.buttons.append(b)
        tk.Label(root, textvariable=self.message, font=('Arial', 11)).pack(pady=10)
        self.refresh()
        self.poll_camera()

    def refresh(self):
        names = {Status.EMPTY: '빈 칸', Status.WAITING: '등록 대기', Status.REGISTERED: '주차중', Status.EXITING: '출차중'}
        for i, b in enumerate(self.buttons, 1):
            status = self.ctrl.parking.bays[i].status
            b.config(text=f'{i}번\n{names[status]}', bg='#F6CECE' if status != Status.EMPTY else '#D9F0D6')
        self.root.after(500, self.refresh)

    def poll_camera(self):
        try:
            self.ctrl.update_camera()
        except Exception as e:
            self.message.set(f"카메라 오류: {e}")
        self.root.after(500, self.poll_camera)

    def select(self, number):
        status = self.ctrl.parking.bays[number].status
        if status == Status.EMPTY:
            self.message.set('차량이 없는 칸입니다')
        elif status == Status.WAITING:
            self.message.set('얼굴·지문 등록 장치 연동 대기 중')
        elif status == Status.REGISTERED:
            self.message.set('얼굴·지문 인증 장치 연동 대기 중')
        else:
            self.message.set('출차 진행 중입니다')
