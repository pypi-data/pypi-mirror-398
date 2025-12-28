import importlib.metadata

from pydantic_settings import BaseSettings

metadata = importlib.metadata.metadata("pymecli")
# module_dir = Path(__file__).resolve().parent.parent

# project = read_toml(str(module_dir / "./pyproject.toml"))["project"]


class Settings(BaseSettings):
    # API配置
    API_V1_STR: str = "/api/v1"
    NAME: str = metadata["Name"]
    DESCRIPTION: str = f"{metadata['Summary']}, FastAPI提供[onnx-paddleocr识别、douzero、clash订阅转换]"
    VERSION: str = metadata["Version"]

    print(f"project: {NAME}")
    print(f"version: {VERSION}")
    print(f"description: {DESCRIPTION}")

    class Config:
        env_prefix = "MY_CLI_API_"  # 添加环境变量前缀
        case_sensitive = True

    def reload(self):
        new_settings = Settings()
        for field in Settings.model_fields:
            setattr(self, field, getattr(new_settings, field))


settings = Settings()
