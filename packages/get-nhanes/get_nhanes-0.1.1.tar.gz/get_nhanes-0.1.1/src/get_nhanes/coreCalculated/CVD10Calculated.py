

from get_nhanes.coreCalculated import *
from get_nhanes.coreCalculated.SBPCalculated import fit_sbp
from get_nhanes import race_combine
from get_nhanes.utils import save_result, sort_by_seqn


def calculate_risk(df):
    """
    根据给定的公式计算 Risk，保留所有行，年龄<30或>79的行Risk设为NaN
    """
    result_df = df.copy()
    result_df['log_odds'] = np.nan
    result_df['Risk'] = np.nan

    # 定义分类变量映射函数
    def map_binary_variable(value):
        if pd.isna(value):
            return np.nan
        try:
            val = float(value)
            if val == 1.0:
                return 1.0
            if val == 2.0:
                return 2.0
            else:
                return np.nan
        except (ValueError, TypeError):
            return np.nan

    # 定义吸烟变量映射函数
    def map_smoker_refined(value):
        if pd.isna(value):
            return np.nan
        try:
            val = float(value)
            if val == 1.0 or val == 2.0:
                return 1.0
            elif val == 3.0: # NHANES SMQ040: 3 is Not at all
                return 2.0
            else:
                return np.nan
        except:
            return np.nan

    # 定义糖尿病综合映射函数
    def map_diabetes(row):
        d1 = row.get('diq010', np.nan)
        fbg = row.get('fbg', np.nan)
        
        # 辅助函数：判断是否为1
        def is_yes(v):
            try:
                return float(v) == 1.0
            except:
                return False
        
        # 辅助函数：判断是否为2 (No)
        def is_no(v):
            try:
                return float(v) == 2.0
            except:
                return False

        # Logic: fbg >= 126 or diq010 = 1 -> 1
        is_diabetic = False
        
        if is_yes(d1):
            is_diabetic = True
            
        try:
            if float(fbg) >= 126:
                is_diabetic = True
        except:
            pass
            
        if is_diabetic:
            return 1.0
            
        if is_no(d1):
             return 2.0
             
        return np.nan

    # 处理分类变量映射
    result_df['diq010'] = result_df.apply(map_diabetes, axis=1)
    result_df['smq040'] = result_df['smq040'].apply(map_smoker_refined)
    result_df['bpq050a'] = result_df['bpq050a'].apply(map_binary_variable)
    result_df['bpq100d'] = result_df['bpq100d'].apply(map_binary_variable)
    result_df['bpq020'] = result_df['bpq020'].apply(map_binary_variable)

    # 定义高血压逻辑
    def map_hypertension(row):
        sbp = row.get('mSBP', np.nan)
        dbp = row.get('mDBP', np.nan)
        bpq020 = row.get('bpq020', np.nan) # Ever told high blood pressure
        bpq050a = row.get('bpq050a', np.nan) # Taking meds for HBP
        
        is_htn = False
        
        try:
            if float(sbp) >= 140 or float(dbp) >= 90:
                is_htn = True
        except:
            pass
            
        try:
            if float(bpq020) == 1.0 or float(bpq050a) == 1.0:
                is_htn = True
        except:
            pass
            
        if is_htn:
            return 1.0
            
        has_valid_no_evidence = False
        try:
            if float(bpq020) == 2.0:
                has_valid_no_evidence = True
        except:
            pass
            
        try:
             if float(sbp) < 140 and float(dbp) < 90:
                 has_valid_no_evidence = True
        except:
            pass
            
        if has_valid_no_evidence:
            return 2.0
            
        return np.nan

    result_df['hypertension'] = result_df.apply(map_hypertension, axis=1)

    # 处理年龄：转换为浮点数，不修改原始值
    result_df['age'] = result_df['age'].astype(float)

    # 处理性别
    def gender_converter(gender_val):
        gender_str = str(gender_val).strip()
        if gender_str in ['1', '1.0']:
            return 1.0
        elif gender_str in ['2', '2.0']:
            return 2.0
        else:
            return np.nan
    result_df['gender'] = result_df['gender'].apply(gender_converter).astype(float)

    # -------------------------------------------------------------------------
    # PREVENT Model Variable Truncation (Winsorization)
    # Applying bounds as described in AHA PREVENT model documentation:
    # TC: 130-320 mg/dL
    # HDL: 20-100 mg/dL
    # SBP: 90-200 mmHg
    # eGFR: 14-140 mL/min/1.73m²
    # -------------------------------------------------------------------------
    
    # Ensure numeric types
    for col in ['TC', 'hdl', 'mSBP', 'eGFR']:
        result_df[col] = pd.to_numeric(result_df[col], errors='coerce')

    # Apply clipping
    result_df['TC'] = result_df['TC'].clip(lower=130, upper=320)
    result_df['hdl'] = result_df['hdl'].clip(lower=20, upper=100)
    result_df['mSBP'] = result_df['mSBP'].clip(lower=90, upper=200)
    result_df['eGFR'] = result_df['eGFR'].clip(lower=14, upper=140)
    # -------------------------------------------------------------------------

    # 定义有效行：年龄>=30 且性别非空
    valid_rows = result_df['age'].notna() & (result_df['age'] >= 30) & result_df['gender'].notna()

    # 男性 log_odds 计算
    male_condition = (result_df['gender'] == 1.0) & valid_rows
    if male_condition.any():
        male_df = result_df[male_condition].copy()
        # 使用 min(age, 79) 进行计算，不修改原始 age
        age_for_calc = np.minimum(male_df['age'], 79)
        log_odds_male = (
            -3.031168 +
            0.7688528 * ((age_for_calc - 55) / 10) +
            0.0736174 * (((male_df['TC'] - male_df['hdl']) * 0.02586 - 3.5)) -
            0.0954431 * (((male_df['hdl'] * 0.02586 - 1.3) / 0.3)) -
            0.4347345 * ((np.minimum(male_df['mSBP'], 110) - 110) / 20) +
            0.3362658 * ((np.maximum(male_df['mSBP'], 110) - 130) / 20) +
            0.7692857 * (male_df['diq010'] == 1).astype(int) +
            0.4386871 * (male_df['smq040'] == 1).astype(int) +
            0.5378979 * ((np.minimum(male_df['eGFR'], 60) - 60) / -15) +
            0.0164827 * ((np.maximum(male_df['eGFR'], 60) - 90) / -15) +
            0.288879 * (male_df['bpq050a'] == 1).astype(int) -
            0.1337349 * (male_df['bpq100d'] == 1).astype(int) -
            0.0475924 * (male_df['bpq050a'] == 1).astype(int) * ((np.maximum(male_df['mSBP'], 110) - 130) / 20) +
            0.150273 * (male_df['bpq100d'] == 1).astype(int) * (((male_df['TC'] - male_df['hdl']) * 0.02586 - 3.5)) -
            0.0517874 * ((age_for_calc - 55) / 10) * (((male_df['TC'] - male_df['hdl']) * 0.02586 - 3.5)) +
            0.0191169 * ((age_for_calc - 55) / 10) * (((male_df['hdl'] * 0.02586 - 1.3) / 0.3)) -
            0.1049477 * ((age_for_calc - 55) / 10) * ((np.maximum(male_df['mSBP'], 110) - 130) / 20) -
            0.2251948 * ((age_for_calc - 55) / 10) * (male_df['diq010'] == 1).astype(int) -
            0.0895067 * ((age_for_calc - 55) / 10) * (male_df['smq040'] == 1).astype(int) -
            0.1543702 * ((age_for_calc - 55) / 10) * ((np.minimum(male_df['eGFR'], 60) - 60) / -15)
        )
        result_df.loc[male_condition, 'log_odds'] = log_odds_male

    # 女性 log_odds 计算
    female_condition = (result_df['gender'] == 2.0) & valid_rows
    if female_condition.any():
        female_df = result_df[female_condition].copy()
        # 使用 min(age, 79) 进行计算，不修改原始 age
        age_for_calc = np.minimum(female_df['age'], 79)
        log_odds_female = (
            -3.307728 +
            0.7939329 * ((age_for_calc - 55) / 10) +
            0.0305239 * (((female_df['TC'] - female_df['hdl']) * 0.02586 - 3.5)) -
            0.1606857 * (((female_df['hdl'] * 0.02586 - 1.3) / 0.3)) -
            0.2394003 * ((np.minimum(female_df['mSBP'], 110) - 110) / 20) +
            0.360078 * ((np.maximum(female_df['mSBP'], 110) - 130) / 20) +
            0.8667604 * (female_df['diq010'] == 1).astype(int) +
            0.5360739 * (female_df['smq040'] == 1).astype(int) +
            0.6045917 * ((np.minimum(female_df['eGFR'], 60) - 60) / -15) +
            0.0433769 * ((np.maximum(female_df['eGFR'], 60) - 90) / -15) +
            0.3151672 * (female_df['bpq050a'] == 1).astype(int) -
            0.1477655 * (female_df['bpq100d'] == 1).astype(int) -
            0.0663612 * (female_df['bpq050a'] == 1).astype(int) * ((np.maximum(female_df['mSBP'], 110) - 130) / 20) +
            0.1197879 * (female_df['bpq100d'] == 1).astype(int) * (((female_df['TC'] - female_df['hdl']) * 0.02586 - 3.5)) -
            0.0819715 * ((age_for_calc - 55) / 10) * (((female_df['TC'] - female_df['hdl']) * 0.02586 - 3.5)) +
            0.0306769 * ((age_for_calc - 55) / 10) * (((female_df['hdl'] * 0.02586 - 1.3) / 0.3)) -
            0.0946348 * ((age_for_calc - 55) / 10) * ((np.maximum(female_df['mSBP'], 110) - 130) / 20) -
            0.27057 * ((age_for_calc - 55) / 10) * (female_df['diq010'] == 1).astype(int) -
            0.078715 * ((age_for_calc - 55) / 10) * (female_df['smq040'] == 1).astype(int) -
            0.1637806 * ((age_for_calc - 55) / 10) * ((np.minimum(female_df['eGFR'], 60) - 60) / -15)
        )
        result_df.loc[female_condition, 'log_odds'] = log_odds_female

    # 计算 Risk
    result_df['Risk'] = np.exp(result_df['log_odds']) / (1 + np.exp(result_df['log_odds'])) * 100

    return result_df

def fit_cvd10():
    # 年龄 性别 种族
    years = ['1999-2000', '2001-2002', '2003-2004', '2005-2006', '2007-2008', '2009-2010']
    features = ['seqn', 'ridageyr','riagendr','ridreth1','sdmvstra','sdmvpsu']
    metricName = "demo"
    demo_data1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    years = ['2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'ridageyr','riagendr','ridreth1','ridreth3','sdmvstra','sdmvpsu']
    metricName = "demo"
    demo_data2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    demo_data = pd.concat([demo_data1, demo_data2], axis=0)
    demo_data = race_combine(demo_data)

    demo_data.rename(columns={'ridageyr': 'age',
                             'riagendr':'gender'}, inplace=True)



    # ----------------------------------------------------------------------------------------------------
    # 提取 HDL-C lbdhdl -> mg/dL
    years = ['1999-2000']
    # 使用小写指标
    features = ['seqn', 'lbdhdl']
    metricName = "lab13"
    hdl1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    hdl1.rename(columns={'lbdhdl': 'hdl'}, inplace=True)

    years = ['2001-2002']
    # 使用小写指标
    features = ['seqn', 'lbdhdl']
    metricName = "l13_b"
    hdl2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    hdl2.rename(columns={'lbdhdl': 'hdl'}, inplace=True)

    years = ['2003-2004']
    # 使用小写指标
    features = ['seqn', 'lbxhdd']
    metricName = "l13_c"
    hdl3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    hdl3.rename(columns={'lbxhdd': 'hdl'}, inplace=True)

    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    # 使用小写指标
    features = ['seqn', 'lbdhdd']
    metricName = "hdl"
    hdl4 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    hdl4.rename(columns={'lbdhdd': 'hdl'}, inplace=True)

    hdl_data = pd.concat([hdl1, hdl2, hdl3, hdl4], axis=0)

    # ----------------------------------------------------------------------------------------------------
    # 提取eGFR
    egfr_data = fit_egfr()
    egfr_data = egfr_data.drop(columns=['age','gender','Scr'])


    # ----------------------------------------------------------------------------------------------------
    # 提取收缩压,舒张压
    sbp_data = fit_sbp()


    # ----------------------------------------------------------------------------------------------------
    # 提取总胆固醇 TC LBXTC mg/dL
    years = ['1999-2000']
    # 使用小写指标
    features = ['seqn', 'lbxtc']
    metricName = "lab13"
    TC1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    TC1.rename(columns={'lbxtc': 'TC'}, inplace=True)

    years = ['2001-2002','2003-2004']
    features = ['seqn', 'lbxtc']
    metricName = "l13_"
    TC2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    TC2.rename(columns={'lbxtc': 'TC'}, inplace=True)

    years = ['2005-2006', '2007-2008','2009-2010' ,'2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'lbxtc']
    metricName = "tchol"
    TC3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    TC3.rename(columns={'lbxtc': 'TC'}, inplace=True)

    # 合并所有triglyceride数据
    TC_data = pd.concat([TC1, TC2, TC3], axis=0)


    # ----------------------------------------------------------------------------------------------------
    # 现在是否抽烟 -> SMQ040
    years = ['1999-2000', '2001-2002', '2003-2004', '2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014',
             '2015-2016', '2017-2018']
    features = ['seqn','smq040']
    metricName = "smq"
    smq_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    # ----------------------------------------------------------------------------------------------------
    """
    BPQ050A --->  正在服用降压药
    BPQ020  --->  是否有被告知高血压
    BPQ090D --->  是否被告知要为了降低胆固醇 服用处方药
    BPQ100D --->  目前正在服用处方药（看作是使用Statin）
    """
    years = ['1999-2000', '2001-2002', '2003-2004', '2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014',
             '2015-2016', '2017-2018']
    features = ['seqn', 'bpq050a','bpq020','bpq090d','bpq100d']
    metricName = "bpq"
    hypertensive_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    # ----------------------------------------------------------------------------------------------------
    # 被医生告知有糖尿病(DIQ010) 1是的 2不是 3边界
    # 目前服用降血糖药物(DIQ070)
    years = ['1999-2000', '2001-2002', '2003-2004', '2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014',
             '2015-2016', '2017-2018']
    features = ['seqn','diq010']
    metricName = "diq"
    diabetes_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    # ----------------------------------------------------------------------------------------------------
    # Fasting Glucose (FBG) 空腹血糖 mg/dL
    years = ['1999-2000']
    features = ['seqn', 'lbxglu']
    metric_name = "lab10am"
    fbg1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )
    fbg1.rename(columns={'lbxglu': 'fbg'}, inplace=True)

    years = ['2001-2002','2003-2004']
    features = ['seqn', 'lbxglu']
    metric_name = "l10am_"
    fbg2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )
    fbg2.rename(columns={'lbxglu': 'fbg'}, inplace=True)

    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'lbxglu']
    metric_name = "glu"
    fbg3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )
    fbg3.rename(columns={'lbxglu': 'fbg'}, inplace=True)

    # Merge all FBG data
    fbg_data = pd.concat([fbg1, fbg2, fbg3], axis=0)

    # ----------------------------------------------------------------------------------------------------
    # combine_all_data

    # Reset indices (original code remains)
    demo_data = demo_data.reset_index(drop=True)
    hdl_data = hdl_data.reset_index(drop=True)
    egfr_data = egfr_data.reset_index(drop=True)
    sbp_data = sbp_data.reset_index(drop=True)
    TC_data = TC_data.reset_index(drop=True)
    smq_data = smq_data.reset_index(drop=True)
    hypertensive_data = hypertensive_data.reset_index(drop=True)
    diabetes_data = diabetes_data.reset_index(drop=True)
    fbg_data = fbg_data.reset_index(drop = True)


    # 以demo_data为基础进行左连接
    cvd10_Data = demo_data
    for df in [TC_data, hdl_data, sbp_data, egfr_data, smq_data, diabetes_data, hypertensive_data,fbg_data]:
        cvd10_Data = pd.merge(cvd10_Data, df, on='seqn', how='outer')
    
    cvd10_Data = sort_by_seqn(cvd10_Data)

    x = calculate_risk(cvd10_Data)
    return x

def calculation_cvd10(feature_data=fit_cvd10(), save_path=None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "CVD10_results.csv"
    else:
        save_path = save_path + "CVD10_results.csv"
    save_result(feature_data, save_path, "CVD10 calculation")

if __name__ == '__main__':
    calculation_cvd10()