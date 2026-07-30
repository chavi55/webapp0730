import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# 1. 페이지 기본 설정 (와이드 레이아웃)
st.set_page_config(
    page_title="전국 시·도별 중학생(14~16세) 인구 비율 지도",
    layout="wide"
)

st.title("전국 시·도별 중학생(14~16세) 인구 비율 지도")
st.caption("2015년~최신 연도 행정동별 인구 데이터를 기반으로 시·도별 중학생 비율을 시각화합니다.")

# 2. 데이터 불러오기 및 시·도 단위 전처리
@st.cache_data
def load_population_data():
    """인구 CSV 데이터를 불러와 시·도(코드 2자리) 단위로 정제하는 함수"""
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/population_yearly.csv.gz"
    
    # '코드' 열은 문자열(10자리)로 읽어오기
    df = pd.read_csv(url, dtype={'코드': str})
    df['코드'] = df['코드'].str.zfill(10)
    
    # 행정동 코드 앞 2자리를 잘라 시도코드 생성 (예: '11' = 서울특별시)
    df['시도코드'] = df['코드'].str[:2]
    
    # 중학생(14~16세) 및 전체 인구 컬럼 정의
    middle_school_cols = ['계_14세', '계_15세', '계_16세']
    total_cols = [c for c in df.columns if c.startswith('계_')]
    
    # 그룹화 기준 (연도, 시도, 시도코드, 월)
    group_cols = ['연도', '시도', '시도코드']
    if '월' in df.columns:
        group_cols.append('월')
        
    df_grouped = df.groupby(group_cols)[total_cols].sum().reset_index()
    
    # 중학생 인구수 및 전체 인구수 계산
    df_grouped['중학생인구'] = df_grouped[middle_school_cols].sum(axis=1)
    df_grouped['전체인구'] = df_grouped[total_cols].sum(axis=1)
    
    # 중학생 비율(%) 계산
    df_grouped['중학생비율'] = (df_grouped['중학생인구'] / df_grouped['전체인구'].replace(0, pd.NA)) * 100
    df_grouped['중학생비율'] = df_grouped['중학생비율'].fillna(0).round(2)
    
    # 지정된 5단계 구간 나누기 (시·도 단위 분포에 대응)
    bins = [-1, 19, 23, 28, 38, 100]
    labels = ['19% 미만', '19% 이상 ~ 23% 미만', '23% 이상 ~ 28% 미만', '28% 이상 ~ 38% 미만', '38% 이상']
    
    df_grouped['비율구간'] = pd.cut(df_grouped['중학생비율'], bins=bins, labels=labels)
    
    return df_grouped

@st.cache_data
def load_sido_geojson():
    """시·도 GeoJSON 경계 데이터 로드"""
    # 대한민국 시도 경계 GeoJSON URL
    url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo.json"
    res = requests.get(url)
    return res.json()

# 데이터 로딩
try:
    with st.spinner("데이터를 불러오는 중입니다..."):
        df_all = load_population_data()
        geojson_data = load_sido_geojson()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 3. 사이드바 - 연도 선택 슬라이더
min_year = int(df_all['연도'].min())
max_year = int(df_all['연도'].max())

st.sidebar.header("⚙️ 지도 설정")
selected_year = st.sidebar.slider(
    "조회할 연도를 선택하세요",
    min_value=min_year,
    max_value=max_year,
    value=max_year,
    step=1
)

st.sidebar.info(f"📅 **선택된 연도:** {selected_year}년")

# 선택한 연도 데이터만 필터링
df_pop = df_all[df_all['연도'] == selected_year].copy()

# 4. 지도 시각화 설정 (Plotly Choropleth Mapbox)

# 5단계 색상 맵 설정
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

# 시도 경계 지도 생성
fig = px.choropleth_mapbox(
    df_pop,
    geojson=geojson_data,
    locations='시도코드',
    featureidkey='properties.code',  # 시도 GeoJSON의 2자리 코드 속성 매칭
    color='비율구간',
    color_discrete_map=color_discrete_map,
    category_orders=category_orders,
    animation_frame=animation_frame,
    hover_name='시도',
    hover_data={
        '시도코드': True,
        '중학생비율': ':.2f%',
        '중학생인구': ':,',
        '전체인구': ':,',
        '비율구간': False
    },
    mapbox_style="white-bg",  # 배경 타일 없이 경계선만 표시
    center={"lat": 35.9, "lon": 127.7},
    zoom=6,
    opacity=0.85
)

# 호버 서식 및 레이아웃 설정
fig.update_layout(
    margin={"r": 0, "t": 30, "l": 0, "b": 0},
    hoverlabel=dict(
        bgcolor="#f0f4ff",            # 은은한 파란색 배경
        bordercolor="#0055ff",        # 네모 박스 테두리 파란색
        font_size=14,
        font_color="#002266",
        font_family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"
    ),
    hovermode="closest",
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

# 마우스 올렸을 때(호버) 파란색 테두리 강조 및 안내 박스 생성
fig.update_traces(
    marker_line_width=2,
    marker_line_color="#0055ff",  # 호버 강조용 파란색 라인
    hovertemplate=(
        "<b>📍 %{hovertext} (시·도코드: %{location})</b><br>"
        "------------------------------<br>"
        "<b>• 중학생 비율:</b> %{customdata[1]:.2f}%<br>"
        "<b>• 중학생 인구수:</b> %{customdata[2]:,}명<br>"
        "<b>• 전체 인구수:</b> %{customdata[3]:,}명"
        "<extra></extra>"
    )
)

# 지도 출력
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# 5. 하단 시·도별 상위 / 하위 순위 표 표시
st.subheader(f"📊 {selected_year}년 시·도별 중학생 비율 순위")

if animation_frame and '월' in df_pop.columns:
    latest_month = df_pop['월'].max()
    df_rank_base = df_pop[df_pop['월'] == latest_month].copy()
    st.caption(f"* 아래 순위표는 **{selected_year}년 {latest_month}월** 기준입니다.")
else:
    df_rank_base = df_pop.copy()

# 표 가공
df_display = df_rank_base[['시도', '시도코드', '중학생비율', '중학생인구', '전체인구']].copy()
df_display.columns = ['시·도명', '시도코드', '중학생 비율(%)', '중학생 수(명)', '전체 인구(명)']

# 비율 높은 순 정렬
top_sido = df_display.sort_values(by='중학생 비율(%)', ascending=False).reset_index(drop=True)
top_sido.index = top_sido.index + 1

# 비율 낮은 순 정렬
bottom_sido = df_display.sort_values(by='중학생 비율(%)', ascending=True).reset_index(drop=True)
bottom_sido.index = bottom_sido.index + 1

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"##### 🥇 {selected_year}년 중학생 비율 높은 시·도 순위")
    st.dataframe(top_sido, use_container_width=True)

with col2:
    st.markdown(f"##### 🔻 {selected_year}년 중학생 비율 낮은 시·도 순위")
    st.dataframe(bottom_sido, use_container_width=True)
