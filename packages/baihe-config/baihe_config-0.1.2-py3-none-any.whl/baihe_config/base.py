from pathlib import Path

from pydantic import BaseModel


class BaseConfig(BaseModel):
    """
    基础配置类，继承自 `BaseModel`。

    该类包含以下私有属性：
    - `_persistent` (bool): 标记对象是否应该持久化。
    - `_filepath` (Path): 用于存储持久化数据的文件路径。
    - `_loading` (bool): 标记当前是否处于加载模式。
    """
    _persistent: bool  # 持久化
    _filepath: Path  # 文件储存位置
    _loading: bool = False  # 标志位，指示是否在加载模式

    def __init__(self, persistent=False, filepath=None, **data):
        """
        初始化 `BaseConfig` 对象。

        参数:
            persistent (bool): 是否启用持久化。默认为 `False`。
            filepath (str, optional): 持久化文件路径。如果未提供，则使用类名生成默认路径。
            **data: 传递给父类的其他初始化参数。

        初始化过程包括：
        1. 调用父类的 `__init__` 方法。
        2. 设置 `_filepath` 属性。
        3. 设置 `_persistent` 属性。
        4. 如果启用持久化，调用 `load` 方法从文件中加载数据。
        """
        super().__init__(**data)
        self._filepath = Path(filepath or f'{self.__class__.__name__.lower()}.json')
        self._persistent = persistent
        if self._persistent:
            self.load()

    def load(self):
        """
        加载数据并将其应用于当前对象。

        在加载模式下，方法会尝试从指定的文件中读取 JSON 数据并使用
        `setattr` 方法将其应用于对象的字段。如果文件不存在或数据无效，
        则会调用 `save` 方法保存当前设置。

        该方法在执行前会将 `_loading` 标志设置为 True，以防止循环调用。

        异常处理:
            - FileNotFoundError: 如果文件未找到，调用 `save` 方法。
            - ValueError: 如果 JSON 数据验证失败，调用 `save` 方法。
        """
        self._loading = True  # 进入加载模式

        try:
            with self._filepath.open('r') as f:
                new_obj = self.model_validate_json(f.read())
                # 使用 setattr 批量设置所有字段
                for field in self.__class__.model_fields:
                    setattr(self, field, getattr(new_obj, field))
        except (FileNotFoundError, ValueError):
            self.save()

        self._loading = False  # 退出加载模式

    def save(self):
        """
        将当前设置保存到 _file_path 指定的 JSON 文件中。
        """
        # 检查目录是否存在
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        with self._filepath.open('w') as f:
            data = self.model_dump_json(indent=4)
            f.write(data)

    def __setattr__(self, key, value):
        """
        重写 `__setattr__` 方法，用于在属性更改时自动保存数据。

        参数:
            key (str): 要设置的属性名。
            value: 要设置的属性值。
        """
        # 获取当前属性的旧值，如果属性名在字段中则获取其值，否则为 None
        is_field = True if key in self.__class__.model_fields else False
        old_value = getattr(self, key, None)  # 获取旧值

        # 使用父类的 `__setattr__` 方法设置新值
        super().__setattr__(key, value)

        # 如果旧值存在且不同于新值，并且不在加载模式且处于持久化状态，则保存当前设置
        if is_field and old_value != value and not self._loading and self._persistent:
            self.save()

    @property
    def persistent(self):
        return self._persistent

    @persistent.setter
    def persistent(self, value):
        self._persistent = value
        if self._persistent:
            self.load()

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, value):
        self._filepath = Path(value)
        if self._persistent:
            self.load()
