from typing import Dict
from confclasses import confclass

@confclass
class LoggingConfig:
    level: str = "info"
    loggers: Dict[str, str] = {
        "botocore": "warn",
        "paramiko": "warn"
    }
    """key value dictionary to override log level on, some modules make a lot of noise, botocore for example"""

@confclass
class Config:
    log: LoggingConfig
    group_tag_key: str = "group"
    """Tag key to use when filtering, this is usually set during ssm setup."""
    aws_profile: str = "default"
    """AWS profile to use when connecting to AWS services, often overridden by --profile"""
    
CONFIG = Config()
