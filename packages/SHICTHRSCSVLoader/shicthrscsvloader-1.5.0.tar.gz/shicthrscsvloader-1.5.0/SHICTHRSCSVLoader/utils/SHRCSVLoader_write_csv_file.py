import csv
import os

def write_csv_file(data: dict, path: str, write_encoding: str = 'GB2312') -> bool:
    """
    data: 要写入的数据，格式为{row_num: {column_name: value}}
    path: CSV文件路径
    write_encoding: 写入编码 默认为GB2312
    """

    # 确保目录存在
    try:
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        # 如果数据为空，创建一个空文件
        if not data:
            with open(path, 'w', encoding=write_encoding, newline='') as f:
                f.write('')
            return True
            
        # 获取所有列名
        all_columns = set()
        for row in data.values():
            all_columns.update(row.keys())
        sorted_columns = sorted(all_columns)
        
        with open(path, 'w', encoding=write_encoding, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted_columns)
            writer.writeheader()
            
            # 按行号排序数据并写入
            for row_num in sorted(data.keys()):
                writer.writerow(data[row_num])
        return True
    except:
        return False