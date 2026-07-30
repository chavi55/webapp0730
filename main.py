import streamlit as st

# 1. 페이지 설정
st.set_page_config(
    page_title="MBTI 3D Room Studio",
    page_icon="🏠",
    layout="centered"
)

# 2. 감성적인 Dark / Pastel 3D 다이오라마 스타일 CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #12131C;
        color: #F1F0F5;
    }
    .room-card {
        background-color: #1E1F2E;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        border: 1px solid #2D2F45;
        margin-top: 15px;
        margin-bottom: 25px;
    }
    .mbti-badge {
        background-color: #8B5CF6;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 8px;
    }
    .room-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 8px;
        color: #FFFFFF;
    }
    .room-desc {
        color: #A0A3BD;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. MBTI별 3D 방 이미지 및 테마 설명 데이터
ROOM_DATA = {
    "INFP": {
        "title": "꿈꾸는 식물학자의 다락방",
        "image": "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&q=80",
        "desc": "따스한 햇살이 드는 창가, 빈티지 서적과 푸릇푸릇한 식물들이 가득한 조용한 비밀 공간입니다.",
        "concept": "🌱 파스텔 그린 & 몽환적인 코지 룸"
    },
    "INFJ": {
        "title": "심야의 고요한 서재",
        "image": "https://images.unsplash.com/photo-1505691938895-1758d7feb511?w=800&q=80",
        "desc": "벽면을 채운 책장과 작은 차 테이블. 나만의 단단한 생각을 가다듬을 수 있는 따뜻한 램프 조명 스튜디오.",
        "concept": "📖 웜 우드 & 정돈된 서재"
    },
    "INTP": {
        "title": "미래지향 멀티 모니터 연구실",
        "image": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&q=80",
        "desc": "복잡한 회로보드, 네온 조명과 여러 대의 화면. 오롯이 나만의 지적 탐구에 몰입하는 미니멀 공간.",
        "concept": "👾 사이버 칠 & 디스플레이 데스크"
    },
    "INTJ": {
        "title": "체스판 같은 완벽한 데스크 룸",
        "image": "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=800&q=80",
        "desc": "군더더기 없는 미니멀리즘 가구와 짙은 스모키 톤의 인테리어. 전략과 집중을 위한 완벽한 구도.",
        "concept": "📐 모노톤 미니멀 스튜디오"
    },
    "ENFP": {
        "title": "알록달록 아이디어 아트 룸",
        "image": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&q=80",
        "desc": "영감이 솟아구치는 파스텔톤 소품과 귀여운 피규어, 벽면에 붙은 가득한 포스트잇 스페이스.",
        "concept": "🎨 파스텔 팝 & 크리에이티브 공간"
    },
    "ENTP": {
        "title": "자유로운 얼리어답터의 아지트",
        "image": "https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=800&q=80",
        "desc": "다양한 가젯과 피규어, 톡톡 튀는 오브제들이 조화를 이루는 창의적이고 감각적인 아지트.",
        "concept": "⚡ 레트로 펑크 & 테크 데스크"
    },
    "ENFJ": {
        "title": "손님을 맞이하는 따스한 티룸",
        "image": "https://images.unsplash.com/photo-1540518614846-7ede433c5172?w=800&q=80",
        "desc": "부드러운 쇼파와 다정한 쿠션, 언제든 누군가를 초대해 진솔한 대화를 나누고 싶은 온기 있는 방.",
        "concept": "☕ 샌드 베이지 & 코튼 라이트"
    },
    "ENTJ": {
        "title": "도심 야경이 보이는 모던 팬트하우스",
        "image": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=800&q=80",
        "desc": "탁 트인 통창 너머의 야경과 세련된 가죽 스튜디오 체어. 목표를 설계하는 현대적인 공간.",
        "concept": "🏙️ 미드센추리 모던 & 라운지"
    },
    "ISFP": {
        "title": "아늑한 캔버스 아틀리에",
        "image": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=800&q=80",
        "desc": "부드러운 패브릭 소재, 바이닐 스피커, 햇살이 부서져 내리는 오감을 자극하는 감성 화실.",
        "concept": "🛋️ 오프화이트 & 바이닐 아지트"
    },
    "ISFJ": {
        "title": "폭신한 니트 쿠션이 있는 침실",
        "image": "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?w=800&q=80",
        "desc": "정돈된 침구와 무드등, 마음을 편안하게 해주는 은은한 은신처 같은 포근한 3D 침실.",
        "concept": "🧸 포근한 크림 & 베이지 라이트"
    },
    "ISTP": {
        "title": "디테일한 DIY 게이밍 게라지",
        "image": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&q=80",
        "desc": "기계 공구와 정교한 도구들, 고성능 게이밍 세팅이 하나로 어우러진 손재주꾼의 방.",
        "concept": "🛠️ 메탈릭 다크 & 스포트라이트"
    },
    "ISTJ": {
        "title": "단정함의 정석, 타임리스 스터디",
        "image": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=800&q=80",
        "desc": "모든 물건이 제자리에 정리된 칼같은 정돈감. 클래식한 우드 톤의 차분하고 신뢰감 있는 방.",
        "concept": "📐 디테일 우드 & 오거나이즈"
    },
    "ESFP": {
        "title": "트로피컬 선셋 비치하우스",
        "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&q=80",
        "desc": "해질녘 분홍빛 노을이 물드는 테라스와 통통 튀는 인테리어 소품이 매력적인 파티 룸.",
        "concept": "🌊 코랄 핑크 & 트로피컬 3D"
    },
    "ESFJ": {
        "title": "행복한 홈파티 아일랜드",
        "image": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=800&q=80",
        "desc": "소중한 사람들과 맛있는 음식을 나눌 수 있는 따뜻하고 왁자지껄한 다이닝 스페이스.",
        "concept": "🍞 옐로우 웜 & 키친 베이커리"
    },
    "ESTP": {
        "title": "액티비티 스포츠 기어 룸",
        "image": "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800&q=80",
        "desc": "스케이트보드와 운동 기구, 스피디한 감각이 돋보이는 에너제틱 3D 스튜디오.",
        "concept": "🛹 다이나믹 블록 & 스트릿"
    },
    "ESTJ": {
        "title": "스마트 프라이빗 오피스",
        "image": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&q=80",
        "desc": "효율적인 동선과 체계적인 스케줄러가 돋보이는 완벽한 생산성 중심의 세련된 방.",
        "concept": "💼 딥 블루 & 오피스 스튜디오"
    }
}

# 4. 앱 헤더
st.title("🏠 MBTI 3D Cozy Room Studio")
st.caption("16가지 MBTI 성향에 딱 맞는 3D 분위기의 아기자기한 방을 찾아드려요.")

st.divider()

# 5. MBTI 선택
selected_mbti = st.selectbox(
    "✨ 당신의 MBTI를 선택해 주세요",
    list(ROOM_DATA.keys()),
    index=0
)

# 6. 선택된 방 정보
room = ROOM_DATA[selected_mbti]

# 방 카드 UI
st.markdown(f"""
<div class="room-card">
    <span class="mbti-badge">{selected_mbti} Style</span>
    <div class="room-title">{room['title']}</div>
    <div style="color: #C084FC; font-weight: 500; font-size: 0.9rem;">{room['concept']}</div>
    <p class="room-desc">{room['desc']}</p>
</div>
""", unsafe_allow_html=True)

# 7. 아기자기한 3D 방 이미지 출력
st.image(room["image"], use_column_width=True, caption=f"3D Visual for {selected_mbti}")

st.divider()
st.caption("💡 팁: 원하는 이미지를 우클릭하여 저장하거나 배경화면으로 활용해 보세요!")
