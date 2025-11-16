# src/dashboard/pages/02_blog_wordcloud.py
"""
블로그 상위 글 & 워드클라우드 페이지
"""

from __future__ import annotations

import pathlib
import streamlit as st

from dashboard import queries


def _resolve_image_path(image_rel_path: str) -> pathlib.Path:
    """
    DB에 상대 경로(예: data/wordcloud/2025-11/ev3_2025-11.png)가 저장되어 있다고 가정.
    현재 파일 기준으로 프로젝트 루트까지 올라간 뒤, 해당 경로를 합친다.
    """
    current = pathlib.Path(__file__).resolve()
    # .../SKN22-1st-3Team/src/dashboard/pages/02_blog_wordcloud.py
    project_root = current.parents[3]  # SKN22-1st-3Team
    return project_root / image_rel_path


def main():
    st.title("📝 블로그 리뷰 & 워드클라우드")

    months = queries.get_available_months()
    latest_month = queries.get_latest_month()
    models_df = queries.get_car_models()

    if not months or latest_month is None:
        st.info("표시할 월간 데이터가 없습니다.")
        return

    if models_df.empty:
        st.info("모델 정보가 없습니다. car_model 테이블을 먼저 채워주세요.")
        return

    models_df = models_df.copy()
    models_df["label"] = models_df["brand_name"] + " " + models_df["model_name_kr"]
    label_to_id = dict(zip(models_df["label"], models_df["model_id"]))

    with st.sidebar:
        selected_month = st.selectbox(
            "기준 월",
            options=months,
            index=months.index(latest_month),
            format_func=lambda d: d.strftime("%Y-%m"),
        )
        selected_label = st.selectbox(
            "모델 선택",
            options=models_df["label"].tolist(),
        )

    selected_model_id = int(label_to_id[selected_label])
    st.subheader(f"{selected_label} – {selected_month.strftime('%Y-%m')} 기준")

    col_wc, col_articles = st.columns([1, 1])

    # 워드클라우드 이미지
    with col_wc:
        st.markdown("#### ☁ 워드클라우드")

        image_rel_path = queries.get_blog_wordcloud_path(
            model_id=selected_model_id, month=selected_month
        )

        if not image_rel_path:
            st.info("워드클라우드 이미지가 없습니다.")
        else:
            file_path = _resolve_image_path(image_rel_path)
            if file_path.exists():
                st.image(str(file_path), use_container_width=True)
                st.caption(f"이미지 경로: {image_rel_path}")
            else:
                st.warning(
                    f"워드클라우드 이미지 파일을 찾을 수 없습니다.\n- {file_path}"
                )

        st.markdown("#### 🔠 상위 키워드")
        token_df = queries.get_blog_token_top(
            selected_model_id, selected_month, top_n=30
        )
        if token_df.empty:
            st.write("토큰 데이터가 없습니다.")
        else:
            st.dataframe(token_df, use_container_width=True)

    # 블로그 글 목록
    with col_articles:
        st.markdown("#### 📰 상위 블로그 글")

        articles_df = queries.get_blog_articles(
            model_id=selected_model_id, month=selected_month
        )

        if articles_df.empty:
            st.write("수집된 블로그 글이 없습니다.")
        else:
            for _, row in articles_df.iterrows():
                rank = row.get("search_rank", None)
                title = row.get("title", "")
                url = row.get("url", "")
                summary = row.get("summary", "")

                if rank is not None:
                    st.markdown(f"**[{rank}] [{title}]({url})**")
                else:
                    st.markdown(f"**[{title}]({url})**")

                if summary:
                    preview = summary.strip()
                    if len(preview) > 250:
                        preview = preview[:250] + "..."
                    st.write(preview)

                st.divider()


if __name__ == "__main__":
    main()
