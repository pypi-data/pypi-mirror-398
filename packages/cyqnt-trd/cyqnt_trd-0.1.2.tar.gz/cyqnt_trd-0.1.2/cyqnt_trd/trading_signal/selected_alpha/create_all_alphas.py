"""
创建所有101个Alpha因子文件的脚本

从alpha_cal_reference.py读取实现，转换为适配crypto数据格式的alpha因子文件。
"""

import re
import os
import sys

# 添加路径以便导入参考文件
sys.path.insert(0, '/Users/user/Desktop/repo/crypto_trading')

def convert_alpha_code(code, alpha_num):
    """
    将参考代码转换为适配crypto数据格式的代码
    
    Args:
        code: 原始alpha实现代码
        alpha_num: alpha编号
    
    Returns:
        转换后的代码字符串
    """
    # 替换变量名
    code = code.replace('self.open', 'open_price')
    code = code.replace('self.high', 'high_price')
    code = code.replace('self.low', 'low_price')
    code = code.replace('self.close', 'close_price')
    code = code.replace('self.volume', 'volume')
    code = code.replace('self.returns', 'returns')
    code = code.replace('self.vwap', 'vwap')
    
    # 处理DataFrame操作 - 移除.to_frame()和.CLOSE
    code = re.sub(r'\.to_frame\(\)', '', code)
    code = re.sub(r'\.CLOSE', '', code)
    
    # 处理DataFrame创建 - 转换为Series
    # 处理 pd.DataFrame(np.ones_like(...), index=..., columns=...) 的情况
    code = re.sub(
        r'pd\.DataFrame\(np\.(ones|zeros)_like\(([^)]+)\),\s*index=([^,)]+)(?:,\s*columns=[^)]+)?\)',
        r'pd.Series(np.\1_like(\2), index=\3)',
        code
    )
    code = re.sub(
        r'pd\.DataFrame\(np\.(ones|zeros)_like\(([^)]+)\),\s*index=([^,)]+)\)',
        r'pd.Series(np.\1_like(\2), index=\3)',
        code
    )
    
    # 处理DataFrame索引操作
    code = re.sub(r'alpha\.at\[([^\]]+),[\'"]close[\'"]\]', r'alpha[\1]', code)
    code = re.sub(r'alpha\[([^\]]+)\] =', r'alpha[\1] =', code)
    
    # 处理pow方法 - Series的pow需要特殊处理
    code = re.sub(r'(\w+)\.pow\((\d+)\)', r'(\1 ** \2)', code)
    
    # 处理sum函数 - 确保使用ts_sum
    code = re.sub(r'\bsum\((\w+), (\d+)\)', r'ts_sum(\1, \2)', code)
    
    # 处理return语句 - 转换为result赋值
    if 'return' in code:
        # 提取所有return语句，保留最后一个
        return_matches = list(re.finditer(r'return\s+(.+)', code, re.DOTALL))
        if return_matches:
            # 使用最后一个return
            last_return = return_matches[-1]
            return_expr = last_return.group(1).strip()
            # 移除所有return语句
            code = re.sub(r'return\s+.+', '', code, flags=re.DOTALL)
            # 添加result赋值
            code = code.rstrip() + f"\n        result = {return_expr}"
        else:
            # 如果没有找到return表达式，添加result = None
            code = code + "\n        result = None"
    else:
        # 如果代码没有return，查找最后一个赋值
        lines = [l.strip() for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]
        if lines:
            last_line = lines[-1]
            if '=' in last_line:
                # 提取变量名
                var_name = last_line.split('=')[0].strip()
                code = code + f"\n        result = {var_name}"
            else:
                # 假设最后一行是表达式
                code = code + f"\n        result = {last_line}"
        else:
            code = code + "\n        result = None"
    
    return code


def extract_alpha_implementation(ref_file_path, alpha_num):
    """
    从参考文件中提取指定alpha的实现
    
    Args:
        ref_file_path: 参考文件路径
        alpha_num: alpha编号（如1, 2, 101）
    
    Returns:
        alpha实现代码，如果没有找到则返回None
    """
    with open(ref_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 构建alpha方法名
    alpha_name = f'alpha{alpha_num:03d}'
    
    # 查找alpha方法
    pattern = rf'def {alpha_name}\(self\):(.*?)(?=\n    # Alpha#|\n    def alpha|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        code = match.group(1).strip()
        # 提取注释中的公式
        formula_pattern = rf'# Alpha#{alpha_num}\s+(.+?)\n'
        formula_match = re.search(formula_pattern, content)
        formula = formula_match.group(1).strip() if formula_match else f"Alpha#{alpha_num} formula"
        return code, formula
    
    return None, None


def generate_alpha_file(alpha_num, implementation_code=None, formula=""):
    """
    生成单个alpha文件
    
    Args:
        alpha_num: alpha编号
        implementation_code: 实现代码（如果为None则生成占位符）
        formula: 公式描述
    """
    
    if implementation_code:
        # 转换代码
        converted_code = convert_alpha_code(implementation_code, alpha_num)
        
        # 生成完整实现
        code_body = f"""        # 实现Alpha因子逻辑
        {converted_code}
        
        # 返回最后一个值（如果是Series）或直接返回值
        if isinstance(result, pd.Series):
            result_value = result.iloc[-1] if len(result) > 0 else 0.0
        elif isinstance(result, (int, float, np.number)):
            result_value = float(result)
        else:
            result_value = 0.0
        
        # 处理NaN和无穷大
        if pd.isna(result_value) or np.isinf(result_value):
            return 0.0
        
        return float(result_value)"""
    else:
        # 生成占位符实现
        code_body = f"""        # TODO: 实现Alpha#{alpha_num}因子
        # 公式: {formula}
        # 注意：此alpha在参考文件中未找到实现，需要手动实现
        
        return 0.0"""
    
    file_content = f'''"""
Alpha#{alpha_num} 因子

公式: {formula}

说明：
此alpha因子基于WorldQuant的101个alpha因子公式实现。
适配crypto交易数据格式（open_price, high_price, low_price, close_price, volume, quote_volume）。

标签：待补充
"""

import pandas as pd
import numpy as np
from typing import Optional
from .alpha_utils import (
    ts_sum, sma, stddev, correlation, covariance,
    ts_rank, product, ts_min, ts_max, delta, delay,
    rank, scale, ts_argmax, ts_argmin, decay_linear,
    sign, abs, log, signed_power
)


def alpha{alpha_num}_factor(
    data_slice: pd.DataFrame,
    **kwargs
) -> float:
    """
    Alpha#{alpha_num} 因子计算
    
    Args:
        data_slice: 数据切片，必须包含以下列：
                   - open_price: 开盘价
                   - high_price: 最高价
                   - low_price: 最低价
                   - close_price: 收盘价
                   - volume: 成交量
                   - quote_volume: 成交额（用于计算vwap）
        **kwargs: 其他可选参数
    
    Returns:
        因子值（最后一个时间点的值）
    """
    try:
        if len(data_slice) < 2:
            return 0.0
        
        # 提取数据列
        open_price = data_slice['open_price']
        high_price = data_slice['high_price']
        low_price = data_slice['low_price']
        close_price = data_slice['close_price']
        volume = data_slice['volume']
        quote_volume = data_slice.get('quote_volume', volume * close_price)  # 如果没有quote_volume，使用volume*close_price估算
        
        # 计算收益率
        returns = close_price.pct_change().fillna(0)
        
        # 计算VWAP (Volume Weighted Average Price)
        # vwap = quote_volume / volume，如果volume为0则使用close_price
        vwap = (quote_volume / (volume + 1e-10)).fillna(close_price)
        
        # 计算adv20 (20日平均成交量)
        adv20 = sma(volume, 20)
        
{code_body}
        
    except Exception as e:
        # 如果计算出错，返回0
        return 0.0
'''
    
    return file_content


def main():
    """主函数：生成所有101个alpha文件"""
    ref_file_path = '/Users/user/Desktop/repo/crypto_trading/alpha_cal_reference.py'
    output_dir = '/Users/user/Desktop/repo/crypto_trading/cyqnt_trd/trading_signal/selected_alpha'
    
    # 从参考文件中提取所有alpha编号
    with open(ref_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有alpha方法
    alpha_pattern = r'def alpha(\d+)\(self\):'
    found_alphas = set(int(match.group(1)) for match in re.finditer(alpha_pattern, content))
    
    print(f"找到 {len(found_alphas)} 个alpha实现")
    
    # 生成所有101个alpha文件
    for alpha_num in range(1, 102):
        # 提取实现
        if alpha_num in found_alphas:
            impl_code, formula = extract_alpha_implementation(ref_file_path, alpha_num)
        else:
            impl_code, formula = None, f"Alpha#{alpha_num} (未在参考文件中找到)"
        
        # 生成文件内容
        file_content = generate_alpha_file(alpha_num, impl_code, formula)
        
        # 写入文件
        file_path = os.path.join(output_dir, f"alpha{alpha_num}.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        status = "✓" if alpha_num in found_alphas else "○"
        print(f"{status} Generated alpha{alpha_num}.py")
    
    print(f"\n完成！已生成101个alpha文件到 {output_dir}")


if __name__ == "__main__":
    main()

