import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

# ---------------------------------------------------------
# 1. 페이지 및 모바일 UX 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="동탄-광교 내집마련 트래커",
    page_icon="🏡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DB_FILE = "real_estate_db.json"

# ---------------------------------------------------------
# 2. 초기 데이터 베이스 세팅 및 저장/로드 로직
# ---------------------------------------------------------
DEFAULT_DATA = {
    "complexes": [
        {"id": 1, "name": "e편한세상 반월 나노시티역", "rank": 1, "target_min": 77000, "target_max": 80000, "ceiling": 85000, "status": "HOLDING", "desc": "가장 균형 좋음 (2017년식 / 1,387세대)"},
        {"id": 2, "name": "능동역센트럴경남아너스빌", "rank": 2, "target_min": 76000, "target_max": 78000, "ceiling": 80000, "status": "HOLDING", "desc": "가격 메리트 시 강력 (2008년식 / 641세대)"},
        {"id": 3, "name": "동탄예당마을푸르지오", "rank": 3, "target_min": 75000, "target_max": 80000, "ceiling": 85000, "status": "HOLDING", "desc": "올수리 프리미엄 반영 필요 (2008년식 / 914세대)"},
        {"id": 4, "name": "동탄예당마을롯데캐슬", "rank": 4, "target_min": 85000, "target_max": 87000, "ceiling": 90000, "status": "HOLDING", "desc": "예당 핵심 입지 (2008년식 / 1,222세대)"},
        {"id": 5, "name": "동탄역 에일린의뜰", "rank": 5, "target_min": 75000, "target_max": 80000, "ceiling": 82000, "status": "HOLDING", "desc": "동탄역 생활권 준신축 (2016년식 / 489세대)"},
        {"id": 100, "name": "광교 상급지 목표 단지", "rank": 0, "target_min": 130000, "target_max": 140000, "ceiling": 150000, "status": "TARGET", "desc": "3~5년 후 최종 갈아타기 목표 단지"}
    ],
    "listings": [
        {"id": 1, "complex_id": 2, "building": "802동", "floor": "10층", "price": 78000, "date": "2026-03-08", "memo": "집주인 거주 / 관리 상태 양호. 7.6억 네고 시 매수"},
        {"id": 2, "complex_id": 2, "building": "809동", "floor": "12층", "price": 83000, "date": "2026-03-08", "memo": "풀수리(확장, 샷시, 에어컨). 8.0억 이하 네고 필요"},
        {"id": 3, "complex_id": 3, "building": "푸르지오 올수리", "floor": "중층", "price": 89000, "date": "2026-03-08", "memo": "6~7천 들여 올수리. 8.9억은 거절, 8.2억 이하 대기"},
        {"id": 4, "complex_id": 4, "building": "롯데캐슬 중층", "floor": "중층", "price": 92000, "date": "2026-03-08", "memo": "KB일반가 8.85억 대비 높음. 추격매수 금지"},
        {"id": 5, "complex_id": 1, "building": "e편한 중층", "floor": "중층", "price": 85000, "date": "2026-03-08", "memo": "최근 호가 8.5~10억 상승. 7.7~8.0억 조정 시까지 대기"}
    ]
}

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=2)
        return DEFAULT_DATA
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

db = load_db()

# 금액 단위 변환 함수 (만원 -> 억/천만원)
def format_price(price_10k):
    if price_10k is None or price_10k == 0:
        return "-"
    uk = price_10k // 10000
    rest = price_10k % 10000
    if rest == 0:
        return f"{uk}억"
    elif uk == 0:
        return f"{rest:,}만"
    else:
        return f"{uk}억 {rest:,}"

# ---------------------------------------------------------
# 3. 모바일 헤더 UI
# ---------------------------------------------------------
st.markdown("### 🏡 동탄 매수 & 광교 갈아타기 트래커")
st.caption("1차: 감당 가능한 84㎡ 안전마진 매수 ➔ 2차: 3~5년 후 광교 이동")

# 핵심 원칙 가이드 카드
st.info("**💡 매수 원칙:** 내가 감당 가능한 범위에서 가장 좋은 84㎡를 시장가보다 싸게 사고, 2022년 하락장 방어가 증명된 단지를 선택한다.")

# ---------------------------------------------------------
# 4. 탭 구성 (목표/현황, 매물입력, 히스토리/갭분석)
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📌 단지 현황", "➕ 호가 등록", "📊 히스토리/갭"])

# ---------------------------------------------------------
# TAB 1: 단지별 목표가 & 현재 최저 호가 비교
# ---------------------------------------------------------
with tab1:
    st.subheader("🎯 관심 단지별 매수 목표가 현황")
    
    # 단지별 최저 호가 계산
    complexes = db["complexes"]
    listings = db["listings"]
    
    # 순위순 정렬
    holding_complexes = sorted([c for c in complexes if c["status"] == "HOLDING"], key=lambda x: x["rank"])
    
    for comp in holding_complexes:
        comp_id = comp["id"]
        comp_listings = [l for l in listings if l["complex_id"] == comp_id]
        
        # 최저 호가 계산
        min_asking = min([l["price"] for l in comp_listings]) if comp_listings else None
        
        with st.container():
            st.markdown(f"#### {comp['rank']}위. {comp['name']}")
            st.caption(f"ℹ️ {comp['desc']}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🎯 목표 매수가", f"{format_price(comp['target_min'])} ~ {format_price(comp['target_max'])}")
            
            if min_asking:
                diff = min_asking - comp['target_max']
                diff_str = "🟢 범위 진입" if diff <= 0 else f"🔴 +{diff/10000:.1f}억"
                c2.metric("🔍 현재 최저호가", format_price(min_asking), delta=diff_str, delta_color="inverse")
            else:
                c2.metric("🔍 현재 최저호가", "등록 매물 없음")
                
            c3.metric("🚨 마지노선(거절)", format_price(comp['ceiling']))
            
            # 매물별 세부 정보
            if comp_listings:
                with st.expander(f"📋 등록된 매물 ({len(comp_listings)}건) 보기"):
                    for item in comp_listings:
                        st.markdown(f"- **[{item['building']} / {item['floor']}]** `{format_price(item['price'])}` ({item['date']})")
                        st.caption(f"  └ 메모: {item['memo']}")
            st.divider()

# ---------------------------------------------------------
# TAB 2: 모바일 호가 신규 등록 및 관리
# ---------------------------------------------------------
with tab2:
    st.subheader("📝 새로운 매물 호가 추가하기")
    
    with st.form("add_listing_form"):
        # 단지 선택
        comp_options = {c["id"]: f"[{c['rank']}위] {c['name']}" for c in holding_complexes}
        selected_comp_id = st.selectbox("단지 선택", options=list(comp_options.keys()), format_func=lambda x: comp_options[x])
        
        c_bld, c_flr = st.columns(2)
        building = c_bld.text_input("동 (예: 802동)", value="")
        floor = c_flr.text_input("층 (예: 10층 / 중층)", value="중층")
        
        price_10k = st.number_input("호가 (만원 단위입력, 예: 78000 = 7억 8천)", min_value=10000, max_value=300000, value=78000, step=1000)
        st.write(f"👉 **입력 금액:** {format_price(price_10k)}")
        
        date_str = st.date_input("확인 일자", datetime.now()).strftime("%Y-%m-%d")
        memo = st.text_area("매물 특징 / 협상 메모", placeholder="예: 풀수리 완료, 7.6억 네고 가능 시 매수 검토")
        
        submitted = st.form_submit_button("💾 매물 호가 저장하기", use_container_width=True)
        
        if submitted:
            new_id = max([l["id"] for l in db["listings"]], default=0) + 1
            new_listing = {
                "id": new_id,
                "complex_id": selected_comp_id,
                "building": building if building else "미정",
                "floor": floor,
                "price": price_10k,
                "date": date_str,
                "memo": memo
            }
            db["listings"].append(new_listing)
            save_db(db)
            st.success("✅ 새로운 매물 호가가 성공적으로 저장되었습니다!")
            st.rerun()

# ---------------------------------------------------------
# TAB 3: 가격 변동 히스토리 & 광교 갈아타기 갭 분석
# ---------------------------------------------------------
with tab3:
    st.subheader("📈 매물 호가 추이")
    
    # DataFrame 변환
    if db["listings"]:
        df_list = []
        comp_dict = {c["id"]: c["name"] for c in db["complexes"]}
        
        for l in db["listings"]:
            df_list.append({
                "단지명": comp_dict.get(l["complex_id"], "기타"),
                "매물": f"{l['building']} ({l['floor']})",
                "호가(억원)": l["price"] / 10000,
                "날짜": l["date"]
            })
        
        df = pd.DataFrame(df_list)
        
        fig = px.line(df, x="날짜", y="호가(억원)", color="단지명", markers=True, title="단지별 호가 변동 그래프")
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # 광교 갈아타기 갭 분석
    st.subheader("🚀 광교 상급지 갈아타기 갭(Gap) 계산기")
    
    gwanggyo_target = st.number_input("광교 목표 단지 예상 가격 (만원)", value=135000, step=1000)
    st.write(f"🏢 광교 목표가: **{format_price(gwanggyo_target)}**")
    
    my_buy_target = st.number_input("1차 동탄 매수 예정가 (만원)", value=78000, step=1000)
    st.write(f"🏠 1차 매수가: **{format_price(my_buy_target)}**")
    
    gap = gwanggyo_target - my_buy_target
    st.metric("🔑 필요 갈아타기 갭 (추가 자본금/대출 필요액)", format_price(gap))