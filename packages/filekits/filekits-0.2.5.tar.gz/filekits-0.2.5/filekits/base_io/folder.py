import os
import shutil

# 遍历文件夹地址，返回指定类型或包含指定名称的文件列表
def find_files( folder_path , extension , filename_match = "" ) :
    file_list = [ ]
    # 遍历目录
    for root , dirs , files in os.walk( folder_path ) :
        # 遍历文件，检查文件扩展名
        for filename in files :
            if filename.endswith( extension ) :
                if filename_match == "" :
                    file_list.append( os.path.join( root , filename ) )
                else :
                    if filename_match in filename :
                        file_list.append( os.path.join( root , filename ) )
    return file_list


# 清空指定文件夹
def clear_folder( folder_path ) :
    # 检测文件夹是否存在，如果不存在就创建
    if not os.path.exists( folder_path ) :
        os.makedirs( folder_path )
    shutil.rmtree( folder_path )
    os.mkdir( folder_path )


# 从当前文件路径开始，往上层遍历，遇到指定名称的文件夹后停止，返回对应的绝对路径
def find_parent_folder( target_folder_name ) :
    # 获取当前文件路径
    current_file_path = os.path.dirname( __file__ )
    
    # 从当前路径开始往上遍历
    current_path = current_file_path
    
    while current_path and current_path != os.path.dirname( current_path ) :
        # 检查当前目录名是否为目标文件夹名
        if os.path.basename( current_path ) == target_folder_name :
            return current_path
        
        # 移动到父目录
        parent_path = os.path.dirname( current_path )
        
        # 如果已经到达根目录，停止遍历
        if parent_path == current_path :
            break
            
        current_path = parent_path
    
    # 如果没有找到目标文件夹，返回None
    return None


# 递归打印目录树结构，可选择导出为文件
def print_folder_tree(folder_path, indent='', output_file=None):
    """
    递归打印文件夹树结构
    
    参数:
        folder_path: 要遍历的起始路径
        indent: 缩进字符，用于递归调用
        output_file: 输出文件路径，如果提供则将结果写入文件，否则打印到控制台
    """
    # 确保路径存在
    if not os.path.exists(folder_path):
        error_msg = f"错误: 路径 '{folder_path}' 不存在"
        if output_file:
            with open(output_file, 'a', encoding='utf-8') as f:  # type: ignore
                f.write(error_msg + '\n')
        else:
            print(error_msg)
        return
    
    # 判断是否为Markdown格式（通过文件扩展名）
    is_markdown = output_file is not None and output_file.lower().endswith('.md')
    
    # 如果是Markdown格式且是第一次调用，写入标题和代码块开始标记
    if is_markdown and indent == '':
        with open(output_file, 'w', encoding='utf-8') as f:  # type: ignore
            f.write(f"# 目录树结构: {os.path.basename(folder_path)}\n\n")
            f.write("```\n")
    
    # 获取目录中的所有项目，并排序
    items = sorted(os.listdir(folder_path))
    
    # 遍历目录中的每个项目
    for i, item in enumerate(items):
        item_path = os.path.join(folder_path, item)
        
        # 判断是否是最后一个项目，用于决定树形结构符号
        is_last = i == len(items) - 1
        
        # 根据是否是最后一个项目选择不同的树形符号
        if is_last:
            prefix = "└── "
            next_indent = indent + "    "
        else:
            prefix = "├── "
            next_indent = indent + "│   "
        
        # 构建输出行
        if os.path.isdir(item_path):
            line = f"{indent}{prefix}{item}/"
        else:
            line = f"{indent}{prefix}{item}"
        
        # 输出到控制台或文件
        if output_file:
            with open(output_file, 'a', encoding='utf-8') as f:  # type: ignore
                f.write(line + '\n')
        else:
            print(line)
        
        # 如果是目录，递归调用
        if os.path.isdir(item_path):
            print_folder_tree(item_path, next_indent, output_file)
    
    # 如果是Markdown格式且是第一次调用，写入代码块结束标记
    if is_markdown and indent == '':
        with open(output_file, 'a', encoding='utf-8') as f:  # type: ignore
            f.write("```\n")