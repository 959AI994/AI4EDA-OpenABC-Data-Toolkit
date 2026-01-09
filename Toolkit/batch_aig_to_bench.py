#!/usr/bin/env python3
"""
批量将 .aig 文件转换为 .bench 格式
"""
import os
import subprocess
from pathlib import Path
import sys

# 配置
BENCHMARK_ROOT = "/home/wjx/pythonproject/data/ACE/benchmark"
ABC_PATH = "/home/wjx/abc/abc"

# 需要处理的子目录
SUBDIRS = ["comb", "core", "EPFL", "openlsd"]

def convert_aig_to_bench(aig_file, bench_file):
    """使用 ABC 将 .aig 文件转换为 .bench 文件"""
    # 添加 short_names 命令以处理包含括号的信号名称
    abc_cmd = f'read_aiger {aig_file}; short_names; write_bench {bench_file}; quit'
    
    try:
        result = subprocess.run(
            [ABC_PATH, '-c', abc_cmd],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0 and os.path.exists(bench_file):
            return True, "Success"
        else:
            return False, f"ABC error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Timeout (>60s)"
    except Exception as e:
        return False, str(e)

def main():
    total_files = 0
    success_count = 0
    failed_count = 0
    failed_files = []
    
    print("=" * 70)
    print("批量 AIG 到 BENCH 转换工具")
    print("=" * 70)
    
    # 遍历每个子目录
    for subdir in SUBDIRS:
        source_dir = os.path.join(BENCHMARK_ROOT, subdir)
        target_dir = os.path.join(BENCHMARK_ROOT, f"{subdir}_bench")
        
        # 检查源目录是否存在
        if not os.path.exists(source_dir):
            print(f"\n⚠️  源目录不存在: {source_dir}")
            continue
        
        # 创建目标目录
        os.makedirs(target_dir, exist_ok=True)
        print(f"\n📁 处理目录: {subdir}")
        print(f"   源目录: {source_dir}")
        print(f"   目标目录: {target_dir}")
        
        # 查找所有 .aig 文件
        aig_files = list(Path(source_dir).rglob("*.aig"))
        
        if not aig_files:
            print(f"   ⚠️  未找到 .aig 文件")
            continue
        
        print(f"   找到 {len(aig_files)} 个 .aig 文件")
        
        # 转换每个文件
        for i, aig_path in enumerate(aig_files, 1):
            total_files += 1
            
            # 构建目标文件路径（保持子目录结构）
            rel_path = aig_path.relative_to(source_dir)
            bench_path = Path(target_dir) / rel_path.with_suffix('.bench')
            
            # 创建子目录（如果需要）
            bench_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 显示进度
            print(f"   [{i}/{len(aig_files)}] {aig_path.name} ... ", end='', flush=True)
            
            # 执行转换
            success, message = convert_aig_to_bench(str(aig_path), str(bench_path))
            
            if success:
                # 获取文件大小
                bench_size = os.path.getsize(bench_path)
                size_kb = bench_size / 1024
                print(f"✅ ({size_kb:.1f} KB)")
                success_count += 1
            else:
                print(f"❌ {message}")
                failed_count += 1
                failed_files.append((str(aig_path), message))
    
    # 打印总结
    print("\n" + "=" * 70)
    print("转换完成！")
    print("=" * 70)
    print(f"总文件数: {total_files}")
    print(f"成功: {success_count} ✅")
    print(f"失败: {failed_count} ❌")
    
    if failed_files:
        print("\n失败的文件列表:")
        for file_path, error in failed_files:
            print(f"  - {file_path}")
            print(f"    错误: {error}")
    
    print("=" * 70)
    
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

