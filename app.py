import streamlit as st
import pandas as pd
import plotly.express as px

# ===============
# 基本設定
# ===============
st.set_page_config(
    page_title="消費者物価指数（2020年基準）",
    layout="wide",
    page_icon=":chart_with_upwards_trend:",
)

st.title("消費者物価指数（2020年基準）")
st.caption("e-Stat 公開データ（2020年6月~2025年12月における半年ごとのデータ）")

df = pd.read_csv("cpi_data.csv")

# ===============
# 前処理
# ===============
# *地域名（コード除去）
df["地域名"] = df["地域（2020年基準）"].str.strip()

# *品目名（コード除去）
df["品目名"] = df["2020年基準品目"].str.replace(r"^\d+\s+", "", regex=True).str.strip()

# *年・月の抽出（半年データ）
df["年"] = df["時間軸（年・月）"].str.extract(r"(\d{4})").astype(int)
df["月"] = df["時間軸（年・月）"].str.extract(r"(\d{1,2})月").astype(int)

df["指数"] = pd.to_numeric(df["指数"], errors="coerce")
df["前年同月比【%】"] = pd.to_numeric(df["前年同月比【%】"], errors="coerce")

# *並び順を安定させる
df = df.sort_values(["年", "月"])

# ===============
# サイドバー
# ===============
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

# ===============
# データ抽出
# ===============
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

    st.subheader("アプリの使い方")
    st.write(
        """
        本アプリでは、サイドバーの操作によって表示内容を切り替えることができます。

        **① グラフの表示内容**
        - 「指数・前年同月比」：特定の年・期（6月／12月）における物価水準と前年からの変化率を確認できます。
        - 「時間推移」：指定した期間における消費者物価指数の推移を時系列で確認できます。

        **② 抽出条件**
        - 品目：総合、食料、光熱・水道から分析対象の品目を選択します。
        - 地域：全国や東京都区部など、地域ごとの物価動向を比較できます。
        - 対象年・期／対象期間：単年比較または長期的な推移を目的に応じて指定します。

        操作内容に応じて、グラフは自動的に更新されます。
        """
    )

with tab2:
    # ----------
    # 指数・前年同月比
    # ----------
    if option == "指数・前年同月比":
        st.subheader(f"{year}年{term}の指数および前年同月比")

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
            fig_bar.update_xaxes(
                range=(-10, 140),
                dtick=10,
                showgrid=True,
                gridcolor="rgba(0,0,0,0.2)",
                gridwidth=0.5,
                zeroline=True,
                zerolinewidth=0.5,
                zerolinecolor="black",
                mirror=True,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with st.expander("グラフの見方"):
            st.write(
                """
                上のグラフでは、選択した年・期における **消費者物価指数（指数）** と
                **前年同月比（％）** を横棒グラフで表示しています。

                - **指数**は、2020年を100としたときの物価水準を表します。
                100を上回るほど、基準年より物価が上昇していることを示します。
                - **前年同月比**は、前年同月と比較した物価の変化率を示します。
                正の値は上昇、負の値は下落を意味します。

                0の位置に基準線を表示することで、物価が上昇傾向にあるか、
                あるいは下落しているかを直感的に把握できるようにしています。
                """
            )

    # ----------
    # 時間推移
    # ----------
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
            fig_line.update_xaxes(
                ticks="inside",
                tickwidth=1,
                tickcolor="rgba(0,0,0,0.2)",
                ticklen=6,
                mirror=True,
            )
            st.plotly_chart(fig_line, use_container_width=True)

            if st.checkbox("抽出後データを表示"):
                st.dataframe(
                    df_line[["地域名", "時間軸（年・月）", "品目名", "指数"]],
                    use_container_width=True,
                )

        with st.expander("グラフの見方"):
            st.write(
                """
                このグラフは、選択した期間における消費者物価指数の推移を
                半年ごと（6月・12月）に表示したものです。

                - 縦軸は消費者物価指数（2020年＝100）を表します。
                - 横軸は観測時点（年・月）を表し、時間の経過に伴う変化を確認できます。
                - 複数地域を選択した場合、それぞれの地域の物価動向を比較できます。

                折れ線の傾きが大きいほど、短期間で物価が変化していることを示します。
                """
            )
        with st.expander("簡単な解釈"):
            st.write(
                """
                本データから、全国的に消費者物価指数は
                2020年以降おおむね上昇傾向にあることが分かります。
                特に食料分野では指数・前年同月比ともに高い値を示す時期が多く、
                日常生活における物価上昇の影響が大きいと考えられます。

                一方で、光熱・水道分野では前年同月比がマイナスとなる時期も見られ、
                品目によって物価動向に違いがあることが確認できます。
                """
            )
