#!/usr/bin/env python3
"""
批量将 .bench 文件转换为 .graphml 格式
"""
import os
import subprocess
from pathlib import Path
import sys

# 配置
BENCHMARK_ROOT = "/home/wjx/pythonproject/data/ACE/benchmark"
CONVERTER_SCRIPT = "/home/wjx/pythonproject/OpenABC-2.0/datagen/utilities/andAIG2Graphml.py"

# 需要处理的目录映射：source_dir -> target_dir
DIR_MAPPINGS = {
    "comb_bench": "comb_graphml",
    "core_bench": "core_graphml",
    "EPFL_bench": "EPFL_graphml",
    "openlsd_bench": "openlsd_graphml"
}

def convert_bench_to_graphml(bench_file, output_dir):
    """使用 andAIG2Graphml.py 将 .bench 文件转换为 .graphml 文件"""
    try:
        result = subprocess.run(
            ['python3', CONVERTER_SCRIPT, '--bench', str(bench_file), '--gml', str(output_dir)],
            capture_output=True,
            text=True,
            timeout=None  # 不设置超时限制
        )
        
        # 检查是否生成了输出文件
        expected_output = os.path.join(output_dir, os.path.basename(bench_file) + ".graphml")
        
        if result.returncode == 0 and os.path.exists(expected_output):
            return True, "Success"
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            # 过滤掉 SyntaxWarning
            if "SyntaxWarning" in error_msg and os.path.exists(expected_output):
                return True, "Success (with warnings)"
            return False, f"Conversion error: {error_msg[:100]}"
    except Exception as e:
        return False, str(e)

def main():
    total_files = 0
    success_count = 0
    failed_count = 0
    failed_files = []
    
    print("=" * 70)
    print("批量 BENCH 到 GraphML 转换工具")
    print("=" * 70)
    
    # 遍历每个目录映射
    for source_dir_name, target_dir_name in DIR_MAPPINGS.items():
        source_dir = os.path.join(BENCHMARK_ROOT, source_dir_name)
        target_dir = os.path.join(BENCHMARK_ROOT, target_dir_name)
        
        # 检查源目录是否存在
        if not os.path.exists(source_dir):
            print(f"\n⚠️  源目录不存在: {source_dir}")
            continue
        
        # 创建目标目录
        os.makedirs(target_dir, exist_ok=True)
        print(f"\n📁 处理目录: {source_dir_name}")
        print(f"   源目录: {source_dir}")
        print(f"   目标目录: {target_dir}")
        
        # 查找所有 .bench 文件
        bench_files = list(Path(source_dir).rglob("*.bench"))
        
        if not bench_files:
            print(f"   ⚠️  未找到 .bench 文件")
            continue
        
        print(f"   找到 {len(bench_files)} 个 .bench 文件")
        
        # 转换每个文件
        for i, bench_path in enumerate(bench_files, 1):
            total_files += 1
            
            # 构建目标子目录路径（保持子目录结构）
            rel_path = bench_path.relative_to(source_dir)
            target_subdir = Path(target_dir) / rel_path.parent
            
            # 创建子目录（如果需要）
            target_subdir.mkdir(parents=True, exist_ok=True)
            
            # 显示进度
            bench_size_kb = bench_path.stat().st_size / 1024
            print(f"   [{i}/{len(bench_files)}] {bench_path.name} ({bench_size_kb:.1f} KB) ... ", end='', flush=True)
            
            # 执行转换
            success, message = convert_bench_to_graphml(bench_path, str(target_subdir))
            
            if success:
                # 获取输出文件大小
                graphml_file = target_subdir / (bench_path.name + ".graphml")
                if graphml_file.exists():
                    graphml_size = graphml_file.stat().st_size
                    size_kb = graphml_size / 1024
                    print(f"✅ ({size_kb:.1f} KB)")
                    success_count += 1
                else:
                    print(f"❌ Output file not found")
                    failed_count += 1
                    failed_files.append((str(bench_path), "Output file not found"))
            else:
                print(f"❌ {message}")
                failed_count += 1
                failed_files.append((str(bench_path), message))
    
    # 打印总结
    print("\n" + "=" * 70)
    print("转换完成！")
    print("=" * 70)
    print(f"总文件数: {total_files}")
    print(f"成功: {success_count} ✅")
    print(f"失败: {failed_count} ❌")
    print(f"成功率: {success_count/total_files*100:.1f}%" if total_files > 0 else "N/A")
    
    if failed_files:
        print(f"\n失败的文件列表 (共 {len(failed_files)} 个):")
        for file_path, error in failed_files[:20]:  # 只显示前20个
            print(f"  - {os.path.basename(file_path)}")
            print(f"    错误: {error}")
        if len(failed_files) > 20:
            print(f"  ... 还有 {len(failed_files) - 20} 个失败文件未显示")
    
    print("=" * 70)
    
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

