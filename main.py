import streamlit as st
import pandas as pd
from utils import util

st.title("病棟チーム編成アプリ")

url_readme = "https://github.com/shtakasu/team_building"
url_neben = "https://github.com/shtakasu/team_building/blob/main/data/neben.csv"
url_team = "https://github.com/shtakasu/team_building/blob/main/data/team.csv"
st.markdown("csvファイルの入力の仕方については[こちら](%s)を参照"%url_readme)
st.markdown("neben.csvのサンプルデータ：[ダウンロード](%s)"%url_neben)
st.markdown("team.csvのサンプルデータ：[ダウンロード](%s)"%url_team)

st.markdown("### neben.csvをアップロードしてください：")
uploaded_file1 = st.file_uploader("neben.csv", type="csv")
st.markdown("### team.csvをアップロードしてください：")
uploaded_file2 = st.file_uploader("team.csv", type="csv")

if (uploaded_file1 is not None) and (uploaded_file2 is not None):
    neben_df = pd.read_csv(uploaded_file1)
    team_df = pd.read_csv(uploaded_file2)
    
    #data check
    util.duplicationName_check(neben_df, team_df)
    util.capacity_check(neben_df, team_df)
    util.daycheck(neben_df)
    
    st.markdown("### 制約条件の有無を指定してください：")
    condition4 = st.radio(label="ネーベンが誰もいない日がないようにしますか？",options=("YES","NO"),horizontal=True)
    condition3 = st.radio(label="1年目だけのチームを禁止しますか？",options=("YES","NO"),horizontal=True)
    condition6 = st.radio(label="過去に所属したチームには所属しないようにしますか？",options=("YES","NO"),horizontal=True)
    this_term = st.radio(label="どのタームのチーム編成を行いますか？", options=("1st","2nd","3rd","4th"),horizontal=True)
    
    if st.button("アルゴリズムを実行する"):
        status, t2n = util.optimization(neben_df, team_df, condition3, condition4, condition6)
        
        if status == "Optimal":
            st.markdown("### :red[最適なチーム編成が見つかりました：]")
            t2n_addgrade = util.add_grade(t2n, neben_df)
            st.dataframe(pd.DataFrame.from_dict(t2n_addgrade, orient='index'),use_container_width=True)
            st.markdown("### サマリーを表示します")
            st.write("チーム配属履歴：")
            new_neben_df = util.make_new_nebenData(neben_df,t2n,this_term)
            st.dataframe(util.show_prev_team(new_neben_df),use_container_width=True)
            st.write("曜日毎の休みのメンバー：")
            dayoff_df = util.make_dayoff_data(neben_df, team_df,t2n)
            st.dataframe(dayoff_df,use_container_width=True)
            
        else:
            st.markdown("### :red[最適なチーム編成が見つかりませんでした。条件を見直してください。]")
    
            
