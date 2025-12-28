# 统一 NHANES 1999-2018 的种族/族裔变量：
import numpy as np
import pandas as pd


def race_combine(demo_data):
    """
    统一 NHANES 1999-2018 的种族/族裔变量：
    
    根据NHANES官方文档：
    - 1999-2010: 使用 ridreth1（标准分析变量）
    - 2011+: 使用 ridreth3（新增亚裔分类）
    
    优先级：ridreth3 > ridreth1
    
    统一编码 race（1~6）：
        1: Mexican American (墨西哥裔美国人)
        2: Other Hispanic (其他西班牙裔)
        3: Non-Hispanic White (非西班牙裔白人)
        4: Non-Hispanic Black (非西班牙裔黑人)
        5: Non-Hispanic Asian (非西班牙裔亚裔，仅2011+)
        6: Other/Multiracial (其他/多种族)
    
    Args:
        demo_data: 包含人口统计学数据的DataFrame
        
    Returns:
        处理后的DataFrame，包含统一的race变量
        
    Raises:
        ValueError: 如果没有找到任何种族变量
    """
    # 检查输入
    if demo_data is None or demo_data.empty:
        raise ValueError("输入数据为空")
    
    # 检查可用的种族变量
    available_race_vars = []
    for var in ['ridreth3', 'ridreth1']:
        if var in demo_data.columns and not demo_data[var].isna().all():
            available_race_vars.append(var)
    
    if not available_race_vars:
        raise ValueError("未找到有效的种族变量 (ridreth1, ridreth3)")
    
    # 1️⃣ 创建统一的race变量，处理混合数据
    demo_data['race'] = np.nan  # 初始化为NaN
    
    # 2️⃣ 优先使用ridreth3（如果存在且非空）
    if 'ridreth3' in demo_data.columns:
        # 对于有ridreth3值的行，使用ridreth3映射
        ridreth3_mask = demo_data['ridreth3'].notna()
        
        # RIDRETH3映射: 1,2,3,4,6,7 -> 1,2,3,4,5,6
        ridreth3_conditions = [
            demo_data['ridreth3'] == 1,  # Mexican American
            demo_data['ridreth3'] == 2,  # Other Hispanic
            demo_data['ridreth3'] == 3,  # Non-Hispanic White
            demo_data['ridreth3'] == 4,  # Non-Hispanic Black
            demo_data['ridreth3'] == 6,  # Non-Hispanic Asian
            demo_data['ridreth3'] == 7,  # Other/Multiracial
        ]
        ridreth3_choices = [1, 2, 3, 4, 5, 6]
        
        # 对所有数据应用映射，然后只保留有ridreth3值的行的结果
        ridreth3_race = np.select(ridreth3_conditions, ridreth3_choices, default=np.nan)
        demo_data.loc[ridreth3_mask, 'race'] = ridreth3_race[ridreth3_mask]
    
    # 3️⃣ 对于没有ridreth3值的行，使用ridreth1映射
    if 'ridreth1' in demo_data.columns:
        # 找到还没有race值的行（ridreth3为空或不存在的行）
        ridreth1_mask = demo_data['ridreth1'].notna() & demo_data['race'].isna()
        
        # RIDRETH1映射: 1,2,3,4,5 -> 1,2,3,4,6
        ridreth1_conditions = [
            demo_data['ridreth1'] == 1,  # Mexican American
            demo_data['ridreth1'] == 2,  # Other Hispanic
            demo_data['ridreth1'] == 3,  # Non-Hispanic White
            demo_data['ridreth1'] == 4,  # Non-Hispanic Black
            demo_data['ridreth1'] == 5,  # Other/Multiracial
        ]
        ridreth1_choices = [1, 2, 3, 4, 6]  # 注意：ridreth1的第5类映射为6
        
        # 对所有数据应用映射，然后只保留需要的行的结果
        ridreth1_race = np.select(ridreth1_conditions, ridreth1_choices, default=np.nan)
        demo_data.loc[ridreth1_mask, 'race'] = ridreth1_race[ridreth1_mask]
    
    # 4️⃣ 清理所有种族相关列，只保留整理后的race列
    cols_to_drop = []
    
    # 删除原始种族列
    if 'ridreth1' in demo_data.columns:
        cols_to_drop.append('ridreth1')
    if 'ridreth3' in demo_data.columns:
        cols_to_drop.append('ridreth3')
    
    demo_data = demo_data.drop(columns=cols_to_drop)

    
    return demo_data