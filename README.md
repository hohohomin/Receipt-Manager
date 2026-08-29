# 영수증 스마트 정산 시스템 (Retreat Receipt Manager)

> **"복잡한 영수증과 예산 관리를 자동화하고, 총무의 업무 부담을 줄이기 위한 웹 기반 정산 시스템"**

![Python](https://img.shields.io/badge/Python-3.x-blue.svg) ![Flask](https://img.shields.io/badge/Flask-black?logo=flask) ![SQLite](https://img.shields.io/badge/SQLite-07405E?logo=sqlite&logoColor=white) ![VanillaJS](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)

## 프로젝트 개요
단체 행사 시 다수의 인원이 산발적으로 청구하는 영수증을 효율적으로 취합하고 관리하기 위해 개발되었습니다. 모바일 환경에서 영수증을 찍어 쉽게 제출할 수 있으며, 관리자는 칸반 보드(Kanban Board) 형태의 대시보드에서 예산 현황과 실물 영수증 확인 여부를 직관적으로 파악할 수 있습니다.

## 기술 스택
- **Backend:** Python, Flask, SQLite3
- **Frontend:** HTML5, CSS3, Vanilla JavaScript, SheetJS (Excel Export)
- **Data Processing:** Tesseract OCR, Pillow (Image Processing), PyMuPDF

---

## 단계별 개발 및 최적화 과정 (Development History)

이 프로젝트는 사용자의 피드백을 반영하며 다음과 같이 점진적으로 발전했습니다.

### Phase 1: MVP 구현 및 OCR 도입
- Flask와 SQLite를 활용한 기본적인 CRUD(생성, 읽기, 수정, 삭제) API 구축
- Tesseract OCR을 연동하여 영수증 이미지 및 PDF에서 **날짜와 결제 금액 자동 추출** 기능 구현
- 엑셀(Excel) 자동 추출 기능 연동

### Phase 2: 관리자 UX 개선 (정산 및 실물 확인)
- 총무가 직관적으로 상태를 파악할 수 있도록 리스트에 `[정산완료]`, `[실물확인]` 상태 토글 체크박스 도입
- 기존 데이터를 보존하면서 데이터베이스 스키마(Table)를 동적으로 `ALTER`하여 안전하게 기능 확장

### Phase 3: 칸반 보드 뷰 및 데이터 연동 고도화
- 영수증 내역을 **[팀 ➔ 세부 카테고리]**의 2Depth 구조로 재설계
- 팀별(총괄팀, 찬양팀, 레크팀, 나눔팀) 예산을 설정하고, 모임지원비(인당 12,000원 제한) 등 특수 비즈니스 로직을 백엔드와 프론트엔드 양측에 적용
- 부서별 칸반 보드 UI를 도입하여, 각 부서별 **예산 소진율(%) 및 잔여 예산 자동 계산** 기능 추가

### Phase 4: 수입 관리 및 프라이빗 메모 기능
- 지출뿐만 아니라 '이월금', '후원금' 등 **외부 수입 관리 모듈** 신설 (총 예산에 자동 합산 로직 추가)
- 엑셀 추출 시 관리자만 볼 수 있는 **'총무 전용 프라이빗 메모'** 기능 및 DB 컬럼 추가

### Phase 5: 극한의 OCR 성능 최적화 (Troubleshooting)
무료 호스팅 서버(단일 코어) 환경에서 고해상도 영수증 사진 처리 시 발생하는 **Timeout(통신 실패) 병목 현상 해결**.
1. **Downscaling:** 이미지 해상도 강제 축소(Max 800px)로 픽셀 연산량 80% 감소
2. **1-bit Binarization:** 흑백을 넘어선 1-bit 이진화(Thresholding)로 메모리 점유율 최소화
3. **OCR Whitelist:** 한글 인식의 막대한 연산량을 제거하고, 숫자와 날짜 포맷(`0123456789,-./`)만 스캔하도록 Tesseract 엔진 옵션(`--psm 6`, `whitelist`) 튜닝
> **결과:** 기존 10초 이상 걸리던 분석 속도를 1~2초 내외로 단축하여 타임아웃 문제 100% 해결.

---

## 💻 주요 기능 (Features)

1. **영수증 스캔 및 제출:** OCR을 활용한 금액/날짜 대조 및 사진/PDF 업로드
2. **실시간 예산 모니터링 대시보드:** 총 수입/지출 및 부서별 잔여 예산 시각화
3. **관리자 통합 제어:** 카테고리, 금액, 인원, 일자 등 제출된 영수증의 모든 항목 즉시 수정 가능
4. **원클릭 엑셀 정산:** 날짜순 정렬 및 정산/실물/메모 등 모든 데이터가 포함된 엑셀 `.xlsx` 자동 생성

## ⚙️ 실행 방법 (How to run)

```bash
# 1. 저장소 클론
git clone [https://github.com/사용자이름/Retreat-Receipt-Manager.git](https://github.com/사용자이름/Retreat-Receipt-Manager.git)

# 2. 필수 패키지 설치
pip install -r requirements.txt

# 3. (필수) 시스템에 Tesseract-OCR 설치되어 있어야 함
# Ubuntu: sudo apt-get install tesseract-ocr
# Windows: Tesseract 설치 파일 다운로드 및 환경변수 등록

# 4. 앱 실행
python flask_app.py
