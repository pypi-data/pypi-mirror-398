from PIL import Image
import numpy as np
import io
from io import BytesIO
import configparser
from .color import color
from aoss_client.client import Client
import re

__all__ = [
    'parse_config', 'init_client', 'general_load_image',
    'split_s3path', 's3path_to_ads', 'ads_to_s3path'
]

def parse_config(conf_path, verbose=False):
    """
    解析AOSS配置文件并可选地打印配置信息。
    
    参数:
        conf_path (str): 配置文件路径
        verbose (bool, optional): 是否打印配置信息，默认为False
        
    返回:
        configparser.ConfigParser: 解析后的配置对象
        
    示例:
        >>> config = parse_config('/path/to/aoss.conf', verbose=True)
    
    注意:
        当verbose=True时，会打印以下信息：
        - 默认集群信息
        - 每个section的host_base
        - 加密显示的access_key和secret_key
    """
    config = configparser.ConfigParser()
    config.read(conf_path)
    if verbose:
        # 获取默认集群
        default_cluster = config['DEFAULT'].get('default_cluster', None)
        
        # 打印所有配置信息
        color.cyan("\n=== Your Current AOSS Configuration ===")
        color.yellow(f"Default cluster: {default_cluster}")
        
        for section in config.sections():
            color.cyan(f"\n[{section}]")
            if 'host_base' in config[section]:
                color.yellow(f"host_base: {config[section]['host_base']}")
            if 'access_key' in config[section]:
                color.yellow(f"access_key: {config[section]['access_key'][:2]}" + "*" * (len(config[section]['access_key']) - 2))
            if 'secret_key' in config[section]:
                color.yellow(f"secret_key: {config[section]['secret_key'][:2]}" + "*" * (len(config[section]['secret_key']) - 2))
        
        color.magenta(f"\n初始化ceph client通常需要10s左右，请耐心等待...")
    
    return config

def init_client(conf_path="/mnt/afs/fanjianan/aoss_omni.conf", ret_config=False):
    """
    初始化对象存储客户端并可选地返回配置信息。
    
    参数:
        conf_path (str, optional): 配置文件路径，默认为"/mnt/afs/fanjianan/aoss_omni.conf"
        ret_config (bool, optional): 是否同时返回配置信息，默认为False
        
    返回:
        Client: 对象存储客户端实例
        configparser.ConfigParser: 配置对象（仅当ret_config=True时返回）
        
    示例:
        >>> # 只获取客户端
        >>> client = init_client()
        >>> # 同时获取客户端和配置
        >>> client, config = init_client(ret_config=True)
    """
    config = parse_config(conf_path, verbose=True)
    client = Client(conf_path)
    if ret_config:
        return client, config
    else:
        return client

def general_load_image(img_ptr, client):
    """
    从多种输入类型加载图像并返回PIL.Image对象。
    
    参数:
        img_ptr (Union[np.ndarray, PIL.Image.Image, str]): 图像来源，可以是：
            - NumPy数组（假设为RGB格式）
            - PIL.Image.Image对象
            - 字符串路径（本地文件或S3路径）
        client: S3客户端实例，用于加载S3路径的图像
        
    返回:
        PIL.Image.Image: 加载的图像对象
        
    异常:
        TypeError: 如果输入类型不支持或数据无效
        AssertionError: 如果从S3加载失败
        
    示例:
        >>> # 从NumPy数组加载
        >>> img = general_load_image(np_array, client)
        >>> # 从S3加载
        >>> img = general_load_image('s3://bucket/image.jpg', client)
        >>> # 从本地文件加载
        >>> img = general_load_image('image.jpg', client)
    """
    if isinstance(img_ptr, np.ndarray): # 这里默认它已经是RGB空间的了，否则要进行转换
        image = Image.fromarray(img_ptr.astype('uint8'))
    elif isinstance(img_ptr, Image.Image):
        image = img_ptr
    elif isinstance(img_ptr, str):
        if 's3://' in img_ptr:
            img_bytes = client.get(img_ptr)
            assert (img_bytes is not None), f"从S3加载图像失败: {img_ptr}"
            image = Image.open(io.BytesIO(img_bytes))
        else:
            image = Image.open(img_ptr)
    else:
        raise TypeError("输入不是有效的图像类型")
    return image

def split_s3path(s3path):
    """
    从S3 URL中分离出桶名和剩余路径。
    
    参数:
        s3path (str): S3 URL，格式为's3://bucket/path/to/file'
        
    返回:
        tuple: (bucket_name, key)
            - bucket_name (str): 桶名
            - key (str): 对象键（路径）
            
    异常:
        ValueError: 如果S3路径格式无效
        
    示例:
        >>> bucket, key = split_s3path('s3://my-bucket/path/to/file.txt')
        >>> print(bucket)  # 'my-bucket'
        >>> print(key)     # 'path/to/file.txt'
    """
    path_parts = s3path.split('/')
    if len(path_parts) < 3:
        raise ValueError(f"S3路径格式无效（检查是否输入完整路径）: {s3path}")
    return path_parts[2], '/'.join(path_parts[3:])

def s3path_to_ads(s3path, client, configSec="defualt"):
    """
    将S3路径转换为带认证信息的ADS路径。
    
    参数:
        s3path (str): S3路径，格式为's3://bucket/path/to/file'
        client: S3客户端实例，用于获取配置信息
        configSec (str, optional): 配置文件中的section名，默认为"defualt"
        
    返回:
        str: 带认证信息的ADS路径，格式为's3://{access_key}:{secret_key}@{bucket}.{host_base}/{path}'
        
    异常:
        ValueError: 如果S3路径格式无效或配置section不存在
        
    示例:
        >>> ads_path = s3path_to_ads('s3://my-bucket/path/to/file.txt', client)
        >>> print(ads_path)  # 's3://ak:sk@my-bucket.host.com/path/to/file.txt'
    """
    bucket_name, path_left = split_s3path(s3path)
    config = parse_config(client._conf_path, verbose=False)
    if configSec not in config.sections():
        raise ValueError(f"配置文件中未找到指定的section: {configSec}")
    ak, sk, host_base = config[configSec]['access_key'], config[configSec]['secret_key'], config[configSec]['host_base']
    return f"s3://{ak}:{sk}@{bucket_name}.{host_base}/{path_left}"

def ads_to_s3path(ads_path):
    """
    将ADS路径转换为S3路径。
    
    参数:
        ads_path (str): ADS路径，格式为's3://{ak}:{sk}@{bucket}.{host}/{path}'
        
    返回:
        str: S3路径
        
    异常:
        ValueError: 如果ADS路径格式无效
        
    示例:
        >>> s3_path = ads_to_s3path('s3://access_key:secret_key@my-bucket.host.com/path/to/file.txt')
        >>> print(s3_path)  # 's3://my-bucket/path/to/file.txt'
    """
    # 使用正则表达式检查路径格式
    pattern = r'^s3://[^:]+:[^@]+@([^.]+)\.[^/]+/(.+)$'
    match = re.match(pattern, ads_path)
    if not match:
        raise ValueError(f"ADS路径格式无效: {ads_path}")
    
    # 提取bucket_name和path_left
    bucket_name = match.group(1)
    path_left = match.group(2)
    
    return f"s3://{bucket_name}/{path_left}" 