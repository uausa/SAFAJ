import os
import re
import json
from pathlib import Path
from datetime import datetime
import zipfile
import py7zr
import rarfile
import tarfile
import gzip
import shutil

def check_extracted_files(root_dir):
    # 转换为Path对象以更好地处理路径
    root_path = Path(root_dir)
    if not root_path.exists():
        raise FileNotFoundError(f"目录不存在: {root_dir}")

    # 存储所有压缩包文件名（去除扩展名）和它们的完整路径
    archive_names = {}
    # 存储所有文件和文件夹名及其路径
    all_names = {}

    # 压缩文件扩展名模式
    compression_patterns = [
        r'\.zip$',
        r'\.tar\.gz$',
        r'\.tgz$',
        r'\.tar\.bz2$',
        r'\.tbz2$',
        r'\.tar\.xz$',
        r'\.txz$',
        r'\.gz$',
        r'\.rar$',
        r'\.7z$'
    ]
    
    # 编译正则表达式模式
    compression_regex = re.compile('|'.join(compression_patterns), re.IGNORECASE)

    # 遍历根目录及其子文件夹
    for root, dirs, files in os.walk(root_path):
        for file in files:
            file_path = Path(root) / file
            
            # 获取文件名（不包含任何扩展名）
            file_name = file
            while True:
                file_name, ext = os.path.splitext(file_name)
                if not ext or ext == '.tar':  # 处理.tar.gz这样的双扩展名
                    break
            
            # 记录文件名和路径
            if file_name not in all_names:
                all_names[file_name] = []
            all_names[file_name].append(str(file_path))

            # 检查是否为压缩包
            if compression_regex.search(file):
                if file_name not in archive_names:
                    archive_names[file_name] = []
                archive_names[file_name].append(str(file_path))

    # 检查哪些压缩包未解压
    not_extracted = {name: paths for name, paths in archive_names.items() 
                    if len(all_names.get(name, [])) <= len(paths)}

    # 检查哪些文件名没有对应的压缩包
    no_archive = {name: paths for name, paths in all_names.items() 
                 if name not in archive_names}

    return not_extracted, no_archive

def save_results(not_extracted, no_archive, output_file=None):
    """保存结果到JSON文件"""
    if output_file is None:
        # 使用当前时间创建默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"compression_check_results_{timestamp}.json"
    
    results = {
        "未解压的压缩包": {name: paths for name, paths in not_extracted.items()},
        "没有对应压缩包的文件": {name: paths for name, paths in no_archive.items()}
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"\n结果已保存到文件: {output_file}")

def extract_archive(archive_path, extract_path=None):
    """解压单个压缩文件"""
    archive_path = Path(archive_path)
    
    # 如果没有指定解压路径，则解压到同名文件夹
    if extract_path is None:
        extract_path = archive_path.parent / archive_path.stem
    
    extract_path = Path(extract_path)
    extract_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # 根据文件扩展名选择解压方法
        if archive_path.suffix.lower() == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        
        elif archive_path.suffix.lower() == '.7z':
            with py7zr.SevenZipFile(archive_path, 'r') as sz:
                sz.extractall(extract_path)
        
        elif archive_path.suffix.lower() == '.rar':
            with rarfile.RarFile(archive_path, 'r') as rar:
                rar.extractall(extract_path)
        
        elif '.tar' in archive_path.suffix.lower():
            with tarfile.open(archive_path, 'r:*') as tar:
                tar.extractall(extract_path)
        
        elif archive_path.suffix.lower() == '.gz':
            # 对于单个gzip文件
            output_path = extract_path / archive_path.stem
            with gzip.open(archive_path, 'rb') as gz:
                with open(output_path, 'wb') as out:
                    shutil.copyfileobj(gz, out)
        
        print(f"成功解压: {archive_path}")
        return True
    
    except Exception as e:
        print(f"解压失败 {archive_path}: {str(e)}")
        return False

def extract_all_archives(not_extracted):
    """解压所有未解压的压缩包"""
    success_count = 0
    fail_count = 0
    
    for name, paths in not_extracted.items():
        for archive_path in paths:
            if extract_archive(archive_path):
                success_count += 1
            else:
                fail_count += 1
    
    print(f"\n解压完成统计:")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")

def print_results(not_extracted, no_archive):
    print("\n=== 检查结果 ===")
    
    print("\n1. 未解压的压缩包:")
    if not_extracted:
        for name, paths in not_extracted.items():
            print(f"\n文件名: {name}")
            for path in paths:
                print(f"  位置: {path}")
    else:
        print("所有压缩包都已解压")

    print("\n2. 没有对应压缩包的文件名:")
    if no_archive:
        for name, paths in no_archive.items():
            print(f"\n文件名: {name}")
            for path in paths:
                print(f"  位置: {path}")
    else:
        print("所有文件都有对应的压缩包")

def main():
    # 根目录
    root_dir = r'G:\你的路径文件路径（不含文件名）'
    try:
        # 检查文件
        not_extracted, no_archive = check_extracted_files(root_dir)
        
        # 打印结果
        print_results(not_extracted, no_archive)
        
        # 询问用户是否要保存结果
        save_choice = input("\n是否要保存结果到文件？(y/n): ").lower()
        if save_choice == 'y':
            save_results(not_extracted, no_archive)
        
        # 如果有未解压的文件，询问是否要解压
        if not_extracted:
            extract_choice = input("\n是否要解压未解压的压缩包？(y/n): ").lower()
            if extract_choice == 'y':
                extract_all_archives(not_extracted)
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == '__main__':
    main()
