# Project Structure

이 문서는 `SKN22-1st-3Team` 저장소의 전체 폴더 구성을 한눈에 파악할 수 있도록 정리한 것이다.

## Top-Level Layout

```
SKN22-1st-3Team/
├── README.md
├── requirements.txt
├── LICENSE
├── data/
├── docs/
├── src/
├── archive/
├── .github/
└── .vscode/
```

각 디렉터리의 주요 역할은 아래와 같다.

- `data/` – 수집/정제된 CSV, 이미지 등 분석 데이터. 하위 구조는 [Data Directory](#data-directory) 참고.
- `docs/` – 페이지 설계, ETL 계획, ERD 등 협업 문서. 현재 파일도 이 경로에 위치한다.
- `src/` – 대시보드·ETL·API 등 모든 실행 코드.
- `archive/` – 이전 실험, 백업 산출물, 참고 스크립트(개발자별 폴더 포함).
- `.github/` – 이슈/PR 템플릿 등 GitHub 메타 설정.
- `.vscode/` – 워크스페이스 설정.
- `car_trend_backup.sql`, `logs/`, 기타 루트 파일 – DB 덤프나 보조 스크립트가 위치할 수 있다.

## Data Directory

```
data/
├── raw/             # Crawling/API 원본
│   ├── danawa/      # 다나와 판매/메타 CSV
│   ├── naver/       # 네이버 데이터랩/블로그 원본
│   ├── google/      # 구글 트렌드 wide-format CSV
│   └── ...          # 필요 시 추가 원천
├── processed/       # 정제·통합 완료본
└── wordcloud/       # 생성된 워드클라우드 이미지 (혹은 assets 로 전환)
```

> Admin 페이지에서 “구글 트렌드 보조 지표” 실행 시에는 `data/raw/google/<run_id>/` 아래에 샘플과 동일한 스키마의 CSV를 **직접 업로드**해야 한다.

## Docs Directory

```
docs/
├── project_summary.md
├── etl_planning.md
├── db_schema_and_erd.md
├── page_specification.md
├── project_roadmap.md
├── project_issues.md
├── word_definition.md
├── wireframe_main.png
├── wireframe_pages.png
└── ... (현재 문서 포함)
```

> docs/README.md 참조

## Source Directory (`src/`)

```
src/
├── api/            # 외부 API 클라이언트(Naver 등)
├── db/             # DB 커넥션 및 초기화 유틸
├── etl/
│   ├── sales/      # 다나와 크롤링·정규화·적재 스크립트
│   ├── interest/   # 네이버/구글 관심도 적재 및 집계
│   └── blog/       # 블로그 수집·토큰화·워드클라우드
└── dashboard/
    ├── app.py      # Streamlit 진입점
    ├── assets/     # CSS 등 정적 리소스
    ├── components/ # 공용 UI 위젯
    ├── pages/      # Streamlit multipage 뷰 (01_Overview 등)
    ├── utils/      # UI 헬퍼 (`load_global_css` 등)
    └── queries.py  # 대시보드에서 사용하는 DB 질의 모듈
```

### Dashboard Pages

`src/dashboard/pages/` 아래는 번호 기반 파일명으로 Streamlit 페이지를 정의한다.

- `01_Overview.py` – KPI/판매 vs 관심도 요약
- `02_관심도 분석.py`, `03_보급률 분석.py`, `04_상세 분석.py`, `05_시장 포지션.py`
- `99_admin.py` – ETL 모니터링 & 수동 실행 UI

### Components & Utilities

- `components/` – KPI 카드, 레이아웃 헬퍼, 차트 등 공용 위젯.
- `assets/style.css` – 전체 대시보드 공통 스타일.
- `utils/ui.py` – CSS 로더 등 유틸 함수.

## ETL Scripts (`src/etl/`)

- `sales/` – `run_danawa_model_crawl.py`, `load_danawa_sales_to_db.py` 등 다나와 파이프라인.
- `interest/` – 네이버 데이터랩 수집/정규화(`run_naver_trend_crawl.py`, `load_naver_interest_detail.py`), 구글 트렌드 적재(`load_google_trend.py`), detail→summary 집계(`aggregate_naver_interest.py`).
- `blog/` – 네이버 블로그 검색, 본문 수집, 키워드 토큰화, `generate_wordcloud.py`.

각 스크립트는 CLI 파라미터를 통해 `run_id`, 기간, 브랜드 등을 받으며 Admin 페이지에서 버튼 클릭으로 실행할 수 있다.

## Archive

`archive/`는 팀원이 개별적으로 실험하거나 백업해 둔 코드/데이터를 보관한다. 예: `archive/EomHyungEun/dashboard/`, 과거 Streamlit 버전, SQL 백업 등. 운영 코드에는 직접 사용되지 않지만 참고용으로 유지한다.

---
