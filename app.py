import pandas as pd
import streamlit as st
from datetime import datetime, date

st.set_page_config(page_title="듀링 법인차량 QR 조회", layout="centered")

XLSX_PATH = "data/듀링 법인차량 현황 ver.2.0.xlsx"


@st.cache_data(show_spinner=False)
def load_data(xlsx_path: str):
    cars = pd.read_excel(xlsx_path, sheet_name="법인차량현황")
    maint = pd.read_excel(xlsx_path, sheet_name="정비이력")  # ✅ 시트명

    # 컬럼명 정리
    cars.columns = [str(c).strip() for c in cars.columns]
    maint.columns = [str(c).strip() for c in maint.columns]

    # 키 컬럼 정리
    if "차량ID" in cars.columns:
        cars["차량ID"] = cars["차량ID"].astype(str).str.strip()
    if "차량번호" in cars.columns:
        cars["차량번호"] = cars["차량번호"].astype(str).str.strip()

    if "차량ID" in maint.columns:
        maint["차량ID"] = maint["차량ID"].astype(str).str.strip()
    if "차량번호" in maint.columns:
        maint["차량번호"] = maint["차량번호"].astype(str).str.strip()

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


def get_qp(name: str):
    v = st.query_params.get(name, None)
    if isinstance(v, list):
        v = v[0] if v else None
    v = str(v).strip() if v else None
    return v if v else None


def fmt_km(x):
    """어떤 형식이 와도 최대한 숫자로 추출해 '68,243KM' 형태로 출력"""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "-"
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return "-"

    s2 = (
        s.replace(",", "")
        .replace(" ", "")
        .replace("km", "")
        .replace("KM", "")
        .replace("Km", "")
    )
    try:
        v = int(float(s2))
        return f"{v:,}KM"  # ✅ 원하는 형식
    except Exception:
        return s


def fmt_won(x):
    """어떤 형식이 와도 최대한 숫자로 추출해 '889,650원' 형태로 출력"""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "-"
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return "-"

    s2 = (
        s.replace(",", "")
        .replace(" ", "")
        .replace("원", "")
        .replace("₩", "")
    )
    try:
        v = int(float(s2))
        return f"{v:,}원"
    except Exception:
        return s


cars, maint = load_data(XLSX_PATH)

st.title("🚗 듀링 법인차량 현황 (QR 조회)")

qp_car_id = get_qp("car_id")
car_id = None

with st.sidebar:
    st.header("검색")

    mode = st.radio("조회 방식", ["차량ID", "차량번호"], index=0)

    if mode == "차량ID":
        options = (
            cars.get("차량ID", pd.Series(dtype=str))
            .dropna()
            .astype(str)
            .map(lambda x: x.strip())
            .unique()
            .tolist()
        )
        options.sort()

        if not options:
            st.warning("차량ID 데이터가 없습니다.")
        else:
            # URL car_id가 있으면 선택값 강제 세팅 + rerun
            if qp_car_id and qp_car_id in options:
                if st.session_state.get("car_id_select") != qp_car_id:
                    st.session_state["car_id_select"] = qp_car_id
                    st.rerun()
            else:
                st.session_state.setdefault("car_id_select", options[0])

            car_id = st.selectbox("차량ID 선택", options, key="car_id_select")

    else:
        options = (
            cars.get("차량번호", pd.Series(dtype=str))
            .dropna()
            .astype(str)
            .map(lambda x: x.strip())
            .unique()
            .tolist()
        )
        options.sort()

        if not options:
            st.warning("차량번호 데이터가 없습니다.")
        else:
            st.session_state.setdefault("car_no_select", options[0])
            chosen_num = st.selectbox("차량번호 선택", options, key="car_no_select")

            if st.button("조회"):
                match = cars[cars["차량번호"] == str(chosen_num).strip()]
                car_id = match["차량ID"].iloc[0] if not match.empty else None


if car_id:
    row = cars[cars["차량ID"] == str(car_id).strip()]
    if row.empty:
        st.error(f"해당 차량ID를 찾지 못했습니다: {car_id}")
        st.stop()

    r = row.iloc[0]

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

        # 차량현황 주행거리(있으면)
        if "주행거리" in cars.columns:
            st.write(f"**주행거리**: {fmt_km(r.get('주행거리', None))}")

    with c2:
        ins = str(r.get("보험사", "")).strip()
        ins_phone = str(r.get("보험사연락처", "")).strip()
        st.write(f"**보험사**: {ins if ins else '-'}")
        st.write(f"**보험사 연락처**: {ins_phone if ins_phone else '-'}")
        if ins_phone and ins_phone.lower() != "nan":
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

    # 렌트료 콤마(원)
    rent_fee = r.get("월 렌트료", r.get("월금액", None))
    if pd.notna(rent_fee) and str(rent_fee).strip() != "":
        st.write(f"월 렌트료: {fmt_won(rent_fee)}")

    st.divider()
    st.markdown("### 🧰 정비 이력")

    m = maint.copy()

    # 차량ID 기준 필터
    if "차량ID" in m.columns:
        mm = m[m["차량ID"] == str(car_id).strip()].copy()
    elif "차량번호" in m.columns:
        mm = m[m["차량번호"].str.replace(" ", "") == str(car_no).replace(" ", "")].copy()
    else:
        mm = m.iloc[0:0].copy()

    if mm.empty:
        st.info("정비 이력이 없습니다.")
    else:
        # 날짜: 시간 제거 + 최신순
        if "정비일자" in mm.columns:
            mm["정비일자"] = pd.to_datetime(mm["정비일자"], errors="coerce").dt.date
            mm = mm.sort_values("정비일자", ascending=False)

        # 정비이력 주행거리/금액 포맷
        if "주행거리" in mm.columns:
            mm["주행거리"] = mm["주행거리"].apply(fmt_km)

        # 금액 컬럼명이 '금액' 또는 '정비금액'인 경우 둘 다 처리
        if "금액" in mm.columns:
            mm["금액"] = mm["금액"].apply(fmt_won)
        if "정비금액" in mm.columns:
            mm["정비금액"] = mm["정비금액"].apply(fmt_won)

        st.dataframe(mm, use_container_width=True, hide_index=True)

else:
    st.info("좌측에서 차량을 선택하거나 QR로 접속하세요.")
