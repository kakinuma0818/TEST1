# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime
import itertools

# ---------------------------
# Config / Design
# ---------------------------
PRIMARY_COLOR = "#FF7F50"  # エルメスオレンジ
st.set_page_config(page_title="Keiba UI", layout="wide", initial_sidebar_state="expanded")

st.markdown(f"""
<style>
/* フォント */
html, body, [class*="css"] {{ font-family: Helvetica, Arial, sans-serif; }}
/* 差し色 */
.orange {{ color: {PRIMARY_COLOR}; font-weight: 600; }}
/* ボタン色 */
.stButton>button {{ background-color: {PRIMARY_COLOR}; color: white; border: none; }}
/* データフレーム最大幅 */
div[data-testid="stDataFrameContainer"] {{ max-width: 100%; }}
/* タブ上部固定（擬似） */
section[data-testid="stHorizontalBlock"] {{ position: sticky; top: 0; z-index: 999; background: white; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utility (sample; replace with scraping logic for real data)
# ---------------------------
def sample_race_df():
    data = {
        "枠": [1,2,3,4,5,6],
        "馬番": [1,2,3,4,5,6],
        "馬名": ["アドマイヤテラ","カランダガン","サンプルA","サンプルB","サンプルC","サンプルD"],
        "性齢": ["牡4","セ4","牝3","牡5","牡6","牝4"],
        "斤量": [57,57,54,56,57,55],
        "体重": [500,502,470,480,488,472],
        "距離": [1800,2000,1600,1800,2000,1400],
        "脚質": ["差し","先行","追込","逃げ","先行","差し"],
        "騎手": ["川田","M.バルザローナ","武豊","福永","横山","池添"],
        "調教師": ["(栗東)藤沢","(美浦)高木","(栗東)池江","(美浦)友道","(栗東)田中","(美浦)佐藤"],
        "オッズ": [3.2,5.1,12.5,7.8,20.0,15.0],
        "人気": [1,2,4,3,6,5],
        "スコア": [85,78,70,72,65,68],
        "血統": ["サンデー系","キングマンボ系","ミスプロ系","サンデー系","ノーザン系","ミスプロ系"],
        "馬主": ["A","B","C","D","E","F"],
        "生産者": ["X牧場","Y牧場","Z牧場","W牧場","V牧場","U牧場"],
        "成績": ["1-2-1-2","0-1-1-3","2-0-1-2","1-1-0-3","0-0-1-4","1-1-2-1"],
        "馬場": ["良","稍重","重","良","良","稍重"],
        "枠適性":[3,2,1,3,2,2],
        "馬場適性":[3,2,2,1,1,2],
    }
    return pd.DataFrame(data)

def calculate_all_scores(df):
    # placeholder: in production, implement full scoring here
    df = df.copy()
    # Ensure base numeric column present
    df["スコア"] = df.get("スコア", 0).astype(float)
    return df

def auto_allocate(amount, combos):
    n = max(1, len(combos))
    base = amount // n
    return {combo: base for combo in combos}

# ---------------------------
# Session initialization
# ---------------------------
if 'marks' not in st.session_state:
    st.session_state.marks = {}
if 'manual_scores' not in st.session_state:
    st.session_state.manual_scores = {}
if 'race_meta' not in st.session_state:
    st.session_state.race_meta = {}

# ---------------------------
# Sidebar (top selection area)
# ---------------------------
with st.sidebar:
    st.header("レース選択")
    race_date = st.date_input("日付", date.today(), key="race_date")
    race_course = st.selectbox("競馬場", ["札幌","函館","福島","新潟","東京","中山","中京","京都","阪神","小倉"], key="race_course")
    race_number = st.selectbox("レース番号", list(range(1,13)), key="race_number")
    race_id_input = st.text_input("race_id (任意)", value="", help="netkeiba race_id を直接入れる場合")
    if st.button("更新 🔄"):
        st.session_state.race_meta = {
            "date": race_date.strftime("%Y%m%d"),
            "course": race_course,
            "number": race_number,
            "race_id": race_id_input
        }
        st.experimental_rerun()

# ---------------------------
# Race overview (under selection)
# ---------------------------
col1, col2, col3 = st.columns([2,5,2])
with col1:
    st.markdown(f"**{race_course} {race_number}R**")
with col2:
    race_name = st.text_input("レース名", value=st.session_state.race_meta.get("race_name",""))
    race_grade = st.selectbox("グレード", ["","G1","G2","G3","OP","条件"], key="race_grade")
    race_time = st.text_input("発走時刻", value=st.session_state.race_meta.get("race_time",""))
with col3:
    show_topbold_toggle = st.checkbox("上位（スコア上位6頭）を太字表示", value=True)

# ---------------------------
# Data load (sample for now; replace with scraping)
# ---------------------------
df = sample_race_df()
df = calculate_all_scores(df)

# initialize session keys
for name in df['馬名']:
    if name not in st.session_state.marks:
        st.session_state.marks[name] = ""
    if name not in st.session_state.manual_scores:
        st.session_state.manual_scores[name] = 0

# ---------------------------
# Tabs
# ---------------------------
tabs = st.tabs(["出馬表","スコア","馬券","基本情報","成績"])
tab_ma, tab_sc, tab_be, tab_pr, tab_gr = tabs

# ---------------------------
# 出馬表 (MA) — order adjusted: オッズ then 人気
# ---------------------------
with tab_ma:
    st.subheader("出馬表")
    sort_col = st.selectbox("並び替え", ["スコア順","オッズ順","人気順","馬番順"])
    if sort_col == "スコア順":
        df_display = df.sort_values(by="スコア", ascending=False).reset_index(drop=True)
    elif sort_col == "オッズ順":
        df_display = df.sort_values(by="オッズ", ascending=True).reset_index(drop=True)
    elif sort_col == "人気順":
        df_display = df.sort_values(by="人気", ascending=True).reset_index(drop=True)
    else:
        df_display = df.sort_values(by="馬番", ascending=True).reset_index(drop=True)

    st.write("印（◎ ○ ▲ △ ⭐︎ ×）を選択：")
    for i, row in df_display.iterrows():
        name = row['馬名']
        st.session_state.marks[name] = st.selectbox(
            f"{row['馬番']}. {name} の印",
            options=["", "◎","○","▲","△","⭐︎","×"],
            index=(["", "◎","○","▲","△","⭐︎","×"].index(st.session_state.marks.get(name,"")) if st.session_state.marks.get(name,"") in ["", "◎","○","▲","△","⭐︎","×"] else 0),
            key=f"mark_ma_{name}"
        )

    df_display_show = df_display.copy()
    df_display_show['印'] = df_display_show['馬名'].map(lambda x: st.session_state.marks.get(x,""))
    df_display_show['手動'] = df_display_show['馬名'].map(lambda x: st.session_state.manual_scores.get(x,0))
    df_display_show['合計'] = df_display_show['スコア'] + df_display_show['手動']

    # rename and order columns exactly as requested:
    display_cols = ["馬番","馬名","性齢","斤量","体重","距離","脚質","騎手","調教師","オッズ","人気","合計","スコア","印"]
    # ensure cols exist
    for c in display_cols:
        if c not in df_display_show.columns:
            df_display_show[c] = ""
    # show df
    st.dataframe(df_display_show[display_cols].rename(columns={"合計":"スコア","スコア":"ベーススコア"}), use_container_width=True)

# ---------------------------
# スコア (SC)
# ---------------------------
with tab_sc:
    st.subheader("スコア詳細")
    df_sc = df.copy()
    st.write("手動スコア（-3〜+3）を入力：")
    for i, row in df_sc.iterrows():
        name = row['馬名']
        ms = st.selectbox(f"{name} の手動スコア", options=[-3,-2,-1,0,1,2,3], index=[-3,-2,-1,0,1,2,3].index(st.session_state.manual_scores.get(name,0)), key=f"manual_{name}")
        st.session_state.manual_scores[name] = ms

    df_sc['手動'] = df_sc['馬名'].map(lambda x: st.session_state.manual_scores.get(x,0))
    df_sc['合計'] = df_sc['スコア'] + df_sc['手動']

    display_cols = ["馬名","合計","スコア","性齢","年齢","血統","騎手","馬主","生産者","調教師","成績","競馬場","距離","脚質","枠","馬場","手動"]
    for c in display_cols:
        if c not in df_sc.columns:
            df_sc[c] = ""
    # sort by 合計 desc
    df_sc = df_sc.sort_values("合計", ascending=False).reset_index(drop=True)

    # highlight top3 visually by color in separate column (streamlit dataframe styling is limited)
    st.dataframe(df_sc[display_cols], use_container_width=True)

# ---------------------------
# 馬券 (BE)
# ---------------------------
with tab_be:
    st.subheader("馬券購入")
    bet_type = st.selectbox("馬券種", ["単勝","複勝","ワイド","馬連","馬単","3連複","3連単"])
    horse_names = df['馬名'].tolist()
    selected = st.multiselect("選択馬（表示から選択）", horse_names)
    total_budget = st.number_input("総投資額 (円)", min_value=100, step=100, value=1000)
    auto_alloc = st.checkbox("自動分配（均等）", value=True)

    combos = []
    if bet_type in ["3連複","3連単"]:
        pool = selected if len(selected) >= 3 else df.sort_values('スコア', ascending=False)['馬名'].tolist()[:6]
        combos = list(itertools.permutations(pool, 3)) if bet_type=="3連単" else list(itertools.combinations(pool, 3))
    elif bet_type in ["馬連","馬単","ワイド"]:
        pool = selected if len(selected) >= 2 else df.sort_values('スコア', ascending=False)['馬名'].tolist()[:6]
        combos = list(itertools.permutations(pool, 2))
    else:
        pool = selected if selected else df.sort_values('スコア', ascending=False)['馬名'].tolist()[:6]
        combos = [(h,) for h in pool]

    if auto_alloc:
        allocation = auto_allocate(total_budget, combos)
    else:
        allocation = {c: 0 for c in combos}

    st.write(f"候補数: {len(combos)} (表示上限 50 件)")
    for i, combo in enumerate(list(combos)[:50]):
        combo_str = " - ".join(combo)
        alloc = allocation.get(combo, 0)
        cols = st.columns([4,2,2])
        cols[0].write(combo_str)
        cols[1].write(f"想定投資: {alloc} 円")
        allocation[combo] = cols[2].number_input(f"投資額 ({i})", min_value=0, step=50, value=int(alloc), key=f"alloc_{i}")

    total_spent = sum(allocation.values())
    st.write(f"合計投資額: {total_spent} 円 / 設定総額: {total_budget} 円")
    if st.button("仮購入（シミュレーション）"):
        st.success("購入シミュレーションを実行しました（実購入は未接続）")

# ---------------------------
# 基本情報 (PR)
# ---------------------------
with tab_pr:
    st.subheader("基本情報")
    df_pr = df[["馬名","性齢","騎手","馬主","生産者","調教師","血統","体重"]].copy()
    df_pr.rename(columns={"体重":"前走体重"}, inplace=True)
    st.dataframe(df_pr, use_container_width=True)

# ---------------------------
# 成績 (GR)
# ---------------------------
with tab_gr:
    st.subheader("成績（直近5戦）")
    df_gr = pd.DataFrame({
        "馬名": df['馬名'],
        "直近5戦（着順）": df['成績']
    })
    st.dataframe(df_gr, use_container_width=True)

# Footer note
st.markdown("---")
st.caption("UIスケルトン（最終調整版）。スクレイピング・精密スコアリング・実オッズ接続はこの基盤へ統合します。")
