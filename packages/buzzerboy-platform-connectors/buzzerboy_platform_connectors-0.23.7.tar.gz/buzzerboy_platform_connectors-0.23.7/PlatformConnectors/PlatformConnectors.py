"""
Buzzerboy Platform Connectors - Core Configuration Module

This module provides a comprehensive interface for accessing configuration values
from multiple secret sources. It supports various Django application configurations
including database, email, AWS, and authentication settings.

The module supports four secret management patterns:

1. **SECRET_STRING** (default): JSON-encoded secret string from environment variable
2. **ENVIRONMENT_VARIABLES**: Direct access to all environment variables
3. **DOT_ENV**: Load secrets from a .env file
4. **AWS_SECRET_MANAGER**: Load secrets from AWS Secrets Manager

The secret type is configured via Django settings (PLATFORM_SECRET_TYPE) or the
PLATFORM_SECRET_TYPE environment variable.

Secret Type Configuration:
    Set PLATFORM_SECRET_TYPE to one of:

    - 'secret_string' (default): Use SECRET_STRING environment variable with JSON
    - 'environment_variables': Use all environment variables directly
    - 'dot_env': Load from .env file (path configurable via PLATFORM_ENVIRONMENT_VARIABLES_FILE)
    - 'aws_secret_manager': Load JSON secret from AWS Secrets Manager (name via
      PLATFORM_SECRET_NAME)

Example:
    Basic usage with SECRET_STRING::

        export PLATFORM_SECRET_TYPE='secret_string'
        export SECRET_STRING='{"dbname": "mydb", "username": "admin"}'

        from PlatformConnectors import PlatformConnectors as pc

        db_name = pc.getDBName('default_db')
        db_user = pc.getDBUser('admin')

    Using ENVIRONMENT_VARIABLES::

        export PLATFORM_SECRET_TYPE='environment_variables'
        export dbname='mydb'
        export username='admin'

        from PlatformConnectors import PlatformConnectors as pc

        db_name = pc.getDBName('default_db')

    Using DOT_ENV file::

        export PLATFORM_SECRET_TYPE='dot_env'
        export PLATFORM_ENVIRONMENT_VARIABLES_FILE='/path/to/.env'

        # .env file contains:
        # dbname=mydb
        # username=admin

        from PlatformConnectors import PlatformConnectors as pc

        db_name = pc.getDBName('default_db')

Author:
    Buzzerboy Inc

Version:
    0.8.6
"""

import os, json, sys
from datetime import timedelta
from .SecretType import SecretType

_DOT_ENV_WARNING_SHOWN = False

def get_secret_type():
    """
    Determine the secret type from environment variables.

    This function checks the PLATFORM_SECRET_TYPE environment variable to determine
    which method should be used to load secrets. If not set, it defaults to SECRET_STRING.

    Returns:
        SecretType: The secret type enum value (SECRET_STRING, DOT_ENV, or ENVIRONMENT_VARIABLES).

    Example:
        ::

            # Via Django settings or environment variable
            export PLATFORM_SECRET_TYPE='dot_env'
            # or
            export PLATFORM_SECRET_TYPE='environment_variables'
            # or
            export PLATFORM_SECRET_TYPE='secret_string'

            # Using the function
            secret_type = get_secret_type()
            if secret_type == SecretType.DOT_ENV:
                print("Using .env file for secrets")

    Note:
        Valid values for PLATFORM_SECRET_TYPE are:
        - 'secret_string' or 'SECRET_STRING' (default)
        - 'dot_env' or 'DOT_ENV'
        - 'environment_variables' or 'ENVIRONMENT_VARIABLES'
        - 'aws_secret_manager' or 'AWS_SECRET_MANAGER'
    """
    secret_type_str = None
    try:
        from django.conf import settings
        if getattr(settings, "configured", False):
            secret_type_str = getattr(settings, "PLATFORM_SECRET_TYPE", None)
    except Exception:
        secret_type_str = None

    if secret_type_str is None:
        secret_type_str = os.environ.get('PLATFORM_SECRET_TYPE', None)

    # Default to SECRET_STRING if not specified
    if secret_type_str is None:
        return SecretType.SECRET_STRING

    # Convert string to enum (case-insensitive)
    secret_type_str = secret_type_str.upper()
    if secret_type_str == 'DOT_ENV':
        return SecretType.DOT_ENV
    elif secret_type_str == 'ENVIRONMENT_VARIABLES':
        return SecretType.ENVIRONMENT_VARIABLES
    elif secret_type_str == 'AWS_SECRET_MANAGER':
        return SecretType.AWS_SECRET_MANAGER
    else:
        return SecretType.SECRET_STRING

def getSecrets():
    """
    Retrieve secrets based on the configured secret type.

    This function supports three different methods for loading secrets:

    1. **SECRET_STRING** (default): Reads a JSON-encoded string from the SECRET_STRING
       environment variable and parses it into a dictionary.

    2. **ENVIRONMENT_VARIABLES**: Collects all environment variables and returns
       them as a dictionary.

    3. **DOT_ENV**: Reads secrets from a .env file. The file path can be specified
       using Django settings (PLATFORM_ENVIRONMENT_VARIABLES_FILE) or the
       PLATFORM_ENVIRONMENT_VARIABLES_FILE environment variable, otherwise
       defaults to '.env' in the current directory.

    4. **AWS_SECRET_MANAGER**: Reads a JSON-encoded secret from AWS Secrets Manager.
       The secret name can be specified using Django settings (PLATFORM_SECRET_NAME)
       or the PLATFORM_SECRET_NAME environment variable.

    The secret type is determined by Django settings (PLATFORM_SECRET_TYPE) or the
    PLATFORM_SECRET_TYPE environment variable.

    Returns:
        dict or None: Dictionary containing configuration secrets, or None if
                     secrets cannot be loaded.

    Example:
        Using SECRET_STRING method::

            export PLATFORM_SECRET_TYPE='secret_string'
            export SECRET_STRING='{"dbname": "myapp", "username": "admin"}'

            secrets = getSecrets()
            # Returns: {"dbname": "myapp", "username": "admin"}

        Using ENVIRONMENT_VARIABLES method::

            export PLATFORM_SECRET_TYPE='environment_variables'
            export dbname='myapp'
            export username='admin'

            secrets = getSecrets()
            # Returns: {"dbname": "myapp", "username": "admin", ...all env vars...}

        Using DOT_ENV method::

            export PLATFORM_SECRET_TYPE='dot_env'
            export PLATFORM_ENVIRONMENT_VARIABLES_FILE='/path/to/.env'
            # Or defaults to .env in current directory

            secrets = getSecrets()
            # Returns dictionary with all key-value pairs from .env file

    Note:
        - SECRET_STRING: Does not raise exceptions for invalid JSON. Returns None
          if the SECRET_STRING is not set or contains invalid JSON.
        - ENVIRONMENT_VARIABLES: Returns all environment variables as a dictionary.
        - DOT_ENV: Supports standard .env file format with KEY=value pairs.
        - AWS_SECRET_MANAGER: Requires PLATFORM_SECRET_NAME; raises ValueError
          if missing or empty.
    """
    secret_type = get_secret_type()

    if secret_type == SecretType.SECRET_STRING:
        # Original behavior: parse JSON from SECRET_STRING
        secretString = os.environ.get('SECRET_STRING', None)
        secret_dict = None
        if secretString is not None:
            try:
                secret_dict = json.loads(secretString)
            except json.JSONDecodeError:
                secret_dict = None
        return secret_dict

    elif secret_type == SecretType.ENVIRONMENT_VARIABLES:
        # Return all environment variables as a dictionary
        return dict(os.environ)

    elif secret_type == SecretType.DOT_ENV:
        global _DOT_ENV_WARNING_SHOWN
        if not _DOT_ENV_WARNING_SHOWN:
            sys.stderr.write(
                "\033[33m\n\nBUZZERBOY COMPLIANCE WARNING: .env file secrets are not HIPAA or SOC2 compliant.\033[0m\n"
            )
            sys.stderr.write(
                "\033[33m---------------------------------------------------\033[0m\n"
            )            
            _DOT_ENV_WARNING_SHOWN = True

        # Load from .env file
        env_file_path = None
        try:
            from django.conf import settings
            if getattr(settings, "configured", False):
                env_file_path = getattr(settings, "PLATFORM_ENVIRONMENT_VARIABLES_FILE", None)
        except Exception:
            env_file_path = None

        if env_file_path is None:
            env_file_path = os.environ.get('PLATFORM_ENVIRONMENT_VARIABLES_FILE', None)

        if not env_file_path:
            env_file_path = '.env'

        return load_dot_env_file(env_file_path)

    elif secret_type == SecretType.AWS_SECRET_MANAGER:
        secret_name = None
        try:
            from django.conf import settings
            if getattr(settings, "configured", False):
                secret_name = getattr(settings, "PLATFORM_SECRET_NAME", None)
        except Exception:
            secret_name = None

        if secret_name is None:
            secret_name = os.environ.get('PLATFORM_SECRET_NAME', None)

        if not secret_name:
            raise ValueError("PLATFORM_SECRET_NAME must be set for AWS Secrets Manager")

        region_name = None
        try:
            from django.conf import settings
            if getattr(settings, "configured", False):
                region_name = getattr(settings, "PLATFORM_AWS_REGION", None)
        except Exception:
            region_name = None

        if region_name is None:
            region_name = os.environ.get('PLATFORM_AWS_REGION', None)

        if not region_name:
            region_name = "us-east-1"

        try:
            import boto3
        except Exception as exc:
            raise ImportError("boto3 is required for AWS Secrets Manager secrets") from exc

        client = boto3.client('secretsmanager', region_name=region_name)
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get('SecretString')
        if secret_string is None:
            secret_binary = response.get('SecretBinary')
            if secret_binary is None:
                return None
            try:
                import base64
                decoded = base64.b64decode(secret_binary)
                secret_string = decoded.decode('utf-8')
            except Exception:
                return None

        try:
            return json.loads(secret_string)
        except json.JSONDecodeError:
            return None

    return None

def getValueFromdDict(data, key, default=""):
    """
    Safely retrieve a value from a dictionary with a default fallback.
    
    Args:
        data (dict or None): The dictionary to search in. Can be None.
        key (str): The key to look for in the dictionary.
        default (str, optional): Default value to return if key is not found
                                or dictionary is None. Defaults to "".
    
    Returns:
        Any: The value associated with the key, or the default value.
    
    Example:
        ::
        
            config = {"host": "localhost", "port": "5432"}
            host = getValueFromdDict(config, "host", "127.0.0.1")  # Returns "localhost"
            timeout = getValueFromdDict(config, "timeout", "30")   # Returns "30" (default)
            
            # Safe with None dictionary
            value = getValueFromdDict(None, "key", "default")      # Returns "default"
    """
    if data is not None:
        return data.get(key, default)
    return default

def load_dot_env_file(env_file_path):
    """
    Load a .env file into a dictionary.

    Args:
        env_file_path (str): Path to the .env file.

    Returns:
        dict or None: Parsed key-value pairs, or None if file is missing/unreadable.
    """
    if not os.path.exists(env_file_path):
        return None

    try:
        from decouple import RepositoryEnv
        return RepositoryEnv(env_file_path).data
    except Exception as exc:
        raise ImportError("python-decouple is required for .env loading") from exc

def get_config_value(key, default=''):
    """
    Retrieve configuration value from secrets or environment variables.
    
    This is the primary configuration access function that implements the dual-source
    configuration pattern. It first attempts to get the value from the JSON-encoded
    secret string, then falls back to environment variables.
    
    Args:
        key (str): The configuration key to retrieve.
        default (str, optional): Default value if key is not found in either source.
                                Defaults to ''.
    
    Returns:
        str: The configuration value from secrets, environment, or default.
    
    Example:
        ::
        
            # With SECRET_STRING containing {"database_host": "prod.db.com"}
            host = get_config_value('database_host', 'localhost')  # Returns "prod.db.com"
            
            # With environment variable DATABASE_PORT=5432
            port = get_config_value('DATABASE_PORT', '3306')       # Returns "5432"
            
            # Neither source has the key
            timeout = get_config_value('timeout', '30')            # Returns "30"
    
    Note:
        The function prioritizes the SECRET_STRING source over environment variables.
        This allows for centralized secret management while maintaining environment
        variable compatibility.
    """
    secrets = getSecrets()
    if secrets is not None:
        if key in secrets:
            return secrets.get(key)
        return os.environ.get(key, default)
    return os.environ.get(key, default)


def environConfig (key, default=""):
    """
    Direct environment variable access function.
    
    Provides direct access to environment variables without checking the
    SECRET_STRING source. Useful when you specifically need environment
    variable values.
    
    Args:
        key (str): The environment variable name.
        default (str, optional): Default value if environment variable is not set.
                                Defaults to "".
    
    Returns:
        str: The environment variable value or default.
    
    Example:
        ::
        
            path = environConfig('PATH', '/usr/bin')
            home = environConfig('HOME', '/tmp')
    """
    return os.environ.get(key, default)

def getDebugValue(default=False): 
    """
    Get the DEBUG configuration value for Django applications.
    
    Args:
        default (bool, optional): Default debug value. Defaults to False.
    
    Returns:
        Any: The DEBUG configuration value from secrets/environment or default.
    
    Example:
        ::
        
            DEBUG = getDebugValue(False)  # For production
            DEBUG = getDebugValue(True)   # For development
    """
    return get_config_value('DEBUG', default)

def getAdvancedDebugValue(default=False):
    """
    Get the ADVANCED_DEBUG configuration value for enhanced debugging.
    
    Args:
        default (bool, optional): Default advanced debug value. Defaults to False.
    
    Returns:
        Any: The ADVANCED_DEBUG configuration value from secrets/environment or default.
    
    Example:
        ::
        
            ADVANCED_DEBUG = getAdvancedDebugValue(False)
    """
    return get_config_value('ADVANCED_DEBUG', default)

# Email Configuration Functions
# ============================

def getEmailHost(default=""): 
    """
    Get the email server hostname.
    
    Args:
        default (str, optional): Default email host. Defaults to "".
    
    Returns:
        str: Email server hostname (e.g., 'smtp.gmail.com', 'smtp.office365.com').
    
    Example:
        ::
        
            EMAIL_HOST = getEmailHost('smtp.gmail.com')
    """
    return get_config_value('email_host', default)

def getEmailPort(default=""): 
    """
    Get the email server port number.
    
    Args:
        default (str, optional): Default email port. Defaults to "".
    
    Returns:
        str: Email server port (e.g., '587', '465', '25').
    
    Example:
        ::
        
            EMAIL_PORT = int(getEmailPort('587'))
    """
    return get_config_value('email_port', default)

def getEmailUser(default=""): 
    """
    Get the email authentication username.
    
    Args:
        default (str, optional): Default email username. Defaults to "".
    
    Returns:
        str: Email authentication username/email address.
    
    Example:
        ::
        
            EMAIL_HOST_USER = getEmailUser('noreply@example.com')
    """
    return get_config_value('email_user', default)

def getEmailPassword(default=""): 
    """
    Get the email authentication password.
    
    Args:
        default (str, optional): Default email password. Defaults to "".
    
    Returns:
        str: Email authentication password or app-specific password.
    
    Example:
        ::
        
            EMAIL_HOST_PASSWORD = getEmailPassword()
    
    Note:
        Store email passwords securely using the SECRET_STRING method or
        environment variables. Never hardcode passwords in source code.
    """
    return get_config_value('email_password', default)

def getEmailUseTLS(default=True): 
    """
    Get the email TLS encryption setting.
    
    Args:
        default (bool, optional): Default TLS setting. Defaults to True.
    
    Returns:
        Any: TLS encryption setting for email connections.
    
    Example:
        ::
        
            EMAIL_USE_TLS = getEmailUseTLS(True)
    """
    return get_config_value('email_use_tls', default)

def getEmailDefaultFromEmail(default=""): 
    """
    Get the default sender email address.
    
    Args:
        default (str, optional): Default from email. Defaults to "".
    
    Returns:
        str: Default email address used as sender for outgoing emails.
    
    Example:
        ::
        
            DEFAULT_FROM_EMAIL = getEmailDefaultFromEmail('noreply@example.com')
    """
    return get_config_value('email_default_from_email', default)

def getEmailBackend(default="django.core.mail.backends.console.EmailBackend"): 
    """
    Get the Django email backend class.
    
    Args:
        default (str, optional): Default email backend class. 
                                Defaults to console backend for development.
    
    Returns:
        str: Django email backend class path.
    
    Example:
        ::
        
            # Production SMTP backend
            EMAIL_BACKEND = getEmailBackend('django.core.mail.backends.smtp.EmailBackend')
            
            # Development console backend (default)
            EMAIL_BACKEND = getEmailBackend()
    
    Note:
        Common backends:
        - 'django.core.mail.backends.smtp.EmailBackend' (production)
        - 'django.core.mail.backends.console.EmailBackend' (development)
        - 'django.core.mail.backends.filebased.EmailBackend' (testing)
    """
    return get_config_value('email_backend', default)

def getContactEmail(default=""): 
    """
    Get the contact/support email address.
    
    Args:
        default (str, optional): Default contact email. Defaults to "".
    
    Returns:
        str: Contact email address for customer support or inquiries.
    
    Example:
        ::
        
            CONTACT_EMAIL = getContactEmail('support@example.com')
    """
    return get_config_value('contactus_email', default)

# Database Configuration Functions
# =================================

def getDBName(default=""): 
    """
    Get the database name for Django database configuration.
    
    Args:
        default (str, optional): Default database name. Defaults to "".
    
    Returns:
        str: Database name for the Django application.
    
    Example:
        ::
        
            DATABASES = {
                'default': {
                    'NAME': getDBName('myapp_production'),
                    # ... other settings
                }
            }
    """
    return get_config_value('dbname', default)

def getDBUser(default=""): 
    """
    Get the database username for authentication.
    
    Args:
        default (str, optional): Default database username. Defaults to "".
    
    Returns:
        str: Database username for connection authentication.
    
    Example:
        ::
        
            'USER': getDBUser('db_admin'),
    """
    return get_config_value('username', default)

def getDBHost(default=""): 
    """
    Get the database host/server address.
    
    Args:
        default (str, optional): Default database host. Defaults to "".
    
    Returns:
        str: Database server hostname or IP address.
    
    Example:
        ::
        
            'HOST': getDBHost('localhost'),
            'HOST': getDBHost('db.example.com'),
    """
    return get_config_value('host', default)

def getDBPort(default=""): 
    """
    Get the database server port number.
    
    Args:
        default (str, optional): Default database port. Defaults to "".
    
    Returns:
        str: Database server port number.
    
    Example:
        ::
        
            'PORT': getDBPort('5432'),  # PostgreSQL
            'PORT': getDBPort('3306'),  # MySQL
    """
    return get_config_value('port', default)

def getDBPassword(default=""): 
    """
    Get the database password for authentication.
    
    Args:
        default (str, optional): Default database password. Defaults to "".
    
    Returns:
        str: Database password for connection authentication.
    
    Example:
        ::
        
            'PASSWORD': getDBPassword(),
    
    Note:
        Store database passwords securely using the SECRET_STRING method or
        environment variables. Never hardcode passwords in source code.
    """
    return get_config_value('password', default)

def getDBEngine(default=""): 
    """
    Get the Django database engine class.
    
    Args:
        default (str, optional): Default database engine. Defaults to "".
    
    Returns:
        str: Django database engine class path.
    
    Example:
        ::
        
            'ENGINE': getDBEngine('django.db.backends.postgresql'),
            'ENGINE': getDBEngine('django.db.backends.mysql'),
            'ENGINE': getDBEngine('django.db.backends.sqlite3'),
    
    Note:
        Common engines:
        - 'django.db.backends.postgresql' (PostgreSQL)
        - 'django.db.backends.mysql' (MySQL/MariaDB)
        - 'django.db.backends.sqlite3' (SQLite)
        - 'django.db.backends.oracle' (Oracle)
    """
    return get_config_value('engine', default)

# AWS Configuration Functions
# ============================

def getRegionName(default=""): 
    """
    Get the AWS region name for service configurations.
    
    Args:
        default (str, optional): Default AWS region. Defaults to "".
    
    Returns:
        str: AWS region name (e.g., 'us-east-1', 'eu-west-1').
    
    Example:
        ::
        
            AWS_S3_REGION_NAME = getRegionName('us-east-1')
    """
    return get_config_value('region_name', default)

def getFileOverWrite(default=""): 
    """
    Get the file overwrite setting for AWS S3.
    
    Args:
        default (str, optional): Default file overwrite setting. Defaults to "".
    
    Returns:
        str: File overwrite configuration for S3 uploads.
    
    Example:
        ::
        
            AWS_S3_FILE_OVERWRITE = getFileOverWrite('False')
    """
    return get_config_value('file_overwrite', default)

def getACL(default=""): 
    """
    Get the default Access Control List (ACL) for AWS S3 objects.
    
    Args:
        default (str, optional): Default ACL setting. Defaults to "".
    
    Returns:
        str: S3 ACL setting (e.g., 'public-read', 'private').
    
    Example:
        ::
        
            AWS_DEFAULT_ACL = getACL('private')
    """
    return get_config_value('default_acl', default)

def getSignatureVersion(default=""): 
    """
    Get the AWS signature version for API requests.
    
    Args:
        default (str, optional): Default signature version. Defaults to "".
    
    Returns:
        str: AWS signature version (e.g., 's3v4').
    
    Example:
        ::
        
            AWS_S3_SIGNATURE_VERSION = getSignatureVersion('s3v4')
    """
    return get_config_value('signature_version', default)

def getAWSAccessKey(default=""): 
    """
    Get the AWS access key ID for authentication.
    
    Args:
        default (str, optional): Default access key. Defaults to "".
    
    Returns:
        str: AWS access key ID for API authentication.
    
    Example:
        ::
        
            AWS_ACCESS_KEY_ID = getAWSAccessKey()
    
    Note:
        Store AWS credentials securely using the SECRET_STRING method or
        environment variables. Consider using IAM roles instead of access keys
        when possible.
    """
    return get_config_value('access_key', default)

def getAWSSecretKey(default=""): 
    """
    Get the AWS secret access key for authentication.
    
    Args:
        default (str, optional): Default secret key. Defaults to "".
    
    Returns:
        str: AWS secret access key for API authentication.
    
    Example:
        ::
        
            AWS_SECRET_ACCESS_KEY = getAWSSecretKey()
    
    Note:
        Store AWS credentials securely using the SECRET_STRING method or
        environment variables. Consider using IAM roles instead of access keys
        when possible.
    """
    return get_config_value('secret_access_key', default)

def getBucketName(default=""): 
    """
    Get the AWS S3 bucket name for file storage.
    
    Args:
        default (str, optional): Default bucket name. Defaults to "".
    
    Returns:
        str: S3 bucket name for file storage operations.
    
    Example:
        ::
        
            AWS_STORAGE_BUCKET_NAME = getBucketName('my-app-media')
    """
    return get_config_value('bucket_name', default)

# AWS Bedrock Configuration Functions
# ====================================

def getBedrockModelId(default=""): 
    """
    Get the AWS Bedrock model ID for AI operations.
    
    Args:
        default (str, optional): Default model ID. Defaults to "".
    
    Returns:
        str: Bedrock model identifier (e.g., 'anthropic.claude-v2').
    
    Example:
        ::
        
            BEDROCK_MODEL_ID = getBedrockModelId('anthropic.claude-v2')
    """
    return get_config_value('bedrock_model_id', default)

def getBedrockEndpointUrl(default=""): 
    """
    Get the AWS Bedrock endpoint URL.
    
    Args:
        default (str, optional): Default endpoint URL. Defaults to "".
    
    Returns:
        str: Bedrock service endpoint URL.
    
    Example:
        ::
        
            BEDROCK_ENDPOINT_URL = getBedrockEndpointUrl()
    """
    return get_config_value('bedrock_endpoint_url', default)

def getBedrockKnowledgeBaseId(default=""): 
    """
    Get the AWS Bedrock knowledge base ID.
    
    Args:
        default (str, optional): Default knowledge base ID. Defaults to "".
    
    Returns:
        str: Bedrock knowledge base identifier for RAG operations.
    
    Example:
        ::
        
            BEDROCK_KNOWLEDGE_BASE_ID = getBedrockKnowledgeBaseId()
    """
    return get_config_value('bedrock_knowledge_base_id', default)

def getBedrockMaxTokens(default=0):
    """
    Get the maximum tokens setting for Bedrock model responses.
    
    Args:
        default (int, optional): Default max tokens. Defaults to 0.
    
    Returns:
        int: Maximum number of tokens for model responses.
    
    Example:
        ::
        
            BEDROCK_MAX_TOKENS = getBedrockMaxTokens(4000)
    
    Note:
        The function safely converts string values to integers, returning
        the default value if conversion fails.
    """
    value = get_config_value('bedrock_max_tokens', default)
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def getBedrockTemperature(default=0.0):
    """
    Get the temperature setting for Bedrock model creativity.
    
    Args:
        default (float, optional): Default temperature. Defaults to 0.0.
    
    Returns:
        float: Model temperature setting (0.0 = deterministic, 1.0 = creative).
    
    Example:
        ::
        
            BEDROCK_TEMPERATURE = getBedrockTemperature(0.7)
    
    Note:
        The function safely converts string values to floats, returning
        the default value if conversion fails.
    """
    value = get_config_value('bedrock_temperature', default)
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def getBedrockKnowledgeDataSourceId(default=""): 
    """
    Get the Bedrock knowledge base data source ID.
    
    Args:
        default (str, optional): Default data source ID. Defaults to "".
    
    Returns:
        str: Knowledge base data source identifier.
    
    Example:
        ::
        
            BEDROCK_DATA_SOURCE_ID = getBedrockKnowledgeDataSourceId()
    """
    return get_config_value('bedrock_knowledge_data_source_id', default)

def getBedrockKnowledgeBasicAgentID(default=""): 
    """
    Get the Bedrock basic agent ID.
    
    Args:
        default (str, optional): Default agent ID. Defaults to "".
    
    Returns:
        str: Bedrock basic agent identifier.
    
    Example:
        ::
        
            BEDROCK_BASIC_AGENT_ID = getBedrockKnowledgeBasicAgentID()
    """
    return get_config_value('bedrock_knowledge_basic_agent_id', default)

def getBedrockKnowledgeBasicAgentAliasID(default=""): 
    """
    Get the Bedrock basic agent alias ID.
    
    Args:
        default (str, optional): Default agent alias ID. Defaults to "".
    
    Returns:
        str: Bedrock basic agent alias identifier.
    
    Example:
        ::
        
            BEDROCK_BASIC_AGENT_ALIAS_ID = getBedrockKnowledgeBasicAgentAliasID()
    """
    return get_config_value('bedrock_knowledge_basic_agent_alias_id', default)

def getBedrockKnowledgeEvidenceCollectionAgentID(default=""): 
    """
    Get the Bedrock evidence collection agent ID.
    
    Args:
        default (str, optional): Default agent ID. Defaults to "".
    
    Returns:
        str: Bedrock evidence collection agent identifier.
    
    Example:
        ::
        
            BEDROCK_EVIDENCE_AGENT_ID = getBedrockKnowledgeEvidenceCollectionAgentID()
    """
    return get_config_value('bedrock_knowledge_evidence_collection_agent_id', default)

def getBedrockKnowledgeEvidenceCollectionAgentAliasID(default=""): 
    """
    Get the Bedrock evidence collection agent alias ID.
    
    Args:
        default (str, optional): Default agent alias ID. Defaults to "".
    
    Returns:
        str: Bedrock evidence collection agent alias identifier.
    
    Example:
        ::
        
            BEDROCK_EVIDENCE_AGENT_ALIAS_ID = getBedrockKnowledgeEvidenceCollectionAgentAliasID()
    """
    return get_config_value('bedrock_knowledge_evidence_collection_agent_alias_id', default)

# AI Configuration Functions  
# ============================

def getAIDailyLimit(default=50000): 
    """
    Get the daily AI usage limit.
    
    Args:
        default (int, optional): Default daily limit. Defaults to 50000.
    
    Returns:
        int: Daily limit for AI API calls or tokens.
    
    Example:
        ::
        
            AI_DAILY_LIMIT = getAIDailyLimit(100000)
    
    Note:
        The function safely converts string values to integers, returning
        the default value if conversion fails.
    """
    value = get_config_value('ai_daily_limit', default)
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def getAIWarningThreshold(default=80):
    """
    Get the AI usage warning threshold percentage.
    
    Args:
        default (int, optional): Default warning threshold. Defaults to 80.
    
    Returns:
        int: Warning threshold as percentage of daily limit.
    
    Example:
        ::
        
            AI_WARNING_THRESHOLD = getAIWarningThreshold(90)  # 90% of daily limit
    
    Note:
        The function safely converts string values to integers, returning
        the default value if conversion fails.
    """
    value = get_config_value('ai_warning_threshold', default) 
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def getAIVisualMultiplier(default=2.0):
    """
    Get the AI visual content processing multiplier.
    
    Args:
        default (float, optional): Default visual multiplier. Defaults to 2.0.
    
    Returns:
        float: Multiplier for visual content processing costs.
    
    Example:
        ::
        
            AI_VISUAL_MULTIPLIER = getAIVisualMultiplier(1.5)
    
    Note:
        Visual content (images) typically requires more processing resources
        than text, hence the multiplier for cost calculations.
    """
    value = get_config_value('ai_visual_multiplier', default)
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# Authentication Provider Configuration Functions
# ===============================================

def getMicrosoftClientID(default=""): 
    """
    Get the Microsoft OAuth client ID.
    
    Args:
        default (str, optional): Default client ID. Defaults to "".
    
    Returns:
        str: Microsoft OAuth application client ID.
    
    Example:
        ::
        
            MICROSOFT_CLIENT_ID = getMicrosoftClientID()
    """
    return get_config_value('microsoft_client_id', default)

def getMicrosoftClientSecret(default=""): 
    """
    Get the Microsoft OAuth client secret.
    
    Args:
        default (str, optional): Default client secret. Defaults to "".
    
    Returns:
        str: Microsoft OAuth application client secret.
    
    Example:
        ::
        
            MICROSOFT_CLIENT_SECRET = getMicrosoftClientSecret()
    
    Note:
        Store OAuth secrets securely using the SECRET_STRING method or
        environment variables. Never hardcode secrets in source code.
    """
    return get_config_value('microsoft_client_secret', default)

def getGoogleClientID(default=""): 
    """
    Get the Google OAuth client ID.
    
    Args:
        default (str, optional): Default client ID. Defaults to "".
    
    Returns:
        str: Google OAuth application client ID.
    
    Example:
        ::
        
            GOOGLE_CLIENT_ID = getGoogleClientID()
    """
    return get_config_value('google_client_id', default)

def getGoogleClientSecret(default=""): 
    """
    Get the Google OAuth client secret.
    
    Args:
        default (str, optional): Default client secret. Defaults to "".
    
    Returns:
        str: Google OAuth application client secret.
    
    Example:
        ::
        
            GOOGLE_CLIENT_SECRET = getGoogleClientSecret()
    
    Note:
        Store OAuth secrets securely using the SECRET_STRING method or
        environment variables. Never hardcode secrets in source code.
    """
    return get_config_value('google_client_secret', default)

# SAML Configuration Functions
# =============================

def getXMLSecBinaryPath(default=""): 
    """
    Get the XMLSec binary path for SAML authentication.
    
    Args:
        default (str, optional): Default binary path. Defaults to "".
    
    Returns:
        str: Path to XMLSec binary for SAML signature validation.
    
    Example:
        ::
        
            XMLSEC_BINARY_PATH = getXMLSecBinaryPath('/usr/bin/xmlsec1')
    """
    return get_config_value('xmlsec_binary_path', default)

def getSamlLoginURL(default=""): 
    """
    Get the SAML login URL for authentication redirects.
    
    Args:
        default (str, optional): Default SAML login URL. Defaults to "".
    
    Returns:
        str: SAML identity provider login URL.
    
    Example:
        ::
        
            SAML_LOGIN_URL = getSamlLoginURL('https://idp.example.com/sso')
    """
    return get_config_value('saml_login_url', default)


# Application Configuration Functions
# ====================================

def getAccountEmailSubjectPrefix(default=""): 
    """
    Get the email subject prefix for account-related emails.
    
    Args:
        default (str, optional): Default subject prefix. Defaults to "".
    
    Returns:
        str: Prefix to prepend to account email subjects.
    
    Example:
        ::
        
            ACCOUNT_EMAIL_SUBJECT_PREFIX = getAccountEmailSubjectPrefix('[MyApp] ')
    """
    return get_config_value('account_email_subject_prefix', default)

def getInternalIPs(default=None): 
    """
    Get the list of internal IP addresses for Django DEBUG_TOOLBAR.
    
    Args:
        default (list, optional): Default IP list. Defaults to [].
    
    Returns:
        list: List of internal IP addresses.
    
    Example:
        ::
        
            INTERNAL_IPS = getInternalIPs(['127.0.0.1', '192.168.1.0/24'])
    """
    if default is None:
        default = []
    return get_config_value('internal_ips', default)

def getSiteID(default=1):
    """
    Get the Django site ID for the sites framework.
    
    Args:
        default (int, optional): Default site ID. Defaults to 1.
    
    Returns:
        int: Django site ID for multi-site configurations.
    
    Example:
        ::
        
            SITE_ID = getSiteID(2)
    
    Note:
        The function safely converts string values to integers, returning
        the default value if conversion fails.
    """
    site_id = get_config_value('site_id', default)
    try:
        return int(site_id)
    except ValueError:
        return default

def getEncryptedModelFieldsKey(default=""): 
    """
    Get the encryption key for Django encrypted model fields.
    
    Args:
        default (str, optional): Default encryption key. Defaults to "".
    
    Returns:
        str: Encryption key for field-level encryption.
    
    Example:
        ::
        
            FIELD_ENCRYPTION_KEY = getEncryptedModelFieldsKey()
    
    Note:
        Store encryption keys securely using the SECRET_STRING method or
        environment variables. Never hardcode keys in source code.
    """
    return get_config_value('encrypted_model_fields_key', default)

def getIronfortSupportEmail(default=""): 
    """
    Get the Ironfort support email address.
    
    Args:
        default (str, optional): Default support email. Defaults to "".
    
    Returns:
        str: Support email address for Ironfort services.
    
    Example:
        ::
        
            IRONFORT_SUPPORT_EMAIL = getIronfortSupportEmail('support@ironfort.com')
    """
    return get_config_value('support_email', default)

def getTempOTPCode(default=""): 
    """
    Get the temporary OTP code for testing purposes.
    
    Args:
        default (str, optional): Default OTP code. Defaults to "".
    
    Returns:
        str: Temporary OTP code for development/testing.
    
    Example:
        ::
        
            TEMP_OTP_CODE = getTempOTPCode('123456')
    
    Warning:
        This should only be used in development environments. Never use
        temporary OTP codes in production.
    """
    return get_config_value('temp_otp_code', default)


# Logging and Application Metadata Functions
# ===========================================

def get_logger_engine(default=""): 
    """
    Get the logging engine configuration.
    
    Args:
        default (str, optional): Default logger engine. Defaults to "".
    
    Returns:
        str: Logging engine identifier or configuration.
    
    Example:
        ::
        
            LOGGER_ENGINE = get_logger_engine('cloudwatch')
    """
    return get_config_value('logger_engine', default)

def get_product_name(default=""):
    """
    Get the product name for application identification.
    
    Args:
        default (str, optional): Default product name. Defaults to "".
    
    Returns:
        str: Product name for branding and identification.
    
    Example:
        ::
        
            PRODUCT_NAME = get_product_name('BuzzerBoy Platform')
    """
    return get_config_value('product_name', default)

def get_app_name(default=""):
    """
    Get the application name for service identification.
    
    Args:
        default (str, optional): Default app name. Defaults to "".
    
    Returns:
        str: Application name for service identification.
    
    Example:
        ::
        
            APP_NAME = get_app_name('platform-connectors')
    """
    return get_config_value('app_name', default)

def get_tier(default=""):
    """
    Get the deployment tier (environment) identifier.
    
    Args:
        default (str, optional): Default tier. Defaults to "".
    
    Returns:
        str: Deployment tier (e.g., 'development', 'staging', 'production').
    
    Example:
        ::
        
            DEPLOYMENT_TIER = get_tier('production')
    """
    return get_config_value('tier', default)

def get_group_name(default=""):
    """
    Get the group name for resource organization.
    
    Args:
        default (str, optional): Default group name. Defaults to "".
    
    Returns:
        str: Group name for organizing resources and permissions.
    
    Example:
        ::
        
            GROUP_NAME = get_group_name('platform-services')
    """
    return get_config_value('group_name', default)

def get_group_name_cloudwatch_logs(default=""):
    """
    Get the CloudWatch logs group name for AWS logging.
    
    Args:
        default (str, optional): Default log group name. Defaults to "".
    
    Returns:
        str: CloudWatch log group name for centralized logging.
    
    Example:
        ::
        
            CLOUDWATCH_LOG_GROUP = get_group_name_cloudwatch_logs('/aws/lambda/my-function')
    """
    return get_config_value('group_name_cloudwatch_logs', default)


# Django REST Framework Configuration Functions
# ==============================================

def getRestFrameworkPageSize(default=10):
    """
    Get the default page size for Django REST Framework pagination.
    
    Args:
        default (int, optional): Default page size. Defaults to 10.
    
    Returns:
        int: Number of items per page for API responses.
    
    Example:
        ::
        
            REST_FRAMEWORK = {
                'PAGE_SIZE': getRestFrameworkPageSize(25)
            }
    
    Note:
        The function safely converts string values to integers, returning
        the default value if conversion fails.
    """
    value = get_config_value('rest_framework_page_size', default)
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def getAccessTokenLifetime(default=1):
    """
    Get the access token lifetime in days for OAuth/JWT authentication.
    
    Args:
        default (int, optional): Default lifetime in days. Defaults to 1.
    
    Returns:
        int: Access token lifetime in days.
    
    Example:
        ::
        
            ACCESS_TOKEN_LIFETIME = timedelta(days=getAccessTokenLifetime(7))
    
    Note:
        The function safely converts string values to integers, returning
        the default value if conversion fails.
    """
    value = get_config_value('access_token_lifetime', default)
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def getRefreshTokenLifetime(default=7):
    """
    Get the refresh token lifetime in days for OAuth/JWT authentication.
    
    Args:
        default (int, optional): Default lifetime in days. Defaults to 7.
    
    Returns:
        int: Refresh token lifetime in days.
    
    Example:
        ::
        
            REFRESH_TOKEN_LIFETIME = timedelta(days=getRefreshTokenLifetime(30))
    
    Note:
        The function safely converts string values to integers, returning
        the default value if conversion fails.
    """
    value = get_config_value('refresh_token_lifetime', default)
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
