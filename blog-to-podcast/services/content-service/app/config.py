import os


class Settings:
    use_mock: bool = os.getenv("USE_MOCK", "true").lower() == "true"


settings = Settings()
