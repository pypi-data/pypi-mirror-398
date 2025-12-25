from typing import List, Optional, Union
from pyscreeps_arena.ui.qrecipe.model import PartsVector

class NamedRecipe:
    def __init__(self, name: str, recipe: List[str]):
        self.name = name
        self.recipe = recipe

class CreepLogicSettings:
    """
    爬虫逻辑设置类，用于定义爬虫的基本属性和行为。
    """
    
    def __init__(self):
        # ---------------------- 爬虫本体 | Creep --------------------------- #
        self.draw: bool = False  # 是否绘制爬虫信息
        self.layer: int = 10  # 爬虫绘制图层，默认为10
        
        # ---------------------- 流程与结构 | Flow & Struct --------------------------- #
        self.link: Union[List[str], str, None] = None  # 爬虫逻辑链接
        self.once: bool = True  # 是否禁用死亡后重生
        
        # ---------------------- 孵化选项 | Spawning --------------------------- #
        self.spawnable = True  # 是否可以孵化标志
        self.recipe: Union[List[str], NamedRecipe] = ["MOVE"]  # 爬虫配方，默认为["MOVE"]
        self.optimise: bool = True  # 自动优化配方标志
        self.extension: bool = True  # 使用extension标志
        self.direction: Optional[int] = None  # 出生方向
        
        # ---------------------- 基本信息 | Basic Info --------------------------- #
        self.name: str = ""  # 爬虫名称
    
    def to_dict(self) -> dict:
        """
        将设置转换为字典格式
        """
        return {
            "name": self.name,
            "draw": self.draw,
            "layer": self.layer,
            "link": self.link,
            "once": self.once,
            "spawnable": self.spawnable,
            "recipe": self.recipe if isinstance(self.recipe, list) else self.recipe.name,
            "optimise": self.optimise,
            "extension": self.extension,
            "direction": self.direction
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CreepLogicSettings":
        """
        从字典格式创建设置对象
        """
        settings = cls()
        settings.name = data.get("name", "")
        settings.draw = data.get("draw", False)
        settings.layer = data.get("layer", 10)
        settings.link = data.get("link", None)
        settings.once = data.get("once", True)
        settings.spawnable = data.get("spawnable", True)
        settings.recipe = data.get("recipe", ["MOVE"])
        settings.optimise = data.get("optimise", True)
        settings.extension = data.get("extension", True)
        settings.direction = data.get("direction", None)
        return settings
    
    def reset(self):
        """
        重置所有设置为默认值
        """
        self.__init__()
