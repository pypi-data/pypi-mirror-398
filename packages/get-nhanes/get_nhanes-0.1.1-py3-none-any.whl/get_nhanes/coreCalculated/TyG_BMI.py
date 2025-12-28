from functools import reduce
import pandas as pd
from get_nhanes.coreCalculated import BMICalculated, TyGCalculated
from get_nhanes.utils import save_result, sort_by_seqn


def fit_tyg_bmi():
    """计算并合并TyG和BMI数据，生成TyG_BMI指标"""
    bmi_data = BMICalculated.fit_bmi()
    tyg_data = TyGCalculated.fit_tyg()

    # 合并BMI和TyG数据
    bmi_data = bmi_data.reset_index(drop=True)
    tyg_data = tyg_data.reset_index(drop=True)

    # 按seqn合并所有数据框
    dataframes = [bmi_data, tyg_data]
    tyg_bmi_data = reduce(lambda left, right: pd.merge(left, right, on='seqn', how='outer'), dataframes)
    tyg_bmi_data = sort_by_seqn(tyg_bmi_data)

    # 计算TYG * BMI
    try:
        tyg_bmi_data["TyG_BMI"] = tyg_bmi_data["TyG"] * tyg_bmi_data["BMI"]
        tyg_bmi_data.drop(columns=['weight', 'height', 'triglycerid', 'fbg'], inplace=True)
    except Exception as e:
        raise RuntimeError(f"计算TyG_BMI时发生错误: {e}")

    return tyg_bmi_data


def calculation_tyg_bmi(feature_data=None, save_path=None):
    """保存TyG_BMI计算结果到CSV文件"""
    if feature_data is None:
        feature_data = fit_tyg_bmi()

    if save_path is None:
        save_path = "TyG_BMI_results.csv"
    else:
        save_path = save_path + "TyG_BMI_results.csv"

    save_result(feature_data, save_path, "TyG_BMI calculation")


if __name__ == '__main__':
    calculation_tyg_bmi()