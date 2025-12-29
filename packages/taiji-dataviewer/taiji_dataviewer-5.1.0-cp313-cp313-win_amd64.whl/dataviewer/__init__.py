__version__ = "5.1.0"

# 延迟导入，只有用户访问 dataviewer.main 时才会 import
def __getattr__(name: str):
    if name == "main":
        from .mainWindow import main
        return main
    raise AttributeError(f"module {__name__} has no attribute {name}")
