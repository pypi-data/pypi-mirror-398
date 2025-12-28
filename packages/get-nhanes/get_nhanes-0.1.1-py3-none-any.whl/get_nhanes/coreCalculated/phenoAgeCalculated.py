
from functools import reduce

import numpy as np
import pandas as pd
from get_nhanes import get_nhanes_data
from get_nhanes.utils import save_result, sort_by_seqn

def fit_phenoage():
    # ----------------------------------------------------------------------------------------------------
    # 提取 Triglyceride
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']

    years = ['1999-2000']
    # 使用小写指标
    features = ['seqn','lbxsal']
    metricName = "lab18"
    albumin_gL1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    years = ['2001-2002','2003-2004']
    # 使用小写指标
    features = ['seqn','lbxsal']
    metricName = "l40"
    albumin_gL2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    # 使用小写指标
    features = ['seqn','lbxsal']
    metricName = "biopro"
    albumin_gL3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    # 合并所有albumin_gL数据
    albumin_gL_data = pd.concat([albumin_gL1, albumin_gL2, albumin_gL3], axis=0)

    # 增加新列 albumin_gL，其值等于 albumin 列的值乘以 10
    albumin_gL_data['albumin_gL'] = albumin_gL_data['lbxsal'] * 10

    albumin_gL_data = albumin_gL_data.drop(columns=['lbxsal'])

    # ----------------------------------------------------------------------------------------------------
    # 提取creat_umol
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']

    years = ['1999-2000']
    # 使用小写指标
    features = ['seqn','lbxscr']
    metricName = "lab18"
    creat_umol1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    # 对其进行线性变化
    creat_umol1['lbxscr'] = 1.013 * creat_umol1['lbxscr'] + 0.147


    years = ['2001-2002']
    # 使用小写指标
    features = ['seqn','lbdscr']
    metricName = "l40_b"
    creat_umol2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    creat_umol2.rename(columns={'lbdscr': 'lbxscr'}, inplace=True)


    years = ['2003-2004']
    # 使用小写指标
    features = ['seqn','lbxscr']
    metricName = "l40_c"
    creat_umol3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    years = ['2005-2006']
    # 使用小写指标
    features = ['seqn','lbxscr']
    metricName = "biopro"
    creat_umol4 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    creat_umol4['lbxscr'] = (-0.016) + 0.978 * creat_umol4['lbxscr']

    years = ['2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    features = ['seqn','lbxscr']
    metricName = "biopro"
    creat_umol5 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    # 合并所有creat_umol数据
    creat_umol_data = pd.concat([creat_umol1, creat_umol2, creat_umol3,creat_umol4,creat_umol5], axis=0)

    # 增加新列 albumin_gL，其值等于 albumin 列的值乘以 10
    creat_umol_data['creat_umol'] = creat_umol_data['lbxscr'] * 88.4017
    creat_umol_data = creat_umol_data.drop(columns=['lbxscr'])



    # ----------------------------------------------------------------------------------------------------
    # 提取glucose_mmol
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']

    years = ['1999-2000']
    # 使用小写指标
    features = ['seqn','lbxsgl']
    metricName = "lab18"
    glucose_mmol1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    years = ['2001-2002','2003-2004']
    # 使用小写指标
    features = ['seqn','lbxsgl']
    metricName = "l40"
    glucose_mmol2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    # 使用小写指标
    features = ['seqn','lbxsgl']
    metricName = "biopro"
    glucose_mmol3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    # 合并所有albumin_gL数据
    glucose_mmol_data = pd.concat([glucose_mmol1, glucose_mmol2, glucose_mmol3], axis=0)

    glucose_mmol_data['glucose_mmol'] = glucose_mmol_data['lbxsgl'] * 0.0555
    glucose_mmol_data = glucose_mmol_data.drop(columns=['lbxsgl'])


    # ----------------------------------------------------------------------------------------------------
    # 提取lncrp
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    # 使用小写指标
    features = ['seqn','lbxcrp']
    metricName = "lab11"
    lncrp1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    years = ['2001-2002']
    # 使用小写指标
    features = ['seqn','lbxcrp']
    metricName = "l11_b"
    lncrp2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    years = ['2003-2004']
    # 使用小写指标
    features = ['seqn','lbxcrp']
    metricName = "l11_c"
    lncrp3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    years = ['2005-2006','2007-2008', '2009-2010','2011-2012', '2013-2014']
    features = ['seqn','lbxcrp']
    metricName = "crp"
    lncrp4 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    years = ['2015-2016','2017-2018']
    features = ['seqn','lbxhscrp']
    metricName = "hscrp"
    lncrp5 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    lncrp5['lbxcrp'] = lncrp5['lbxhscrp'] / 10
    lncrp5 = lncrp5.drop(columns=['lbxhscrp'])

    lncrp_data = pd.concat([lncrp1, lncrp2, lncrp3,lncrp4,lncrp5], axis=0)

    lncrp_data["lncrp"] = np.log(lncrp_data['lbxcrp'] + 1)
    lncrp_data = lncrp_data.drop(columns=['lbxcrp'])

    # ----------------------------------------------------------------------------------------------------
    # 提取lymph
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    features = ['seqn','lbxlypct']
    metricName = "lab25"
    lymph1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    years = ['2001-2002','2003-2004']
    features = ['seqn','lbxlypct']
    metricName = "l25"
    lymph2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    features = ['seqn','lbxlypct']
    metricName = "cbc"
    lymph3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    lymph_data = pd.concat([lymph1, lymph2, lymph3], axis=0)
    lymph_data.rename(columns={'lbxlypct': 'lymph'}, inplace=True)




    # ----------------------------------------------------------------------------------------------------
    # 提取mvc
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    features = ['seqn','lbxmcvsi']
    metricName = "lab25"
    mvc1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    years = ['2001-2002','2003-2004']
    features = ['seqn','lbxmcvsi']
    metricName = "l25"
    mvc2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    features = ['seqn','lbxmcvsi']
    metricName = "cbc"
    mvc3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    mvc_data = pd.concat([mvc1, mvc2, mvc3], axis=0)
    mvc_data.rename(columns={'lbxmcvsi': 'mcv'}, inplace=True)



    # ----------------------------------------------------------------------------------------------------
    # 提取rdw
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    features = ['seqn','lbxrdw']
    metricName = "lab25"
    rdw1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    years = ['2001-2002','2003-2004']
    features = ['seqn','lbxrdw']
    metricName = "l25"
    rdw2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    features = ['seqn','lbxrdw']
    metricName = "cbc"
    rdw3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    rdw_data = pd.concat([rdw1, rdw2, rdw3], axis=0)
    rdw_data.rename(columns={'lbxrdw': 'rdw'}, inplace=True)


    # ----------------------------------------------------------------------------------------------------
    # 提取alp
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    features = ['seqn','lbxsapsi']
    metricName = "lab18"
    alp1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    years = ['2001-2002']
    features = ['seqn','lbdsapsi']
    metricName = "l40_b"
    alp2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alp2.rename(columns={'lbdsapsi': 'lbxsapsi'}, inplace=True)

    years = ['2003-2004']
    features = ['seqn','lbxsapsi']
    metricName = "l40_c"
    alp3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    features = ['seqn','lbxsapsi']
    metricName = "biopro"
    alp4 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    alp_data = pd.concat([alp1, alp2, alp3, alp4], axis=0)
    alp_data.rename(columns={'lbxsapsi': 'alp'}, inplace=True)
    # alp_data.to_csv("1999-2018_alp_data.csv", index=False)


    # ----------------------------------------------------------------------------------------------------
    # 提取wbc
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    features = ['seqn','lbxwbcsi']
    metricName = "lab25"
    wbc1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    years = ['2001-2002','2003-2004']
    features = ['seqn','lbxwbcsi']
    metricName = "l25"
    wbc2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    features = ['seqn','lbxwbcsi']
    metricName = "cbc"
    wbc3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    wbc_data = pd.concat([wbc1, wbc2, wbc3], axis=0)
    wbc_data.rename(columns={'lbxwbcsi': 'wbc'}, inplace=True)


    # ----------------------------------------------------------------------------------------------------
    # 提取age
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    features = ['seqn','ridageyr']
    metricName = "demo"
    age_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    age_data.rename(columns={'ridageyr': 'age'}, inplace=True)


    # ----------------------------------------------------------------------------------------------------
    # combine_all_data
    age_data = age_data.reset_index(drop=True)
    albumin_gL_data = albumin_gL_data.reset_index(drop=True)
    alp_data = alp_data.reset_index(drop=True)
    creat_umol_data = creat_umol_data.reset_index(drop=True)
    glucose_mmol_data = glucose_mmol_data.reset_index(drop=True)
    lncrp_data = lncrp_data.reset_index(drop=True)
    lymph_data = lymph_data.reset_index(drop=True)
    mvc_data = mvc_data.reset_index(drop=True)
    rdw_data = rdw_data.reset_index(drop=True)
    wbc_data = wbc_data.reset_index(drop=True)

    # 按seqn合并所有数据框
    dataframes = [albumin_gL_data, creat_umol_data, glucose_mmol_data, lncrp_data,
                  lymph_data, mvc_data, rdw_data, alp_data, wbc_data, age_data]

    bioAgeFeatures_Data = reduce(lambda left, right: pd.merge(left, right, on='seqn',how='outer'), dataframes)
    bioAgeFeatures_Data = sort_by_seqn(bioAgeFeatures_Data)



    xb = (
            -19.90667
            + (-0.03359355 * bioAgeFeatures_Data['albumin_gL'])
            + (0.009506491 * bioAgeFeatures_Data['creat_umol'])
            + (0.1953192 * bioAgeFeatures_Data['glucose_mmol'])
            + (0.09536762 * bioAgeFeatures_Data['lncrp'])
            + (-0.01199984 * bioAgeFeatures_Data['lymph'])
            + (0.02676401 * bioAgeFeatures_Data['mcv'])
            + (0.3306156 * bioAgeFeatures_Data['rdw'])
            + (0.001868778 * bioAgeFeatures_Data['alp'])
            + (0.05542406 * bioAgeFeatures_Data['wbc'])
            + (0.08035356 * bioAgeFeatures_Data['age'])
    )

    m = 1 - (np.exp((-1.51714 * np.exp(xb)) / 0.007692696))

    # 确保 m 的值在合法范围内，避免对数计算报错
    m = np.where(m >= 1, 1 - 1e-10, m)  # 将 m 的值限制在小于1的范围内
    m = np.where(m <= 0, 1e-10, m)  # 将 m 的值限制在大于0的范围内

    phenoage0 = ((np.log(-0.0055305 * (np.log(1 - m))) / 0.09165) + 141.50225)

    features = bioAgeFeatures_Data.drop(
        columns=["albumin_gL", "creat_umol", "glucose_mmol", "lncrp", "lymph", "mcv", "rdw", "alp", "wbc"])
    features["phenoage0"] = phenoage0
    features["phenoage_advance"] = features["phenoage0"] - features["age"]

    return features

def calculation_phenoage(features=fit_phenoage(), save_path=None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "phenoage0_results.csv"
    else:
        save_path = save_path + "PhenoAge_results.csv"
    save_result(features, save_path, "PhenoAge calculation")



if __name__ == '__main__':
    calculation_phenoage()
