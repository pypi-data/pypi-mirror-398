import random
from fvgtools.utils import load_jsonl_as_list, load_json, color

__all__ = ['sample_by_repeat_time', 'count_total_sample']

def sample_by_repeat_time(sample_target, repeat_time, random_seed=None):
    """
    根据repeat_time对数据进行采样或重复。
    
    参数:
        sample_target (Union[str, list]): 采样目标，可以是：
            - str: JSONL文件路径（本地路径）
            - list: 直接传入的数据列表
        repeat_time (float): 采样/重复参数：
            - 如果 0 < repeat_time <= 1.0：表示采样比例（例如0.5表示保留50%的数据）
            - 如果 repeat_time > 1.0：表示每个样本重复的次数（例如2.0表示每个样本重复2次，
                                      2.5表示每个样本重复2次，并有50%概率再重复1次）
        random_seed (int, optional): 随机种子，用于可重复的采样结果
        
    返回:
        list: 处理后的数据列表
        
    异常:
        ValueError: 如果repeat_time <= 0
        TypeError: 如果sample_target类型不支持
        
    示例:
        >>> # 从文件采样
        >>> sampled_data = sample_by_repeat_time('data.jsonl', 0.5)
        
        >>> # 直接对列表采样
        >>> data = [{'id': 1}, {'id': 2}, {'id': 3}]
        >>> sampled_data = sample_by_repeat_time(data, 0.5)
        
        >>> # 每个样本重复2.3次（平均）
        >>> repeated_data = sample_by_repeat_time('data.jsonl', 2.3)
        
        
        >>> # 使用随机种子保证可重复性
        >>> sampled_data = sample_by_repeat_time(
        ...     'data.jsonl', 0.5, random_seed=42
        ... )
    """
    if repeat_time <= 0:
        raise ValueError(f"repeat_time必须大于0，当前值: {repeat_time}")
    
    # 设置随机种子（如果提供）
    if random_seed is not None:
        random.seed(random_seed)
    
    # 根据输入类型加载数据
    if isinstance(sample_target, str):
        # 如果是字符串，视为文件路径
        data = load_jsonl_as_list(sample_target)
    elif isinstance(sample_target, list):
        # 如果是列表，直接使用
        data = sample_target
    else:
        raise TypeError(
            f"sample_target必须是str（文件路径）或list（数据列表），"
            f"当前类型: {type(sample_target)}"
        )
    
    # 分解repeat_time为整数部分和小数部分
    int_part = int(repeat_time)
    frac_part = repeat_time - int_part
    
    result = []
    
    # 处理整数部分：每个样本重复int_part次
    if int_part > 0:
        result.extend(data * int_part)
    
    # 处理小数部分：随机采样frac_part比例的数据
    if frac_part > 0:
        sample_size = int(len(data) * frac_part)
        result.extend(random.sample(data, sample_size))
    
    return result

def count_total_sample(json_path, load_file=True):
    """
    计算一个数据配置JSON文件中，按repeat_time加权后的样本总数。
    
    参数:
        json_path (str): JSON配置文件路径
        load_file (bool, optional): 是否真实加载jsonl文件。默认为True
            - True: 加载jsonl文件获取实际长度
            - False: 直接使用配置中的length字段
    
    返回:
        float: 按repeat_time加权后的样本总数
    
    注意:
        - JSON文件结构应至少包含: {key: {annotation: jsonl路径, repeat_time: 重复倍数, length: 预期长度}}，缺少会抛出 KeyError
        - 如果load_file=True且实际长度与配置的length不一致，会以洋红色打印警告信息
    
    示例:
        >>> # 直接使用配置中的length
        >>> total = count_total_sample('data.json', load_file=False)
        >>> # 加载文件获取实际长度
        >>> total = count_total_sample('data.json', load_file=True)
    """
    data = load_json(json_path)
    total = 0
    
    for key, value in data.items():
        repeat_time = value['repeat_time']
        jsonl_length = value['length']
        jsonl_path = value['annotation']
        if load_file:
            # 加载jsonl文件获取实际长度
            actual_length = len(load_jsonl_as_list(jsonl_path))
            total += repeat_time * actual_length

            if actual_length != jsonl_length:
                color.magenta(f"⚠️  警告 [{key}]: 实际长度 {actual_length} != 数据文件中的长度 {jsonl_length}")
        else:
            total += repeat_time * jsonl_length
    
    return total