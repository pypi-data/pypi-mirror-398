class color:
    """
    简单的颜色打印工具类。
    
    使用方法:
        >>> color.red("这是红色")  # 直接打印并返回着色字符串
        >>> color.blue("这是蓝色")  # 直接打印并返回着色字符串
        >>> color.custom("自定义颜色", color="ff5733")  # HEX颜色代码（6位）
        >>> color.custom("自定义颜色", color="#ff5733")  # HEX颜色代码（7位）
        >>> color.custom("自定义颜色", color=(255, 87, 51))  # RGB元组
        >>> print(f"混合颜色: {color.red('红色')} 和 {color.custom('橙色', '#ff5733')}")
        
    支持的颜色:
        - 基础颜色: black, red, green, yellow, blue, magenta, cyan, white
        - 文本样式: bold, underline
        - 自定义颜色:
            - RGB元组: color.custom(text, color=(r, g, b))
            - HEX字符串: color.custom(text, color="#ff5733") 或 color.custom(text, color="ff5733")
    """
    @staticmethod
    def _colorize(text, color_code):
        colored_text = f"\033[{color_code}m{text}\033[0m"
        print(colored_text)
        return colored_text
    
    @staticmethod
    def _rgb_to_ansi(r, g, b):
        """将RGB颜色转换为ANSI转义序列"""
        return f"38;2;{r};{g};{b}"
    
    @staticmethod
    def _hex_to_rgb(hex_color):
        """将HEX颜色代码转换为RGB值"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError("HEX颜色代码必须是6位（例如：ff5733）")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def _validate_rgb(rgb):
        """验证RGB值是否合法"""
        if not isinstance(rgb, (tuple, list)) or len(rgb) != 3:
            raise ValueError("RGB颜色必须是一个包含3个元素的元组或列表")
        if not all(isinstance(x, int) and 0 <= x <= 255 for x in rgb):
            raise ValueError("RGB颜色值必须是0-255之间的整数")
        return True

    @staticmethod
    def black(text): 
        return color._colorize(text, color._rgb_to_ansi(0, 0, 0))
    
    @staticmethod
    def red(text): 
        return color._colorize(text, color._rgb_to_ansi(255, 0, 0))
    
    @staticmethod
    def green(text): 
        return color._colorize(text, color._rgb_to_ansi(0, 255, 0))
    
    @staticmethod
    def yellow(text): 
        return color._colorize(text, color._rgb_to_ansi(255, 255, 0))
    
    @staticmethod
    def blue(text): 
        return color._colorize(text, color._rgb_to_ansi(0, 0, 255))
    
    @staticmethod
    def magenta(text): 
        return color._colorize(text, color._rgb_to_ansi(255, 0, 255))
    
    @staticmethod
    def cyan(text): 
        return color._colorize(text, color._rgb_to_ansi(0, 255, 255))
    
    @staticmethod
    def white(text): 
        return color._colorize(text, color._rgb_to_ansi(255, 255, 255))
    
    @staticmethod
    def bold(text): return color._colorize(text, '1')
    
    @staticmethod
    def underline(text): return color._colorize(text, '4')

    @staticmethod
    def custom(text, color):
        """
        使用自定义颜色打印文本。
        
        参数:
            text (str): 要打印的文本
            color (Union[str, Tuple[int, int, int]]): 颜色值，可以是以下格式：
                - RGB元组：(r, g, b)，每个值都是0-255之间的整数
                - HEX字符串：'ff5733' 或 '#ff5733'
        
        返回:
            str: 着色后的字符串
            
        示例:
            >>> color.custom("文本", color="ff5733")
            >>> color.custom("文本", color="#ff5733")
            >>> color.custom("文本", color=(255, 87, 51))
        """
        if isinstance(color, str):
            r, g, b = color._hex_to_rgb(color)
        else:
            color._validate_rgb(color)
            r, g, b = color
        
        return color._colorize(text, color._rgb_to_ansi(r, g, b))
    
    # 保留 rgb 和 hex 方法作为向后兼容
    @staticmethod
    def rgb(r, g, b):
        """使用RGB值创建自定义颜色（建议使用更通用的custom方法）"""
        return lambda text: color.custom(text, (r, g, b))
    
    @staticmethod
    def hex(hex_color):
        """使用HEX颜色代码创建自定义颜色（建议使用更通用的custom方法）"""
        return lambda text: color.custom(text, hex_color) 