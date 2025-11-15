# 전체 데이터를 입력 받아오는 경우
# 장점: 1개의 제품에 대해서만 검색해서 빠르게 데이터가 보여질 수 있음 
# 단점: 다른 차들과의 검색 트랜드를 한번에 확인 할 수 없음 
        # 오타 발생시 데이터 추출 불가 (ex: "아반떼"=데이터 집계완료 / "아반테"=데이터 집계불가)

# 네이버 검색지수 단위(=Index) 설명
# 네이버는 특정 기간에서 검색량이 가장 많은 시점을 100으로 설정하고
# 나머지는 그 기준에 따라 비율로 환산해줘.
# 예를 들어:
# 그 기간 동안 특정 키워드가 가장 많이 검색된 날이 100
# 검색량이 절반이면 → 50
# 1이면 → 최고검색량의 1/100 수준
# 즉, 1은 실제 검색량 1건이 아니라 ‘최대 검색량 대비 1% 수준’이라는 의미에 가까워.


# fetch_datalab.py
import requests
import json
import csv
import os
from dotenv import load_dotenv

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
    raise ValueError("⚠️ NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET가 .env에 존재하지 않습니다.")

url = "https://openapi.naver.com/v1/datalab/search"

headers = {
    "X-Naver-Client-Id": NAVER_CLIENT_ID,
    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    "Content-Type": "application/json"
}

# 브랜드별 차종 정리
HYUNDAI_MODELS = [
    "아반떼", "그랜저", "싼타페", "쏘나타 디 엣지", "투싼",
    "디 올 뉴 팰리세이드", "포터2", "코나", "스타리아", "아이오닉 5",
    "캐스퍼 일렉트릭", "아이오닉 9", "디 올 뉴 넥쏘", "포터2 일렉트릭", "베뉴",
    "캐스퍼", "코나 일렉트릭", "더 뉴 아이오닉6", "ST1", "아반떼 N",
    "아이오닉 5 N"
]

KIA_MODELS = [
    "쏘렌토", "카니발", "스포티지", "셀토스",
    "K5", "봉고 3", "레이", "K8", "모닝",
    "PV5", "EV3", "EV5", "니로", "레이 EV",
    "EV6", "EV4", "타스만", "EV9", "K9", "니로 EV"
]

def get_brand(car_name: str) -> str:
    if car_name in HYUNDAI_MODELS:
        return "HYUNDAI"
    elif car_name in KIA_MODELS:
        return "KIA"
    else:
        return "UNKNOWN"

# 브랜드별 차량 키워드에 대한 데이터 수집 (데이터 수집이 오래 걸리면 기간 수정 필요)
def fetch_trend(car_name):

    brand_name = get_brand(car_name)

    if brand_name == "UNKNOWN":
        print(f" '{car_name}'는 등록된 자동차명이 없습니다.")
        return []

    keyword_groups = [{"groupName": car_name, "keywords": [car_name]}]
    brand_name = get_brand(car_name)

    genders = {"male": "m", "female": "f"}
    devices = {"pc": "pc", "mobile": "mo"}

    records = []

    for gender_label, gender_code in genders.items():
        for device_label, device_code in devices.items():

            body = {
                "startDate": "2023-01-01",
                "endDate": "2025-10-31",
                "timeUnit": "month",
                "keywordGroups": keyword_groups,
                "device": device_code,
                "gender": gender_code
            }

            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

            for result in data["results"]:
                for row in result["data"]:
                    records.append({
                        "date": row["period"],
                        "brand": brand_name,
                        "product": car_name,
                        "device": device_label,
                        "gender": gender_label,
                        "query": row["ratio"]
                    })

# CSV 저장
    csv_filename = f"naver_datalab_product_input.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["date", "brand", "product", "device", "gender", "query"]
        )
        writer.writeheader()
        writer.writerows(records)

    print(f"CSV 저장 완료 → {csv_filename}")
    print("총 데이터 건수:", len(records))

# 결과 내용 출력
if __name__ == "__main__":
    car_name = input("차량명을 입력하세요: ")
    fetch_trend(car_name)

