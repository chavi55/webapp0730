import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="전국 중학생(14~16세) 인구 비율 지도",
    layout="wide"
)

st.title("전국 시군구별 중학생(14~16세) 인구 비율 지도")
st.caption("2015년~최신 연도 행정동별 인구 데이터를 기반으로 시군구별 중학생 비율을 시각화합니다.")

# 2. 데이터 불러오기 및 전처리 (캐싱 활용)
@st.cache_data
def load_population_data():
    """인구 CSV 데이터를 불러오고 최신 연도 및 시군구별 데이터를 정제하는 함수"""
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/population_yearly.csv.gz"
    
    # '코드' 열은 10자리 문자열로 불러와 앞자리가 0인 경우 누락되지 않도록 처리
    df = pd.read_csv(url, dtype={'코드': str})
    df['코드'] = df['코드'].str.zfill(10)
    
    # 최신 연도 데이터 필터링
    latest_year = df['연도'].max()
    df_latest = df[df['연도'] == latest_year].copy()
    
    # 행정동 코드 10자리 중 앞 5자리를 잘라 시군구 코드 생성
    df_latest['시군구코드'] = df_latest['코드'].str[:5]
    
    # 중학생(14~16세) 및 전체 인구 컬럼 정의
    middle_school_cols = ['계_14세', '계_15세', '계_16세']
    total_cols = [c for c in df_latest.columns if c.startswith('계_')]
    
    # 그룹화 기준 설정 (월 데이터 유무 체크)
    group_cols = ['시도', '시군구코드']
    if '월' in df_latest.columns:
        group_cols.append('월')
        
    df_grouped = df_latest.groupby(group_cols)[total_cols].sum().reset_index()
    
    # 인구수 계산
    df_grouped['중학생인구'] = df_grouped[middle_school_cols].sum(axis=1)
    df_grouped['전체인구'] = df_grouped[total_cols].sum(axis=1)
    
    # 중학생 비율(%) 계산 (0 나누기 방지)
    df_grouped['중학생비율'] = (df_grouped['중학생인구'] / df_grouped['전체인구'].replace(0, pd.NA)) * 100
    df_grouped['중학생비율'] = df_grouped['중학생비율'].fillna(0).round(2)
    
    # 5단계 구간 나누기 (19%, 23%, 28%, 38%)
    bins = [-1, 19, 23, 28, 38, 100]
    labels = ['19% 미만', '19% 이상 ~ 23% 미만', '23% 이상 ~ 28% 미만', '28% 이상 ~ 38% 미만', '38% 이상']
    
    df_grouped['비율구간'] = pd.cut(df_grouped['중학생비율'], bins=bins, labels=labels)
    
    return df_grouped, latest_year

@st.cache_data
def load_geojson():
    """GeoJSON 시군구 경계 데이터를 불러오는 함수"""
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/boundaries/sigungu_kr.geojson"
    res = requests.get(url)
    return res.json()

# 데이터 로딩
try:
    with st.spinner("데이터를 불러오는 중입니다..."):
        df_pop, latest_year = load_population_data()
        geojson_data = load_geojson()
    st.sidebar.success(f"데이터 기준 연도: **{latest_year}년**")
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 3. 지도 시각화 설정 (Plotly Choropleth Mapbox)

# 5단계 이산형 단계구분 색상 맵 설정 (연한 색 -> 진한 색)
color_discrete_map = {
    '19% 미만': '#f7fbff',
    '19% 이상 ~ 23% 미만': '#c6dbef',
    '23% 이상 ~ 28% 미만': '#6baed6',
    '28% 이상 ~ 38% 미만': '#2171b5',
    '38% 이상': '#08519c'
}

category_orders = {
    '비율구간': ['19% 미만', '19% 이상 ~ 23% 미만', '23% 이상 ~ 28% 미만', '28% 이상 ~ 38% 미만', '38% 이상']
}

animation_frame = '월' if '월' in df_pop.columns else None

# 지도 생성
fig = px.choropleth_mapbox(
    df_pop,
    geojson=geojson_data,
    locations='시군구코드',
    featureidkey='properties.코드',  # 시군구 코드 5자리 매칭
    color='비율구간',
    color_discrete_map=color_discrete_map,
    category_orders=category_orders,
    animation_frame=animation_frame,
    hover_name='시도',
    hover_data={
        '시군구코드': True,
        '중학생비율': ':.2f%',
        '중학생인구': ':,',
        '전체인구': ':,',
        '비율구간': False
    },
    mapbox_style="white-bg",  # 지도 배경 타일 없이 경계선만 표시
    center={"lat": 35.9, "lon": 127.7},  # 대한민국 중심
    zoom=6,
    opacity=0.85
)

# 호버 테두리 색상(파란색) 및 툴팁 박스 위치(왼쪽 위) 세부 레이아웃 적용
fig.update_layout(
    margin={"r": 0, "t": 30, "l": 0, "b": 0},
    
    # 마우스 오버 시 정보를 지도의 왼쪽 위에 고정된 네모 박스 스타일로 표시
    hoverlabel=dict(
        bgcolor="white",             # 네모 박스 배경색
        font_size=14,                # 글자 크기
        font_color="#111111",        # 글자 색상
        font_family="Malgun Gothic, Apple SD Gothic Neo, sans-serif",
        bordercolor="#0055ff"        # 호버 네모 박스 테두리 파란색
    ),
    hovermode="closest",
    
    # 우측 상단 범례 설정
    legend_title_text='중학생 인구 비율 구간',
    legend=dict(
        yanchor="top",
        y=0.98,
        xanchor="right",
        x=0.98,
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="#cccccc",
        borderwidth=1
    )
)

# 마우스를 올렸을 때(호버) 영역 경계선을 파란색으로 강조
fig.update_traces(
    marker_line_width=1.5,
    marker_line_color="#0055ff",  # 파란색 테두리
    # 마우스 오버 시 상단 좌측 네모 박스에 들어갈 텍스트 형태 지정
    hovertemplate=(
        "<b>📍 %{hovertext} (코드: %{location})</b><br>"
        "------------------------------<br>"
        "<b>• 중학생 비율:</b> %{customdata[1]:.2f}%<br>"
        "<b>• 중학생 인구수:</b> %{customdata[2]:,}명<br>"
        "<b>• 전체 인구수:</b> %{customdata[3]:,}명"
        "<extra></extra>"
    )
)

# 스트림릿에 지도 출력
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# 4. 지도 하단 상위 / 하위 10개 시군구 표 표시
st.subheader("📊 시군구별 중학생 비율 상위 / 하위 10개 지역")

# 월별 애니메이션 데이터가 있을 경우 가장 최근 월 기준으로 순위 표출
if animation_frame and '월' in df_pop.columns:
    latest_month = df_pop['월'].max()
    df_rank_base = df_pop[df_pop['월'] == latest_month].copy()
    st.caption(f"* 아래 순위표는 가장 최근 데이터인 **{latest_month}월** 기준입니다.")
else:
    df_rank_base = df_pop.copy()

# 표에 표시할 데이터 가공
df_display = df_rank_base[['시도', '시군구코드', '중학생비율', '중학생인구', '전체인구']].copy()
df_display.columns = ['시도', '시군구코드', '중학생 비율(%)', '중학생 수(명)', '전체 인구(명)']

# 상위 10개 / 하위 10개 추출
top_10 = df_display.sort_values(by='중학생 비율(%)', ascending=False).head(10).reset_index(drop=True)
top_10.index = top_10.index + 1  # 순위를 1부터 표시

bottom_10 = df_display.sort_values(by='중학생 비율(%)', ascending=True).head(10).reset_index(drop=True)
bottom_10.index = bottom_10.index + 1

# 두 개의 컬럼으로 나란히 표시
col1, col2 = st.columns(2)

with col1:
    st.markdown("##### 🥇 중학생 비율 가장 높은 지역 TOP 10")
    st.dataframe(top_10, use_container_width=True)

with col2:
    st.markdown("##### 🔻 중학생 비율 가장 낮은 지역 TOP 10")
    st.dataframe(bottom_10, use_container_width=True)
