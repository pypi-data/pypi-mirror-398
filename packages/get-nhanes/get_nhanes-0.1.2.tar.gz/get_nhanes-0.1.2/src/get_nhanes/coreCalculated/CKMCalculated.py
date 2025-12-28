

from get_nhanes.coreCalculated import *
from get_nhanes.coreCalculated.CVD10Calculated import fit_cvd10
from get_nhanes.utils import save_result, sort_by_seqn
import pandas as pd
from functools import reduce




# 合并数据
def fit_stage4_data():
     # Stage_4----------------------------------------------------------------------------------------------------
    """
    冠心病:   mcq160c
    心绞痛:   mcq160d
    心力衰竭: mcq160b
    心肌梗塞: mcq160e
    中风:    mcq160f
    """
    years = ['1999-2000', '2001-2002', '2003-2004', '2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014',
             '2015-2016', '2017-2018']
    features = ['seqn','mcq160c','mcq160d','mcq160b','mcq160e','mcq160f']
    metricName = 'mcq'
    stage4_data = get_nhanes_data(
        years = years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    return stage4_data

def fit_stage3_data():
    # Stage_3----------------------------------------------------------------------------------------------------
    """
    存在KDIGO定义的极高风险CKD分期,使用eGFR和尿白蛋白/尿肌酐判断
    (eGFR<30
     eGFR 30~<45 and UACR> 30mg/g
     eGFR 45~<90 and UACR>=300mg/g
     )
    或者使用PREVENT方程估算,高风险定义为>=20%
    """

    # 第一步使用PREVENT计算得到CVD10风险
    """
    CVD10计算
    seqn,age,gender,race,TC,hdl,mSBP,mDBP,eGFR,smq040,diq010,bpq050a,bpq090d,log_odds,Risk
    TC - 总胆固醇 mg/dL
    hdl - mg/dL
    smq040 - 是否抽烟
    diq010 - 糖尿病
    bpq050a - 被要求服用降压药
    bpq090d - 被要求服用降胆固醇药(Statin)
    """
    cvd_data = fit_cvd10()

    # 第二部,根据KDIGO定义的极高风险分期
    """
    G4-G5: eGFR<30
    G3b:   eGFR 30~<45 and UACR> 30mg/g
    G3a-G2:eGFR 45~<90 and UACR>=300mg/g
    """

    # UACR*1000  单位mg/g
    # 尿白蛋白

    # urxumasi mg/L
    years = ['1999-2000']
    features = ['seqn', 'urxumasi']
    metricName = 'lab16'
    alb_ua1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alb_ua1.rename(columns={'urxumasi': 'alb_ua'}, inplace=True)

    years = ['2001-2002', '2003-2004']
    features = ['seqn', 'urxumasi']
    metricName = 'l16_'
    alb_ua2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alb_ua2.rename(columns={'urxumasi': 'alb_ua'}, inplace=True)

    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'urxums']
    metricName = 'alb_cr_'
    alb_ua3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alb_ua3.rename(columns={'urxums': 'alb_ua'}, inplace=True)

    alb_ua_data = pd.concat([alb_ua1, alb_ua2, alb_ua3], axis=0)

    # 尿肌酐
    #  urxucr mg/dL  
    years = ['1999-2000']
    features = ['seqn', 'urxucr']
    metricName = 'lab16'
    alb_Cr1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alb_Cr1.rename(columns={'urxucr': 'alb_cr'}, inplace=True)

    years = ['2001-2002', '2003-2004']
    features = ['seqn', 'urxucr']
    metricName = 'l16_'
    alb_Cr2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alb_Cr2.rename(columns={'urxucr': 'alb_cr'}, inplace=True)

    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'urxucr']
    metricName = 'alb_cr_'
    alb_Cr3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alb_Cr3.rename(columns={'urxucr': 'alb_cr'}, inplace=True)

    alb_Cr_data = pd.concat([alb_Cr1, alb_Cr2, alb_Cr3], axis=0)

    UACR_data = pd.merge(alb_ua_data, alb_Cr_data, on='seqn', how='outer')

    UACR_data['UACR'] = UACR_data['alb_ua'] / UACR_data['alb_cr'] * 100

    UACR_data = UACR_data.drop(columns=['alb_cr', 'alb_ua'])

    stage3_data = pd.merge(cvd_data, UACR_data, on='seqn', how='outer')

    return stage3_data

def fit_stage2_data():
    # Stage_2----------------------------------------------------------------------------------------------------
    """
    中-高风险判断:KDIGO标准
    eGFR: 30~<45 and URCA <30mg/g
    eGFR: 45~<60 and UACR <300mg/g
    eGFR:  60~<90 and UACR 30~<300mg/g
    eGFR:  >=90   and UACR >30mg/g

    空腹血清甘油三酯 >= 135mg/L
    高血压
    糖尿病
    代谢综合症(>=3项以下指标 :
            腰围升高,
            HDL水平低(男性:40mg/L,女性:50mg/L)
            甘油三酯>= 150mg/L
            收缩压>=130mmHg , 舒张压>=80mmHg 或 使用降压药
            糖前期(定义为空腹血糖100 mg/dL至<126 mg/dL或糖化血红蛋白5.7%至<6.5%的个体)(DIQ160)
            )
    """

    # 甘油三脂
    years = ['1999-2000']
    features = ['seqn', 'lbxtr','wtsaf2yr']
    metric_name = "lab13am"
    triglyceride1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )

    years = ['2001-2002', '2003-2004']
    features = ['seqn', 'lbxtr','wtsaf2yr']
    metric_name = "l13am_"
    triglyceride2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )

    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'lbxtr','wtsaf2yr']
    metric_name = "trigly_"
    triglyceride3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )

    # 合并所有甘油三酯数据
    triglyceride_data = pd.concat([triglyceride1, triglyceride2, triglyceride3], axis=0)
    triglyceride_data.rename(columns={'lbxtr': 'triglycerid'}, inplace=True)

    stage2_data = triglyceride_data

    return stage2_data

def fit_stage1_data():
    # Stage_1----------------------------------------------------------------------------------------------------
    """
    BMI指数升高:
        亚裔个体>=23 其他种族>25
    腰围升高:
        亚裔女性:>80cm
        亚裔男性:>90cm
        其他种族女性:88cm
        其他种族男性:102cm
    糖前期:  定义为空腹血糖100 mg/dL至<126 mg/dL
            糖化血红蛋白5.7%至<6.5%的个体)
            DIQ160
    """
    
    # 糖化血红蛋白 - lbxgh 单位: % ----------
    years = ['1999-2000']
    features = ['seqn', 'lbxgh']
    metric_name = "lab10"
    glu1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )
    glu1.rename(columns={'lbxgh': 'glu'}, inplace=True)

    years = ['2001-2002', '2003-2004']
    features = ['seqn', 'lbxgh']
    metric_name = "l10_"
    glu2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )
    glu2.rename(columns={'lbxgh': 'glu'}, inplace=True)

    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'lbxgh']
    metric_name = "ghb_"
    glu3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )
    glu3.rename(columns={'lbxgh': 'glu'}, inplace=True)

    glu_data = pd.concat([glu1, glu2, glu3], axis=0)



    stage1_data = glu_data

    return stage1_data

def fit_stage0_data():
    # Stage_0----------------------------------------------------------------------------------------------------
    """
    BMI正常:
        亚裔:     <23
        其他种族:  <25
    腰围正常:
        亚裔女性: <80
        亚裔男性: <90
        其他女性: <88
        其他男性: <102
    且不符合其他分期标准
    """

    # 腰围
    years = ['1999-2000', '2001-2002', '2003-2004', '2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014',
             '2015-2016', '2017-2018']
    # 使用小写指标
    features = ['seqn', 'bmxwaist']
    metricName = "bmx"
    WC_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    WC_data.rename(columns={'bmxwaist': 'waist'}, inplace=True)

    # BMI数据
    BMI_data = fit_bmi()
    BMI_data = BMI_data.drop(columns=['height', 'weight'])


    stage0_data = pd.merge(WC_data, BMI_data, on='seqn', how='outer')

    return stage0_data


# 判断逻辑
def ckm_stage_4(row):
    """
    Stage 4: 已确诊的心血管疾病
    如果mcq160c,mcq160d,mcq160b,mcq160e,mcq160f 有任意一列为1,Stage为"4"
    冠心病:   mcq160c
    心绞痛:   mcq160d
    心力衰竭: mcq160b
    心肌梗塞: mcq160e
    中风:    mcq160f
    """
    cvd_columns = ['mcq160c', 'mcq160d', 'mcq160b', 'mcq160e', 'mcq160f']

    for col in cvd_columns:
        if col in row.index and pd.notna(row[col]) and row[col] == 1:
            return True
    return False


def ckm_stage_3(row):
    """
    判断患者是否符合 CKM Stage 3 标准：
    1. 10年CVD风险 >= 20% (基于PREVENT方程估算)。
    2. 存在 KDIGO 定义的极高风险（红色区域）CKD 分期。

    该函数假定：
    - 'Risk' 列已经根据年龄（如 >=80 岁设为 79 岁）进行过 PREVENT 估算。
    - 年龄 < 30 岁的患者，'Risk' 字段可能缺失或为 NaN，将仅依赖 eGFR/UACR 判断。
    
    参数:
        row (pd.Series): 包含 'Risk', 'eGFR', 'UACR' 等列的单行数据。
        
    返回:
        bool: 如果符合 CKM Stage 3 标准，返回 True；否则返回 False。
    """
    # 1. 检查PREVENT风险评分 (若有风险评分，则优先使用)
    # CKM 3 期标准之一：10 年 CVD 风险 >= 20%
    if 'Risk' in row.index and pd.notna(row['Risk']) and row['Risk'] >= 20:
        return True

    # 2. 检查 KDIGO CKD 极高风险分期 (红色区域)
    egfr = row.get('eGFR', np.nan)
    uacr = row.get('UACR', np.nan)
    # G4 (15–29) 和 G5 (<15) 组，无论 UACR 如何，均为极高风险 (A1-A3)
    if egfr <=29:
        return True
    
    # G3b 组 (30–44): A2 (30-300) 和 A3 (>300) 均为极高风险
    # A2 定义为 30-300，包含 30
    elif 30 <= egfr <= 44:
        if uacr >= 30: 
            return True
            
    # G3a 组 (45–59): 只有 A3 (>300) 属于极高风险
    # A3 定义为 > 300，不包含 300 (300 属于 A2)
    elif 45 <= egfr <= 59:
        if uacr > 300: 
            return True
    # 3. 不符合以上任何标准
    return False


def ckm_stage_2(row):
    """
    判断患者是否符合 CKM Stage 2 标准：
    1. 存在 KDIGO 定义的中度增加/高风险（黄/橙区域）CKD 分期。
    2. 存在以下任一独立危险因素：高甘油三酯 (>=135 mg/dL)、高血压、糖尿病。
    3. 存在 代谢综合症（>=3项指标）。
    
    参数:
        row (pd.Series): 包含 eGFR, UACR, 危险因素指标的单行数据。
        
    返回:
        bool: 如果符合 CKM Stage 2 标准，返回 True；否则返回 False。
    """
    
    egfr = row.get('eGFR', np.nan)
    uacr = row.get('UACR', np.nan)
    triglycerid = row.get('triglycerid', np.nan)
    sbp = row.get('mSBP', np.nan)
    dbp = row.get('mDBP', np.nan)
    bp_med = row.get('bpq050a', np.nan)
    diabetes = row.get('diq010', np.nan)
    
    # --------------------------------------------------------------------------
    ## 1. 检查 KDIGO 中/高风险分期 (黄/橙区域)
    # --------------------------------------------------------------------------
    
    # 注意: G3aA3 (eGFR 45-59 & UACR > 300) 是 CKM 3 期，因此这里只检查 UACR <= 300 的情况。
    # G4/G5 (eGFR < 30) 是 CKM 3 期，因此不在这里检查。

    
    # G3b 组 (30 <= eGFR < 45): A1 (<30) 是橙区 (High Risk, Stage 2)
    if 30 <= egfr <=44 and uacr < 30:
        return True
    
    # G3a 组 (45 <= eGFR < 60): A1 (<30) 是绿区 (Low Risk), A2 (30-300) 是黄区 (Moderate Risk)
    elif 45 <= egfr <= 59 and uacr <= 300: 
        return True
    
    # G1/G2 组 (eGFR >= 60): A2 (30-300) 是黄区, A3 (>300) 是橙区
    elif egfr >= 60:
        if uacr >= 30:
            return True

    # --------------------------------------------------------------------------
    ## 2. 检查其他独立危险因素 (任一满足即可)
    # --------------------------------------------------------------------------
    
    # A. 高甘油三酯 (阈值 135 mg/dL)
    if pd.notna(triglycerid) and triglycerid >= 135:
        return True
    
    # B. 高血压 (SBP>=130 或 DBP>=80 或使用降压药)
    is_hypertensive = (
        (pd.notna(sbp) and sbp >= 130) or
        (pd.notna(dbp) and dbp >= 80) or
        (pd.notna(bp_med) and bp_med == 1)
    )
    if is_hypertensive:
        return True

    # C. 糖尿病
    if pd.notna(diabetes) and diabetes == 1:
        return True

    # --------------------------------------------------------------------------
    ## 3. 代谢综合症判断 (≥3 项指标)
    # --------------------------------------------------------------------------
    
    metabolic_count = 0
    gender = row.get('gender', np.nan)
    waist = row.get('waist', np.nan)
    hdl = row.get('hdl', np.nan)
    race = row.get('race', np.nan)
    fbg = row.get('fbg', np.nan)
    glu = row.get('glu', np.nan) 
    
    # P1. 腰围升高
    if pd.notna(waist) and pd.notna(gender):
        # 亚裔 (种族=5)
        if pd.notna(race) and race == 5:
            if (gender == 2.0 and waist >= 80) or (gender == 1.0 and waist >= 90):
                metabolic_count += 1
        # 其他种族
        else:
            if (gender == 2.0 and waist >= 88) or (gender == 1.0 and waist >= 102):
                metabolic_count += 1

    # P2. HDL水平低
    if pd.notna(hdl) and pd.notna(gender):
        if (gender == 1.0 and hdl < 40) or (gender == 2.0 and hdl < 50):
            metabolic_count += 1

    # P3. 甘油三酯升高 (注意：代谢综合征标准为 >= 150 mg/dL)
    if pd.notna(triglycerid) and triglycerid >= 150:
        metabolic_count += 1

    # P4. 血压升高或用药 (与独立因素 B 定义一致)
    if is_hypertensive:
        metabolic_count += 1

    # P5. 血糖升高 (空腹血糖 100-125 或 HbA1c 5.7%-6.4% 或已确诊糖尿病)
    # 此处使用您提供的糖前期/HbA1c标准，并可以包含已确诊糖尿病 (diq010 == 1)
    if ((pd.notna(fbg) and 100 <= fbg < 126) or
            (pd.notna(glu) and 5.7 <= glu < 6.5) or
            (pd.notna(diabetes) and diabetes == 1)):
        metabolic_count += 1

    # 代谢综合症：>=3项指标
    if metabolic_count >= 3:
        return True

    return False


def ckm_stage_1(row):
    """
    Stage 1: 低-中风险
    BMI指数升高:
        亚裔个体>=23 其他种族>25
    腰围升高:
        亚裔女性:>=80cm, 亚裔男性:>=90cm
        其他种族女性:>=88cm, 其他种族男性:>=102cm
    糖前期: 空腹血糖100-125 mg/dL 或 糖化血红蛋白5.7%-6.4%
    """
    BMI = row.get('BMI', np.nan)
    waist = row.get('waist', np.nan)
    gender = row.get('gender', np.nan)
    race = row.get('race', np.nan)
    fbg = row.get('fbg', np.nan)
    glu = row.get('glu', np.nan)

    # BMI升高
    if pd.notna(BMI) and pd.notna(race):
        if race in [5]:  # 亚裔
            if BMI >= 23:
                return True
        else:  # 其他种族
            if BMI > 25:
                return True

    # 腰围升高
    if pd.notna(waist) and pd.notna(gender):
        if pd.notna(race) and race in [5]:  # 亚裔
            if (gender == 2.0 and waist >= 80) or (gender == 1.0 and waist >= 90):
                return True
        else:  # 其他种族
            if (gender == 2.0 and waist >= 88) or (gender == 1.0 and waist >= 102):
                return True

    # 糖前期
    if ((pd.notna(fbg) and 100 <= fbg < 126) or
            # TODO ---- 确认单位是否为 % 
            (pd.notna(glu) and 5.7 <= glu < 6.5)):
        return True

    return False


def ckm_stage_0(row):
    """
    Stage 0: 最优健康状态
    BMI正常:
        亚裔:     <23
        其他种族:  <25
    腰围正常:
        亚裔女性: <80, 亚裔男性: <90
        其他女性: <88, 其他男性: <102
    且不符合其他分期标准
    """

    BMI = row.get('BMI', np.nan)
    waist = row.get('waist', np.nan)
    gender = row.get('gender', np.nan)
    race = row.get('race', np.nan)

    # 检查BMI是否正常
    BMI_normal = False
    if pd.notna(BMI) and pd.notna(race):
        if race in [5]:  # 亚裔
            BMI_normal = BMI < 23
        else:  # 其他种族
            BMI_normal = BMI < 25

    # 检查腰围是否正常
    waist_normal = False
    if pd.notna(waist) and pd.notna(gender):
        if pd.notna(race) and race in [5]:  # 亚裔
            waist_normal = (gender == 2.0 and waist < 80) or (gender == 1.0 and waist < 90)
        else:  # 其他种族
            waist_normal = (gender == 2.0 and waist < 88) or (gender == 1.0 and waist < 102)

    # 只有当BMI和腰围都正常时才可能是Stage 0
    return BMI_normal and waist_normal


def fit_CKMStage(df):
    """
    为 DataFrame 添加 CKM 分期列（彻底避免SettingWithCopyWarning）
    参数: df (DataFrame)
    返回: 修改后的 DataFrame
    """
    # 确保使用的是真正的DataFrame而不是视图
    if not isinstance(df, pd.DataFrame):
        raise ValueError("输入必须是pandas DataFrame")

    # 创建副本以确保安全操作
    result_df = df.copy()

    # 定义一个逐行判断的函数
    def get_ckm_stage(row):
        # 判断是否符合 Stage 4 的条件
        if ckm_stage_4(row):
            return "4"
        # 判断是否符合 Stage 3 的条件
        elif ckm_stage_3(row):
            return "3"
        # 判断是否符合 Stage 2 的条件
        elif ckm_stage_2(row):
            return "2"
        # 判断是否符合 Stage 1 的条件
        elif ckm_stage_1(row):
            return "1"
        # 判断是否符合 Stage 0 的条件
        elif ckm_stage_0(row):
            return "0"
        # 如果都不符合则返回 NaN
        else:
            return np.nan

    # 先计算所有的分期结果
    stage_results = result_df.apply(get_ckm_stage, axis=1)

    # 然后安全地赋值
    result_df = result_df.assign(CKMStage=stage_results)

    return result_df

def calculation_ckm(save_path = None):
    stage_0_data = fit_stage0_data()
    stage_1_data = fit_stage1_data()
    stage_2_data = fit_stage2_data()
    stage_3_data = fit_stage3_data()
    stage_4_data = fit_stage4_data()

    dataframes = [stage_0_data, stage_1_data, stage_2_data, stage_3_data, stage_4_data]

    CKM_Data = reduce(lambda left, right: pd.merge(left, right, on='seqn', how='outer'), dataframes)
    
    
    # Calculate CKM Stage
    CKM_Data = fit_CKMStage(CKM_Data)
    CKM_Data = sort_by_seqn(CKM_Data)

    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "CKMStage_results.csv"

    else:
        save_path = save_path + "CKMStage_results.csv"
    save_result(CKM_Data, save_path, "CKM calculation")

if __name__ == '__main__':
    calculation_ckm()
 