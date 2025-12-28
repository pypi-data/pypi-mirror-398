import os # 从上级目录导入配置模块

import pandas as pd

from get_nhanes import config


# 输入选择的年份,然后输出数据

def getMortality(
        years,  # NHANES调查年份列表（如["1999-2000", "2001-2002"]）
        features=None,  # 可选：指定需要提取的列名列表
        output_dir=None,  # 可选：输出目录路径
        save_each_file=False,  # 可选：是否保存每个单独
        merge_output = False
):
    # 从配置中获取基础路径
    try:
        basepath = config.BASE_PATH  # 尝试从配置文件加载基础路径
    except RuntimeError as e:
        raise RuntimeError("NHANES基础路径未配置，请先调用config.set_base_path()") from e
    except ImportError:
        raise RuntimeError("配置模块不可用，请确保config.py存在") from None

    all_data = []

    # 设置输出目录（默认为当前目录下的nhanes_output文件夹）
    output_dir = output_dir or os.path.join(os.getcwd(), "nhanes_output")
    if save_each_file:
        os.makedirs(output_dir, exist_ok=True)  # 如果需要保存单独文件则创建目录

    for year in years:
        # 拼出完整路径
        # x = "E:\\NHANES_DATA\\2024-08-18完整版\\01_NHANES\\mort\\tsv\\nhanes_1999_2000_mort_2019_public.tsv"
        file_path = os.path.join(basepath, "mort" ,"tsv" , "nhanes_" + year.replace("-","_") + "_mort"+".tsv")
        try:
            df = pd.read_csv(file_path, sep="\t", low_memory=False)  # 读取TSV文件

            # 列验证
            if features is None:  # 如果未指定features，则选择所有列
                if "seqn" not in df.columns:  # 必须包含seqn列
                    continue
                selected_columns = df.columns.tolist()
            else:  # 检查指定的features是否存在
                missing = [col for col in features if col not in df.columns]
                if missing:  # 跳过缺失关键列的文件
                    continue
                selected_columns = features

            # 保存单独文件（如果需要）
            if save_each_file:
                output_name = f"{year}_mort.csv"  # 生成输出文件名
                df.loc[:, 'seqn'] = df['seqn'].astype(str) + "_" + year.split("-")[0]
                df[selected_columns].to_csv(
                    os.path.join(output_dir, output_name), index=False  # 保存为CSV
                )

            # 确保'seqn'列存在且year是字符串
            if 'seqn' in selected_columns and isinstance(year, str):
                # 将处理后的数据加入列表
                all_data.append(df[selected_columns])

            else:
                print("错误: 选择的列中缺少'seqn'或year不是字符串")
        except Exception as e:
            print(f"数据处理失败: {file_path} - {str(e)}")

        # # 合并最终数据
        # if all_data:
        #     merged_df = pd.concat(all_data, ignore_index=True)  # 合并所有数据框
        #     return merged_df  # 返回合并后的DataFrame

        if merge_output:
            merged_df = pd.concat(all_data, ignore_index=True)
            year_range = (  # 生成年份范围字符串（如"1999-2002"）
                f"{min(y.split('-')[0] for y in years)}-"
                f"{max(y.split('-')[-1] for y in years)}"
            )
            merged_df.to_csv(year_range + "_mort.csv", index = False)
    return pd.DataFrame()


if __name__ == '__main__':
    years = ["1999-2000",'2001-2002','2003-2004','2005-2006',
             '2007-2008','2009-2010','2011-2012','2013-2014',
             '2015-2016','2017-2018']
    getMortality(years,save_each_file=True,merge_output=True)