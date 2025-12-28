from functools import reduce
import pandas as pd
from get_nhanes.utils import get_nhanes_data, save_result, sort_by_seqn
from get_nhanes.coreCalculated import TyG_BMI


def fit_vai():
    # ----------------------------------------------------------------------------------------------------
    # 提取 WC
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
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
    # 提取 Triglyceride mmol/L
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']

    years = ['1999-2000']
    # 使用小写指标
    features = ['seqn', 'lbdstrsi']
    metricName = "lab18"
    TG1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    years = ['2001-2002','2003-2004']
    # 使用小写指标
    features = ['seqn', 'lbdstrsi']
    metricName = "l40_"
    TG2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    years = ['2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    # 使用小写指标
    features = ['seqn', 'lbdstrsi']
    metricName = "biopro_"
    TG3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )

    # 合并所有triglyceride数据
    TG_data = pd.concat([TG1, TG2, TG3], axis=0)

    TG_data.rename(columns={'lbdstrsi': 'Triglyceride'}, inplace=True)

    # ----------------------------------------------------------------------------------------------------
    # 提取 HDL-C mmol/L
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000']
    # 使用小写指标
    features = ['seqn', 'lbdhdlsi']
    metricName = "lab13"
    HDL1 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    HDL1.rename(columns={'lbdhdlsi': 'HDL'}, inplace=True)

    years = ['2001-2002']
    # 使用小写指标
    features = ['seqn', 'lbdhdlsi']
    metricName = "l13_b"
    HDL2 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    HDL2.rename(columns={'lbdhdlsi': 'HDL'}, inplace=True)

    years = ['2003-2004']
    # 使用小写指标
    features = ['seqn', 'lbdhddsi']
    metricName = "l13"
    HDL3 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    HDL3.rename(columns={'lbdhddsi': 'HDL'}, inplace=True)

    years = ['2005-2006','2007-2008','2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    # 使用小写指标
    features = ['seqn', 'lbdhddsi']
    metricName = "hdl_"
    HDL4 = get_nhanes_data(
        years=years,
        features=features,
        metric_prefix=metricName,
        merge_output=False
    )
    HDL4.rename(columns={'lbdhddsi': 'HDL'}, inplace=True)

    # 合并所有triglyceride数据
    HDL_data = pd.concat([HDL1, HDL2, HDL3,HDL4], axis=0)

    # ----------------------------------------------------------------------------------------------------
    # 提取 Gender
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    years = ['1999-2000', '2001-2002', '2003-2004', '2005-2006', '2007-2008', '2009-2010', '2011-2012', '2013-2014', '2015-2016', '2017-2018']
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
    # 提取 BMI
    # ['1999-2000','2001-2002','2003-2004','2005-2006','2007-2008', '2009-2010', '2011-2012', '2013-2014','2015-2016','2017-2018']
    BMI_data = TyG_BMI.fit_tyg_bmi()
    BMI_data.drop(columns=['TyG_BMI','TyG'], inplace=True)

    # ----------------------------------------------------------------------------------------------------
    # 合并所有数据
    # 合并fbg和triglyceride
    WC_data = WC_data.reset_index(drop=True)
    TG_data = TG_data.reset_index(drop=True)
    HDL_data = HDL_data.reset_index(drop=True)
    gender_data = gender_data.reset_index(drop=True)
    BMI_data = BMI_data.reset_index(drop=True)


    # 按seqn合并所有数据框
    dataframes = [WC_data,TG_data,HDL_data,gender_data,BMI_data]
    VAIfeatures_Data = reduce(lambda left, right: pd.merge(left, right, on='seqn', how='outer'), dataframes)
    VAIfeatures_Data = sort_by_seqn(VAIfeatures_Data)

    # gender,HDL,Triglyceride,waist,BMI
    try:
        # 确保所有字段存在
        required_columns = ['gender', 'HDL', 'Triglyceride', 'waist', 'BMI']
        if not all(col in VAIfeatures_Data.columns for col in required_columns):
            missing = [col for col in required_columns if col not in VAIfeatures_Data.columns]
            raise KeyError(f"Missing columns: {missing}")

        # 使用 apply 逐行计算
        def calculate_vai(row):
            try:
                if row['gender'] == 1:  # 男性
                    return (row['waist'] / (39.68 + 1.88 * row['BMI'])) * \
                        (row['Triglyceride'] / 1.33) * \
                        (1 / row['HDL'])
                elif row['gender'] == 2:  # 女性
                    return (row['waist'] / (36.58 + 1.89 * row['BMI'])) * \
                        (row['Triglyceride'] / 0.81) * \
                        (1 / row['HDL'])
                else:  # 非法性别值
                    return None
            except ZeroDivisionError:
                return None  # 处理除零错误
            except:
                return None  # 其他错误静默处理

        # 应用计算函数
        VAIfeatures_Data["VAI"] = VAIfeatures_Data.apply(calculate_vai, axis=1)

    except Exception as e:
        raise RuntimeError(f"An error occurred while calculating VAI: {e}")

    return VAIfeatures_Data.reset_index(drop=True)


def calculation_vai(feature_data = fit_vai(), save_path=None):
    # 如果 save_path 为空，则保存到当前路径
    if save_path is None:
        save_path = "VAI_results.csv"
    else:
        save_path = save_path + "VAI_results.csv"
    save_result(feature_data, save_path, "VAI calculation")

if __name__ == '__main__':
    calculation_vai()

