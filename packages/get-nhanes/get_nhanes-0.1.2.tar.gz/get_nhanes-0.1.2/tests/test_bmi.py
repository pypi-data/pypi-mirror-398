import unittest
import os
import pandas as pd
from get_nhanes.coreCalculated.BMICalculated import fit_bmi, calculation_bmi

class TestBMIIntegration(unittest.TestCase):

    def test_fit_bmi_real_data(self):
        """Test BMI calculation using REAL local NHANES data"""
        print("\nRunning integration test with real data...")
        
        try:
            # 1. 真实调用数据提取和计算
            # 注意：这需要你的 config.BASE_PATH 配置正确，且本地有相应年份的数据
            result_df = fit_bmi()
            
            # 2. 验证返回数据
            print(f"Data shape: {result_df.shape}")
            
            self.assertFalse(result_df.empty, "Result DataFrame should not be empty")
            self.assertIn('BMI', result_df.columns, "Output should contain 'BMI' column")
            self.assertIn('height', result_df.columns)
            self.assertIn('weight', result_df.columns)
            
            # 3. 输出数据摘要
            print("BMI Statistics Summary:")
            print(result_df['BMI'].describe())

        except FileNotFoundError as e:
            self.skipTest(f"Skipping integration test: Data file not found. {e}")
        except RuntimeError as e:
            self.fail(f"RuntimeError during execution: {e}")

    def test_calculation_bmi_file_generation(self):
        """Test file generation"""
        output_file = "test_BMI_results.csv"
        
        # 确保清理之前的测试文件
        if os.path.exists(output_file):
            os.remove(output_file)
            
        try:
            # 调用生成函数 (这里我们传入 fit_bmi() 的结果以节省时间，或者让它自己重新算)
            # 为了测试完整流程，我们让它自己算
            # 注意: calculation_bmi 默认会调用 fit_bmi
            
            # 由于 calculation_bmi 内部的 save_path 处理逻辑是: save_path + "BMI_results.csv"
            # 我们需要一点技巧来控制输出文件名，或者干脆测试默认行为
            
            # 我们直接测试数据的保存
            df = fit_bmi()
            calculation_bmi(feature_data=df, save_path="") # save_path="" -> "BMI_results.csv"
            
            expected_file = "BMI_results.csv"
            self.assertTrue(os.path.exists(expected_file), f"Output file {expected_file} should exist")
            
            # 清理
            if os.path.exists(expected_file):
                os.remove(expected_file)
                
        except Exception as e:
            self.fail(f"File generation failed: {e}")

if __name__ == '__main__':
    unittest.main()
