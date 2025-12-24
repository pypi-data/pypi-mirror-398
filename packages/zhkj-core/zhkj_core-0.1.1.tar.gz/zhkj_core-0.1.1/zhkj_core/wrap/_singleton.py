import inspect
from functools import wraps
from typing import Optional, Hashable, Any, Dict, Tuple, Union, Callable, List


def singleton(cls_or_constraint: Union[type, Callable, str, List[str], None] = None, *,
              constraint_attr: Optional[Union[str, List[str]]] = None):
    """
    支持指定约束属性的单例装饰器，应用于类或函数
    :param cls_or_constraint: 被装饰的类、函数或约束属性名（用于支持多种调用方式）
    :param constraint_attr: 约束属性名（可选）：
                           - 不指定：使用所有参数作为key（函数）或全局唯一（类）
                           - 指定（类）：按「类 + 约束属性值」生成单例
                           - 指定（函数）：按「函数 + 指定参数值」生成缓存key
    :return: 装饰器包装函数
    """
    # 处理不同的调用方式
    if cls_or_constraint is None:
        # @singleton() 或 @singleton(constraint_attr="id")
        def decorator(target):
            if inspect.isclass(target):
                return _singleton_class_impl(target, constraint_attr)
            elif callable(target):
                return _singleton_function_impl(target, constraint_attr)
            else:
                raise TypeError("singleton 装饰器仅支持类或函数")

        return decorator
    elif inspect.isclass(cls_or_constraint):
        # @singleton 装饰类
        return _singleton_class_impl(cls_or_constraint, constraint_attr)
    elif callable(cls_or_constraint):
        # @singleton 装饰函数
        return _singleton_function_impl(cls_or_constraint, constraint_attr)
    else:
        # @singleton("id") 旧式调用
        def decorator(target):
            if inspect.isclass(target):
                return _singleton_class_impl(target, cls_or_constraint)
            elif callable(target):
                return _singleton_function_impl(target, cls_or_constraint)
            else:
                raise TypeError("singleton 装饰器仅支持类或函数")

        return decorator


def _get_function_constraint_values(func: Callable, constraint_attrs: Union[str, List[str], None],
                                    args: tuple, kwargs: dict) -> Tuple[Hashable, ...]:
    """获取函数约束属性的实际值"""
    if constraint_attrs is None:
        # 没有指定约束属性，使用所有参数
        sorted_kwargs = tuple(sorted(kwargs.items()))
        return (args, sorted_kwargs)

    # 确保 constraint_attrs 是列表形式
    if isinstance(constraint_attrs, str):
        constraint_attrs = [constraint_attrs]

    # 检查函数签名
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())

    # 检查约束属性是否存在于函数参数中
    for attr in constraint_attrs:
        if attr not in params:
            raise ValueError(f"函数 {func.__name__} 中不存在参数 {attr}，无法作为约束属性")

    # 绑定参数
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()

    # 提取约束属性值
    values = []
    for attr in constraint_attrs:
        values.append(bound_args.arguments[attr])

    return tuple(values)


def _singleton_function_impl(func: Callable, constraint_attrs: Optional[Union[str, List[str]]] = None) -> Callable:
    """
    函数单例的实现：缓存函数执行结果
    :param func: 被装饰的函数
    :param constraint_attrs: 约束属性名（可选）：
                           - 不指定：使用所有参数作为缓存key
                           - 字符串：仅使用该参数作为缓存key
                           - 列表：使用多个参数作为缓存key
    """
    # 存储函数执行结果：key=约束属性值组合，value=函数返回值
    cache: Dict[Tuple[Hashable, ...], Any] = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        # 生成缓存key：基于约束属性
        key = _get_function_constraint_values(func, constraint_attrs, args, kwargs)

        # 如果已缓存，直接返回
        if key in cache:
            return cache[key]

        # 首次执行并缓存结果
        result = func(*args, **kwargs)
        cache[key] = result
        return result

    # 添加清除缓存的方法
    def clear_cache(specific_values: Optional[Union[Hashable, List[Hashable]]] = None) -> None:
        """
        清除函数的缓存结果
        :param specific_values: 可选，指定要清除的特定约束属性值对应的结果
        """
        if specific_values is None:
            # 清除所有缓存
            cache.clear()
        else:
            # 确保是列表形式
            if not isinstance(specific_values, list):
                specific_values = [specific_values]

            # 处理单个约束属性的情况
            if isinstance(constraint_attrs, str) or (isinstance(constraint_attrs, list) and len(constraint_attrs) == 1):
                specific_key = (specific_values[0],) if len(specific_values) == 1 else tuple(specific_values)
                if specific_key in cache:
                    del cache[specific_key]
            else:
                # 多约束属性需要精确匹配
                specific_key = tuple(specific_values)
                if specific_key in cache:
                    del cache[specific_key]

    wrapper.clear_cache = clear_cache
    # 存储约束属性信息，便于调试和文档
    wrapper.constraint_attrs = constraint_attrs
    return wrapper


def _singleton_class_impl(cls, constraint_attr: Optional[str] = None):
    """
    类单例的实际实现（保持原有逻辑不变）
    """
    # 存储单例实例：key=单例标识，value=类实例
    instances: Dict[Any, Any] = {}

    # 保存原始的 __new__ 方法
    original_new = cls.__new__

    @wraps(original_new)
    def __new__(cls, *args, **kwargs):
        # 1. 生成单例key（核心逻辑）
        if constraint_attr is None:
            # 无约束属性：key仅为类本身（全局唯一）
            key = cls
        else:
            # 有约束属性：先获取约束属性的实际值
            attr_value = get_constraint_attr_value(cls, constraint_attr, args, kwargs)
            # key=（类, 约束属性值）：确保同一类下不同属性值是不同单例
            key = (cls, attr_value)

        # 2. 如果实例已存在，则直接返回
        if key in instances:
            return instances[key]

        # 3. 创建新实例
        if original_new is object.__new__:
            # 如果原始 __new__ 是 object.__new__，只传递 cls 参数
            instance = original_new(cls)
        else:
            # 否则传递所有参数
            instance = original_new(cls, *args, **kwargs)

        instances[key] = instance
        return instance

    # 替换类的 __new__ 方法
    cls.__new__ = __new__

    # 保存原始的 __init__ 方法
    original_init = cls.__init__

    @wraps(original_init)
    def __init__(self, *args, **kwargs):
        # 检查是否已经初始化过
        if hasattr(self, '_singleton_initialized'):
            return

        # 执行原始初始化逻辑
        original_init(self, *args, **kwargs)

        # 标记为已初始化
        self._singleton_initialized = True

    # 替换类的 __init__ 方法
    cls.__init__ = __init__

    # 修改 classmethod 行为
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if isinstance(attr, classmethod):
            # 保存原始的 classmethod
            original_cm = attr.__func__

            # 创建新的 classmethod
            def new_classmethod(cls, *args, **kwargs):
                # 直接调用类的构造函数，确保使用我们重写的 __new__ 方法
                return cls(*args, **kwargs)

            # 替换 classmethod
            setattr(cls, attr_name, classmethod(new_classmethod))

    # 添加清除缓存的类方法
    @classmethod
    def clear_cache(cls, specific_value: Optional[Hashable] = None) -> None:
        """
        清除类的单例实例缓存
        :param specific_value: 可选，指定要清除的特定约束属性值对应的实例
        """
        if specific_value is None:
            # 清除该类的所有实例
            keys_to_remove = [k for k in instances if k == cls or (isinstance(k, tuple) and k[0] == cls)]
        else:
            # 只清除特定约束属性值对应的实例
            keys_to_remove = [(cls, specific_value)] if constraint_attr else []

        for key in keys_to_remove:
            if key in instances:
                del instances[key]

    cls.clear_cache = clear_cache
    return cls


def get_constraint_attr_value(cls, attr_name: str, args: tuple, kwargs: dict) -> Hashable:
    """
    获取约束属性的实际值（处理「位置参数」和「关键字参数」两种传参方式）
    """
    # 步骤1：检查约束属性是否在类的__init__参数中
    init_signature = inspect.signature(cls.__init__)
    if attr_name not in init_signature.parameters:
        raise ValueError(f"类 {cls.__name__} 的 __init__ 方法中不存在参数 {attr_name}，无法作为约束属性")

    # 步骤2：优先从关键字参数中获取属性值
    if attr_name in kwargs:
        return kwargs[attr_name]

    # 步骤3：从位置参数中获取属性值（需匹配参数位置）
    # 获取__init__的参数列表（排除第一个self参数）
    init_params = list(init_signature.parameters.values())[1:]  # [1:] 跳过self
    # 找到约束属性在参数列表中的索引
    attr_index = None
    for idx, param in enumerate(init_params):
        if param.name == attr_name:
            attr_index = idx
            if idx < len(args):
                return args[idx]
            # 如果位置参数中没有，检查是否有默认值
            if param.default is not inspect.Parameter.empty:
                return param.default
            break

    # 检查位置参数是否足够
    if attr_index is None or attr_index >= len(args):
        raise ValueError(f"类 {cls.__name__} 初始化时，未传入约束属性 {attr_name}（需通过位置参数或关键字参数传递）")

    # 步骤4：返回位置参数中对应的属性值
    return args[attr_index]


# 全局缓存清理函数
def clear_all_singletons() -> None:
    """清除所有单例装饰器管理的缓存（类实例和函数结果）"""
    # 清除所有类的单例缓存
    for cls in list(_singleton_class_impl.instances.keys()):
        if inspect.isclass(cls) or (isinstance(cls, tuple) and inspect.isclass(cls[0])):
            target_cls = cls if inspect.isclass(cls) else cls[0]
            if hasattr(target_cls, 'clear_cache'):
                target_cls.clear_cache()


# 为类单例实现添加一个类级别的实例字典引用
_singleton_class_impl.instances = {}