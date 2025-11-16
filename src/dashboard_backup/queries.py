# src/dashboard/queries.py
"""
대시보드 전용 DB 조회 함수 모음.

- db.connection.get_engine 을 사용해 SQLAlchemy Engine 획득
- pandas DataFrame 으로 결과 반환
"""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Optional
import datetime

import pandas as pd
from sqlalchemy import text

from db.connection import get_engine  # src/db/connection.py


# ---------------------------------------------------------
# 내부 공용 헬퍼
# ---------------------------------------------------------


@lru_cache(maxsize=1)
def _get_engine_cached():
    return get_engine(echo=False)


def _read_sql_df(sql: str, params: Optional[dict] = None) -> pd.DataFrame:
    engine = _get_engine_cached()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


# ---------------------------------------------------------
# 1. 공통: 월 리스트
# ---------------------------------------------------------


def get_available_months() -> list[datetime.date]:
    """
    model_monthly_sales 기반으로 사용 가능한 month 리스트를 반환.
    """
    df = _read_sql_df(
        """
        SELECT DISTINCT month
        FROM model_monthly_sales
        ORDER BY month
        """
    )
    return [row["month"] for _, row in df.iterrows()]


def get_latest_month() -> Optional[datetime.date]:
    df = _read_sql_df("SELECT MAX(month) AS latest FROM model_monthly_sales")
    if df.empty or df.loc[0, "latest"] is None:
        return None
    return df.loc[0, "latest"]


# ---------------------------------------------------------
# 2. 모델 리스트 / 메타
# ---------------------------------------------------------


def get_car_models() -> pd.DataFrame:
    """
    car_model 전체 리스트.
    """
    return _read_sql_df(
        """
        SELECT
            model_id,
            brand_name,
            model_name_kr
        FROM car_model
        ORDER BY brand_name, model_name_kr
        """
    )


# ---------------------------------------------------------
# 3. 월간 판매 요약 (Home/Overview용)
# ---------------------------------------------------------


def get_monthly_sales_summary(month: datetime.date) -> pd.DataFrame:
    """
    특정 month 기준, 모델별 월간 판매 요약.
    """
    return _read_sql_df(
        """
        SELECT
            ms.model_id,
            cm.brand_name,
            cm.model_name_kr,
            ms.month,
            ms.sales_units,
            ms.market_total_units,
            ms.adoption_rate
        FROM model_monthly_sales ms
        JOIN car_model cm ON cm.model_id = ms.model_id
        WHERE ms.month = :month
        ORDER BY ms.sales_units DESC
        """,
        {"month": month},
    )


# ---------------------------------------------------------
# 4. 모델 상세 페이지용: 판매/관심도 트렌드
# ---------------------------------------------------------


def get_model_sales_trend(model_id: int) -> pd.DataFrame:
    """
    해당 모델의 월간 판매 추이.
    """
    return _read_sql_df(
        """
        SELECT
            ms.month,
            ms.sales_units,
            ms.market_total_units,
            ms.adoption_rate
        FROM model_monthly_sales ms
        WHERE ms.model_id = :model_id
        ORDER BY ms.month
        """,
        {"model_id": model_id},
    )


def get_model_interest_trend(model_id: int) -> pd.DataFrame:
    """
    해당 모델의 월간 관심도 (네이버/구글/다나와).
    """
    return _read_sql_df(
        """
        SELECT
            month,
            naver_search_index,
            google_trend_index,
            danawa_pop_rank,
            danawa_pop_rank_size
        FROM model_monthly_interest
        WHERE model_id = :model_id
        ORDER BY month
        """,
        {"model_id": model_id},
    )


# ---------------------------------------------------------
# 5. 블로그/워드클라우드용
# ---------------------------------------------------------


def get_blog_articles(model_id: int, month: datetime.date) -> pd.DataFrame:
    """
    blog_article 테이블에서 해당 모델/월의 상위 블로그 글 목록.
    """
    return _read_sql_df(
        """
        SELECT
            article_id,
            model_id,
            month,
            search_keyword,
            search_rank,
            title,
            url,
            summary,
            content_plain,
            posted_at,
            collected_at
        FROM blog_article
        WHERE model_id = :model_id
          AND month = :month
        ORDER BY search_rank
        """,
        {"model_id": model_id, "month": month},
    )


def get_blog_wordcloud_path(model_id: int, month: datetime.date) -> Optional[str]:
    """
    blog_wordcloud 테이블에서 이미지 경로 반환.
    """
    df = _read_sql_df(
        """
        SELECT image_path
        FROM blog_wordcloud
        WHERE model_id = :model_id
          AND month = :month
        LIMIT 1
        """,
        {"model_id": model_id, "month": month},
    )
    if df.empty:
        return None
    return df.loc[0, "image_path"]


def get_blog_token_top(
    model_id: int, month: datetime.date, top_n: int = 30
) -> pd.DataFrame:
    """
    blog_token_monthly 에서 상위 토큰들 가져오기.
    """
    return _read_sql_df(
        """
        SELECT
            token,
            total_count,
            token_rank
        FROM blog_token_monthly
        WHERE model_id = :model_id
          AND month = :month
        ORDER BY token_rank
        LIMIT :top_n
        """,
        {"model_id": model_id, "month": month, "top_n": top_n},
    )


# ---------------------------------------------------------
# 6. 관리자용: 간단한 카운트/상태
# ---------------------------------------------------------


def get_table_counts() -> pd.DataFrame:
    """
    주요 테이블의 레코드 수를 확인하는 간단한 관리자용 쿼리.
    """
    engine = _get_engine_cached()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT 'car_model' AS table_name, COUNT(*) AS cnt FROM car_model
                UNION ALL
                SELECT 'model_monthly_sales', COUNT(*) FROM model_monthly_sales
                UNION ALL
                SELECT 'model_monthly_interest', COUNT(*) FROM model_monthly_interest
                UNION ALL
                SELECT 'blog_article', COUNT(*) FROM blog_article
                UNION ALL
                SELECT 'blog_token_monthly', COUNT(*) FROM blog_token_monthly
                UNION ALL
                SELECT 'blog_wordcloud', COUNT(*) FROM blog_wordcloud
                """
            )
        ).fetchall()
    return pd.DataFrame(rows, columns=["table_name", "cnt"])
