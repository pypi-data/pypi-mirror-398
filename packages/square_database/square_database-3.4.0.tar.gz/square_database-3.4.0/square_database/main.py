import os.path

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from square_commons import get_api_output_in_standard_format
from square_database_structure import create_database_and_tables
from uvicorn import run

from square_database.configuration import (
    config_bool_create_schema,
    config_int_db_port,
    config_int_host_port,
    config_str_db_ip,
    config_str_db_password,
    config_str_db_username,
    config_str_host_ip,
    config_str_module_name,
    config_str_ssl_crt_file_path,
    config_str_ssl_key_file_path,
    global_object_square_logger,
    config_list_allow_origins,
)
from square_database.routes import core

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=config_list_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(core.router)


@app.get("/")
@global_object_square_logger.auto_logger()
async def root():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=get_api_output_in_standard_format(log=config_str_module_name),
    )


if __name__ == "__main__":
    try:
        if config_bool_create_schema:
            create_database_and_tables(
                db_username=config_str_db_username,
                db_port=config_int_db_port,
                db_password=config_str_db_password,
                db_ip=config_str_db_ip,
            )
        if os.path.exists(config_str_ssl_key_file_path) and os.path.exists(
            config_str_ssl_crt_file_path
        ):
            run(
                app,
                host=config_str_host_ip,
                port=config_int_host_port,
                ssl_certfile=config_str_ssl_crt_file_path,
                ssl_keyfile=config_str_ssl_key_file_path,
            )
        else:
            run(
                app,
                host=config_str_host_ip,
                port=config_int_host_port,
            )

    except Exception as exc:
        global_object_square_logger.logger.critical(exc, exc_info=True)
