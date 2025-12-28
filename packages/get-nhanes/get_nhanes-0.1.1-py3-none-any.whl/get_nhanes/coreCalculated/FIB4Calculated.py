from functools import reduce
import numpy as np
import pandas as pd
from get_nhanes import get_nhanes_data
from get_nhanes.utils import save_result, sort_by_seqn

def fit_fib4():
    # ----------------------------------------------------------------------------------------------------
    # 提取age
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000', '2001-2002', '2003-2004', '2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014',
             '2015-2016', '2017-2018']
    features = ['seqn', 'ridageyr']
    metricName = "demo"
    age_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    age_data.rename(columns={'ridageyr': 'age'}, inplace=True)
    # age_data.to_csv("1999-2018_age_data.csv", index=False)

    # ----------------------------------------------------------------------------------------------------
    # 提取AST
    years = ['1999-2000']
    features = ['seqn','lbxsassi']
    metricName = "lab18"
    ast1_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    ast1_data.rename(columns={'lbxsassi': 'ast'}, inplace=True)

    years = ['2001-2002','2003-2004']
    features = ['seqn', 'lbxsassi']
    metricName = "l40_"
    ast2_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    ast2_data.rename(columns={'lbxsassi': 'ast'}, inplace=True)

    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    features = ['seqn', 'lbxsassi']
    metricName = "biopro_"
    ast3_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    ast3_data.rename(columns={'lbxsassi': 'ast'}, inplace=True)

    ast_data = pd.concat([ast1_data, ast2_data, ast3_data], axis=0)

    # ----------------------------------------------------------------------------------------------------
    # 提取ALT
    years = ['1999-2000']
    features = ['seqn', 'lbxsatsi']
    metricName = "lab18"
    alt1_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alt1_data.rename(columns={'lbxsatsi': 'alt'}, inplace=True)

    years = ['2001-2002', '2003-2004']
    features = ['seqn', 'lbxsatsi']
    metricName = "l40_"
    alt2_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alt2_data.rename(columns={'lbxsatsi': 'alt'}, inplace=True)

    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'lbxsatsi']
    metricName = "biopro_"
    alt3_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    alt3_data.rename(columns={'lbxsatsi': 'alt'}, inplace=True)

    alt_data = pd.concat([alt1_data, alt2_data, alt3_data], axis=0)

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
    # 合并所有数据
    ast_data = ast_data.reset_index(drop=True)
    alt_data = alt_data.reset_index(drop=True)
    PC_data = PC_data.reset_index(drop=True)

    # 按seqn合并所有数据框
    dataframes = [ast_data, alt_data, PC_data,age_data]

    FIB4_Data = reduce(lambda left, right: pd.merge(left, right, on='seqn', how='outer'), dataframes)
    FIB4_Data = sort_by_seqn(FIB4_Data)

    FIB4_Data["FIB4"] = (FIB4_Data["age"] * FIB4_Data["ast"])/(FIB4_Data["Platelet_Count"] * np.sqrt(FIB4_Data["alt"]))

    return FIB4_Data

def calculation_fib4(feature_data=fit_fib4(), save_path=None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "FIB4_results.csv"
    else:
        save_path = save_path + "FIB4_results.csv"
    save_result(feature_data, save_path, "FIB4 calculation")

if __name__ == '__main__':
    calculation_fib4()


