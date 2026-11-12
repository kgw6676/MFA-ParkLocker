class Gate:
    def __init__(self, name):
        self.name = name
        self.is_open = False

    def open(self):
        self.is_open = True
        print(f'{self.name} 차단기 열림 (시뮬레이션)')

    def close(self):
        self.is_open = False
        print(f'{self.name} 차단기 닫힘 (시뮬레이션)')
