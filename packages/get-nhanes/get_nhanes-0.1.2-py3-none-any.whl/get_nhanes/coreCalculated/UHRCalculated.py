from functools import reduce
import pandas as pd
from get_nhanes.coreCalculated import AIPCalculated
from get_nhanes.utils import get_nhanes_data, save_result, sort_by_seqn

def fit_uhr():
    # ------------------------------------------------------------------------------------------------
    # 提取 HDL-C
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
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

    # 合并所有triglyceride数据
    hdl_data = pd.concat([hdl1, hdl2, hdl3, hdl4], axis=0)
    # ------------------------------------------------------------------------------------------------
    # 提取 UA
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    # 使用小写指标
    features = ['seqn', 'lbxsua']
    metricName = "lab18"
    ua1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    ua1.rename(columns={'lbxsua': 'ua'}, inplace=True)

    years = ['2001-2002','2003-2004']
    # 使用小写指标
    features = ['seqn', 'lbxsua']
    metricName = "l40_"
    ua2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    ua2.rename(columns={'lbxsua': 'ua'}, inplace=True)

    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    features = ['seqn', 'lbxsua']
    metricName = "biopro_"
    ua3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    ua3.rename(columns={'lbxsua': 'ua'}, inplace=True)

    # 合并所有triglyceride数据
    ua_data = pd.concat([ua1, ua2, ua3], axis=0)

    # 合并所有数据------------------------
    hdl_data = hdl_data.reset_index(drop=True)
    ua_data = ua_data.reset_index(drop=True)

    # 按seqn合并所有数据框
    dataframes = [hdl_data, ua_data]

    UHR_Data = reduce(lambda left, right: pd.merge(left, right, on='seqn', how='outer'), dataframes)
    UHR_Data = sort_by_seqn(UHR_Data)

    # 计算UHR
    try:
        UHR_Data["UHR"] =  UHR_Data["ua"] / UHR_Data["hdl"] * 1.0
    except Exception as e:
        raise RuntimeError(f"An error occurred while calculating AIP_Data: {e}")
    return UHR_Data

def calculation_uhr(feature_data=fit_uhr(), save_path=None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "UHR_results.csv"
    else:
        save_path = save_path + "UHR_results.csv"
    save_result(feature_data, save_path, "UHR calculation")


if __name__ == '__main__':
    calculation_uhr()