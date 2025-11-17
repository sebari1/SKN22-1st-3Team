# Page Specification – Streamlit Dashboard (`src/dashboard`)

국내 자동차 시장 트렌드 분석 대시보드의 Streamlit 페이지 구성을 나열한다. 각 페이지는 `src/dashboard/pages` 아래의 파일과 직접 매핑된다.

---

## 01_Overview.py

- **목적**: 최신 월 기준 KPI, 판매량 vs 관심도 TOP N, 선택 모델 상세 요약, 블로그 워드클라우드를 한 화면에서 보여준다.
- **핵심 구성**
  1. 기준 월 / 제조사 / TOP N 필터 (`model_monthly_sales`, `model_monthly_interest`, `car_model`)
  2. 판매량 vs 관심도 (Plotly bar+line overlay) 및 KPI 지표
  3. 선택 모델 6개월 추세 (판매/보급률 vs 관심도)
  4. 블로그 워드클라우드 + 토큰/상위 글 (`blog_token_monthly`, `blog_wordcloud`, `blog_article`)
- **사용 데이터**: `model_monthly_sales`, `model_monthly_interest`, `car_model`, `blog_*`

---

## 02\_관심도 분석.py

- **목적**: 네이버/구글 관심도 기반으로 모델별 인기와 디바이스·성별 상세 지표를 비교한다.
- **핵심 구성**
  1. 월/브랜드/TOP N 필터
  2. 관심도 Top N (interest_score 정렬)
  3. 모델별 관심도 상세 카드/테이블
  4. 네이버 detail (device×gender) 뷰 (`model_monthly_interest_detail`)
- **사용 데이터**: `model_monthly_interest`, `model_monthly_interest_detail`, `car_model`

---

## 03\_보급률 분석.py

- **목적**: 다나와 판매량/보급률 데이터를 바탕으로 Top N 모델과 RAW 테이블을 확인한다.
- **핵심 구성**
  1. 기준 월 / 브랜드 / TOP N 필터
  2. 보급률 Top N 차트 (bar)
  3. 모델별 보급률 요약 표
  4. 다나와 월간 판매 RAW 데이터 표 (정렬/다운로드)
- **사용 데이터**: `model_monthly_sales`, `car_model`

---

## 04\_상세 분석.py

- **목적**: 특정 모델을 선택해 기간별 판매/관심도 추이와 블로그 데이터를 종합적으로 확인한다.
- **핵심 구성**
  1. 브랜드/모델/기간 필터
  2. KPI (기간 총 판매량, 평균 보급률, 평균 관심도)
  3. 판매량 vs 관심도 타임라인 (Plotly)
  4. 네이버 vs 구글 검색 지수
  5. 블로그/워드클라우드 스냅샷 (키워드/이미지/상위 글)
- **사용 데이터**: `model_monthly_sales`, `model_monthly_interest`, `model_monthly_interest_detail`, `blog_*`

---

## 05\_시장 포지션.py

- **목적**: 판매량·보급률·관심도(네이버+구글)를 결합한 포지션 맵을 시각화한다.
- **핵심 구성**
  1. 기준 월 선택
  2. Scatter Plot (판매량 vs 관심도, 버블 크기/색상 옵션)
  3. 포지션 테이블 (필요 시 다운로드)
- **사용 데이터**: `model_monthly_sales`, `model_monthly_interest`, `car_model`

---

## 99_admin.py

- **목적**: ETL 상태 모니터링, 테이블 카운트/최신 월 확인, ETL 스크립트 수동 실행 UI 제공.
- **핵심 구성**
  1. 테이블 레코드 수 요약
  2. 데이터셋별 최신 month 요약
  3. ETL 파이프라인 별 설명 + 실행 버튼 (다나와/네이버/구글/블로그)
  4. 실행 로그 표시 (성공/실패/CLI 명령)
- **사용 데이터**: `queries.get_admin_table_counts`, `queries.get_admin_latest_months` (전 테이블 요약)

---

## 공통 참고

- 모든 페이지는 `utils/ui.load_global_css()`로 `assets/style.css`를 적용한다.
- 레이아웃/섹션은 `components/layout.py`의 `page_header`, `section` 등을 재사용한다.
- 데이터 Access는 `src/dashboard/queries.py`의 함수들을 통해 수행한다.
