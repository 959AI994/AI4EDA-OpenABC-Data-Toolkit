#!/usr/bin/env python3
"""
基于AiLO的abc.py生成真实的QoR数据
使用真实的ABC综合工具获取area和delay
"""

import os
import sys
import re
import subprocess
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# 添加AiLO项目路径
sys.path.append('/home/wjx/pythonproject/LO/AiLO')
from dataset.utils import OptDict, OptDict_reverse

def line2arr(line):
    """将优化序列字符串转换为数字数组"""
    operations = line.split(';')
    opt_numbers = []
    for operation in operations:
        operation = operation.strip()
        for key, value in OptDict.items():
            if operation == value:
                opt_numbers.append(key)
                break
    return opt_numbers

def apply_abc_optimization(aig_in, liberty, opt_script, abs_tool_abc):
    """应用ABC优化获取真实的area和delay数据
    
    Args:
        aig_in (str): AIG文件路径
        liberty (str): Liberty库文件路径
        opt_script (str): 优化序列字符串
        abs_tool_abc (str): ABC工具路径
    Returns:
        area, delay (float, float): 真实的面积和延迟
    """
    
    script = "read_aiger {0}; read_lib {1}; strash; {2}; map; print_stats".format(aig_in, liberty, opt_script)
    command = "{0} -c \"{1}\"".format(abs_tool_abc, script)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        output = result.stdout
        
        # 解析ABC输出获取area和delay
        area_match = re.search(r'area =([\d\.]+)', output)
        delay_match = re.search(r'delay =([\d\.]+)', output)
        
        # 如果第一种格式没匹配到，尝试第二种格式
        if not area_match:
            area_match = re.search(r'area\s+=\s*([\d\.]+)', output)
        if not delay_match:
            delay_match = re.search(r'delay\s+=\s*([\d\.]+)', output)
        
        area = float(area_match.group(1)) if area_match else None
        delay = float(delay_match.group(1)) if delay_match else None
        
        return area, delay, opt_script
        
    except subprocess.TimeoutExpired:
        print(f"警告: ABC综合超时 - {aig_in}")
        return None, None, opt_script
    except Exception as e:
        print(f"错误: ABC综合失败 - {aig_in}: {e}")
        return None, None, opt_script

def generate_real_character_csv(epfl_aig_dir, optimization_sequences_dir, target_dir, design_name, 
                               liberty_file, abc_tool, num_sequences=1500):
    """为单个设计生成真实的character.csv文件"""
    print(f"为 {design_name} 生成真实的QoR数据...")
    
    # 查找AIG文件
    aig_file = None
    for subdir in ['arithmetic', 'random_control']:
        potential_aig = Path(epfl_aig_dir) / subdir / f"{design_name}.aig"
        if potential_aig.exists():
            aig_file = str(potential_aig)
            break
    
    if not aig_file:
        print(f"⚠️ 未找到AIG文件: {design_name}")
        return
    
    # 查找优化序列数据
    optimization_data_path = None
    for subdir in ['arithmetic', 'random_control']:
        potential_path = Path(optimization_sequences_dir) / subdir / design_name / "optimization_data.csv"
        if potential_path.exists():
            optimization_data_path = potential_path
            break
    
    if not optimization_data_path:
        print(f"⚠️ 未找到优化序列数据: {design_name}")
        return
    
    # 读取优化序列
    df = pd.read_csv(optimization_data_path)
    
    # 生成优化序列字符串
    opt_scripts = []
    for i in range(min(num_sequences, len(df))):
        source_idx = i % len(df)
        opt_seq_str = df.iloc[source_idx]['opt_seq']
        opt_seq = eval(opt_seq_str) if isinstance(opt_seq_str, str) else opt_seq_str
        
        # 转换为ABC命令字符串
        script_parts = []
        for op_num in opt_seq:
            if op_num in OptDict:
                script_parts.append(OptDict[op_num])
        opt_script = '; '.join(script_parts)
        opt_scripts.append(opt_script)
    
    # 使用多线程并行运行ABC综合
    areas = []
    delays = []
    opt_seqs = []
    
    print(f"  运行ABC综合获取真实QoR数据...")
    
    def process_script(opt_script):
        area, delay, _ = apply_abc_optimization(aig_file, liberty_file, opt_script, abc_tool)
        return opt_script, area, delay
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_script, script) for script in opt_scripts]
        
        for future in tqdm(as_completed(futures), total=len(opt_scripts), desc=f"ABC综合 {design_name}"):
            opt_script, area, delay = future.result()
            
            if area is not None and delay is not None:
                areas.append(area)
                delays.append(delay)
                opt_seqs.append(line2arr(opt_script))
            else:
                # 如果ABC综合失败，使用默认值
                areas.append(0.0)
                delays.append(0.0)
                opt_seqs.append([])
    
    # 保存character.csv (格式: 只有opt_seq, area, delay三列)
    character_data = []
    for i, (area, delay, opt_seq) in enumerate(zip(areas, delays, opt_seqs)):
        character_data.append({
            'opt_seq': opt_seq,  # 直接保存数字列表，pandas会自动处理
            'area': area,
            'delay': delay
        })

    character_df = pd.DataFrame(character_data)
    character_csv_path = target_dir / "character.csv"
    character_df.to_csv(character_csv_path, index=False)
    
    print(f"✓ 生成真实QoR数据: {character_csv_path} ({len(character_data)} 个序列)")
    
    return character_csv_path

def generate_normalization_files(target_dir, design_name, character_csv_path):
    """生成归一化参数文件"""
    print(f"为 {design_name} 生成归一化文件...")
    
    # 读取character.csv计算统计参数
    df = pd.read_csv(character_csv_path)
    
    # 过滤掉无效数据
    valid_df = df[(df['area'] > 0) & (df['delay'] > 0)]
    
    if len(valid_df) == 0:
        print(f"⚠️ 警告: {design_name} 没有有效的QoR数据")
        return
    
    # 计算面积归一化参数
    area_mean = valid_df['area'].mean()
    area_std = valid_df['area'].std()
    
    area_norm_df = pd.DataFrame({
        'mean': [area_mean],
        'std': [area_std]
    })
    area_norm_path = target_dir / "des_area.csv"
    area_norm_df.to_csv(area_norm_path, index=False)
    
    # 计算延迟归一化参数
    delay_mean = valid_df['delay'].mean()
    delay_std = valid_df['delay'].std()
    
    delay_norm_df = pd.DataFrame({
        'mean': [delay_mean],
        'std': [delay_std]
    })
    delay_norm_path = target_dir / "des_delay.csv"
    delay_norm_df.to_csv(delay_norm_path, index=False)
    
    print(f"✓ 面积归一化: mean={area_mean:.2f}, std={area_std:.2f}")
    print(f"✓ 延迟归一化: mean={delay_mean:.2f}, std={delay_std:.2f}")

def copy_graphml_files(epfl_graphml_dir, ailo_dir, design_mapping):
    """复制GraphML文件到AiLO目录结构"""
    print("复制GraphML文件...")
    
    for design_name, target_dir in design_mapping.items():
        # 在arithmetic和random_control子目录中查找GraphML文件
        source_graphml = None
        for subdir in ['arithmetic', 'random_control']:
            potential_path = Path(epfl_graphml_dir) / subdir / f"{design_name}.graphml"
            if potential_path.exists():
                source_graphml = potential_path
                break
        
        if source_graphml:
            target_graphml = target_dir / f"{design_name}.graphml"
            import shutil
            shutil.copy2(source_graphml, target_graphml)
            print(f"✓ 复制: {source_graphml} -> {target_graphml}")
        else:
            print(f"⚠️ 未找到: {design_name}.graphml")

def create_ailo_directory_structure(base_dir, des_class="EPFL"):
    """创建AiLO标准目录结构"""
    root_dir = Path(base_dir) / des_class
    
    # 创建design1和design2目录
    design1_dir = root_dir / "design1"
    design2_dir = root_dir / "design2"
    
    design1_dir.mkdir(parents=True, exist_ok=True)
    design2_dir.mkdir(parents=True, exist_ok=True)
    
    return root_dir, design1_dir, design2_dir

def process_epfl_designs_with_real_qor(epfl_aig_dir, epfl_graphml_dir, optimization_sequences_dir, 
                                      ailo_dir, liberty_file, abc_tool, num_sequences=1500):
    """使用真实ABC综合处理EPFL设计"""
    
    # EPFL设计分组
    design1 = ['adder', 'bar', 'max', 'sin', 'i2c', 'cavlc', 'ctrl', 'int2float', 'priority', 'router']
    design2 = ['div', 'log2', 'multiplier', 'sqrt', 'square', 'arbiter', 'mem_ctrl', 'voter', 'hyp']
    
    # 创建目录结构
    root_dir, design1_dir, design2_dir = create_ailo_directory_structure(ailo_dir)
    
    # 处理design1
    print("=" * 60)
    print("处理 Design1 组 (真实ABC综合)...")
    print("=" * 60)
    
    for design_name in design1:
        print(f"\n处理设计: {design_name}")
        
        # 创建设计目录
        design_dir = design1_dir / design_name
        design_dir.mkdir(exist_ok=True)
        
        # 复制GraphML文件
        copy_graphml_files(epfl_graphml_dir, ailo_dir, {design_name: design_dir})
        
        # 生成真实的character.csv
        character_csv_path = generate_real_character_csv(
            epfl_aig_dir, optimization_sequences_dir, design_dir, design_name,
            liberty_file, abc_tool, num_sequences
        )
        
        # 生成归一化文件
        if character_csv_path and character_csv_path.exists():
            generate_normalization_files(design_dir, design_name, character_csv_path)
    
    # 处理design2
    print("\n" + "=" * 60)
    print("处理 Design2 组 (真实ABC综合)...")
    print("=" * 60)
    
    for design_name in design2:
        print(f"\n处理设计: {design_name}")
        
        # 创建设计目录
        design_dir = design2_dir / design_name
        design_dir.mkdir(exist_ok=True)
        
        # 复制GraphML文件
        copy_graphml_files(epfl_graphml_dir, ailo_dir, {design_name: design_dir})
        
        # 生成真实的character.csv
        character_csv_path = generate_real_character_csv(
            epfl_aig_dir, optimization_sequences_dir, design_dir, design_name,
            liberty_file, abc_tool, num_sequences
        )
        
        # 生成归一化文件
        if character_csv_path and character_csv_path.exists():
            generate_normalization_files(design_dir, design_name, character_csv_path)

def main():
    parser = argparse.ArgumentParser(description="使用真实ABC综合生成AiLO数据集")
    parser.add_argument("--epfl_aig_dir", 
                       default="/home/wjx/pythonproject/data/ACE/benchmark/EPFL",
                       help="EPFL AIG文件目录")
    parser.add_argument("--epfl_graphml_dir", 
                       default="/home/wjx/pythonproject/data/ACE/benchmark/EPFL_graphml",
                       help="EPFL GraphML文件目录")
    parser.add_argument("--optimization_sequences_dir",
                       default="/home/wjx/pythonproject/data/ACE/benchmark/EPFL_optimization_sequences", 
                       help="EPFL优化序列目录")
    parser.add_argument("--ailo_dir",
                       default="/home/wjx/pythonproject/data/ACE/benchmark/EPFL_AiLO_real",
                       help="AiLO数据集输出目录")
    parser.add_argument("--liberty_file",
                       default="/home/wjx/pythonproject/data/ACE/benchmark/asap7.lib",
                       help="Liberty库文件路径")
    parser.add_argument("--abc_tool",
                       default="/home/wjx/pythonproject/data/LogicFactory/build/toolkit/yosys/bin/yosys-abc",
                       help="ABC工具路径")
    parser.add_argument("--num_sequences", type=int, default=1500,
                       help="每个设计生成的序列数量")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AiLO真实数据集生成器 (基于ABC综合)")
    print("=" * 60)
    print(f"EPFL AIG目录: {args.epfl_aig_dir}")
    print(f"EPFL GraphML目录: {args.epfl_graphml_dir}")
    print(f"优化序列目录: {args.optimization_sequences_dir}")
    print(f"AiLO输出目录: {args.ailo_dir}")
    print(f"Liberty文件: {args.liberty_file}")
    print(f"ABC工具: {args.abc_tool}")
    print(f"每个设计序列数: {args.num_sequences}")
    print("=" * 60)
    
    # 检查必要文件
    if not Path(args.liberty_file).exists():
        print(f"错误: Liberty文件不存在: {args.liberty_file}")
        sys.exit(1)
    
    if not Path(args.abc_tool).exists():
        print(f"错误: ABC工具不存在: {args.abc_tool}")
        sys.exit(1)
    
    try:
        # 处理EPFL设计
        process_epfl_designs_with_real_qor(
            args.epfl_aig_dir,
            args.epfl_graphml_dir,
            args.optimization_sequences_dir, 
            args.ailo_dir,
            args.liberty_file,
            args.abc_tool,
            args.num_sequences
        )
        
        print("\n🎉 真实AiLO数据集生成完成!")
        print(f"数据集位置: {args.ailo_dir}")
        print("注意: 这是基于真实ABC综合的数据，训练效果会更好!")
        
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
