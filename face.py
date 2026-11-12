class FaceAuth:
    def enroll(self, number):
        # TODO: 카메라로 얼굴 템플릿 등록
        raise NotImplementedError('얼굴 등록 장치 연결 필요')

    def verify(self, number):
        # TODO: 등록된 얼굴 템플릿과 비교
        raise NotImplementedError('얼굴 인증 장치 연결 필요')

    def delete(self, number):
        # TODO: 등록된 얼굴 정보 삭제
        raise NotImplementedError('얼굴 정보 삭제 구현 필요')
