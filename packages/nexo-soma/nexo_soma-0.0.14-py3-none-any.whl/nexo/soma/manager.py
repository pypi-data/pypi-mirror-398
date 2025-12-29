from pathlib import Path
from typing import Generic, Type
from uuid import UUID
from nexo.google.secret import Format, GoogleSecretManager
from nexo.logging.config import LogConfig
from nexo.logging.logger import ApplicationLoggers
from nexo.schemas.application import ApplicationSettingsT, ApplicationContext
from nexo.schemas.key.rsa import Keys
from nexo.types.string import OptStr
from nexo.utils.loaders.yaml import from_path, from_string
from .config import ApplicationConfigT


class ApplicationManager(Generic[ApplicationSettingsT, ApplicationConfigT]):
    def __init__(
        self,
        operation_id: UUID,
        google_secret_manager: GoogleSecretManager,
        log_config: LogConfig,
        settings: ApplicationSettingsT,
        config_cls: Type[ApplicationConfigT],
        key_password_secret_name: OptStr = None,
        private_key_secret_name: OptStr = None,
        public_key_secret_name: OptStr = None,
    ):
        self._log_config = log_config
        self.settings = settings
        self._config_cls = config_cls
        self._key_password_secret_name = key_password_secret_name
        self._private_key_secret_name = private_key_secret_name
        self._public_key_secret_name = public_key_secret_name

        self.application_context = ApplicationContext.new()

        self._load_config(operation_id, google_secret_manager)
        self._load_keys(operation_id, google_secret_manager)
        self._initialize_loggers()

    def _load_config(
        self, operation_id: UUID, google_secret_manager: GoogleSecretManager
    ):
        use_local = self.settings.USE_LOCAL_CONFIG
        config_path = self.settings.CONFIG_PATH

        if use_local and config_path is not None and isinstance(config_path, str):
            config_path = Path(config_path)
            if config_path.exists() and config_path.is_file():
                data = from_path(config_path)
                self.config: ApplicationConfigT = self._config_cls.model_validate(data)
                return

        name = f"{self.settings.SERVICE_KEY}-config-{self.settings.ENVIRONMENT}"
        read_secret = google_secret_manager.read(
            Format.STRING, name=name, operation_id=operation_id
        )
        data = from_string(read_secret.data.value)
        self.config: ApplicationConfigT = self._config_cls.model_validate(data)

    def _load_keys(
        self, operation_id: UUID, google_secret_manager: GoogleSecretManager
    ):
        if self.settings.PRIVATE_KEY_PASSWORD is not None:
            password = self.settings.PRIVATE_KEY_PASSWORD
        else:
            if self._key_password_secret_name is None:
                raise ValueError(
                    "Provide key password secret name if not provided in environment variable"
                )
            read_key_password = google_secret_manager.read(
                Format.STRING,
                name=self._key_password_secret_name,
                operation_id=operation_id,
            )
            password = read_key_password.data.value

        if self.settings.USE_LOCAL_KEY:
            self.keys = Keys.from_path(
                private=self.settings.PRIVATE_KEY_PATH,
                public=self.settings.PUBLIC_KEY_PATH,
                password=password,
            )
        else:
            if self._private_key_secret_name is None:
                raise ValueError(
                    "Provide private key secret name if not provided in environment variable"
                )
            read_private_key = google_secret_manager.read(
                Format.STRING,
                name=self._private_key_secret_name,
                operation_id=operation_id,
            )
            private = read_private_key.data.value

            if self._public_key_secret_name is None:
                raise ValueError(
                    "Provide public key secret name if not provided in environment variable"
                )
            read_public_key = google_secret_manager.read(
                Format.STRING,
                name=self._public_key_secret_name,
                operation_id=operation_id,
            )
            public = read_public_key.data.value

            self.keys = Keys.from_string(
                private=private, public=public, password=password
            )

    def _initialize_loggers(self):
        self.loggers = ApplicationLoggers.new(
            environment=self.settings.ENVIRONMENT,
            service_key=self.settings.SERVICE_KEY,
            config=self._log_config,
        )
