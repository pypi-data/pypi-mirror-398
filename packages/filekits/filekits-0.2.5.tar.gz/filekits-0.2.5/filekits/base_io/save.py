import os
import json
import pandas as pd


# 检查即将保存的数据
def pre_check_df( data ) :
    # 如果输入是列表，转换为DataFrame
    if isinstance( data , list ) :
        return pd.DataFrame( data )
    # 如果输入已经是DataFrame，直接使用
    elif isinstance( data , pd.DataFrame ) :
        return data
    else :
        raise TypeError( "输入数据必须是列表List或DataFrame类型" )


def save_df( data , output_path , charset = 'utf-8', sepset = None, header = True ) :
    """
    将DataFrame或列表保存为指定格式的文件
    
    参数:
        data: 输入数据，可以是DataFrame或列表
        output_path: 输出文件路径，支持.xlsx、.csv、.txt、.json格式
        charset: 文件编码，默认为'utf-8'
        sepset: 分隔符设置，用于csv/txt文件，默认为None（使用pandas默认设置）
        header: 是否保留表头，默认为True（保留表头）
    
    返回:
        None
    """
    df = pre_check_df( data )

    if ".xlsx" in output_path :
        df.to_excel( output_path , index = False , header = header )

    elif ".csv" in output_path or ".txt" in output_path :
        # 只有在指定了分隔符的情况下才使用，否则使用pandas默认设置
        if sepset is not None:
            df.to_csv( output_path , index = False , encoding = charset , sep = sepset , header = header )
        else:
            df.to_csv( output_path , index = False , encoding = charset , header = header )

    elif ".json" in output_path :
        df.to_json( output_path , orient = 'records' , force_ascii = False , indent = 4 )

    else :
        raise ValueError( "请输入正确的文件名后缀，支持 .xlsx、.csv 和 .json " )
    return


def batch_save_df( data , batch_size, output_path , charset = 'utf-8', sepset = None, header = True ) :
    """
    将DataFrame或列表，按照批次大小，保存为指定格式的文件
    
    参数:
        data: 输入数据，可以是DataFrame或列表
        batch_size: 每个批次的大小（行数）
        output_path: 输出文件路径，支持.xlsx、.csv、.txt、.json格式
        charset: 文件编码，默认为'utf-8'
        sepset: 分隔符设置，用于csv/txt文件，默认为None（使用pandas默认设置）
        header: 是否保留表头，默认为True（保留表头）
    
    返回:
        None
    """
    df = pre_check_df( data )
    
    # 处理批次大小不合理的情况
    if batch_size <= 0 :
        raise ValueError( "批次大小必须大于0" )
    
    # 使用os.path模块更安全地处理文件路径
    base_name = os.path.splitext( output_path )[0]
    extension = os.path.splitext( output_path )[1]
    
    total_rows = len( df )
    # 计算批次数量
    num_batches = ( total_rows + batch_size - 1 ) // batch_size  # 更简洁的计算方式
    print( f"Total rows : {total_rows} , batch size : {batch_size} , split batches : {num_batches}" )

    # 按批次保存
    for i in range( num_batches ) :
        start_idx = i * batch_size
        end_idx = min( ( i + 1 ) * batch_size , total_rows )  # 防止越界
        
        batch_df = df[ start_idx : end_idx ]
        # 生成批次文件名
        batch_output_path = f"{base_name}_{i+1}{extension}"
        # 打印即将保存的批次信息
        print( f"Save batch {i+1} : rows {start_idx} ~ {end_idx-1}" )
        # 保存批次数据
        save_df( batch_df , batch_output_path , charset = charset , sepset = sepset , header = header )
    return


# 字典保存为json文件
def save_json( data_dict, output_file = 'output.json' ) :
    # 将字典转换为JSON格式字符串
    json_str = json.dumps( data_dict, ensure_ascii = False, indent = 4 )
    # 打开文件，以写入模式打开
    with open( output_file, 'w', encoding = 'utf-8' ) as f :
        # 将JSON字符串写入文件
        f.write( json_str )


# 保存为txt文件（支持列表和文本字符串）
def save_txt( data , output_file = 'output.txt' ) :
    with open( output_file , 'w' , encoding = 'utf-8' ) as f :
        # 如果是字符串类型，直接写入
        if isinstance( data , str ) :
            f.write( data )
        # 如果是列表类型，逐行写入
        elif isinstance( data , list ) :
            for item in data :
                f.write( str( item ) + '\n' )
        else :
            raise TypeError( "输入数据必须是字符串或列表类型" )