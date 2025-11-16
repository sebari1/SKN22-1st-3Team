# src/dashboard/app.py
"""
Streamlit 멀티 페이지 대시보드 엔트리 포인트.

실행 명령 (프로젝트 루트에서):
    streamlit run src/dashboard/app.py
"""

import sys
import pathlib

# ---------------------------------------------------------
# 1) src/ 를 sys.path 에 올려서
#    db, dashboard, etl 을 top-level 패키지처럼 사용
# ---------------------------------------------------------
SRC_DIR = pathlib.Path(__file__).resolve().parents[2]  # .../SKN22-1st-3Team/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
import pandas as pd

from dashboard.components.layout import two_columns_ratio
from dashboard.components.kpi import kpi_row
from dashboard.components.charts import bar_chart
from dashboard import queries


def main():
    st.set_page_config(
        page_title="국내 자동차 시장 트렌드 분석",
        layout="wide",
    )

    st.title("🚗 국내 자동차 시장 트렌드 분석 대시보드")
    st.caption("현대/기아 중심의 판매량 · 관심도 · 블로그 리뷰를 한눈에 보는 대시보드")

    st.markdown(
        """
        이 화면은 **전체 개요(Home)** 페이지입니다.  
        왼쪽 사이드바의 **다른 페이지**를 선택하면,
        - 모델별 상세 분석
        - 블로그 / 워드클라우드
        - 관리자/점검 페이지  
        로 이동할 수 있습니다.
        """
    )

    # -------------------------
    # 데이터 로드
    # -------------------------
    months = queries.get_available_months()
    latest_month = queries.get_latest_month()

    if not months or latest_month is None:
        st.info("표시할 월간 데이터가 없습니다. 먼저 ETL 스크립트를 실행해 주세요.")
        return

    # 필터: 기준 월 선택
    with st.sidebar:
        selected_month = st.selectbox(
            "기준 월 선택",
            options=months,
            index=months.index(latest_month),
            format_func=lambda d: d.strftime("%Y-%m"),
        )

    # 월별 요약 (브랜드/모델 기준 합계 등)
    summary_df = queries.get_monthly_sales_summary(selected_month)

    if summary_df.empty:
        st.warning("선택한 월에 대한 판매 데이터가 없습니다.")
        return

    # -------------------------
    # KPI 영역
    # -------------------------
    total_sales = int(summary_df["sales_units"].sum())
    hyundai_sales = int(
        summary_df.loc[summary_df["brand_name"] == "현대", "sales_units"].sum()
    )
    kia_sales = int(
        summary_df.loc[summary_df["brand_name"] == "기아", "sales_units"].sum()
    )

    kpi_row(
        {
            "전체 판매량(대)": f"{total_sales:,}",
            "현대 판매량(대)": f"{hyundai_sales:,}",
            "기아 판매량(대)": f"{kia_sales:,}",
        }
    )

    st.markdown("---")

    # -------------------------
    # 레이아웃: 좌/우 2칼럼
    # -------------------------
    left_col, right_col = two_columns_ratio(2, 1)

    with left_col:
        st.subheader("📊 상위 판매 모델")

        top_n = st.slider("상위 N개 모델", min_value=5, max_value=20, value=10)
        top_df = (
            summary_df.sort_values("sales_units", ascending=False).head(top_n).copy()
        )
        top_df["label"] = top_df["brand_name"] + " " + top_df["model_name_kr"]

        bar_chart(
            df=top_df,
            x="label",
            y="sales_units",
            title=f"{selected_month.strftime('%Y-%m')} 상위 {top_n} 모델 판매량",
            x_tick_angle=-45,
        )

    with right_col:
        st.subheader("📈 브랜드 점유율")

        brand_summary = (
            summary_df.groupby("brand_name", as_index=False)["sales_units"]
            .sum()
            .rename(columns={"sales_units": "total_sales"})
        )

        if len(brand_summary) >= 1:
            # 간단한 파이형 / 막대형 – 여기서는 막대형으로
            bar_chart(
                df=brand_summary,
                x="brand_name",
                y="total_sales",
                title=f"{selected_month.strftime('%Y-%m')} 브랜드별 판매량",
            )
        else:
            st.write("브랜드 데이터가 부족합니다.")

    st.markdown("---")
    st.caption(
        "👉 왼쪽 사이드바에서 다른 페이지를 선택하여 상세 분석을 진행할 수 있습니다."
    )


if __name__ == "__main__":
    main()
