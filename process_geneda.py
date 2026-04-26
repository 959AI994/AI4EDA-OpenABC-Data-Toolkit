#!/usr/bin/env python3
"""
批量处理GenEDA benchmark的Verilog文件
生成AIG和PyG数据
"""
import os
import sys
import tempfile
import subprocess
from pathlib import Path

# 设置环境变量
os.environ['YOSYS_DATDIR'] = '/home/wjx/yosys/share'

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from ai4eda.converters.verilog_to_aig import VerilogToAigConverter
from ai4eda.converters.verilog_to_pt import VerilogToPTConverter

def merge_with_lib(verilog_file, lib_file):
    """合并库文件和Verilog文件，并修复非法字符"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.v', delete=False) as tmp:
        with open(lib_file, 'r') as f:
            tmp.write(f.read())
        tmp.write('\n')
        with open(verilog_file, 'r') as f:
            content = f.read()
            # 替换斜杠为下划线（修复层次化信号名）
            content = content.replace('/', '_')
            # 替换未定义值
            content = content.replace("1'bx", "1'b0")
            content = content.replace("1'bz", "1'b0")
            tmp.write(content)
        return tmp.name

def main():
    # 输入输出路径
    data_dir = "/home/wjx/pythonproject/0reverse/GenEDA-main/reverse_engineering/experiments/geneda_benchmark/task3/data"
    eval_dir = "/home/wjx/pythonproject/0reverse/GenEDA-main/reverse_engineering/experiments/geneda_benchmark/task3/eval"
    lib_file = "/home/wjx/pythonproject/AI4EDA-OpenABC-Data-Toolkit/simple_lib.v"

    # 输出目录
    aig_output = "/home/wjx/pythonproject/0reverse/GenEDA-main/reverse_engineering/experiments/geneda_benchmark/task3/aig_data"
    pyg_output = "/home/wjx/pythonproject/0reverse/GenEDA-main/reverse_engineering/experiments/geneda_benchmark/task3/pyg_data"

    os.makedirs(aig_output, exist_ok=True)
    os.makedirs(pyg_output, exist_ok=True)

    # 初始化转换器，指定yosys路径
    aig_converter = VerilogToAigConverter(yosys_path='/home/wjx/yosys/yosys')
    pyg_converter = VerilogToPTConverter(yosys_abc_path='/home/wjx/yosys/yosys-abc')

    # 处理data目录
    print("处理 data 目录...")
    verilog_files = list(Path(data_dir).glob("*.v"))

    for vf in verilog_files:
        name = vf.stem
        print(f"\n处理: {name}")

        merged = merge_with_lib(str(vf), lib_file)
        try:
            # 生成AIG
            aig_file = os.path.join(aig_output, f"{name}.aig")
            success, msg = aig_converter.convert(merged, aig_file)
            print(f"  AIG: {msg}")

            # 生成PyG
            pt_file = os.path.join(pyg_output, f"{name}.pt")
            success, msg = pyg_converter.convert(merged, pt_file)
            print(f"  PyG: {msg}")
        finally:
            os.unlink(merged)

    # 处理eval目录下的子目录
    print("\n\n处理 eval 目录...")
    for subdir in Path(eval_dir).iterdir():
        if subdir.is_dir() and not subdir.name.startswith('.'):
            print(f"\n处理子目录: {subdir.name}")

            # 创建对应的输出目录
            aig_sub = os.path.join(aig_output, subdir.name)
            pyg_sub = os.path.join(pyg_output, subdir.name)
            os.makedirs(aig_sub, exist_ok=True)
            os.makedirs(pyg_sub, exist_ok=True)

            # 处理该子目录下的所有.v文件
            for vf in subdir.rglob("*.v"):
                name = vf.stem
                # 跳过testbench文件
                if '_tb' in name or 'testbench' in name.lower():
                    print(f"  跳过testbench: {name}")
                    continue

                print(f"  处理: {name}")

                merged = merge_with_lib(str(vf), lib_file)
                try:
                    # 生成AIG
                    aig_file = os.path.join(aig_sub, f"{name}.aig")
                    success, msg = aig_converter.convert(merged, aig_file)
                    print(f"    AIG: {msg}")

                    # 生成PyG
                    pt_file = os.path.join(pyg_sub, f"{name}.pt")
                    success, msg = pyg_converter.convert(merged, pt_file)
                    print(f"    PyG: {msg}")
                finally:
                    os.unlink(merged)

    print("\n\n处理完成！")
    print(f"AIG数据保存在: {aig_output}")
    print(f"PyG数据保存在: {pyg_output}")

if __name__ == "__main__":
    main()
