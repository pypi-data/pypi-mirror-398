import os
import logging
from typing import List, Optional
import pandas as pd
from .. import config


# Monkeypatch pandas.DataFrame.to_csv to add logging
if not hasattr(pd.DataFrame, '_original_to_csv'):
    pd.DataFrame._original_to_csv = pd.DataFrame.to_csv

def to_csv_with_logging(self, path_or_buf=None, *args, **kwargs):
    # Extract custom argument
    task_name = kwargs.pop('task_name', None)
    
    # Call original method
    result = self._original_to_csv(path_or_buf, *args, **kwargs)
    
    # Log success if it's a file path
    if path_or_buf and isinstance(path_or_buf, str):
        if task_name:
            print(f"{task_name} complete. Saved to: {path_or_buf}")
        else:
            print(f"Calculation complete. Saved to: {path_or_buf}")
            
    return result

pd.DataFrame.to_csv = to_csv_with_logging


def save_result(df: pd.DataFrame, save_path: str, task_name: str = "Calculation") -> None:
    """
    Save DataFrame to CSV and print a success message.
    
    Args:
        df: DataFrame to save
        save_path: Path to save the CSV file
        task_name: Name of the task for the success message (default: "Calculation")
    """
    try:
        # Pass task_name to the patched to_csv
        df.to_csv(save_path, index=False, task_name=task_name)
    except Exception as e:
        logging.error(f"Failed to save result to {save_path}: {e}")
        raise



def sort_by_seqn(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort DataFrame by the numeric part of 'seqn' column.
    seqn format is expected to be "number_year" (e.g., "100000_2017").
    
    Args:
        df: DataFrame containing 'seqn' column.
        
    Returns:
        pd.DataFrame: Sorted DataFrame.
    """
    if df.empty or 'seqn' not in df.columns:
        return df

    try:
        # Create a temporary column for sorting
        # Extract the part before '_' and convert to int
        df['seqn_num'] = df['seqn'].astype(str).apply(lambda x: int(x.split('_')[0]) if '_' in x else 0)
        df.sort_values(by='seqn_num', inplace=True)
        df.drop(columns=['seqn_num'], inplace=True)
    except Exception as e:
        logging.warning(f"Could not sort by numeric seqn: {e}. Fallback to string sort.")
        # Fallback to string sort
        df.sort_values(by='seqn', inplace=True)
    
    return df


def get_nhanes_data(
    years: List[str],
    metric_prefix: str,
    features: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
    merge_output: bool = False,
    save_each_file: bool = False,
    strict_features: bool = True,
) -> pd.DataFrame:
    """
    Extract and merge specified metric data from NHANES dataset.

    Args:
        years: List of years to process (e.g., ['2007-2008', '2009-2010'])
        metric_prefix: Target metric filename prefix (e.g., 'DEET')
        features: Features to extract (None for all columns, must include 'seqn')
        output_dir: Output directory (default: ./nhanes_output)
        merge_output: Whether to merge all files and save (default: False)
        save_each_file: Whether to save individual files (default: False)
        strict_features: If True, skip files missing specified features. If False, fill missing with NaN.

    Returns:
        pd.DataFrame: Merged dataset

    Raises:
        ValueError: When parameter validation fails
        FileNotFoundError: When base path doesn't exist
        RuntimeError: When base directory is not configured
    """
    # Get base directory from config
    try:
        basepath = config.BASE_PATH  # 自动从配置文件加载或使用已设置的路径
    except RuntimeError as e:
        raise RuntimeError("NHANES基础路径未配置，请先调用config.set_base_path()") from e
    except ImportError:
        raise RuntimeError("配置模块不可用，请确保config.py存在") from None
    if features is not None:
        # if not features:
        #     raise ValueError("Features list cannot be empty.")
        if "seqn" not in features:
            raise ValueError("Features must include 'seqn'.")
    if not os.path.exists(basepath):
        raise FileNotFoundError(f"Base path not found: {basepath}")
    if not years:
        raise ValueError("Years list cannot be empty.")

    # Set output directory
    output_dir = output_dir or os.path.join(os.getcwd(), "nhanes_output")
    if save_each_file or merge_output:
        os.makedirs(output_dir, exist_ok=True)

    # Initialize data storage
    all_data = []
    search_dirs = [
        "Laboratory",
        "Questionnaire",
        "Examination",
        "Dietary",
        "Demographics",
    ]
    matched_files = []

    # File search logic
    for year in years:
        for data_dir in search_dirs:
            current_path = os.path.join(basepath, year, data_dir, "tsv")
            if not os.path.isdir(current_path):
                continue

            try:
                files = [
                    f
                    for f in os.listdir(current_path)
                    if f.startswith(metric_prefix) and f.endswith(".tsv")
                ]
                matched_files.extend(
                    [(year, data_dir, os.path.join(current_path, f)) for f in files]
                )
            except Exception as e:
                logging.error(f"File scanning error: {current_path} - {str(e)}")

    # Data processing logic
    for year, data_dir, file_path in matched_files:
        try:
            df = pd.read_csv(file_path, sep="\t", low_memory=False)
            # 新增: 确保seqn是整数类型
            if 'seqn' in df.columns:
                # 先转换为数值类型处理NaN
                df['seqn'] = pd.to_numeric(df['seqn'], errors='coerce')
                # 填充缺失值（使用-1标记缺失）
                df['seqn'] = df['seqn'].fillna(-1)
                # 转为整数
                df['seqn'] = df['seqn'].astype('int64')

            # Column validation
            if features is None:
                if "seqn" not in df.columns:
                    continue
                selected_columns = df.columns.tolist()
            else:
                missing = [col for col in features if col not in df.columns]
                if missing:
                    if strict_features:
                        logging.debug(f"Skipping {file_path}: Missing columns {missing}")
                        continue
                    else:
                        # Fill missing columns with NaN
                        for col in missing:
                            df[col] = pd.NA
                selected_columns = features

            # Save individual file
            if save_each_file:
                output_name = f"{year}_{data_dir}_{metric_prefix}.csv"
                save_path = os.path.join(output_dir, output_name)
                save_result(df[selected_columns], save_path, f"Processing {year} {data_dir}")

            # 确保 'seqn' 列存在且 year 是字符串
            if 'seqn' in selected_columns and isinstance(year, str):
                # 直接操作原始 DataFrame 的 'seqn' 列
                df['seqn'] = df['seqn'].astype(str) + "_" + year.split("-")[0]
                # Merge data
                all_data.append(df[selected_columns])
                # print(f"Processed: {year} - {os.path.basename(file_path)}")
            else:
                logging.error("Error: 'seqn' column not found in selected_columns or year is not a string")

        except Exception as e:
            logging.error(f"Data processing failed: {file_path} - {str(e)}")

    # Merge final data
    if all_data:
        merged_df = pd.concat(all_data, ignore_index=True)
        if merge_output:
            year_range = (
                f"{min(y.split('-')[0] for y in years)}-"
                f"{max(y.split('-')[-1] for y in years)}"
            )
            output_filename = f"merged_{metric_prefix}_{year_range}.csv"
            save_path = os.path.join(output_dir, output_filename)
            save_result(merged_df, save_path, f"Merging {metric_prefix}")
        return merged_df
    return pd.DataFrame()