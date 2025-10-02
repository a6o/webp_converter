# WebP 이미지 변환기

> **English** | [**Read in English**](README.md)

이미지를 Webp로 바꿔줍니다. 오른쪽의 Releases에서 exe를 다운받아서 실행해주시면 됩니다. 

그 외 방법은 아래 참조. 

## 파이썬으로 실행하기
```bash
pip install -r requirements.txt
python webp_converter.py
```

## 직접 빌드

### 필수 요구사항
- Python 3.8 이상
- Windows 10/11

### 빌드
```bash
# 저장소 복제
git clone https://github.com/yourusername/webp_converter.git
cd webp_converter

# 의존성 설치
pip install -r requirements.txt

# 실행 파일 빌드
build.bat

# dist/WebP_Converter.exe에서 실행 파일 확인
```

## 버전
- v1.0.3 - 사진 크기 수정 등등
- v1.0.2 - 향상된 설정 대화상자, 빠른 변환