import configparser
import os
import sys

from square_commons import ConfigReader
from square_logger import SquareLogger

try:
    config = configparser.ConfigParser()
    config_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "config.ini"
    )
    config_sample_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "config.sample.ini"
    )
    ldict_configuration = ConfigReader(
        config_file_path, config_sample_file_path
    ).read_configuration()

    # get all vars and typecast
    # ===========================================
    # general
    config_str_module_name = ldict_configuration["GENERAL"]["MODULE_NAME"]
    # ===========================================

    # ===========================================
    # environment
    config_str_host_ip = ldict_configuration["ENVIRONMENT"]["HOST_IP"]
    config_int_host_port = int(ldict_configuration["ENVIRONMENT"]["HOST_PORT"])
    config_str_db_ip = ldict_configuration["ENVIRONMENT"]["DB_IP"]
    config_int_db_port = int(ldict_configuration["ENVIRONMENT"]["DB_PORT"])
    config_list_allow_origins = eval(
        ldict_configuration["ENVIRONMENT"]["ALLOW_ORIGINS"]
    )
    config_str_db_username = ldict_configuration["ENVIRONMENT"]["DB_USERNAME"]
    config_str_db_password = ldict_configuration["ENVIRONMENT"]["DB_PASSWORD"]
    config_str_log_file_name = ldict_configuration["ENVIRONMENT"]["LOG_FILE_NAME"]
    config_bool_create_schema = eval(
        ldict_configuration["ENVIRONMENT"]["CREATE_SCHEMA"]
    )
    config_str_database_module_name = ldict_configuration["ENVIRONMENT"][
        "DATABASE_PACKAGE_NAME"
    ]
    config_str_ssl_crt_file_path = ldict_configuration["ENVIRONMENT"][
        "SSL_CRT_FILE_PATH"
    ]
    config_str_ssl_key_file_path = ldict_configuration["ENVIRONMENT"][
        "SSL_KEY_FILE_PATH"
    ]

    # ===========================================

    # ===========================================
    # square_logger
    config_int_log_level = int(ldict_configuration["SQUARE_LOGGER"]["LOG_LEVEL"])
    config_str_log_path = ldict_configuration["SQUARE_LOGGER"]["LOG_PATH"]
    config_int_log_backup_count = int(
        ldict_configuration["SQUARE_LOGGER"]["LOG_BACKUP_COUNT"]
    )
    config_formatter_choice = ldict_configuration["SQUARE_LOGGER"]["FORMATTER_CHOICE"]
    if config_formatter_choice not in ("human_readable", "json"):
        raise ValueError(f"Invalid formatter choice: {config_formatter_choice}")
    config_bool_enable_redaction = eval(
        ldict_configuration["SQUARE_LOGGER"]["ENABLE_REDACTION"]
    )
    # ===========================================
except Exception as e:
    print(
        "\033[91mMissing or incorrect config.ini file.\n"
        "Error details: " + str(e) + "\033[0m"
    )
    sys.exit()

global_object_square_logger = SquareLogger(
    log_file_name=config_str_log_file_name,
    log_level=config_int_log_level,
    log_path=config_str_log_path,
    log_backup_count=config_int_log_backup_count,
    formatter_choice=config_formatter_choice,
    enable_redaction=config_bool_enable_redaction,
)
