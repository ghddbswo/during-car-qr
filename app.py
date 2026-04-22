import pandas as pd
import streamlit as st
from datetime import datetime, date

st.set_page_config(page_title="듀링 법인차량 QR 조회", layout="centered")

XLSX_PATH = "data/듀링 법인차량 현황 ver.2.0.xlsx"

CAR_SHEET = "법인차량현황"
MAINT_SHEET = "정비이력"

CAR_USECOLS = [
    "차량ID",
    "차량번호",
    "차종",
    "사용자",
    "운용사업장",
    "차량구분",
    "보험사",
    "보험사연락처",
    "보험만료일",
    "검사만료일",
    "계약종료일",
    "월 렌트료",
    "월금액",
    "주행거리",
]

MAINT_USECOLS = [
    "차량ID",
    "차량번호",
    "정비일자",
    "정비내용",
    "정비항목",
    "정비내역",
    "주행거리",
    "금액",
    "정비금액",
    "업체",
    "비고",
]


def safe_read_excel(path: str, sheet_name: str, usecols: list[str] | None = None):
    """
    usecols로 먼저 시도하고, 실패하면 전체 로딩 후 존재 컬럼만 남김
    엑셀 컬럼명이 조금 달라도 앱이 죽지 않도록 처리
    """
    try:
        return pd.read_excel(path, sheet_name=sheet_name, usecols=usecols)
    except Exception:
        df = pd.read_excel(path, sheet_name=sheet_name)
        df.columns = [str(c).strip() for c in df.columns]
        if usecols:
            existing = [c for c in usecols if c in df.columns]
            if existing:
                df = df[existing]
        return df


@st.cache_data(show_spinner=False, ttl=86400)
def load_data(xlsx_path: str):
    cars = safe_read_excel(xlsx_path, CAR_SHEET, CAR_USECOLS)
    maint = safe_read_excel(xlsx_path, MAINT_SHEET, MAINT_USECOLS)

    cars.columns = [str(c).strip() for c in cars.columns]
    maint.columns = [str(c).strip() for c in maint.columns]

    # 문자열 키 컬럼 정리
    for col in ["차량ID", "차량번호"]:
        if col in cars.columns:
            cars[col] = cars[col].astype(str).str.strip()
        if col in maint.columns:
            maint[col] = maint[col].astype(str).str.strip()

    # 날짜 컬럼 미리 정리
    for col in ["보험만료일", "검사만료일", "계약종료일"]:
        if col in cars.columns:
            cars[col] = pd.to_datetime(cars[col], errors="coerce").dt.date

    if "정비일자" in maint.columns:
        maint["정비일자"] = pd.to_datetime(maint["정비일자"], errors="coerce").dt.date

    return cars, maint


def dday(d):
    if d is None or pd.isna(d):
        return None
    return (d - date.today()).days


def fmt_dday(label, d):
    if d is None or pd.isna(d):
        return f"{label}: -"
    dd = dday(d)
    if dd is None:
        return f"{label}: -"
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
        return f"{v:,}KM"
    except Exception:
        return s


def fmt_won(x):
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


def first_nonempty_value(row, columns: list[str]):
    for col in columns:
        if col in row.index:
            val = row.get(col)
            if pd.notna(val) and str(val).strip() != "":
                return val
    return None


cars, maint = load_data(XLSX_PATH)

st.title("🚗 듀링 법인차량 현황 (QR 조회)")

if cars.empty:
    st.error("차량현황 데이터를 불러오지 못했습니다. 엑셀 파일 또는 시트명을 확인하세요.")
    st.stop()

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
            .loc[lambda s: s != ""]
            .unique()
            .tolist()
        )
        options.sort()

        if not options:
            st.warning("차량ID 데이터가 없습니다.")
        else:
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
            .loc[lambda s: s != ""]
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

# QR로 들어온 경우 버튼 안 눌러도 바로 조회
if not car_id and qp_car_id:
    car_id = qp_car_id

if car_id:
    row = cars[cars["차량ID"] == str(car_id).strip()]
    if row.empty:
        st.error(f"해당 차량ID를 찾지 못했습니다: {car_id}")
        st.stop()

    r = row.iloc[0]

    car_no = str(first_nonempty_value(r, ["차량번호"]) or "").strip()
    car_model = str(first_nonempty_value(r, ["차종"]) or "").strip()
    user = str(first_nonempty_value(r, ["사용자"]) or "").strip()
    site = str(first_nonempty_value(r, ["운용사업장"]) or "").strip()
    kind = str(first_nonempty_value(r, ["차량구분"]) or "").strip()

    st.subheader(f"{car_no if car_no else '-'} · {car_model if car_model else '-'}")
    st.caption(f"차량ID: {car_id}")

    c1, c2 = st.columns(2)

    with c1:
        st.write(f"**차량구분**: {kind if kind else '-'}")
        st.write(f"**운용사업장**: {site if site else '-'}")
        st.write(f"**사용자**: {user if user else '-'}")

        if "주행거리" in cars.columns:
            st.write(f"**주행거리**: {fmt_km(r.get('주행거리', None))}")

    with c2:
        ins = str(first_nonempty_value(r, ["보험사"]) or "").strip()
        ins_phone = str(first_nonempty_value(r, ["보험사연락처"]) or "").strip()

        st.write(f"**보험사**: {ins if ins else '-'}")
        st.write(f"**보험사 연락처**: {ins_phone if ins_phone else '-'}")

        if ins_phone and ins_phone.lower() != "nan":
            tel = ins_phone.replace("-", "").replace(" ", "")
            st.markdown(f"[📞 보험사 전화걸기](tel:{tel})")

    ins_end = r.get("보험만료일", None) if "보험만료일" in r.index else None
    insp_end = r.get("검사만료일", None) if "검사만료일" in r.index else None
    contract_end = r.get("계약종료일", None) if "계약종료일" in r.index else None

    st.divider()
    st.markdown("### 📅 만료/계약")
    st.write(fmt_dday("보험만료일", ins_end))
    st.write(fmt_dday("검사만료일", insp_end))
    st.write(fmt_dday("계약종료일(렌트)", contract_end))

    rent_fee = first_nonempty_value(r, ["월 렌트료", "월금액"])
    if rent_fee is not None:
        st.write(f"월 렌트료: {fmt_won(rent_fee)}")

    st.divider()
    st.markdown("### 🧰 정비 이력")

    # 복사 없이 바로 필터
    if "차량ID" in maint.columns:
        mm = maint[maint["차량ID"] == str(car_id).strip()]
    elif "차량번호" in maint.columns:
        mm = maint[maint["차량번호"].astype(str).str.replace(" ", "") == str(car_no).replace(" ", "")]
    else:
        mm = maint.iloc[0:0]

    if mm.empty:
        st.info("정비 이력이 없습니다.")
    else:
        # 정비일자 최신순
        if "정비일자" in mm.columns:
            mm = mm.sort_values("정비일자", ascending=False, na_position="last")

        # 최근 20건만 표시
        mm = mm.head(20).copy()

        if "주행거리" in mm.columns:
            mm["주행거리"] = mm["주행거리"].apply(fmt_km)

        if "금액" in mm.columns:
            mm["금액"] = mm["금액"].apply(fmt_won)

        if "정비금액" in mm.columns:
            mm["정비금액"] = mm["정비금액"].apply(fmt_won)

        # 정비내용 관련 컬럼 정리
        preferred_cols = [
            "정비일자",
            "정비내용",
            "정비항목",
            "정비내역",
            "주행거리",
            "금액",
            "정비금액",
            "업체",
            "비고",
        ]
        display_cols = [c for c in preferred_cols if c in mm.columns]

        if display_cols:
            st.dataframe(mm[display_cols], use_container_width=True, hide_index=True)
        else:
            st.dataframe(mm, use_container_width=True, hide_index=True)

        st.caption("최근 정비이력 20건만 표시됩니다.")

else:
    st.info("좌측에서 차량을 선택하거나 QR로 접속하세요.")
