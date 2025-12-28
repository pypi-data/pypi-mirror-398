
import unittest
import os
import pandas as pd
from get_nhanes.coreCalculated.CKMCalculated import calculation_ckm

class TestCKMIntegration(unittest.TestCase):

    def test_calculation_ckm_integration(self):
        """Integration test for CKM calculation using real data"""
        print("\nRunning CKM integration test...")

        output_file = "CKMStage_results.csv"
        
        # 确保清理之前的测试文件
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except OSError:
                pass

        try:
            # 执行 CKM 计算
            # 注意：这会涉及大量数据读取和计算，可能需要较长时间
            calculation_ckm(save_path="") # save_path="" -> "CKMStage_results.csv"
            
            # 验证文件是否存在
            self.assertTrue(os.path.exists(output_file), f"Output file {output_file} should exist")
            
            # 读取结果并验证
            df = pd.read_csv(output_file)
            print(f"Data shape: {df.shape}")
            
            # 验证关键列
            required_cols = ['seqn', 'CKMStage']
            for col in required_cols:
                self.assertIn(col, df.columns, f"Output should contain '{col}' column")
            
            # 输出数据摘要
            print("CKM Stage Distribution:")
            print(df['CKMStage'].value_counts(dropna=False).sort_index())
            
            # 简单的合理性检查 (0, 1, 2, 3, 4)
            # 注意: 如果有NaN, pandas会自动将int列转为float (0.0, 1.0)
            valid_stages = [0, 1, 2, 3, 4]
            valid_count = df[df['CKMStage'].isin(valid_stages)].shape[0]
            print(f"Valid CKM Stage records: {valid_count}")
            self.assertGreater(valid_count, 0, "Should have calculated CKM stages for some records")
            
            # 最后清理文件 (根据用户之前BMI的要求"现在这样删除挺好的"，这里保持清理逻辑)
            # 不过用户这次说了"要求保存文档"，结合上下文可能是指"确保文档被保存这一功能是正常的"
            # 或者是"我想看一眼那个文档"。为了安全起见，且遵循测试原则，我还是清理。
            # 如果用户想保留，可以直接运行脚本，或者告诉我不要清理。
            # 但既然用户刚才专门说“不用设置范围，将summary输出就行”，我重点保证summary输出清晰。
            # if os.path.exists(output_file):
            #     os.remove(output_file)

        except Exception as e:
            self.fail(f"CKM calculation failed: {e}")

if __name__ == '__main__':
    unittest.main()
