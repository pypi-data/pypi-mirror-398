
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


import numpy as np
import pandas as pd
from functools import reduce
from get_nhanes import get_nhanes_data


def get_weight():

    # 1999-2000  2001-2002 四年权重 -> 换算到20年权重：2/10
    years = ['1999-2000', '2001-2002']
    features = ['seqn', 'wtmec4yr']
    metricName = "demo"
    weight4_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    if not weight4_data.empty:
        weight4_data = weight4_data[['seqn', 'wtmec4yr']].copy()
        weight4_data['wtmec20yr'] = pd.to_numeric(weight4_data['wtmec4yr'], errors='coerce') * (2.0 / 10.0)
        weight4_data = weight4_data[['seqn', 'wtmec20yr']]
    else:
        weight4_data = pd.DataFrame(columns=['seqn', 'wtmec20yr'])

    # 2003-2018  两年权重 -> 换算到20年权重：1/10
    years = ['2003-2004', '2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'wtmec2yr']
    metricName = "demo"
    weight2_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    if not weight2_data.empty:
        weight2_data = weight2_data[['seqn', 'wtmec2yr']].copy()
        weight2_data['wtmec20yr'] = pd.to_numeric(weight2_data['wtmec2yr'], errors='coerce') * (1.0 / 10.0)
        weight2_data = weight2_data[['seqn', 'wtmec20yr']]
    else:
        weight2_data = pd.DataFrame(columns=['seqn', 'wtmec20yr'])

    # 合并，并只保留 seqn 与 wtmec20yr（小写）
    result = pd.concat([weight4_data, weight2_data], axis=0, ignore_index=True)

    return result


def calculation_weight(feature_data=get_weight(), save_path=None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "weight_results.csv"
    else:
        save_path = save_path + "weight_results.csv"
    feature_data.to_csv(save_path, index=False)


if __name__ == '__main__':
    calculation_weight()
