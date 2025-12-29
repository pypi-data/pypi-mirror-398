# Copyright 2025 UsamaAliceWhite All Rights Reserved


# 標準モジュール
from __future__ import annotations
from dataclasses import dataclass
from logging import DEBUG, Formatter,getLogger, Logger
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from threading import Lock


# 引数管理
@dataclass
class _LoggingConfig:
    file_path: Path | str
    when: str
    interval: int
    backup_count: int
    encoding: str
    level: int
    text_format: str
    date_format: str


# ロギング機能
class _LoggingFunctions:
    # 初期化
    _instance: _LoggingFunctions | None = None
    _initialized: bool = False
    _lock: Lock = Lock()

    # インスタンスの制御
    def __new__(cls, *args, **kwargs) -> _LoggingFunctions:
        # Anonymous
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    # Anonymous
    def __init__(self, config: _LoggingConfig) -> None:

        # 初回実行を確認
        if self._initialized:
            return None
        with self._lock:
            if self._initialized:
                return None

            # Anonymous
            self.config: _LoggingConfig = config

            # Anonymous
            self._setup_handler()

    # ログハンドラーの設定
    def _setup_handler(self) -> None:
        # ログファイルのディレクトリを作成
        try:
            file_path = Path(self.config.file_path)
            directory_path: Path = file_path.parent
            directory_path.mkdir(exist_ok= True, parents= True)
        except Exception as e:
            raise RuntimeError("Failed to create the log directory.") from e

        # ログハンドラーを作成及び設定
        try:
            file_handler: TimedRotatingFileHandler = TimedRotatingFileHandler(
                filename= str(file_path),
                when= self.config.when,
                interval= self.config.interval,
                backupCount= self.config.backup_count,
                encoding= self.config.encoding
            )
            file_handler.setFormatter(
                Formatter(
                    fmt= self.config.text_format,
                    datefmt= self.config.date_format
                )
            )
            file_handler.setLevel(self.config.level)
        except Exception as e:
            raise RuntimeError(
                "Failed to configure the log file handler."
            ) from e
        
        # Anonymous
        self.file_handler: TimedRotatingFileHandler = file_handler
        self._initialized = True
    
    # ロガーの設定
    def setup_logger(self, name: str, level: int) -> Logger:
        # ロギングの初期化を確認
        if not self._initialized:
            raise RuntimeError("Logging system has not been initialized.")
        
        # ロガーを作成及び設定
        with self._lock:
            try:
                logger: Logger = getLogger(name)
                if self.file_handler not in logger.handlers:
                    logger.setLevel(level)
                    logger.addHandler(self.file_handler)
                    logger.propagate = False
            except Exception as e:
                raise RuntimeError("Failed to setup logger.") from e
            
        # Anonymous
        return logger
    

# ロガーの取得
class GetLogger:
    # Anonymous
    def __new__(cls,
                log_file_path: Path | str = Path.home() / "Unknown.log",
                log_when: str = "midnight",
                log_interval: int = 1,
                log_backup_count: int = 99,
                log_encoding: str = "utf-8",
                log_level: int = DEBUG,
                log_text_format: str = (
                    "%(asctime)s - %(name)-50s - %(funcName)-40s - "
                    "%(levelname)-8s - %(message)s"
                ),
                log_date_format: str = "%Y-%m-%d %H:%M:%S",
                logger_name: str = "Unknown",
                logger_level: int = DEBUG) -> Logger:
        # ロギングを初期化
        config = _LoggingConfig(
            file_path= log_file_path,                    
            when= log_when,
            interval= log_interval,
            backup_count= log_backup_count,
            encoding= log_encoding,
            level= log_level,
            text_format= log_text_format,
            date_format= log_date_format
        )
        log = _LoggingFunctions(config= config)

        # ロガーを取得
        logger: Logger = log.setup_logger(
            name= logger_name,
            level= logger_level
        )

        # Anonymous
        return logger