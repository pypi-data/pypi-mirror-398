# 确保命令模块被导入，从而完成注册到 CommandRegistry
from .docx_file_parse_cmd import DocxFileParseCommand
from .docx_file_partition_cmd import DocxFilePartitionCommand 
from .rtf_file_parse_cmd import RtfFileParseCommand
from .rtf_file_partition_cmd import RtfFilePartitionCommand
from .file_type_identify_cmd import FileTypeIdentificationCommand
from .enhance_level_cmd import EnhanceLevelCommand
from .enhance_tree_cmd import EnhanceTreeCommand

__all__ = [
    "DocxFileParseCommand",
    "DocxFilePartitionCommand",
    "RtfFileParseCommand",
    "RtfFilePartitionCommand",
    "FileTypeIdentificationCommand",
    "EnhanceLevelCommand",
    "EnhanceTreeCommand",
]
