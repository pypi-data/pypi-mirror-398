import math
import pandas as pd
from functools import reduce

from get_nhanes import get_nhanes_data
from get_nhanes.utils import save_result, sort_by_seqn
from get_nhanes.coreCalculated import VAICalculated, BMICalculated

def fit_bri():
    # ----------------------------------------------------------------------------------------------------
    # 提取 WC
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
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

    # ----------------------------------------------------------------------------------------------------
    # 提取 height
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']

    years = ['1999-2000', '2001-2002', '2003-2004', '2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014',
             '2015-2016', '2017-2018']
    # 使用小写指标
    features = ['seqn', 'bmxht']
    metric_name = "bmx"
    height_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )
    height_data.rename(columns={'bmxht': 'height'}, inplace=True)

    # 按seqn合并所有数据框
    dataframes = [WC_data, height_data]

    BRIfeatures_Data = reduce(lambda left, right: pd.merge(left, right, on='seqn', how='outer'), dataframes)
    BRIfeatures_Data = sort_by_seqn(BRIfeatures_Data)

    try:
        BRIfeatures_Data['BRI'] = BRIfeatures_Data.apply(lambda row: 364.2 - 365.5 * math.sqrt(
            1 - ((row['waist'] / (2 * math.pi)) ** 2) / ((0.5 * row['height']) ** 2)), axis=1)
    except Exception as e:
        raise RuntimeError(f"An error occurred while calculating BRI: {e}")

    return BRIfeatures_Data

def calculation_bri(feature_data=fit_bri(), save_path=None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "BRI_results.csv"
    else:
        save_path = save_path + "BRI_results.csv"
    save_result(feature_data, save_path, "BRI calculation")

if __name__ == '__main__':
    calculation_bri()