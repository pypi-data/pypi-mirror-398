from functools import reduce
import numpy as np
import pandas as pd

from get_nhanes.utils import get_nhanes_data, save_result, sort_by_seqn


def fit_bmi():
    # ----------------------------------------------------------------------------------------------------
    # 提取 height
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']

    years = ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    # 使用小写指标
    features = ['seqn','bmxht']
    metric_name = "bmx"
    height_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )
    height_data.rename(columns={'bmxht': 'height'},inplace=True)

    # ----------------------------------------------------------------------------------------------------
    # 提取 weight
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    # 使用小写指标
    features = ['seqn', 'bmxwt']
    metric_name = "bmx"
    weight_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )
    weight_data.rename(columns={'bmxwt': 'weight'}, inplace=True)


    # ----------------------------------------------------------------------------------------------------------------------------------------------------
    # 合并数据
    height_data = height_data.reset_index(drop=True)
    weight_data = weight_data.reset_index(drop=True)

    # 按seqn合并所有数据框
    dataframes = [height_data, weight_data]

    BMI_Data = reduce(lambda left, right: pd.merge(left, right, on='seqn', how='outer'), dataframes)

    BMI_Data = sort_by_seqn(BMI_Data)

    # 计算BMI
    try:
        BMI_Data['BMI'] = BMI_Data['weight']/((BMI_Data['height']/100)**2)
    except Exception as e:
        raise RuntimeError(f"An error occurred while calculating BMI: {e}")

    return BMI_Data

def calculation_bmi(feature_data=fit_bmi(), save_path=None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "BMI_results.csv"
    else:
        save_path = save_path + "BMI_results.csv"
    save_result(feature_data, save_path, "BMI calculation")


if __name__ == '__main__':
    calculation_bmi()
