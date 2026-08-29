# 영수증 정산 시스템 (Retreat Receipt Manager)

단체 행사 시 다수의 인원이 산발적으로 청구하는 영수증을 효율적으로 취합하고, 실시간으로 예산을 관리하기 위해 개발한 웹 기반 정산 시스템입니다. 
기존 수기 작성이나 엑셀 취합 방식의 번거로움을 해결하고, 제한된 서버 환경에서 발생하는 이미지 처리 병목 현상을 소프트웨어적으로 최적화한 프로젝트입니다.

## Tech Stack
- Backend: Python 3.x, Flask, SQLite3
- Frontend: HTML5, CSS3, Vanilla JavaScript, SheetJS
- Data Processing: Pillow (PIL), pytesseract, PyMuPDF (fitz)

## 프로젝트 발전 과정 및 트러블슈팅

실제 사용자(총무)의 요구사항을 반영하며 단계적으로 기능을 고도화하고 성능을 최적화했습니다.

### 1. MVP 구현 및 기초 OCR 연동
- Flask와 SQLite를 활용해 영수증 이미지와 청구 내역을 저장하는 기본 시스템 구축.
- Tesseract OCR을 연동하여 영수증 내 결제 금액과 일자를 자동 추출해 사용자가 입력한 값과 대조하는 기능 구현.

### 2. 칸반 보드 기반의 예산 추적 기능 도입
- 지출 내역을 [팀 -> 세부 카테고리]의 2 Depth 구조로 재설계.
- 팀별(총괄, 찬양, 레크, 나눔) 배정 예산 대비 지출 금액을 계산하여 잔여 예산 및 소진율(%)을 실시간으로 보여주는 칸반 보드 UI 도입.
- 특수 비즈니스 로직 적용: '모임지원비' 항목의 경우 참석 인원에 따라 1인당 한도(12,000원)를 계산하여 지원 가능 금액을 시스템이 자동 보정.

### 3. 관리자(총무) 기능 고도화
- 외부 수입 관리: 지출뿐만 아니라 이월금, 후원금 등 수입 내역을 추가하여 총 예산에 동적 반영되도록 로직 수정.
- 실무 맞춤형 UX: 관리자 대시보드 내에서 [정산완료], [실물영수증 확인] 상태를 토글할 수 있는 기능 추가.
- 프라이빗 메모: 엑셀 추출 시에만 포함되고 일반 사용자에게는 노출되지 않는 관리자 전용 메모 컬럼 추가.

### 4. 제한된 서버 환경에서의 OCR 성능 극한 최적화 (Troubleshooting)

[문제 상황]
무료 호스팅 서버(단일 코어, 제한된 메모리) 환경에서 스마트폰으로 촬영한 고해상도(5~15MB) 원본 이미지를 OCR로 분석할 때, 처리 시간이 10초 이상 소요되어 다중 접속 시 HTTP Timeout 에러가 빈번하게 발생했습니다.

[해결 과정]
서버 사양을 업그레이드하는 대신, 소프트웨어 단에서 이미지 연산량을 최소화하는 3단계 전처리 파이프라인을 구축했습니다.

① Downscaling (픽셀 연산량 축소)
Pillow를 활용해 원본 이미지의 종횡비를 유지한 채 최대 해상도를 800x800px로 제한하여 연산 픽셀 수를 대폭 감소시켰습니다.

② 1-Bit Binarization (메모리 점유율 최소화)
단순한 그레이스케일(8-bit) 변환에 그치지 않고, 임계값(Threshold=140)을 설정해 모든 픽셀을 완벽한 흑(0)과 백(255)으로 치환하는 1-bit 이진화 연산을 적용했습니다.
```python
img = img.convert('L')
img = img.point(lambda x: 0 if x < 140 else 255, '1')
```

③ Whitelist & PSM Tuning (엔진 연산 범위 통제)
영수증에서 추출해야 할 핵심 정보는 '숫자(금액)'와 '날짜'뿐이므로, 연산이 무거운 한국어 모델 대신 가벼운 영어 모델을 사용했습니다. 
또한 whitelist 옵션을 주입해 알파벳 등 불필요한 문자 탐색을 원천 차단했습니다.
```python
custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789,-./'
extracted_text = pytesseract.image_to_string(img, lang='eng', config=custom_config)
```

[최종 결과]
기존 10~15초 소요되던 분석 시간을 1.5초 이내로 단축(약 85~90% 성능 향상)시켜 Timeout 문제를 완전히 해결하고 사용자 경험을 개선했습니다.

## 핵심 기능 요약
- 스마트 영수증 제출: 이미지/PDF 업로드 및 OCR 자동 금액 대조.
- 실시간 예산 대시보드: 팀별/카테고리별 지출 현황 및 수입 내역 합산 관리.
- 관리자 통합 제어: 영수증 정보 즉각 수정, 정산/실물 토글, 비밀 메모 작성.
- 원클릭 엑셀 내보내기: SheetJS를 활용하여 화면에 렌더링된 데이터를 완벽한 포맷의 정산 내역서로 자동 변환.

## 로컬 환경 실행 방법

1. Repository 클론 및 필수 패키지 설치
```bash
git clone https://github.com/사용자이름/Retreat-Receipt-Manager.git
cd Retreat-Receipt-Manager
pip install -r requirements.txt
```

2. Tesseract OCR 설치 (시스템 환경)
- Ubuntu: sudo apt-get install tesseract-ocr
- Windows: Tesseract-OCR 바이너리 설치 후 시스템 환경변수(PATH)에 등록

3. 로컬 서버 실행
```bash
python flask_app.py
```
브라우저에서 [http://127.0.0.1:5000](http://127.0.0.1:5000) 으로 접속하여 확인합니다.
