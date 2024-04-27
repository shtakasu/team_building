import streamlit as st
import pandas as pd
import pulp 

def optimization(neben_df, team_df, condition3, condition4, condition6):

    #define problem
    problem = pulp.LpProblem("assign", pulp.LpMaximize)

    #define variables
    neben = neben_df["name"].to_list()
    team = team_df["team"].to_list()
    nt = [(n,t) for n in neben for t in team]
    x = pulp.LpVariable.dicts("x", nt, cat="Binary")

    #Contidion 1: Each neben must be assigned to exactly one team
    for n in neben:
        problem += pulp.lpSum([x[n,t] for t in team]) == 1

    #Condition 2: Each team must be within capacity defined by "team.csv"
    for t in team:
        problem += pulp.lpSum([x[n,t] for n in neben]) <= team_df[team_df["team"]==t]["max_capacity"].iloc[0]
        problem += pulp.lpSum([x[n,t] for n in neben]) >= team_df[team_df["team"]==t]["min_capacity"].iloc[0]

    #Condition 3: A team with only freshmen is prohibited
    if condition3 == "YES":
        senior = [row.name for row in neben_df.itertuples() if row.grade>=2]
        for t in team:
            problem += pulp.lpSum([x[n,t] for n in senior]) >= 1 

    #Condition 4: A day with no nebens is prohibited
    if condition4 == "YES":
        days = ["Mon","Tue","Wed","Thu","Fri","Sat"]
        day2neben = {} #dict {day:[neben list]}
        for day in days:
            day2neben[day] = neben_df[neben_df["dayoff1"]==day]["name"].to_list() + neben_df[neben_df["dayoff2"]==day]["name"].to_list()
        for t in team:
            for day in days:
                problem += pulp.lpSum([x[n,t] for n in neben]) >= 1+pulp.lpSum([x[n,t] for n in day2neben[day]]) # (members >= 1+dayoff_members)

    #Condition 5: already fixed team
    neben_fixed_df = neben_df[neben_df["fixed"].notna()]
    for n in neben:
        if n in neben_fixed_df["name"].to_list():
            fixed_team = neben_fixed_df[neben_fixed_df["name"]==n]["fixed"].iloc[0]
            problem += x[n,fixed_team] == 1
            
    #Condition 6: A neben must not be assigned to previous teams
    if condition6 == "YES":
        neben2preteam = {}
        for n in neben:
            neben2preteam[n] = [neben_df[neben_df["name"]==n]["term1team"].iloc[0],neben_df[neben_df["name"]==n]["term2team"].iloc[0],neben_df[neben_df["name"]==n]["term3team"].iloc[0]]
        for n in neben:
            #if fixed team defined in Condition 5 is one of the previous teams, remove it from previous team list
            if n in neben_fixed_df["name"].to_list():
                fixed_team = neben_fixed_df[neben_fixed_df["name"]==n]["fixed"].iloc[0]
                if fixed_team in neben2preteam[n]:
                    neben2preteam[n].remove(fixed_team)
            for t in team:
                if t in neben2preteam[n]:
                    problem += x[n,t] == 0
    
    #Condition 7: Given nebens must be assigned to the liaison teams or the ward teams
    liaison_neben = neben_df[neben_df["liaisonORward"]=="L"]["name"].to_list()
    liaison_team = team_df[team_df["liaisonORward"]=="L"]["team"].to_list()
    ward_neben = neben_df[neben_df["liaisonORward"]=="W"]["name"].to_list()
    ward_team = team_df[team_df["liaisonORward"]=="W"]["team"].to_list()
    for n in liaison_neben:
        problem += pulp.lpSum([x[n,t] for t in liaison_team]) == 1
    for n in ward_neben:
        problem += pulp.lpSum([x[n,t] for t in ward_team]) == 1
        
    #solve
    status = problem.solve()
    if pulp.LpStatus[status] == "Optimal":
        #show result
        t2n = {} #dict{team:[neben list]}　
        for t in team:
            t2n[t] = [n for n in neben if x[n,t].value()==1]

        return pulp.LpStatus[status], t2n
    
    else:
        return pulp.LpStatus[status], None
    
def duplicationName_check(neben_df, team_df):
    team_name = team_df["team"].to_list()
    neben_name = neben_df["name"].to_list()
    dupl_team_bool = (len(team_name) != len(set(team_name)))
    dupl_neben_bool = (len(neben_name) != len(set(neben_name)))
    if dupl_team_bool:
        raise ValueError("チーム名にダブりがあります")
    if dupl_neben_bool:
        raise ValueError("ネーベン名にダブりがあります")
    return 0

def capacity_check(neben_df, team_df):
    neben_number = len(neben_df["name"])
    team_number = len(team_df["team"])
    max_capacity = team_df["max_capacity"].sum()
    min_capacity = team_df["min_capacity"].sum()
    if neben_number>max_capacity:
        raise ValueError(f"全チームの最大許容人員の合計（{max_capacity}人）よりもネーベン数（{neben_number}人）が多いです")
    if neben_number<min_capacity:
        raise ValueError(f"全チームの最小必要人員の合計（{min_capacity}人）よりもネーベン数（{neben_number}人）が少ないです")
    for i in range(team_number):
        team_name = team_df["team"][i]
        if (team_df["max_capacity"].to_list())[i] < (team_df["min_capacity"].to_list())[i]:
            raise ValueError(f"チーム{team_name}において、maex_capacityよりもmin_capacityの方が大きいです")
        
    return 0

def daycheck(neben_df):
    days = set((neben_df["dayoff1"].dropna()).to_list() + (neben_df["dayoff2"].dropna()).to_list())
    correct_days = ["Mon","Tue","Wed","Thu","Fri","Sat"]
    for day in days:
        if not (day in correct_days):
            raise ValueError(f"曜日 {day} を正しい形式で記載してください（Mon,Tue,Wed,Thu,Fri,Satのいずれか）")
        
def make_new_nebenData(neben_df,t2n,this_term):
    term_name = {"1st":"term1team", "2nd":"term2team", "3rd":"term3team", "4th":"term4team"}
    for n in neben_df["name"].to_list():
        for k, v in t2n.items():
            if n in v:
                neben_df.loc[neben_df["name"]==n, term_name[this_term]] = k
    return neben_df

def show_prev_team(neben_df):
    df = neben_df[["name", "term1team","term2team","term3team","term4team"]]
    df.columns = ["name","1st term", "2nd term","3rd term", "4th term"]
    return df

def make_dayoff_data(neben_df,team_df,t2n):
    weekdays = ["Mon","Tue","Wed","Thu","Fri","Sat"]
    df = pd.DataFrame(columns=["team"]+weekdays)
    teams = team_df["team"].to_list()
    nebens = neben_df["name"].to_list()
    df["team"] = teams
    tw2n = {(t,w):[] for t in teams for w in weekdays}
    n2t = {}
    for n in nebens:
        for k, v in t2n.items():
            if n in v:
                n2t[n]=k
    for row in neben_df[["name","dayoff1"]].dropna().itertuples():
        tw2n[n2t[row.name],row.dayoff1].append(row.name)
    for row in neben_df[["name","dayoff2"]].dropna().itertuples():
        tw2n[n2t[row.name],row.dayoff2].append(row.name)
    for t in teams:
        for w in weekdays:
            if len(tw2n[t,w]) >0:
                content = tw2n[t,w][0]
                for i in range(1,len(tw2n[t,w])):
                    content = content + ", " + tw2n[t,w][i]
                df.loc[df["team"]==t, w] = content
    return df
   
def add_grade(t2n, neben_df):
    t2n_addgrade = {}
    for t, members in t2n.items():
        members_added_grade = []
        for n in members:
            grade = neben_df[neben_df["name"]==n]["grade"].iloc[0]
            members_added_grade.append(n+f" (grade {grade})")
        t2n_addgrade[t] = members_added_grade
    return t2n_addgrade
    
    
    