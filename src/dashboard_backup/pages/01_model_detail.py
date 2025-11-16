# src/dashboard/pages/01_model_detail.py
"""
모델 상세 페이지:
- 모델 선택
- 판매 추이
- 관심도(네이버/구글/다나와) 추이
"""

import streamlit as st
import pandas as pd

from dashboard.components.layout import two_columns_ratio
from dashboard.components.charts import line_chart, bar_chart
from dashboard.components.kpi import kpi_row
from dashboard import queries


def main():
    st.title("🚗 모델 상세 분석")

    months = queries.get_available_months()
    latest_month = queries.get_latest_month()
    models_df = queries.get_car_models()

    if models_df.empty:
        st.info("모델 정보가 없습니다. car_model 테이블을 먼저 채워주세요.")
        return

    models_df = models_df.copy()
    models_df["label"] = models_df["brand_name"] + " " + models_df["model_name_kr"]

    with st.sidebar:
        selected_label = st.selectbox(
            "모델 선택",
            options=models_df["label"].tolist(),
        )

    row_model = models_df.loc[models_df["label"] == selected_label].iloc[0]
    model_id = int(row_model["model_id"])

    st.subheader(f"{row_model['brand_name']} {row_model['model_name_kr']}")

    # ---------------- 판매 추이 ----------------
    sales_df = queries.get_model_sales_trend(model_id)
    if not sales_df.empty:
        kpi_row(
            {
                "최근 월 판매량(대)": f"{int(sales_df.iloc[-1]['sales_units']):,}",
                "데이터 기간": f"{sales_df['month'].min().strftime('%Y-%m')} ~ {sales_df['month'].max().strftime('%Y-%m')}",
            }
        )

        line_chart(
            sales_df,
            x="month",
            y="sales_units",
            title="월간 판매량 추이",
            y_title="판매량(대)",
        )
    else:
        st.info("판매 데이터가 없습니다.")

    st.markdown("---")

    # ---------------- 관심도 추이 ----------------
    st.subheader("🔍 월간 관심도 추이 (네이버/구글/다나와)")

    interest_df = queries.get_model_interest_trend(model_id)
    if interest_df.empty:
        st.info("관심도 데이터가 없습니다.")
        return

    # 네이버 / 구글 각각 라인
    if interest_df["naver_search_index"].notnull().any():
        line_chart(
            interest_df.dropna(subset=["naver_search_index"]),
            x="month",
            y="naver_search_index",
            title="네이버 검색 지수",
            y_title="index",
        )

    if interest_df["google_trend_index"].notnull().any():
        line_chart(
            interest_df.dropna(subset=["google_trend_index"]),
            x="month",
            y="google_trend_index",
            title="구글 트렌드 지수",
            y_title="index",
        )

    if interest_df["danawa_pop_rank"].notnull().any():
        st.subheader("📈 다나와 인기 순위 (낮을수록 상위)")
        line_chart(
            interest_df.dropna(subset=["danawa_pop_rank"]),
            x="month",
            y="danawa_pop_rank",
            title="다나와 인기 순위",
            y_title="순위",
        )


if __name__ == "__main__":
    main()
