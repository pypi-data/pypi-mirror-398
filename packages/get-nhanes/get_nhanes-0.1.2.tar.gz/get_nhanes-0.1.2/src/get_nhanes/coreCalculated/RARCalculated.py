from functools import reduce
import pandas as pd
from get_nhanes.utils import get_nhanes_data, save_result, sort_by_seqn

def fit_rar():    # ----------------------------------------------------------------------------------------------------
    # 提取RDW
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    features = ['seqn', 'lbxrdw']
    metricName = "lab25"
    rdw1_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    rdw1_data.rename(columns={'lbxrdw': 'rdw'}, inplace=True)

    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['2001-2002','2003-2004']
    features = ['seqn', 'lbxrdw']
    metricName = "l25_"
    rdw2_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    rdw2_data.rename(columns={'lbxrdw': 'rdw'}, inplace=True)

    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    features = ['seqn', 'lbxrdw']
    metricName = "cbc_"
    rdw3_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    rdw3_data.rename(columns={'lbxrdw': 'rdw'}, inplace=True)

    # 合并所有RDW数据
    rdw_data = pd.concat([rdw1_data, rdw2_data, rdw3_data], axis=0)

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
    years = ['2001-2002','2003-2004']
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
    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
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
    # 合并所有数据
    rdw_data = rdw_data.reset_index(drop=True)
    alb_data = alb_data.reset_index(drop=True)

    # 按seqn合并所有数据框
    dataframes = [rdw_data, alb_data]

    RARfeatures_Data = reduce(lambda left, right: pd.merge(left, right, on='seqn', how='outer'), dataframes)
    RARfeatures_Data = sort_by_seqn(RARfeatures_Data)



    try:
        RARfeatures_Data['RAR'] = RARfeatures_Data['rdw'] / RARfeatures_Data['alb']
    except Exception as e:
        raise RuntimeError(f"An error occurred while calculating TyG: {e}")
    return RARfeatures_Data

def calculation_rar(feature_data = fit_rar(), save_path = None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "RAR_results.csv"
    else:
        save_path = save_path + "RAR_results.csv"
    save_result(feature_data, save_path, "RAR calculation")

if __name__ == '__main__':
    calculation_rar()