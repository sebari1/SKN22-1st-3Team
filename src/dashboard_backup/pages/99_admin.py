# src/dashboard/pages/99_admin.py
"""
간단한 관리자/점검 페이지.

- 주요 테이블 레코드 수
- DB 연결 테스트 등
"""

import streamlit as st

from dashboard import queries


def main():
    st.title("🛠 관리자 / 점검")

    st.subheader("DB 테이블 레코드 수")
    df = queries.get_table_counts()
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("가용 월 목록")
    months = queries.get_available_months()
    if not months:
        st.write("월간 데이터가 없습니다.")
    else:
        st.write(", ".join(m.strftime("%Y-%m") for m in months))


if __name__ == "__main__":
    main()
