__version__ = "1.3.0"

# 延迟导入，只有用户访问 datacollector.main 时才会 import
def __getattr__(name: str):
    if name == "main":
        from .DataCollector import main
        return main
    raise AttributeError(f"module {__name__} has no attribute {name}")
