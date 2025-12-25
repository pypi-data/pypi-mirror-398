from amsdal.contrib.app_config import AppConfig


class MLPluginAppConfig(AppConfig):
    name = "amsdal_ml"
    verbose_name = "AMSDAL ML Plugin"

    def on_ready(self) -> None: ...
