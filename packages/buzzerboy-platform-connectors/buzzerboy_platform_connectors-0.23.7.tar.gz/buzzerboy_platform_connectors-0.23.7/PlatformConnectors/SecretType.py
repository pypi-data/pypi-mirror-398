from enum import Enum

class SecretType(Enum):
    SECRET_STRING = "secret_string"
    DOT_ENV = "dot_env"
    ENVIRONMENT_VARIABLES = "environment_variables"
    AWS_SECRET_MANAGER = "aws_secret_manager"
