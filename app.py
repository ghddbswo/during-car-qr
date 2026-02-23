import pandas as pd
import streamlit as st
from datetime import datetime, date

st.set_page_config(page_title="듀링 법인차량 QR 조회", layout="centered")

@st.cache_data(show_spinner=False)
def load_data(xlsx_path: str):
    cars = pd.read_excel(xlsx_path, sheet_name="법인차량현황")
    maint = pd.read_excel(xlsx_path, sheet_name="정비현황")
    # normalize columns
    cars.columns = [str(c).strip() for c in cars.columns]
    maint.columns = [str(c).strip() for c in maint.columns]
    return cars, maint

def to_date(x):
    if pd.isna(x):
        return None
    if isinstance(x, (datetime, pd.Timestamp)):
        return x.date()
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

def dday(d):
    if d is None:
        return None
    return (d - date.today()).days

def fmt_dday(label, d):
    if d is None:
        return f"{label}: -"
    dd = dday(d)
    if dd >= 0:
        return f"{label}: {d} (D-{dd})"
    return f"{label}: {d} (D+{abs(dd)})"

XLSX_PATH = "data/듀링 법인차량 현황 ver.2.0.xlsx"

cars, maint = load_data(XLSX_PATH)

st.title("🚗 듀링 법인차량 현황 (QR 조회)")

# read from query param
car_id = st.query_params.get("car_id", None)

with st.sidebar:
    st.header("검색")
    mode = st.radio("조회 방식", ["차량ID", "차량번호"], index=0)
    if mode == "차량ID":
        options = [x for x in cars.get("차량ID", pd.Series()).dropna().astype(str).unique()]
        chosen = st.selectbox("차량ID 선택", options, index=0 if options else None)
        if st.button("조회"):
            car_id = chosen
    else:
        options = [x for x in cars.get("차량번호", pd.Series()).dropna().astype(str).unique()]
        chosen_num = st.selectbox("차량번호 선택", options, index=0 if options else None)
        if st.button("조회"):
            match = cars[cars["차량번호"].astype(str) == str(chosen_num)]
            car_id = match["차량ID"].astype(str).iloc[0] if not match.empty else None

if car_id:
    row = cars[cars["차량ID"].astype(str) == str(car_id)]
    if row.empty:
        st.error(f"해당 차량ID를 찾지 못했습니다: {car_id}")
        st.stop()
    r = row.iloc[0]

    # key fields
    car_no = str(r.get("차량번호", "")).strip()
    car_model = str(r.get("차종", "")).strip()
    user = str(r.get("사용자", "")).strip()
    site = str(r.get("운용사업장", "")).strip()
    kind = str(r.get("차량구분", "")).strip()

    st.subheader(f"{car_no} · {car_model}")
    st.caption(f"차량ID: {car_id}")

    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**차량구분**: {kind if kind else '-'}")
        st.write(f"**운용사업장**: {site if site else '-'}")
        st.write(f"**사용자**: {user if user else '-'}")
    with c2:
        ins = str(r.get("보험사", "")).strip()
        ins_phone = str(r.get("보험사연락처", "")).strip()
        st.write(f"**보험사**: {ins if ins else '-'}")
        st.write(f"**보험사 연락처**: {ins_phone if ins_phone else '-'}")
        if ins_phone and ins_phone != "nan":
            tel = ins_phone.replace("-", "").replace(" ", "")
            st.markdown(f"[📞 보험사 전화걸기](tel:{tel})")

    ins_end = to_date(r.get("보험만료일", None))
    insp_end = to_date(r.get("검사만료일", None))
    contract_end = to_date(r.get("계약종료일", None))

    st.divider()
    st.markdown("### 📅 만료/계약")
    st.write(fmt_dday("보험만료일", ins_end))
    st.write(fmt_dday("검사만료일", insp_end))
    st.write(fmt_dday("계약종료일(렌트)", contract_end))

    rent_fee = r.get("월 렌트료", r.get("월금액", None))

    if pd.notna(rent_fee) and str(rent_fee).strip() != "":
        rent_fee = int(float(rent_fee))  # 숫자로 변환 + 소수점 제거
        st.write(f"월 렌트료: {rent_fee:,}원")

    # maintenance
    st.divider()
    st.markdown("### 🧰 정비 이력")
    # attempt linkage by 차량번호 first, fallback by 차량ID if present
    m = maint.copy()
    if "차량번호" in m.columns:
        mm = m[m["차량번호"].astype(str) == car_no]
    elif "차량ID" in m.columns:
        mm = m[m["차량ID"].astype(str) == str(car_id)]
    else:
        mm = m.iloc[0:0]

    if mm.empty:
        st.info("정비 이력이 없습니다.")
    else:
        # show latest first if there is a date column
        date_cols = [c for c in mm.columns if "일" in c or "date" in c.lower()]
        if date_cols:
            dc = date_cols[0]
            try:
                mm[dc] = pd.to_datetime(mm[dc], errors="coerce")
                mm = mm.sort_values(dc, ascending=False)
            except Exception:
                pass
        st.dataframe(mm, use_container_width=True, hide_index=True)

else:
    st.info("왼쪽에서 차량ID/차량번호로 조회하거나, QR 링크로 접속하세요. 예: ?car_id=DR-CAR-01")
