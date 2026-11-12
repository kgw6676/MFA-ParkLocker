class FingerprintAuth:
    def enroll(self, number):
        # TODO: 지문 센서 등록
        raise NotImplementedError('지문 센서 연결 필요')

    def verify(self, number):
        # TODO: 지문 센서 대조
        raise NotImplementedError('지문 센서 연결 필요')

    def delete(self, number):
        # TODO: 지문 센서 템플릿 삭제
        raise NotImplementedError('지문 정보 삭제 구현 필요')
