import streamlit as st

# 1. 페이지 기본 설정 (감성적인 제목 및 아이콘)
st.set_page_config(
    page_title="Lofi & Vibe MBTI Jukebox",
    page_icon="🎧",  # ✅ page_icon으로 수정
    layout="centered",
)

# 2. 커스텀 CSS로 '느좋' (느낌 좋은) Lofi/빈티지 감성 연출
st.markdown("""
    <style>
    /* 배경 및 기본 폰트 감성 설정 */
    .stApp {
        background-color: #181623;
        color: #E2E1E7;
    }
    /* 카드 느낌의 컨테이너 스타일 */
    .vibe-card {
        background-color: #232035;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        border: 1px solid #342F4C;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    /* 서브텍스트 강조 */
    .highlight-text {
        color: #C084FC;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# 3. MBTI별 Lofi 트랙 및 분위기 데이터
MBTI_VIBES = {
    "INFP": {
        "title": "비 오는 날, 창가에 앉아 드로잉하기",
        "artist": "Lofi Rain & Piano Dreams",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "vibe_desc": "깊은 상상 속으로 빠져드는 잔잔한 피아노 선율과 빗소리 레이어.",
        "quote": "공상 속에 잠겨도 괜찮아요. 그곳이 당신의 가장 편안한 은신처니까요."
    },
    "INFJ": {
        "title": "새벽 2시, 서재의 작은 스탠드 조명",
        "artist": "Midnight Study Session",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "vibe_desc": "차분하고 정돈된 비트 위로 흐르는 고요한 재즈 기타 리프.",
        "quote": "복잡한 생각은 잠시 내려두고, 밤이 주는 침묵을 온전히 누려보세요."
    },
    "INTP": {
        "title": "끝없는 코드 스크롤과 미지근한 커피",
        "artist": "Cyber Chill & Glitch Lofi",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "vibe_desc": "아날로그 신디사이저와 일정한 템포의 신비로운 칠홉 비트.",
        "quote": "당신의 호기심이 가장 차분하게 피어나는 시간입니다."
    },
    "INTJ": {
        "title": "체스판 위의 조용한 계획",
        "artist": "Minimalist Focus Beats",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
        "vibe_desc": "절제된 드럼 앤 베이스 기반의 몰입감을 높여주는 로파이 사운드.",
        "quote": "목표를 향해 한 걸음씩, 조용하지만 확실하게 완벽해지는 공간."
    },
    "ENFP": {
        "title": "노을 지는 한강변에서의 스케이트보드",
        "artist": "Sunset Pop Lofi",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
        "vibe_desc": "따뜻하고 몽환적인 싱어송라이터 느낌의 팝 비트.",
        "quote": "당신이 반짝이는 아이디어를 떠올릴 때 세상은 한 층 더 칠해집니다."
    },
    "ENTP": {
        "title": "새벽 트위치 방송 라이브와 디스코드",
        "artist": "Neon Groove & Chill Vibe",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
        "vibe_desc": "톡톡 튀는 샘플링과 리드미컬한 바이브가 매력적인 로파이 펑크.",
        "quote": "재미있는 상상이 끝없이 이어져도 좋아요. 지금은 자유로운 시간이니까."
    },
    "ENFJ": {
        "title": "모두가 떠난 뒤 따스한 조명이 남은 카페",
        "artist": "Warm Coffee & Friendly Guitar",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3",
        "vibe_desc": "포근한 어쿠스틱 기타와 마음을 감싸주는 로파이 바이닐 텍스처.",
        "quote": "타인을 밝히느라 애쓴 당신에게 오늘은 따스한 휴식이 필요해요."
    },
    "ENTJ": {
        "title": "도심이 내려다보이는 야경과 루프탑",
        "artist": "Night City Skyline Beats",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
        "vibe_desc": "세련되고 묵직한 묵직한 베이스 라인의 심야형 칠홉.",
        "quote": "잠시 성장의 주행을 멈추고, 오늘 이룬 성취를 음미해보세요."
    },
    "ISFP": {
        "title": "연보랏빛 하늘과 바이닐 레코드 플레이어",
        "artist": "Cozy Bedroom Bedroom-pop",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3",
        "vibe_desc": "특유의 로파이 노이즈 질감과 스포티파이 감성 필터 오디오.",
        "quote": "말하지 않아도 전해지는 음악의 온도가 당신을 감싸줄 거예요."
    },
    "ISFJ": {
        "title": "퐁퐁 올라오는 차 김과 폭신한 수면바지",
        "artist": "Soft Herbal Tea Beats",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3",
        "vibe_desc": "부드러운 오르골 느낌의 EP 소리와 잔잔한 소품집 어쿠스틱.",
        "quote": "당신의 다정함 덕분에 오늘 하루도 누구가는 따뜻했습니다."
    },
    "ISTP": {
        "title": "심야 드라이브, 한적한 국도와 보라색 조명",
        "artist": "Night Drive Wave",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3",
        "vibe_desc": "감각적이고 서늘한 텍스처의 로파이 신스웨이브.",
        "quote": "아무런 목적지 없이 흘러가는 길 위에서 찾는 자유로움."
    },
    "ISTJ": {
        "title": "깨끗하게 정리된 책상과 따뜻한 우드 향",
        "artist": "Clean Mechanical Keyboard Lofi",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3",
        "vibe_desc": "아주 일정한 템포와 정갈한 재즈 3중주 기반의 비트.",
        "quote": "약속된 평온함 속에서 가장 완전한 휴식을 찾아냅니다."
    },
    "ESFP": {
        "title": "햇살이 쏟아지는 주말 브런치 테라스",
        "artist": "Sunny Afternoon Bossa Lofi",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-13.mp3",
        "vibe_desc": "경쾌한 보사노바 리듬에 로파이 감성이 더해진 트랙.",
        "quote": "오늘이라는 매 순간을 가장 아름답게 즐길 줄 아는 당신에게."
    },
    "ESFJ": {
        "title": "친구들과 함께 찍은 필름 카메라 사진첩",
        "artist": "Memories & Warm Polaroids",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-14.mp3",
        "vibe_desc": "추억을 떠올리게 만드는 클래식한 멜로디의 칠아웃 음악.",
        "quote": "소중한 사람들과 함께 만든 소소한 기적들을 기억해요."
    },
    "ESTP": {
        "title": "해질녘 해변의 버스킹과 파도 소리",
        "artist": "Beach Sunset Chillstep",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-15.mp3",
        "vibe_desc": "시원한 시티팝과 힙합 비트가 섞인 감각적인 Lofi 트랙.",
        "quote": "바람을 가르는 지금 이 순간, 가장 선명하게 살아있음을 느껴요."
    },
    "ESTJ": {
        "title": "일과를 완벽히 마친 뒤 마시는 시원한 음료",
        "artist": "Accomplished Evening Chill",
        "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-16.mp3",
        "vibe_desc": "안정감 있고 세련된 일렉트릭 피아노 선율의 칠홉.",
        "quote": "수고 많았던 하루, 이제 마음의 짐을 완전히 내려놓을 시간입니다."
    }
}

# 4. 앱 헤더 화면
st.title("🎧 Lofi & Vibe MBTI Jukebox")
st.caption("당신의 MBTI에 딱 맞는 '느좋' 로파이 분위기와 음악을 찾아드려요.")

st.divider()

# 5. MBTI 선택 셀렉트박스
mbti_list = list(MBTI_VIBES.keys())
selected_mbti = st.selectbox(
    "✨ 당신의 MBTI를 선택해 주세요",
    mbti_list,
    index=0,
    help="16가지 MBTI 중 하나를 선택하면 맞춤 Lofi 트랙이 재생됩니다."
)

# 6. 선택한 MBTI 분위기 카드 연출
vibe_data = MBTI_VIBES[selected_mbti]

st.markdown(f"""
<div class="vibe-card">
    <span class="highlight-text">[{selected_mbti} 맞춤 바이브]</span>
    <h2 style="margin-top: 8px; margin-bottom: 8px;">{vibe_data['title']}</h2>
    <p style="color: #A09CB0; margin-bottom: 4px;">🎵 <b>Recommended Track:</b> {vibe_data['artist']}</p>
    <p style="font-size: 0.95rem; line-height: 1.5;">{vibe_data['vibe_desc']}</p>
</div>
""", unsafe_allow_html=True)

# 7. 오디오 플레이어 (Streamlit 기본 지원)
st.audio(vibe_data["audio"], format="audio/mp3")

# 8. 감성 문구 인용구 표출
st.info(f"💡 *\"{vibe_data['quote']}\"*")

# 9. 푸터 (하단 안내)
st.divider()
st.caption("☕ 이어폰을 끼고 편안하게 감상해 보세요. Streamlit Cloud 배포 완료!")
