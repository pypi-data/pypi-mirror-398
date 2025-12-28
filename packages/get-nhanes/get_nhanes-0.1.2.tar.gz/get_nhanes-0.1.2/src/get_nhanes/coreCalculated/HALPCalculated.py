from functools import reduce
import pandas as pd
from get_nhanes import get_nhanes_data
from get_nhanes.utils import save_result, sort_by_seqn
from get_nhanes.coreCalculated import SIICalculated, RARCalculated


def fit_halp():
    # ----------------------------------------------------------------------------------------------------
    # hemoglobin
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    features = ['seqn', 'lbxhgb']
    metricName = "lab25"
    hemoglobin1_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    hemoglobin1_data.rename(columns={'lbxhgb': 'hemoglobin'}, inplace=True)

    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['2001-2002', '2003-2004']
    features = ['seqn', 'lbxhgb']
    metricName = "l25_"
    hemoglobin2_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    hemoglobin2_data.rename(columns={'lbxhgb': 'hemoglobin'}, inplace=True)

    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'lbxhgb']
    metricName = "cbc_"
    hemoglobin3_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    hemoglobin3_data.rename(columns={'lbxhgb': 'hemoglobin'}, inplace=True)

    hemoglobin_data = pd.concat([hemoglobin1_data, hemoglobin2_data, hemoglobin3_data], axis=0)

    # ----------------------------------------------------------------------------------------------------
    # 提取ALB
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    features = ['seqn', 'lbdsalsi']
    metricName = "lab18"
    alb1_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alb1_data.rename(columns={'lbdsalsi': 'alb'}, inplace=True)

    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['2001-2002', '2003-2004']
    features = ['seqn', 'lbdsalsi']
    metricName = "l40_"
    alb2_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alb2_data.rename(columns={'lbdsalsi': 'alb'}, inplace=True)

    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'lbdsalsi']
    metricName = "biopro_"
    alb3_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alb3_data.rename(columns={'lbdsalsi': 'alb'}, inplace=True)

    alb_data = pd.concat([alb1_data, alb2_data, alb3_data], axis=0)

    # ----------------------------------------------------------------------------------------------------
    # 计算淋巴细胞&血小板计数
    # ----------------------------------------------------------------------------------------------------
    # 提取Platelet Count
    years = ['1999-2000']
    features = ['seqn', 'lbxpltsi']
    metricName = "lab25"
    PC1_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    PC1_data.rename(columns={'lbxpltsi': 'Platelet_Count'}, inplace=True)

    years = ['2001-2002', '2003-2004']
    features = ['seqn', 'lbxpltsi']
    metricName = "l25_"
    PC2_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    PC2_data.rename(columns={'lbxpltsi': 'Platelet_Count'}, inplace=True)

    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'lbxpltsi']
    metricName = "cbc_"
    PC3_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    PC3_data.rename(columns={'lbxpltsi': 'Platelet_Count'}, inplace=True)

    PC_data = pd.concat([PC1_data, PC2_data, PC3_data], axis=0)

    # ----------------------------------------------------------------------------------------------------
    # 提取 lymphocyte 淋巴细胞
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    # 使用小写指标
    features = ['seqn', 'lbdlymno']
    metricName = "lab25"
    lymphocyte_data1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    lymphocyte_data1.rename(columns={'lbdlymno': 'Lymphocyte'}, inplace=True)

    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['2001-2002', '2003-2004']
    # 使用小写指标
    features = ['seqn', 'lbdlymno']
    metricName = "l25_"
    lymphocyte_data2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    lymphocyte_data2.rename(columns={'lbdlymno': 'Lymphocyte'}, inplace=True)

    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    # 使用小写指标
    features = ['seqn', 'lbdlymno']
    metricName = "cbc_"
    lymphocyte_data3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    lymphocyte_data3.rename(columns={'lbdlymno': 'Lymphocyte'}, inplace=True)

    lymphocyte_data = pd.concat([lymphocyte_data1, lymphocyte_data2, lymphocyte_data3], axis=0)



    # ----------------------------------------------------------------------------------------------------
    # 合并所有数据
    hemoglobin_data = hemoglobin_data.reset_index(drop=True)
    alb_data = alb_data.reset_index(drop=True)
    PC_data = PC_data.reset_index(drop=True)
    lymphocyte_data = lymphocyte_data.reset_index(drop=True)

    # 按seqn合并所有数据框
    dataframes = [hemoglobin_data, alb_data,PC_data, lymphocyte_data, ]

    HALPfeatures_Data = reduce(lambda left, right: pd.merge(left, right, on='seqn', how='outer'), dataframes)
    HALPfeatures_Data = sort_by_seqn(HALPfeatures_Data)

    try:
        HALPfeatures_Data['HALP'] = (HALPfeatures_Data['hemoglobin'] * HALPfeatures_Data['alb'] * HALPfeatures_Data['Lymphocyte']) / HALPfeatures_Data['Platelet_Count']
    except Exception as e:
        raise RuntimeError(f"An error occurred while calculating TyG: {e}")

    return HALPfeatures_Data

def calculation_halp(feature_data = fit_halp(), save_path = None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "HALP_results.csv"
    else:
        save_path = save_path + "HALP_results.csv"
    save_result(feature_data, save_path, "HALP calculation")

if __name__ == '__main__':
    calculation_halp()