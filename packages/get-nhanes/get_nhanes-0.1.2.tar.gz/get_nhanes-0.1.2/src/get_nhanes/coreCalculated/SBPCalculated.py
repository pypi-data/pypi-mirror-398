

import numpy as np
import pandas as pd

from get_nhanes.utils import get_nhanes_data, save_result, sort_by_seqn

def fit_sbp():
    # SBP
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000','2001-2002']
    # 使用小写指标
    features = ['seqn', 'bpxsar','bpxdar']
    metricName = "bpx"
    sbp1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    sbp1.rename(columns={'bpxsar': 'mSBP',
                         'bpxdar': 'mDBP'}, inplace=True)


    years = ['2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    features = ['seqn', 'bpxsy1','bpxsy2','bpxsy3','bpxsy4','bpxdi1','bpxdi2','bpxdi3','bpxdi4']
    metricName = "bpx"
    sbp2 = get_nhanes_data(years=years, features=features, metric_prefix=metricName, merge_output=False)
    # 自定义平均值计算函数
    def custom_mean(row):
        valid_values = row[row.notnull()]
        if len(valid_values) == 0:
            return np.nan  # 如果没有有效值，返回 NaN
        elif len(valid_values) == 1:
            return valid_values.iloc[0]  # 如果只有一个有效值，返回该值
        else:
            return valid_values.mean()  # 否则返回平均值

    # 计算 BPXSY 的平均值并创建 mSBP 列
    sbp2['mSBP'] = sbp2.filter(like='bpxsy').apply(custom_mean, axis=1)

    # 计算 BPXDI 的平均值并创建 mDBP 列
    sbp2['mDBP'] = sbp2.filter(like='bpxdi').apply(custom_mean, axis=1)
    
    sbp2 = sbp2.drop(columns=['bpxsy1','bpxsy2','bpxsy3','bpxsy4','bpxdi1','bpxdi2','bpxdi3','bpxdi4'])

    sbp_data = pd.concat([sbp1, sbp2], axis=0)
    
    return sort_by_seqn(sbp_data)

def calculation_sbp(feature_data = fit_sbp(), save_path = None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "SBP_results.csv"
    else:
        save_path = save_path + "SBP_results.csv"
    save_result(feature_data, save_path, "SBP calculation")


if __name__ == '__main__':
    calculation_sbp()