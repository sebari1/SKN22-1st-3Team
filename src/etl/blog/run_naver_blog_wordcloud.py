# src/etl/blog/run_naver_blog_wordcloud.py

from __future__ import annotations

import argparse
import collections
import datetime
import os
import time
from pathlib import Path
from typing import List, Dict, Tuple, Any

import requests
from bs4 import BeautifulSoup
from kiwipiepy import Kiwi
from sqlalchemy import text

from src.db.connection import get_engine

BASE_DIR = Path(__file__).resolve().parents[3]


# -----------------------------
# DB 유틸
# -----------------------------
def get_models_for_blog_target(limit: int | None = None) -> List[Dict[str, Any]]:
    """
    워드클라우드/블로그 수집 대상 car_model 목록을 가져온다.
    """
    engine = get_engine(echo=False)
    sql = text(
        """
        SELECT model_id, brand_name, model_name_kr
        FROM car_model
        ORDER BY brand_name, model_name_kr
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()

    if limit is not None:
        rows = rows[:limit]

    return rows


def has_tokens_for_month(model_id: int, month: datetime.date) -> bool:
    """
    이미 해당 model_id + month에 blog_token_monthly 데이터가 있는지 확인.
    있으면 이번 수집은 스킵.
    """
    engine = get_engine(echo=False)
    sql = text(
        """
        SELECT 1
        FROM blog_token_monthly
        WHERE model_id = :model_id
          AND month = :month
        LIMIT 1
        """
    )
    with engine.connect() as conn:
        row = conn.execute(sql, {"model_id": model_id, "month": month}).first()
    return row is not None


def insert_tokens(
    model_id: int,
    month: datetime.date,
    token_counts: List[Tuple[str, int]],
    top_k: int = 50,
) -> None:
    """
    토큰/빈도 리스트를 blog_token_monthly에 upsert.
    DDL:
      - token_rank 컬럼 사용
      - UNIQUE KEY (model_id, month, token) 기준으로 ON DUPLICATE KEY UPDATE
    """
    engine = get_engine(echo=False)
    sql = text(
        """
        INSERT INTO blog_token_monthly (
            model_id,
            month,
            token,
            total_count,
            token_rank,
            created_at
        )
        VALUES (
            :model_id,
            :month,
            :token,
            :total_count,
            :rank,
            NOW()
        )
        ON DUPLICATE KEY UPDATE
            total_count = VALUES(total_count),
            token_rank = VALUES(token_rank)
        """
    )

    with engine.begin() as conn:
        for rank, (token, count) in enumerate(token_counts[:top_k], start=1):
            conn.execute(
                sql,
                {
                    "model_id": model_id,
                    "month": month,
                    "token": token,
                    "total_count": count,
                    "rank": rank,
                },
            )


def insert_blog_article(
    model_id: int,
    month: datetime.date,
    search_keyword: str,
    search_rank: int,
    title: str,
    url: str,
    summary: str,
    content_plain: str,
    posted_at: datetime.datetime | None = None,
) -> None:
    """
    블로그 글을 blog_article에 저장.
    - month: 기준 월 (워드클라우드 기준 월, ex) 2025-11-01)
    - search_keyword: 네이버 API에 사용한 검색어 (예: 'EV3 후기')
    - search_rank: 검색 결과 내 순위 (1, 2, 3)
    - summary: 내용 요약 (앞 N자)
    - content_plain: 전체 본문 텍스트
    - posted_at: 원문 게시일 (모르면 NULL)
    """
    engine = get_engine(echo=False)
    sql = text(
        """
        INSERT INTO blog_article (
            model_id,
            month,
            search_keyword,
            search_rank,
            title,
            url,
            summary,
            content_plain,
            posted_at
        )
        VALUES (
            :model_id,
            :month,
            :search_keyword,
            :search_rank,
            :title,
            :url,
            :summary,
            :content_plain,
            :posted_at
        )
        ON DUPLICATE KEY UPDATE
            summary       = VALUES(summary),
            content_plain = VALUES(content_plain),
            posted_at     = VALUES(posted_at),
            collected_at  = CURRENT_TIMESTAMP
        """
    )
    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "model_id": model_id,
                "month": month,
                "search_keyword": search_keyword,
                "search_rank": search_rank,
                "title": title,
                "url": url,
                "summary": summary,
                "content_plain": content_plain,
                "posted_at": posted_at,
            },
        )


# -----------------------------
# 블로그 본문 크롤링 (requests 기반)
# -----------------------------
def _fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.text


def extract_blog_text(url: str) -> str:
    """
    네이버 블로그(및 외부 블로그)의 본문 텍스트를 추출한다.

    1차: 직접 HTML에서 본문 영역 찾기
    2차: iframe#mainFrame 이 있으면 그 src를 다시 요청해서 본문 찾기
    3차: 그래도 안 되면 전체 텍스트
    """
    try:
        html = _fetch_html(url)
    except Exception as e:
        print(f"    [WARN] 1차 fetch 실패: {e}")
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # 1) 최신 스마트에디터 3.0 구조
    container = soup.select_one("div.se-main-container")
    if container:
        return container.get_text(separator="\n")

    # 2) 구형 블로그 에디터 구조
    legacy = soup.select_one("div#content")
    if legacy:
        return legacy.get_text(separator="\n")

    # 3) iframe 구조 (구버전 blog.naver.com)
    iframe = soup.select_one("iframe#mainFrame")
    if iframe and iframe.has_attr("src"):
        from urllib.parse import urljoin

        iframe_src = iframe["src"]
        iframe_url = urljoin("https://blog.naver.com", iframe_src)

        try:
            inner_html = _fetch_html(iframe_url)
        except Exception as e:
            print(f"    [WARN] iframe fetch 실패: {e}")
            return ""

        inner = BeautifulSoup(inner_html, "html.parser")

        for selector in [
            "div.se-main-container",
            "div#postViewArea",
            "div#contentArea",
        ]:
            area = inner.select_one(selector)
            if area:
                return area.get_text(separator="\n")

        return inner.get_text(separator="\n")

    # 4) 그 외의 경우: 전체 텍스트 fallback
    return soup.get_text(separator="\n")


# -----------------------------
# Kiwi 기반 명사 추출
# -----------------------------
kiwi = Kiwi()


def tokenize_text(text: str) -> List[str]:
    """
    한글 텍스트에서 명사류(N*) 토큰만 추출.
    """
    results = kiwi.tokenize(text)
    tokens: List[str] = []

    for w in results:
        if w.tag.startswith("N"):
            form = w.form.strip()
            if len(form) > 1 and not form.isdigit():
                tokens.append(form)
    return tokens


def build_token_counts_from_articles(texts: List[str]) -> List[Tuple[str, int]]:
    """
    여러 블로그 본문 텍스트 리스트 → 토큰 빈도 리스트.
    """
    all_tokens: List[str] = []
    for t in texts:
        all_tokens.extend(tokenize_text(t))

    counter = collections.Counter(all_tokens)
    sorted_items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return sorted_items


# -----------------------------
# 네이버 블로그 검색 API
# -----------------------------
def get_naver_credentials() -> Tuple[str, str]:
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경 변수가 없습니다."
        )

    return client_id, client_secret


def build_search_query(brand_name: str, model_name: str) -> str:
    """
    모델별 검색어 생성 규칙.
    필요하면 '시승기', '리뷰' 등으로 조정 가능.
    """
    return f"{model_name} 후기"


def search_naver_blogs_via_api(
    query: str,
    max_results: int = 3,
    sort: str = "sim",
) -> List[Dict[str, str]]:
    client_id, client_secret = get_naver_credentials()

    url = "https://openapi.naver.com/v1/search/blog.json"
    params = {
        "query": query,
        "display": max_results,
        "start": 1,
        "sort": sort,
    }
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }

    resp = requests.get(url, headers=headers, params=params, timeout=5)

    if resp.status_code != 200:
        print(
            f"[WARN] 네이버 블로그 검색 API 실패: query={query}, status={resp.status_code}"
        )
        return []

    data = resp.json()
    items = data.get("items", [])

    results: List[Dict[str, str]] = []
    for item in items[:max_results]:
        # title 안의 HTML 태그 제거
        soup_title = BeautifulSoup(item.get("title", ""), "html.parser")
        title = soup_title.get_text(" ", strip=True)
        link = item.get("link", "").strip()
        if link:
            results.append({"title": title, "url": link})

    return results


# -----------------------------
# 메인 실행 플로우
# -----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="네이버 블로그 워드클라우드용 토큰/원문 수집 (Kiwi + Naver API)"
    )
    parser.add_argument("--run-id", required=True, help="실행 ID (예: 25_11_16)")
    parser.add_argument(
        "--limit-models", type=int, default=None, help="테스트용 모델 제한"
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=3,
        help="모델별 수집할 블로그 글 개수 (기본 3개)",
    )
    parser.add_argument(
        "--summary-length",
        type=int,
        default=500,
        help="blog_article.summary 에 저장할 글자 수 (기본 500자)",
    )
    args = parser.parse_args()

    today = datetime.date.today()
    month = today.replace(day=1)
    print(f"[INFO] 수집 기준 월 = {month}")

    models = get_models_for_blog_target(limit=args.limit_models)
    print(f"[INFO] 대상 모델 수: {len(models)}")

    for m in models:
        model_id = m["model_id"]
        brand = m["brand_name"]
        model_name = m["model_name_kr"]

        if has_tokens_for_month(model_id, month):
            print(f"[INFO] 스킵 (이미 수집됨) → {brand} {model_name}")
            continue

        query = build_search_query(brand, model_name)
        print(f"[INFO] 검색 시작: query='{query}'")

        articles = search_naver_blogs_via_api(
            query,
            max_results=args.max_articles,
            sort="sim",
        )
        if not articles:
            print(f"[WARN] 검색 결과 없음: {brand} {model_name}")
            continue

        texts: List[str] = []
        for idx, a in enumerate(articles, start=1):
            try:
                print(f"  [INFO] 텍스트 수집: {a['title']} ({a['url']})")
                text_body = extract_blog_text(a["url"])
                if text_body.strip():
                    summary = text_body[: args.summary_length]

                    insert_blog_article(
                        model_id=model_id,
                        month=month,  # 위에서 today.replace(day=1)로 만든 기준 월
                        search_keyword=query,  # build_search_query에서 만든 검색어
                        search_rank=idx,  # 1, 2, 3
                        title=a["title"],
                        url=a["url"],
                        summary=summary,
                        content_plain=text_body,
                        posted_at=None,  # 나중에 필요하면 파싱
                    )

                    texts.append(text_body)
                time.sleep(0.8)
            except Exception as e:
                print(f"  [WARN] 본문 크롤링 실패: {e}")

        if not texts:
            print(f"[WARN] 본문 없음: {brand} {model_name}")
            continue

        token_counts = build_token_counts_from_articles(texts)
        if not token_counts:
            print(f"[WARN] 토큰 없음: {brand} {model_name}")
            continue

        insert_tokens(model_id, month, token_counts)
        print(
            f"[INFO] 저장 완료 → {brand} {model_name}, "
            f"토큰 수={len(token_counts)}, 글 수={len(texts)}"
        )

        time.sleep(1.5)


if __name__ == "__main__":
    main()
