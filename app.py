import streamlit as st
import pandas as pd
import plotly.express as px

st.title("消費者物価指数（2020年基準）")
st.caption("e-Stat 公開データ（6月・12月の半年データ）")

df = pd.read_csv("cpi_data.csv")

# *地域名（コード除去）
df["地域名"] = df["地域（2020年基準）"].str.strip()

# *品目名（コード除去）
df["品目名"] = df["2020年基準品目"].str.replace(r"^\d+\s+", "", regex=True).str.strip()

# *年・月の抽出（半年データ）
df["年"] = df["時間軸（年・月）"].str.extract(r"(\d{4})").astype(int)
df["月"] = df["時間軸（年・月）"].str.extract(r"(\d{1,2})月").astype(int)

df["指数"] = pd.to_numeric(df["指数"], errors="coerce")
df["前年同月比【%】"] = pd.to_numeric(df["前年同月比【%】"], errors="coerce")

# 数値列を数値型に
df["指数"] = pd.to_numeric(df["指数"], errors="coerce")
df["前年同月比【%】"] = pd.to_numeric(df["前年同月比【%】"], errors="coerce")

# *並び順を安定させる
df = df.sort_values(["年", "月"])

df["時間軸コード"] = df["時間軸（年・月） コード"].astype(int)

# =========================
# サイドバー（表示モード選択）
# =========================
with st.sidebar:
    st.subheader("表示設定")

    option = st.radio(
        "グラフの表示内容を選択してください", ["指数・前年同月比", "時間推移"]
    )

    st.divider()

    st.subheader("抽出条件")

    item = st.selectbox("品目を選択してください", df["品目名"].unique())

    if option == "指数・前年同月比":
        area = st.selectbox("地域を選択してください", df["地域名"].unique())

        year = st.selectbox("対象年", sorted(df["年"].unique()))

        term = st.radio("対象期", ["6月(上期)", "12月(下期)"])

        month = 6 if term == "6月(上期)" else 12

    else:
        area = st.multiselect(
            "地域を選択してください（複数選択可）",
            df["地域名"].unique(),
            default=["全国", "東京都区部"],
        )

        year_range = st.slider(
            "対象期間（年）",
            min_value=int(df["年"].min()),
            max_value=int(df["年"].max()),
            value=(int(df["年"].min()), int(df["年"].max())),
        )

# =========================
# データ抽出
# =========================
if option == "指数・前年同月比":
    df_bar = df[
        (df["品目名"] == item)
        & (df["地域名"] == area)
        & (df["年"] == year)
        & (df["月"] == month)
    ]
else:
    df_line = df[
        (df["品目名"] == item)
        & (df["地域名"].isin(area))
        & (df["年"] >= year_range[0])
        & (df["年"] <= year_range[1])
    ]


tab1, tab2 = st.tabs(["概要", "グラフ"])

with tab1:
    st.subheader("アプリ概要")
    st.write(
        """
        本アプリは、政府統計ポータルサイト e-Stat が公開している
        **消費者物価指数（CPI：2020年基準）** を用いて、
        地域別・品目別の物価動向を可視化するものです。

        データは **6月・12月の半年ごとの観測値**であるため、
        単年比較と時系列分析で入力項目を切り替える設計としています。
        """
    )

    with st.expander("消費者物価指数（CPI）とは"):
        st.write(
            """
            消費者物価指数（CPI）は、一定の財・サービスの価格変化を基に算出される指標で、
            基準年（本データでは2020年）を100として物価水準の変化を表します。
            """
        )

with tab2:
    if option == "指数・前年同月比":
        st.subheader(f"{year}年{term}の状況")

        if df_bar.empty:
            st.warning(
                f"指定された条件（{area}、{year}年{month}月）に該当するデータが見つかりません。"
            )
        else:
            # *データ整形
            df_melted = df_bar.melt(
                id_vars=["地域名", "品目名"],
                value_vars=["指数", "前年同月比【%】"],
                var_name="指標",
                value_name="値",
            )

            fig_bar = px.bar(
                df_melted,
                x="値",
                y="指標",
                color="指標",
                orientation="h",
                text="値",
                title=f"{area} - {item}",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.subheader("消費者物価指数の推移（半年ごと）")

        if df_line.empty:
            st.warning("選択した条件に該当するデータがありません。")
        else:
            fig_line = px.line(
                df_line,
                x="時間軸（年・月）",
                y="指数",
                color="地域名",
                markers=True,
                labels={
                    "時間軸（年・月）": "期間",
                    "指数": "消費者物価指数（2020年=100）",
                    "地域名": "地域",
                },
            )
            st.plotly_chart(fig_line, use_container_width=True)

            if st.checkbox("抽出後データを表示"):
                st.dataframe(
                    df_line[["地域名", "時間軸（年・月）", "品目名", "指数"]],
                    use_container_width=True,
                )
