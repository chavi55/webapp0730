import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="전국 인구 지표 지도 대시보드",
    layout="wide"
)

st.title("🗺️ 전국 인구 지표 지도 대시보드")
st.caption("2015년~최신 연도 행정동별 인구 데이터를 바탕으로 주요 인구 지표 변화를 시각화합니다.")

# 2. 데이터 로딩 및 전처리 (캐싱)
@st.cache_data
def load_population_data():
    """인구 CSV 데이터를 불러오고 코드 보정 및 지표별 비율을 계산하는 함수"""
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/population_yearly.csv.gz"
    
    try:
        df = pd.read_csv(url, dtype={'코드': str})
    except Exception as e:
        st.error(f"데이터 로딩 중 오류 발생: {e}")
        st.stop()
        
    df['코드'] = df['코드'].str.zfill(10)
    
    # [행정구역 개편 코드 보정]
    # 10자리 코드 및 5자리/2자리 코드 변환용 사전 처리
    df['코드_보정'] = df['코드']
    
    # 1. 대구 군위군 (47720 -> 27720)
    df.loc[df['코드_보정'].str.startswith('47720'), '코드_보정'] = '27720' + df['코드_보정'].str[5:]
    
    # 2. 시·도 코드 생성 (앞 2자리)
    df['시도코드'] = df['코드_보정'].str[:2]
    
    # 3. 강원특별자치도(42 -> 51), 전북특별자치도(45 -> 52) 보정
    df['시도코드'] = df['시도코드'].replace({'42': '51', '45': '52'})
    df['시군구코드'] = df['시도코드'] + df['코드_보정'].str[2:5]
    
    # 인구 컬럼 수집
    total_cols = [c for c in df.columns if c.startswith('계_')]
    
    # 1) 중학생 (14~16세)
    middle_school_cols = ['계_14세', '계_15세', '계_16세']
    
    # 2) 유소년 (0~14세)
    child_cols = [f'계_{i}세' for i in range(15)]
    
    # 3) 고령자 (65세 이상)
    elderly_cols = []
    for c in total_cols:
        age_str = c.replace('계_', '').replace('세 이상', '').replace('세', '')
        if age_str.isdigit() and int(age_str) >= 65:
            elderly_cols.append(c)
        elif '100' in c:
            elderly_cols.append(c)

    # 그룹화 (연도, 시도, 시도코드, 월)
    group_cols = ['연도', '시도', '시도코드']
    if '월' in df.columns:
        group_cols.append('월')
        
    df_grouped = df.groupby(group_cols)[total_cols].sum().reset_index()
    
    # 인구 수 합계
    df_grouped['전체인구'] = df_grouped[total_cols].sum(axis=1)
    df_grouped['중학생인구'] = df_grouped[middle_school_cols].sum(axis=1)
    df_grouped['유소년인구'] = df_grouped[child_cols].sum(axis=1)
    df_grouped['고령인구'] = df_grouped[elderly_cols].sum(axis=1)
    
    # 비율 계산 (%)
    safe_total = df_grouped['전체인구'].replace(0, pd.NA)
    df_grouped['중학생 비율'] = (df_grouped['중학생인구'] / safe_total * 100).fillna(0).round(2)
    df_grouped['유소년 비율'] = (df_grouped['유소년인구'] / safe_total * 100).fillna(0).round(2)
    df_grouped['고령화율'] = (df_grouped['고령인구'] / safe_total * 100).fillna(0).round(2)
    
    return df_grouped

@st.cache_data
def load_sido_geojson():
    """시·도 GeoJSON 경계 데이터 로드"""
    url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo.json"
    res = requests.get(url)
    return res.json()

# 데이터 로딩 실행
with st.spinner("데이터 및 경계 정보를 로딩하는 중입니다..."):
    df_all = load_population_data()
    geojson_data = load_sido_geojson()

# GeoJSON에 존재하는 시도코드 리스트 추출 (미매칭 확인용)
geojson_codes = {feat['properties']['code'] for feat in geojson_data['features']}

# 3. 사이드바 컨트롤러 (지표 선택, 연도 슬라이더, 시도 선택)
st.sidebar.header("⚙️ 지도 및 지표 설정")

# 지표 선택
indicator_option = st.sidebar.selectbox(
    "📊 분석할 지표를 선택하세요",
    ["중학생 비율 (14~16세)", "유소년 비율 (0~14세)", "고령화율 (65세 이상)"]
)

# 연도 슬라이더
min_year = int(df_all['연도'].min())
max_year = int(df_all['연도'].max())
selected_year = st.sidebar.slider(
    "📅 연도 선택",
    min_value=min_year,
    max_value=max_year,
    value=max_year,
    step=1
)

# 시·도 필터 드롭다운
sido_list = ["전국"] + sorted(df_all['시도'].unique().tolist())
selected_sido = st.sidebar.selectbox("📍 지역(시·도) 선택", sido_list)

# 4. 선택 지표별 구간값 및 색상 정의
if indicator_option == "중학생 비율 (14~16세)":
    val_col = '중학생 비율'
    pop_col = '중학생인구'
    # 요구사항: 19% · 23% · 28% · 38% 고정 구간
    bins = [-1, 19, 23, 28, 38, 100]
    labels = ['19% 미만', '19% 이상 ~ 23% 미만', '23% 이상 ~ 28% 미만', '28% 이상 ~ 38% 미만', '38% 이상']

elif indicator_option == "유소년 비율 (0~14세)":
    val_col = '유소년 비율'
    pop_col = '유소년인구'
    # 유소년 비율 분포 맞춤 구간
    bins = [-1, 8, 10, 12, 14, 100]
    labels = ['8% 미만', '8% 이상 ~ 10% 미만', '10% 이상 ~ 12% 미만', '12% 이상 ~ 14% 미만', '14% 이상']

else:  # 고령화율 (65세 이상)
    val_col = '고령화율'
    pop_col = '고령인구'
    # 고령화율 분포 맞춤 구간
    bins = [-1, 14, 20, 25, 30, 100]
    labels = ['14% 미만(초기)', '14% 이상 ~ 20% 미만', '20% 이상 ~ 25% 미만', '25% 이상 ~ 30% 미만', '30% 이상']

color_discrete_map = {
    labels[0]: '#f7fbff',
    labels[1]: '#c6dbef',
    labels[2]: '#6baed6',
    labels[3]: '#2171b5',
    labels[4]: '#08519c'
}

# 선택된 연도의 데이터 필터링 및 구간 범주 적용
df_year = df_all[df_all['연도'] == selected_year].copy()
df_year['비율구간'] = pd.cut(df_year[val_col], bins=bins, labels=labels)

# 애니메이션을 위한 최근 월 기준 데이터 추출
animation_frame = '월' if '월' in df_year.columns else None
if animation_frame:
    latest_month = df_year['월'].max()
    df_current = df_year[df_year['월'] == latest_month].copy()
else:
    df_current = df_year.copy()

# 5. 지도 위에 표시할 요약 지표 카드 (st.metric 3종)
st.subheader(f"📌 {selected_year}년 {indicator_option} 요약 지표")

nat_total = df_current['전체인구'].sum()
nat_target = df_current[pop_col].sum()
nat_ratio = round((nat_target / nat_total) * 100, 2) if nat_total > 0 else 0

top_row = df_current.sort_values(by=val_col, ascending=False).iloc[0]
bottom_row = df_current.sort_values(by=val_col, ascending=True).iloc[0]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("전국 평균 비율", f"{nat_ratio}%", f"{selected_year}년 기준")
with col2:
    st.metric("가장 높은 시·도", f"{top_row['시도']} ({top_row[val_col]}%)", f"대상 인구: {top_row[pop_col]:,}명")
with col3:
    st.metric("가장 낮은 시·도", f"{bottom_row['시도']} ({bottom_row[val_col]}%)", f"대상 인구: {bottom_row[pop_col]:,}명")

st.markdown("---")

# 6. 시도 선택에 따른 지도 중심점 및 줌 레벨 조정
center_dict = {
    "전국": {"lat": 35.9, "lon": 127.7, "zoom": 6},
    "서울특별시": {"lat": 37.5665, "lon": 126.9780, "zoom": 9.5},
    "부산광역시": {"lat": 35.1796, "lon": 129.0756, "zoom": 9.5},
    "대구광역시": {"lat": 35.8714, "lon": 128.6014, "zoom": 9.5},
    "인천광역시": {"lat": 37.4563, "lon": 126.7052, "zoom": 9.0},
    "광주광역시": {"lat": 35.1595, "lon": 126.8526, "zoom": 10},
    "대전광역시": {"lat": 36.3504, "lon": 127.3845, "zoom": 10},
    "울산광역시": {"lat": 35.5384, "lon": 129.3114, "zoom": 9.5},
    "세종특별자치시": {"lat": 36.4800, "lon": 127.2890, "zoom": 10},
    "경기도": {"lat": 37.4138, "lon": 127.5183, "zoom": 8.0},
    "강원특별자치도": {"lat": 37.8228, "lon": 128.1555, "zoom": 7.5},
    "충청북도": {"lat": 36.6357, "lon": 127.4912, "zoom": 8.0},
    "충청남도": {"lat": 36.5184, "lon": 126.8000, "zoom": 8.0},
    "전북특별자치도": {"lat": 35.7175, "lon": 127.1530, "zoom": 8.0},
    "전라남도": {"lat": 34.8161, "lon": 126.4629, "zoom": 8.0},
    "경상북도": {"lat": 36.5760, "lon": 128.5056, "zoom": 7.5},
    "경상남도": {"lat": 35.2383, "lon": 128.6924, "zoom": 8.0},
    "제주특별자치도": {"lat": 33.4890, "lon": 126.4983, "zoom": 9.0}
}

view = center_dict.get(selected_sido, center_dict["전국"])

# 7. 지도 시각화
fig = px.choropleth_mapbox(
    df_year,
    geojson=geojson_data,
    locations='시도코드',
    featureidkey='properties.code',
    color='비율구간',
    color_discrete_map=color_discrete_map,
    category_orders={'비율구간': labels},
    animation_frame=animation_frame,
    hover_name='시도',
    hover_data={
        '시도코드': True,
        val_col: ':.2f%',
        pop_col: ':,',
        '전체인구': ':,',
        '비율구간': False
    },
    mapbox_style="white-bg",
    center={"lat": view["lat"], "lon": view["lon"]},
    zoom=view["zoom"],
    opacity=0.85
)

fig.update_layout(
    margin={"r": 0, "t": 30, "l": 0, "b": 0},
    hoverlabel=dict(
        bgcolor="#f0f4ff",
        bordercolor="#0055ff",
        font_size=14,
        font_color="#002266",
        font_family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"
    ),
    hovermode="closest",
    legend_title_text=f'{indicator_option} 구간',
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

fig.update_traces(
    marker_line_width=1.2,
    marker_line_color="#444444",
    hovertemplate=(
        "<b>📍 %{hovertext} (코드: %{location})</b><br>"
        "------------------------------<br>"
        f"<b>• {indicator_option}:</b> %{{customdata[1]:.2f}}%<br>"
        f"<b>• 해당 인구수:</b> %{{customdata[2]:,}}명<br>"
        "<b>• 전체 인구수:</b> %{customdata[3]:,}명"
        "<extra></extra>"
    )
)

st.plotly_chart(fig, use_container_width=True)

# 경계 미매칭 지역 안내 문구 출력
unmatched = set(df_year['시도코드'].unique()) - geojson_codes
if unmatched:
    st.caption("ℹ️ **안내:** 행정구역 개편으로 경계 파일과 일치하지 않는 일부 매칭 불가 지역은 회색으로 표시됩니다.")

st.markdown("---")

# 8. 하단 비율 순위 표 (상위 / 하위)
st.subheader(f"📊 {selected_year}년 시·도별 {indicator_option} 순위")

df_rank = df_current[['시도', '시도코드', val_col, pop_col, '전체인구']].copy()
df_rank.columns = ['시·도명', '시도코드', f'{val_col}(%)', '해당 인구(명)', '전체 인구(명)']

top_df = df_rank.sort_values(by=f'{val_col}(%)', ascending=False).reset_index(drop=True)
top_df.index = top_df.index + 1

bottom_df = df_rank.sort_values(by=f'{val_col}(%)', ascending=True).reset_index(drop=True)
bottom_df.index = bottom_df.index + 1

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"##### 🥇 {indicator_option} 높은 순위")
    st.dataframe(top_df, use_container_width=True)

with col_b:
    st.markdown(f"##### 🔻 {indicator_option} 낮은 순위")
    st.dataframe(bottom_df, use_container_width=True)
