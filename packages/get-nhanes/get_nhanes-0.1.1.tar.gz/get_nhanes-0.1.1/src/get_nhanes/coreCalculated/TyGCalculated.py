from functools import reduce
import numpy as np
import pandas as pd
from get_nhanes.utils import get_nhanes_data, save_result, sort_by_seqn


def fit_tyg():
    # ----------------------------------------------------------------------------------------------------
    # Extract triglyceride data
    years = ['1999-2000']
    features = ['seqn', 'lbxtr']
    metric_name = "lab13am"
    triglyceride1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )

    years = ['2001-2002', '2003-2004']
    features = ['seqn', 'lbxtr']
    metric_name = "l13am_"
    triglyceride2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )


    years = ['2005-2006', '2007-2008','2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'lbxtr']
    metric_name = "trigly_"
    triglyceride3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )

    # Merge all triglyceride data
    triglyceride_data = pd.concat([triglyceride1, triglyceride2, triglyceride3], axis=0)
    triglyceride_data.rename(columns={'lbxtr': 'triglycerid'}, inplace=True)

    # ----------------------------------------------------------------------------------------------------
    # Extract fasting blood glucose (FBG) data
    years = ['1999-2000']
    features = ['seqn', 'lbxglu']
    metric_name = "lab10am"
    fbg1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )
    fbg1.rename(columns={'lbxglu': 'fbg'}, inplace=True)

    years = ['2001-2002','2003-2004']
    features = ['seqn', 'lbxglu']
    metric_name = "l10am_"
    fbg2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )
    fbg2.rename(columns={'lbxglu': 'fbg'}, inplace=True)

    years = ['2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
    features = ['seqn', 'lbxglu']
    metric_name = "glu"
    fbg3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metric_name,
        merge_output=False
    )
    fbg3.rename(columns={'lbxglu': 'fbg'}, inplace=True)

    # Merge all FBG data
    fbg_data = pd.concat([fbg1, fbg2, fbg3], axis=0)

    # ----------------------------------------------------------------------------------------------------
    # Merge FBG and triglyceride data
    triglyceride_data = triglyceride_data.reset_index(drop=True)
    fbg_data = fbg_data.reset_index(drop=True)

    # Merge all dataframes by 'seqn'
    dataframes = [triglyceride_data, fbg_data]
    tyg_features_data = reduce(lambda left, right: pd.merge(left, right, on='seqn', how='outer'), dataframes)
    tyg_features_data = sort_by_seqn(tyg_features_data)

    # Calculate TyG index
    try:
        tyg_features_data['TyG'] = np.log(tyg_features_data['triglycerid'] * tyg_features_data['fbg'] / 2)
    except Exception as e:
        raise RuntimeError(f"An error occurred while calculating TyG: {e}")
    return tyg_features_data


def calculation_tyg(feature_data=None, save_path=None):
    """Save TyG calculation results to a CSV file."""
    if feature_data is None:
        feature_data = fit_tyg()
    if save_path is None:
        save_path = "TyG_results.csv"
    else:
        save_path = save_path + "TyG_results.csv"
    save_result(feature_data, save_path, "TyG calculation")


if __name__ == '__main__':
    calculation_tyg()