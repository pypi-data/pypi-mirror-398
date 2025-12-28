from functools import reduce
import numpy as np
import pandas as pd
from get_nhanes.utils import get_nhanes_data, save_result, sort_by_seqn
from get_nhanes.coreCalculated import VAICalculated


def fit_egfr():

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

    # ----------------------------------------------------------------------------------------------------
    # 提取 Gender
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000', '2001-2002', '2003-2004', '2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014',
             '2015-2016', '2017-2018']
    # 使用小写指标
    features = ['seqn', 'riagendr']
    metricName = "demo"
    gender_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    gender_data.rename(columns={'riagendr': 'gender'}, inplace=True)

    # ----------------------------------------------------------------------------------------------------
    # 提取Scr
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    features = ['seqn', 'lbxscr']  #mg/dL
    metricName = "lab18"
    Scr1_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    Scr1_data.rename(columns={'lbxscr': 'Scr'}, inplace=True)

    years = ['2001-2002']
    features = ['seqn', 'lbdscr'] #mg/dL
    metricName = "l40_b"
    Scr2_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    Scr2_data.rename(columns={'lbdscr': 'Scr'}, inplace=True)

    years = ['2003-2004']
    features = ['seqn', 'lbxscr']
    metricName = "l40_c"
    Scr3_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    Scr3_data.rename(columns={'lbxscr': 'Scr'}, inplace=True)

    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    features = ['seqn', 'lbxscr'] #mg/dL
    metricName = "biopro_"
    Scr4_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    Scr4_data.rename(columns={'lbxscr': 'Scr'}, inplace=True)

    # 合并所有Src数据
    Scr_data = pd.concat([Scr1_data, Scr2_data, Scr3_data,Scr4_data], axis=0)

    # ----------------------------------------------------------------------------------------------------
    # 合并所有数据
    age_data = age_data.reset_index(drop=True)
    gender_data = gender_data.reset_index(drop=True)
    Scr_data = Scr_data.reset_index(drop=True)

    # 按seqn合并所有数据框
    dataframes = [age_data, gender_data, Scr_data]

    eGFRfeatures_Data = reduce(lambda left, right: pd.merge(left, right, on='seqn', how='outer'), dataframes)
    eGFRfeatures_Data = sort_by_seqn(eGFRfeatures_Data)

    # ----------------------------------------------------------------------------------------------------
    # 定义eGFR计算函数
    def calculate_egfr(row):
        scr = row['Scr']
        age = row['age']
        gender = row['gender']

        # 性别编码：1为男性，2为女性
        if gender == 2:  # 女性
            if scr <= 0.7:
                egfr = 142 * (scr / 0.7) ** (-0.241) * (0.9938 ** age) * 1.012
            else:
                egfr = 142 * (scr / 0.7) ** (-1.200) * (0.9938 ** age) * 1.012
        elif gender == 1:  # 男性
            if scr <= 0.9:
                egfr = 142 * (scr / 0.9) ** (-0.302) * (0.9938 ** age)
            else:
                egfr = 142 * (scr / 0.9) ** (-1.200) * (0.9938 ** age)
        else:
            # 如果性别未知，返回NaN
            egfr = np.nan

        return egfr

    try:
        # 应用函数计算eGFR并添加到DataFrame
        eGFRfeatures_Data['eGFR'] = eGFRfeatures_Data.apply(calculate_egfr, axis=1)
    except Exception as e:
        raise RuntimeError(f"计算eGFR时发生错误: {e}")
        # 返回DataFrame（可选）

    return eGFRfeatures_Data

def calculation_egfr(feature_data=fit_egfr(), save_path=None):

    if save_path is None:
        save_path = "eGFR_results.csv"
    else:
        save_path = save_path + "eGFR_results.csv"
    save_result(feature_data, save_path, "eGFR calculation")


if __name__ == '__main__':
    calculation_egfr()

