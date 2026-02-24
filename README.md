# 듀링 법인차량 QR 조회 앱

## 1) 준비
```bash
pip install -r requirements.txt
```

## 2) 실행(로컬)
```bash
streamlit run app.py
```

## 3) 배포 후 QR 재생성
- 배포 URL을 확보한 뒤, 엑셀의 `QR_설정` 시트에서 `BASE_URL`을 배포 URL로 변경
  - 예: https://during-car.streamlit.app
- QR을 새로 만들려면 `regen_qr.py`의 BASE_URL을 수정 후 실행:
```bash
python regen_qr.py
```

## 파일 구성
- data/듀링 법인차량 현황 ver.2.0.xlsx : 원본 DB (엑셀)
- qr_codes/ : 차량별 QR 이미지
- QR_스티커_A4.pdf : A4 스티커(3x4) PDF
