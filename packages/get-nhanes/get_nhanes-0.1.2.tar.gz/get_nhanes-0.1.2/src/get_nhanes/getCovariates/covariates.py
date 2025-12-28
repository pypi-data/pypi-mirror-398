
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


import numpy as np
import pandas as pd
from functools import reduce
from get_nhanes import get_nhanes_data
from get_nhanes.utils import save_result,race_combine


def fit_covariates():

    years = ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010']
    # 年龄 性别 种族1 教育3 教育2 婚姻 收入
    features = ['seqn','ridageyr','riagendr','ridreth1','dmdeduc3','dmdeduc2','dmdmartl','indfmpir']
    metricName = "demo"
    demo_data1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )


    years = ['2011-2012', '2013-2014','2015-2016', '2017-2018']
    # 年龄 性别 种族1 教育3 教育2 婚姻 收入
    features = ['seqn', 'ridageyr', 'riagendr','ridreth1','ridreth3', 'dmdeduc3', 'dmdeduc2', 'dmdmartl', 'indfmpir']
    metricName = "demo"
    demo_data2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    # 合并所有MC数据
    demo_data = pd.concat([demo_data1, demo_data2], axis=0)
    demo_data = race_combine(demo_data)


    # SMQ 抽烟 SMQ020 - 一生中至少吸过 100 支香烟
    years = ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010','2011-2012', '2013-2014','2015-2016', '2017-2018']
    features = ['seqn','smq020']
    metricName = "smq"
    smq_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    # ALQ 饮酒 ALQ130 过去12个月平均每日饮酒量
    # 0.0:ALQ130 ≤ 2(适量饮酒，男女通用)
    # 1.0:ALQ130 > 2
    # 2.0:ALQ130 == 77 or ALQ130 == 99 (未知)
    years = ['1999-2000', '2001-2002', '2003-2004', '2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014',
             '2015-2016', '2017-2018']
    features = ['seqn', 'alq130']
    metricName = "alq"
    alq_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    alq_data['alq130'] = alq_data['alq130'].apply(
        lambda x: 2.0 if x == 77 or x == 99 else (0.0 if x <= 2 else 1.0))

    dataframes = [demo_data, smq_data, alq_data]

    convariates_data = reduce(lambda left, right: pd.merge(left, right, on='seqn'), dataframes)


    return convariates_data

def calculation_covariates(feature_data=fit_covariates(), save_path=None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "covariates_results.csv"
    else:
        save_path = save_path + "covariates_results.csv"
    save_result(feature_data, save_path, "Covariates calculation")




if __name__ == '__main__':
    calculation_covariates()
