import os
import pandas as pd
import qrcode
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

BASE_URL = "https://during-car-qr-ufmsb3kchhcxzdryxnrury.streamlit.app"
XLSX_PATH = "data/듀링 법인차량 현황 ver.2.0.xlsx"
# 한글 폰트 등록 (윈도우: 맑은 고딕)
c.setFont("Helvetica", 9)
pdfmetrics.registerFont(TTFont("Malgun", FONT_PATH))
def build_qr(url: str, out_path: str):
    img = qrcode.make(url)
    img.save(out_path)

def make_pdf(car_rows, qr_dir, out_pdf):
    page_w, page_h = A4
    c = canvas.Canvas(out_pdf, pagesize=A4)

    cols, rows = 3, 4  # 3x4 labels
    margin_x, margin_y = 10*mm, 10*mm
    cell_w = (page_w - 2*margin_x) / cols
    cell_h = (page_h - 2*margin_y) / rows

    def draw_label(ix, car_id, car_no, car_model, qr_path):
        col = ix % cols
        row = ix // cols
        x0 = margin_x + col * cell_w
        y0 = page_h - margin_y - (row+1)*cell_h

        # QR
        qr_size = min(cell_w, cell_h) * 0.55
        qr_x = x0 + 8
        qr_y = y0 + 8
        c.drawImage(ImageReader(qr_path), qr_x, qr_y, width=qr_size, height=qr_size, preserveAspectRatio=True, mask='auto')
        # 차량 정보
        c.setFont("Malgun", 9)
        c.drawString(qr_x, qr_y - 12, f"ID: {car_id}")
        c.drawString(qr_x, qr_y - 22, f"번호: {car_no}")
        # URL hint
        c.setFont("Malgun", 8)
        c.drawString(qr_x + qr_size + 10, qr_y + qr_size - 10, "QR로 차량조회")
        c.setFont("Malgun", 7)
        c.drawString(qr_x + qr_size + 10, qr_y + qr_size - 24, BASE_URL)

    per_page = cols * rows
    for i, r in enumerate(car_rows):
        if i % per_page == 0 and i != 0:
            c.showPage()
        ix = i % per_page
        draw_label(ix, r["차량ID"], r.get("차량번호",""), r.get("차종",""), os.path.join(qr_dir, f'{r["차량ID"]}.png'))

    c.save()

def main():
    os.makedirs("qr_codes", exist_ok=True)
    cars = pd.read_excel(XLSX_PATH, sheet_name="법인차량현황")
    cars = cars.dropna(subset=["차량ID"])
    cars["차량ID"] = cars["차량ID"].astype(str)

    rows=[]
    for _, r in cars.iterrows():
        car_id = str(r["차량ID"])
        url = f"{BASE_URL}?car_id={car_id}"
        out = os.path.join("qr_codes", f"{car_id}.png")
        build_qr(url, out)
        rows.append({"차량ID": car_id, "차량번호": str(r.get("차량번호","")), "차종": str(r.get("차종",""))})

    make_pdf(rows, "qr_codes", "QR_스티커_A4.pdf")
    print("완료: qr_codes/ 및 QR_스티커_A4.pdf 생성")

if __name__ == "__main__":
    main()
