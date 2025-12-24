import json
import pickle
from io import BytesIO
from .color import color

__all__ = [
    'load_json', 'save_json',
    'load_pickle', 'save_pickle',
    'load_jsonl_as_list', 'save_list_to_jsonl',
    'load_jsonl_as_lines', 'save_lines_to_jsonl',
    'load_txt_as_lines', 'save_lines_to_txt'
]

def load_json(json_path, client=None):
    """
    加载JSON文件，支持本地文件和S3路径。
    
    参数:
        json_path (str): JSON文件路径，可以是本地路径或S3路径（以's3://'开头）
        client (optional): S3客户端实例，当读取S3路径时必需
        
    返回:
        dict/list: JSON文件内容
        
    异常:
        AssertionError: 如果文件扩展名不是.json
        ValueError: 如果读取S3路径时未提供client
        AssertionError: 如果从S3读取失败
        
    示例:
        >>> # 读取本地文件
        >>> data = load_json('config.json')
        >>> # 读取S3文件
        >>> data = load_json('s3://bucket/config.json', client=s3_client)
    """
    assert json_path.endswith(".json"), f"文件 {json_path} 不是JSON文件"
    if "s3://" in json_path:
        if client is None:
            raise ValueError("从S3读取JSON文件时必须提供client参数")
        json_bytes = client.get(json_path)
        assert (json_bytes is not None), f"从S3读取JSON文件失败: {json_path}"
        json_file = json.load(BytesIO(json_bytes))
    else:
        json_file = json.load(open(json_path, 'r'))
    return json_file

def save_json(data, json_path, client=None, verbose=True):
    """
    保存数据到JSON文件，支持本地文件和S3路径。
    
    参数:
        data (dict/list): 要保存的数据
        json_path (str): 保存路径，可以是本地路径或S3路径（以's3://'开头）
        client (optional): S3客户端实例，当写入S3路径时必需
        verbose (bool, optional): 是否打印保存成功信息，默认为True
        
    异常:
        ValueError: 如果写入S3路径时未提供client
        
    示例:
        >>> # 保存到本地文件
        >>> save_json({'key': 'value'}, 'config.json')
        >>> # 保存到S3
        >>> save_json({'key': 'value'}, 's3://bucket/config.json', client=s3_client)
    
    注意:
        - JSON将以UTF-8编码保存，ensure_ascii=False
        - 保存时会使用4空格缩进
    """
    if "s3://" in json_path:
        if client is None:
            raise ValueError("向S3写入JSON文件时必须提供client参数")
        json_bytes = json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')
        client.put(json_path, json_bytes)
    else:
        json.dump(data, open(json_path, 'w'), indent=4, ensure_ascii=False)
    if verbose:
        color.green(f"已成功将JSON数据写入文件: {json_path}")

def load_pickle(pkl_path, client=None):
    """
    加载Pickle文件，支持本地文件和S3路径。
    
    参数:
        pkl_path (str): Pickle文件路径，可以是本地路径或S3路径（以's3://'开头）
        client (optional): S3客户端实例，当读取S3路径时必需
        
    返回:
        Any: Pickle文件中存储的Python对象
        
    异常:
        ValueError: 如果读取S3路径时未提供client
        AssertionError: 如果从S3读取失败
        
    示例:
        >>> # 读取本地文件
        >>> data = load_pickle('data.pkl')
        >>> # 读取S3文件
        >>> data = load_pickle('s3://bucket/data.pkl', client=s3_client)
    """
    if "s3://" in pkl_path:
        if client is None:
            raise ValueError("从S3读取Pickle文件时必须提供client参数")
        pkl_bytes = client.get(pkl_path)
        assert (pkl_bytes is not None), f"从S3读取Pickle文件失败: {pkl_path}"
        pkl_file = pickle.load(BytesIO(pkl_bytes))
    else:
        pkl_file = pickle.load(open(pkl_path, 'rb'))
    return pkl_file

def save_pickle(data, save_path, client=None, verbose=True):
    """
    保存数据到Pickle文件，支持本地文件和S3路径。
    
    参数:
        data (Any): 要保存的Python对象
        save_path (str): 保存路径，可以是本地路径或S3路径（以's3://'开头）
        client (optional): S3客户端实例，当写入S3路径时必需
        verbose (bool, optional): 是否打印保存成功信息，默认为True
        
    异常:
        ValueError: 如果写入S3路径时未提供client
        
    示例:
        >>> # 保存到本地文件
        >>> save_pickle([1, 2, 3], 'data.pkl')
        >>> # 保存到S3
        >>> save_pickle([1, 2, 3], 's3://bucket/data.pkl', client=s3_client)
    """
    if "s3://" in save_path:
        if client is None:
            raise ValueError("向S3写入Pickle文件时必须提供client参数")
        pkl_bytes = pickle.dumps(data)
        client.put(save_path, pkl_bytes)
    else:
        pickle.dump(data, open(save_path, 'wb'))
    if verbose:
        color.green(f"已成功将Pickle数据写入文件: {save_path}")

def load_jsonl_as_list(file_path, client=None):
    """
    加载JSONL文件为Python列表，每行解析为一个JSON对象。支持本地文件和S3路径。
    
    参数:
        file_path (str): JSONL文件路径，可以是本地路径或S3路径（以's3://'开头）
        client (optional): S3客户端实例，当读取S3路径时必需
        
    返回:
        list: 包含所有JSON对象的列表
        
    异常:
        AssertionError: 如果文件扩展名不是.jsonl
        ValueError: 如果读取S3路径时未提供client
        AssertionError: 如果从S3读取失败
        
    示例:
        >>> # 读取本地文件
        >>> data = load_jsonl_as_list('data.jsonl')
        >>> # 读取S3文件
        >>> data = load_jsonl_as_list('s3://bucket/data.jsonl', client=s3_client)
    """
    assert file_path.endswith(".jsonl"), f"文件 {file_path} 不是JSONL文件"
    data = []
    if "s3://" in file_path:
        if client is None:
            raise ValueError("从S3读取JSONL文件时必须提供client参数")
        jsonl_bytes = client.get(file_path)
        assert (jsonl_bytes is not None), f"从S3读取JSONL文件失败: {file_path}"
        for line in BytesIO(jsonl_bytes):
            data.append(json.loads(line))
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line))
    return data

def save_list_to_jsonl(data, file_path, verbose=True):
    """
    将Python列表保存为JSONL文件，每个元素保存为一行JSON。
    
    参数:
        data (list): 要保存的数据列表
        file_path (str): 保存路径
        verbose (bool, optional): 是否打印保存成功信息，默认为True
        
    示例:
        >>> data = [{'id': 1}, {'id': 2}]
        >>> save_list_to_jsonl(data, 'output.jsonl')
    
    注意:
        - 每个列表元素必须是可JSON序列化的对象
        - 使用UTF-8编码保存，ensure_ascii=False
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    if verbose:
        color.green(f"已成功将list写入文件: {file_path}")

def load_jsonl_as_lines(file_path, client=None):
    """
    读取JSONL文件的原始行内容，不进行JSON解析。支持本地文件和S3路径。
    
    参数:
        file_path (str): JSONL文件路径，可以是本地路径或S3路径（以's3://'开头）
        client (optional): S3客户端实例，当读取S3路径时必需
        
    返回:
        list: 文件的行内容列表，每行末尾的换行符会被移除
        
    示例:
        >>> # 读取本地文件
        >>> lines = load_jsonl_as_lines('data.jsonl')
        >>> # 读取S3文件
        >>> lines = load_jsonl_as_lines('s3://bucket/data.jsonl', client=client)
    """
    if "s3://" in file_path:
        if client is None:
            raise ValueError("从S3读取JSONL文件时必须提供client参数")
        jsonl_bytes = client.get(file_path)
        assert (jsonl_bytes is not None), f"从S3读取JSONL文件失败: {file_path}"
        lines = [line.decode('utf-8').strip() for line in BytesIO(jsonl_bytes)]
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f]
    return lines

def save_lines_to_jsonl(lines, file_path, client=None, verbose=True):
    """
    将文本行列表保存为JSONL文件。支持本地文件和S3路径。
    
    参数:
        lines (list): 要保存的文本行列表
        file_path (str): 保存路径，可以是本地路径或S3路径（以's3://'开头）
        client (optional): S3客户端实例，当写入S3路径时必需
        verbose (bool, optional): 是否打印保存成功信息，默认为True
        
    示例:
        >>> # 保存到本地文件
        >>> save_lines_to_jsonl(['{"id": 1}', '{"id": 2}'], 'output.jsonl')
        >>> # 保存到S3
        >>> save_lines_to_jsonl(lines, 's3://bucket/output.jsonl', client=client)
    """
    if "s3://" in file_path:
        if client is None:
            raise ValueError("向S3写入JSONL文件时必须提供client参数")
        content = '\n'.join(lines).encode('utf-8')
        client.put(file_path, content)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
    if verbose:
        color.green(f"已成功将str lines写入文件: {file_path}")

def load_txt_as_lines(file_path):
    """
    读取文本文件的行内容。
    
    参数:
        file_path (str): 文本文件路径
        
    返回:
        list: 文件的行内容列表，每行末尾的换行符会被移除
        
    示例:
        >>> lines = load_txt_as_lines('data.txt')
    """
    file_lines = []
    with open(file_path, 'r') as f:
        for line in f:
            file_lines.append(line.strip())
    return file_lines

def save_lines_to_txt(lines, file_path, verbose=True):
    """
    将文本行列表保存为文本文件。
    
    参数:
        lines (list): 要保存的文本行列表
        file_path (str): 保存路径
        verbose (bool, optional): 是否打印保存成功信息，默认为True
        
    示例:
        >>> lines = ['line1', 'line2']
        >>> save_lines_to_txt(lines, 'output.txt')
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')
    if verbose:
        color.green(f"已成功将str lines写入文件: {file_path}") 