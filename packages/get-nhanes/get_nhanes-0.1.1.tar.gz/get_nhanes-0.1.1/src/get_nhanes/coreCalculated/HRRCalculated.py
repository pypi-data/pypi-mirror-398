from functools import reduce
import pandas as pd
from get_nhanes.utils import get_nhanes_data, save_result, sort_by_seqn

def fit_hrr():
    # ----------------------------------------------------------------------------------------------------
    # rdw
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
    years = ['2001-2002', '2003-2004']
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
    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'lbxrdw']
    metricName = "cbc_"
    rdw3_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    rdw3_data.rename(columns={'lbxrdw': 'rdw'}, inplace=True)

    rdw_data = pd.concat([rdw1_data, rdw2_data, rdw3_data], axis=0)

    # ----------------------------------------------------------------------------------------------------
    # hct
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    features = ['seqn', 'lbxhct']
    metricName = "lab25"
    hct1_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    hct1_data.rename(columns={'lbxhct': 'hct'}, inplace=True)

    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['2001-2002', '2003-2004']
    features = ['seqn', 'lbxhct']
    metricName = "l25_"
    hct2_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    hct2_data.rename(columns={'lbxhct': 'hct'}, inplace=True)

    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'lbxhct']
    metricName = "cbc_"
    hct3_data = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    hct3_data.rename(columns={'lbxhct': 'hct'}, inplace=True)

    hct_data = pd.concat([hct1_data, hct2_data, hct3_data], axis=0)

    # ----------------------------------------------------------------------------------------------------
    # 合并所有数据
    rdw_data = rdw_data.reset_index(drop=True)
    hct_data = hct_data.reset_index(drop=True)

    # 按seqn合并所有数据框
    dataframes = [rdw_data, hct_data]

    HRRfeatures_Data = reduce(lambda left, right: pd.merge(left, right, on='seqn', how='outer'), dataframes)
    HRRfeatures_Data = sort_by_seqn(HRRfeatures_Data)

    # ----------------------------------------------------------------------------------------------------
    # 计算HRR
    try:
        HRRfeatures_Data['HRR'] = HRRfeatures_Data['rdw'] / HRRfeatures_Data['hct']
    except Exception as e:
        raise RuntimeError(f"An error occurred while calculating TyG: {e}")

    return HRRfeatures_Data


def calculation_hrr(feature_data = fit_hrr(), save_path = None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "HRR_results.csv"
    else:
        save_path = save_path + "HRR_results.csv"
    save_result(feature_data, save_path, "HRR calculation")

if __name__ == '__main__':
    calculation_hrr()