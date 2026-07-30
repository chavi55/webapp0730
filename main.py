import re
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(page_title="전국 인구 지표 지도 및 동네별 분석", layout="wide")
st.title("🗺️ 전국 인구 지표 지도 및 동네별 분석")
st.caption("시군구별 지도 및 읍·면·동 단위 인구 비율 분석 (행정안전부 주민등록 인구)")

POP_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/population_yearly.csv.gz"
GEO_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/boundaries/sigungu_kr.geojson"

# 2. 데이터 로딩 (캐싱)
@st.cache_data(show_spinner="인구 데이터를 불러오는 중입니다...")
def load_population():
    df = pd.read_csv(POP_URL, dtype={"코드": str})
    df["코드"] = df["코드"].str.zfill(10)
    
    # [행정구역 개편 코드 보정]
    df["코드_보정"] = df["코드"]
    # 대구 군위군 (47720 -> 27720)
    df.loc[df["코드_보정"].str.startswith("47720"), "코드_보정"] = "27720" + df["코드_보정"].str[5:]
    
    # 시도코드(앞 2자리) 생성 및 강원(42->51), 전북(45->52) 보정
    sido_code = df["코드_보정"].str[:2].replace({"42": "51", "45": "52"})
    # 최종 시군구코드(5자리)
    df["시군구코드"] = sido_code + df["코드_보정"].str[2:5]
    
    return df

@st.cache_data(show_spinner="지도 경계를 불러오는 중입니다...")
def load_geojson():
    return requests.get(GEO_URL, timeout=30).json()

df_raw = load_population()
geojson = load_geojson()

# 경계 파일 내 지자체 이름 및 시도 정보 추출
geo_names = pd.DataFrame([
    {
        "시군구코드": str(f["properties"]["코드"]),
        "시군구": f["properties"]["시군구"],
        "시도": f["properties"]["시도"],
    }
    for f in geojson["features"]
])
geo_codes = set(geo_names["시군구코드"].unique())

# 연령대 컬럼 분류
total_cols = [c for c in df_raw.columns if c.startswith("계_")]

def age_of(col):
    m = re.match(r"계_(\d+)세", col)
    return int(m.group(1)) if m else None

elderly_cols = [c for c in total_cols if age_of(c) is not None and age_of(c) >= 65]
child_cols = [c for c in total_cols if age_of(c) is not None and age_of(c) <= 14]
youth_cols = [c for c in total_cols if age_of(c) is not None and 9 <= age_of(c) <= 24]  # 청소년 (9~24세)

# 인구 합계 계산
df_raw["전체인구"] = df_raw[total_cols].sum(axis=1)
df_raw["고령인구"] = df_raw[elderly_cols].sum(axis=1)
df_raw["유소년인구"] = df_raw[child_cols].sum(axis=1)
df_raw["청소년인구"] = df_raw[youth_cols].sum(axis=1)

# 3. 사이드바 컨트롤러
st.sidebar.header("⚙️ 지도 및 지표 설정")

# 지표 선택
indicator = st.sidebar.selectbox(
    "📊 분석할 지표를 선택하세요",
    ["청소년 비율 (9~24세)", "유소년 비율 (0~14세)", "고령화율 (65세 이상 비율)"]
)

# 연도 선택 슬라이더
min_year = int(df_raw["연도"].min())
max_year = int(df_raw["연도"].max())
selected_year = st.sidebar.slider("📅 연도 선택", min_value=min_year, max_value=max_year, value=max_year, step=1)

# 시도 선택
sido_options = ["전국"] + sorted(geo_names["시도"].unique().tolist())
selected_sido = st.sidebar.selectbox("📍 지역(시·도) 선택", sido_options)

# 4. 선택 연도 데이터 필터링 및 시군구 그룹화
df_year = df_raw[df_raw["연도"] == selected_year].copy()
grouped = df_year.groupby("시군구코드")[["전체인구", "고령인구", "유소년인구", "청소년인구"]].sum().reset_index()

grouped["고령화율"] = (grouped["고령인구"] / grouped["전체인구"] * 100).round(2)
grouped["유소년비율"] = (grouped["유소년인구"] / grouped["전체인구"] * 100).round(2)
grouped["청소년비율"] = (grouped["청소년인구"] / grouped["전체인구"] * 100).round(2)

# GeoJSON 정보와 통합
merged = grouped.merge(geo_names, on="시군구코드", how="left")

# 5. 지표별 설정 및 구간(BINS) 지정
if indicator == "청소년 비율 (9~24세)":
    val_col = "청소년비율"
    target_pop_col = "청소년인구"
    bins = [0, 12, 15, 18, 21, 100]
    labels = ["12% 미만", "12~15%", "15~18%", "18~21%", "21% 이상"]
    colors = {
        "12% 미만": "#e8f5e9",
        "12~15%": "#a5d6a7",
        "15~18%": "#66bb6a",
        "18~21%": "#388e3c",
        "21% 이상": "#1b5e20",
    }
elif indicator == "유소년 비율 (0~14세)":
    val_col = "유소년비율"
    target_pop_col = "유소년인구"
    bins = [0, 10, 13, 16, 19, 100]
    labels = ["10% 미만", "10~13%", "13~16%", "16~19%", "19% 이상"]
    colors = {
        "10% 미만": "#f7fbff",
        "10~13%": "#c6dbef",
        "13~16%": "#6baed6",
        "16~19%": "#2171b5",
        "19% 이상": "#08519c",
    }
else:  # 고령화율
    val_col = "고령화율"
    target_pop_col = "고령인구"
    bins = [0, 19, 23, 28, 38, 100]
    labels = ["19% 미만", "19~23%", "23~28%", "28~38%", "38% 이상"]
    colors = {
        "19% 미만": "#fee6ce",
        "19~23%": "#fdc086",
        "23~28%": "#f79646",
        "28~38%": "#e8590c",
        "38% 이상": "#a63603",
    }

merged["단계"] = pd.cut(merged[val_col], bins=bins, labels=labels, right=False)

# 6. 상단 카드 지표
st.subheader(f"📌 {selected_year}년 {indicator} 요약 지표")

nat_total = merged["전체인구"].sum()
nat_target = merged[target_pop_col].sum()
nat_ratio = round((nat_target / nat_total) * 100, 2) if nat_total > 0 else 0

valid_merged = merged.dropna(subset=["시군구"])
top_region = valid_merged.nlargest(1, val_col).iloc[0]
bottom_region = valid_merged.nsmallest(1, val_col).iloc[0]

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("전국 평균 비율", f"{nat_ratio}%", f"{selected_year}년 기준")
with c2:
    st.metric("가장 높은 시군구", f"{top_region['시도']} {top_region['시군구']} ({top_region[val_col]}%)", f"인구: {int(top_region[target_pop_col]):,}명")
with c3:
    st.metric("가장 낮은 시군구", f"{bottom_region['시도']} {bottom_region['시군구']} ({bottom_region[val_col]}%)", f"인구: {int(bottom_region[target_pop_col]):,}명")

st.markdown("---")

# 7. 지도 시각화
if selected_sido != "전국":
    plot_df = merged[merged["시도"] == selected_sido].copy()
else:
    plot_df = merged.copy()

fig = px.choropleth(
    plot_df,
    geojson=geojson,
    locations="시군구코드",
    featureidkey="properties.코드",
    color="단계",
    category_orders={"단계": labels},
    color_discrete_map=colors,
    hover_name="시군구",
    hover_data={val_col: ":.2f%", "시도": True, "전체인구": ":,", "시군구코드": False, "단계": False},
    labels={val_col: f"{indicator}(%)", "전체인구": "전체 인구"},
)

fig.update_geos(fitbounds="locations", visible=False)
fig.update_traces(marker_line_width=1.0, marker_line_color="#444444")
fig.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    height=600,
    legend_title_text=f"{indicator} ({selected_year}년)",
    legend=dict(yanchor="top", y=0.98, xanchor="right", x=0.98, bgcolor="rgba(255, 255, 255, 0.9)", bordercolor="#cccccc", borderwidth=1)
)

st.plotly_chart(fig, use_container_width=True)

unmatched_count = len(set(grouped["시군구코드"]) - geo_codes)
if unmatched_count > 0:
    st.caption("ℹ️ **안내:** 행정구역 개편으로 경계 파일과 코드가 안 맞는 일부 지역은 회색으로 표시됩니다.")

st.markdown("---")

# 8. 🏙️ 동네(읍·면·동)별 비율 막대그래프 섹션
st.subheader(f"🏘️ 시군구 내 동네(읍·면·동)별 {indicator} 비교")

# 시도 필터링된 시군구 목록
available_sigungus = valid_merged[valid_merged["시도"] == selected_sido]["시군구"].unique() if selected_sido != "전국" else valid_merged["시군구"].unique()
available_sigungus = sorted(list(set(available_sigungus)))

selected_sigungu = st.selectbox("📍 상세 분석할 시·군·구를 선택하세요", available_sigungus)

# 선택한 시군구의 행정동 데이터 추출
sigungu_code_target = valid_merged[valid_merged["시군구"] == selected_sigungu]["시군구코드"].iloc[0]
df_dong = df_year[df_year["시군구코드"] == sigungu_code_target].copy()

# [수정된 핵심 부분] 실제 존재하는 행정동 컬럼을 찾아서 지정
possible_dong_cols = ["읍면동명", "행정동명", "읍면동", "행정동", "구분", "동명", "지역"]
dong_col = None

for col in possible_dong_cols:
    if col in df_dong.columns:
        dong_col = col
        break

# 만약 위 이름들 중에 없으면, 숫자 인구 컬럼이나 코드가 아닌 첫 번째 문자열 컬럼을 찾습니다.
if dong_col is None:
    text_cols = [c for c in df_dong.select_dtypes(include=['object', 'string']).columns if c not in ['코드', '코드_보정', '시군구코드', '시도', '연도']]
    dong_col = text_cols[0] if text_cols else "코드"

# 읍면동별 비율 재계산
dong_grouped = df_dong.groupby(dong_col)[["전체인구", "고령인구", "유소년인구", "청소년인구"]].sum().reset_index()
dong_grouped["고령화율"] = (dong_grouped["고령인구"] / dong_grouped["전체인구"] * 100).round(2)
dong_grouped["유소년비율"] = (dong_grouped["유소년인구"] / dong_grouped["전체인구"] * 100).round(2)
dong_grouped["청소년비율"] = (dong_grouped["청소년인구"] / dong_grouped["전체인구"] * 100).round(2)

dong_grouped = dong_grouped.sort_values(by=val_col, ascending=False).reset_index(drop=True)

# 시군구 평균값
sigungu_avg = (df_dong[target_pop_col].sum() / df_dong["전체인구"].sum() * 100) if df_dong["전체인구"].sum() > 0 else 0

# 막대그래프 시각화
fig_bar = px.bar(
    dong_grouped,
    x=dong_col,
    y=val_col,
    text=val_col,
    title=f"<b>{selected_sigungu} 동네별 {indicator} (평균: {sigungu_avg:.2f}%)</b>",
    labels={dong_col: "동네 (읍·면·동)", val_col: f"{indicator} (%)"},
    color=val_col,
    color_continuous_scale="Viridis" if indicator.startswith("청소년") else "Blues"
)

fig_bar.add_hline(
    y=sigungu_avg,
    line_dash="dash",
    line_color="red",
    annotation_text=f"시군구 평균 ({sigungu_avg:.2f}%)",
    annotation_position="top right"
)

fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
fig_bar.update_layout(height=450, xaxis_tickangle=-45, yaxis=dict(range=[0, max(dong_grouped[val_col].max() * 1.15, 10)]))

st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# 9. 지도 아래 순위 표
c_left, c_right = st.columns(2)
display_cols = ["시도", "시군구", val_col, "전체인구"]

with c_left:
    st.subheader(f"🔴 {indicator} 높은 곳 10")
    st.dataframe(valid_merged.nlargest(10, val_col)[display_cols].reset_index(drop=True), use_container_width=True)

with c_right:
    st.subheader(f"🟢 {indicator} 낮은 곳 10")
    st.dataframe(valid_merged.nsmallest(10, val_col)[display_cols].reset_index(drop=True), use_container_width=True)
