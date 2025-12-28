import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

logger = logging.getLogger(__name__)

def merge_excel_files(output_file: str, input_files: List[str]) -> None:
    """
    将多个 Excel/CSV 文件合并为一个包含多个 sheet 的 Excel 文件。
    读取每个输入文件的所有 sheet（如果是 CSV 则视为单个 sheet），并合并到一个输出 Excel 中。
    保持 sheet 名称不变（对于 Excel）。

    Args:
        output_file: 输出 Excel 文件的路径。
        input_files: 输入 Excel/CSV 文件路径列表。
    """
    logger.info(f"正在将 {len(input_files)} 个文件合并到 {output_file}...")
    
    # 确保输出目录存在
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for file_path in input_files:
            logger.info(f"正在读取文件: {file_path}")
            path_obj = Path(file_path)
            try:
                suffix = path_obj.suffix.lower()
                if suffix == '.csv':
                    # 处理 CSV 文件
                    sheet_name = path_obj.stem
                    # 截断 sheet 名称以符合 Excel 限制 (31 字符)
                    if len(sheet_name) > 31:
                        sheet_name = sheet_name[:31]
                        logger.warning(f"Sheet 名称过长，已截断为: {sheet_name}")
                    
                    df = pd.read_csv(file_path)
                    logger.info(f"  - 添加 sheet '{sheet_name}'，包含 {len(df)} 行")
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                elif suffix in ['.xlsx', '.xls', '.xlsm']:
                    # 处理 Excel 文件
                    # 使用 ExcelFile 避免一次性加载所有 sheet，虽然这里我们需要所有 sheet，
                    # 但这样写更通用且方便后续优化
                    excel_file = pd.ExcelFile(file_path)
                    for sheet_name in excel_file.sheet_names:
                        df = excel_file.parse(sheet_name)
                        logger.info(f"  - 添加 sheet '{sheet_name}'，包含 {len(df)} 行")
                        # 写入输出文件
                        # 注意：如果不同文件中有重复的 sheet 名称，pandas/ExcelWriter 可能会自动处理
                        # (例如添加数字后缀) 或者覆盖，具体取决于版本。
                        # 鉴于需求是“保持 sheet 名称不变”，我们按原样传递 sheet_name。
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    logger.warning(f"不支持的文件类型: {file_path}，已跳过")

            except Exception as e:
                logger.error(f"处理文件 {file_path} 时出错: {e}")
                raise e

    logger.info(f"成功将文件合并到 {output_file}")


def split_excel_file(input_excel_file: str, split: bool = False) -> Dict[str, Any]:
    """
    将一个大 Excel 文件按 sheet 拆分为多个 Excel 文件。

    Args:
        input_excel_file: 输入 Excel 文件路径。
        split: 如果为 True，则拆分文件并写入磁盘。

    Returns:
        包含 sheet 列表的字典，例如：{"sheets": ["Sheet1", "Sheet2"]}
    """
    logger.info(f"正在读取 Excel 文件: {input_excel_file}")
    
    try:
        # 使用 ExcelFile 类来延迟加载，避免一次性读取所有数据到内存
        excel_file = pd.ExcelFile(input_excel_file)
        sheet_names = excel_file.sheet_names
        
        if split:
            logger.info(f"正在将 {len(sheet_names)} 个 sheet 拆分为单独的文件...")
            input_path = Path(input_excel_file)
            parent_dir = input_path.parent
            stem = input_path.stem
            
            for sheet_name in sheet_names:
                # 逐个读取 sheet，节省内存
                df = excel_file.parse(sheet_name)
                
                # 构建输出文件名: {原文件名}_{sheet名}.xlsx
                output_filename = f"{stem}_{sheet_name}.xlsx"
                output_path = parent_dir / output_filename
                
                logger.info(f"  - 正在将 sheet '{sheet_name}' 写入 {output_filename}")
                df.to_excel(output_path, sheet_name=sheet_name, index=False)
            
            logger.info("拆分完成。")
            
        return {"sheets": sheet_names}

    except Exception as e:
        logger.error(f"处理文件 {input_excel_file} 时出错: {e}")
        raise e
