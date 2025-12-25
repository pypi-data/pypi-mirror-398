import importlib
import json

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from square_commons import get_api_output_in_standard_format

from square_database.configuration import (
    config_int_db_port,
    config_str_database_module_name,
    config_str_db_ip,
    config_str_db_password,
    config_str_db_username,
    global_object_square_logger,
)
from square_database.messages import messages
from square_database.models.core import (
    InsertRowsV0Response,
    GetRowsV0Response,
    EditRowsV0Response,
    DeleteRowsV0Response,
)
from square_database.utils.common_operations import (
    snake_to_capital_camel,
    enum_fallback_serializer,
    apply_filters,
    apply_order_by,
)


@global_object_square_logger.auto_logger()
def util_insert_rows_v0(insert_rows_model):
    try:
        local_str_database_url = (
            f"postgresql://{config_str_db_username}:{config_str_db_password}@"
            f"{config_str_db_ip}:{str(config_int_db_port)}/{insert_rows_model.database_name}"
        )
        database_engine = create_engine(local_str_database_url)

        # Connect to database
        with database_engine.connect() as database_connection:
            # ===========================================
            # check if schema exists
            schema_result = database_connection.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"
                ),
                {"schema": insert_rows_model.schema_name},
            ).scalar()

            if not schema_result:
                output_content = get_api_output_in_standard_format(
                    message=messages["INCORRECT_SCHEMA_NAME"]
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=output_content,
                )
            # connect to schema
            database_connection.execute(
                text(f"SET search_path TO {insert_rows_model.schema_name}")
            )
            try:
                table_class_name = snake_to_capital_camel(insert_rows_model.table_name)
                table_module_path = (
                    f"{config_str_database_module_name}.{insert_rows_model.database_name}"
                    f".{insert_rows_model.schema_name}.tables"
                )
                table_module = importlib.import_module(table_module_path)
                table_class = getattr(table_module, table_class_name)
            except Exception as e:
                output_content = get_api_output_in_standard_format(
                    message=messages["INCORRECT_TABLE_NAME"], log=str(e)
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=output_content,
                )
            local_object_session = sessionmaker(bind=database_engine)
            session = local_object_session()
            try:
                if insert_rows_model.skip_conflicts:
                    stmt = (
                        insert(table_class)
                        .values(insert_rows_model.data)
                        .on_conflict_do_nothing()
                        .returning(*table_class.__table__.columns)
                    )
                else:
                    stmt = (
                        insert(table_class)
                        .values(insert_rows_model.data)
                        .returning(*table_class.__table__.columns)
                    )

                result = session.execute(stmt)
                inserted_rows = result.fetchall()
                session.commit()
                return_this = json.loads(
                    json.dumps(
                        [
                            {
                                key: value
                                for key, value in row._asdict().items()
                                if not key.startswith("_sa_")
                            }
                            for row in inserted_rows
                        ],
                        default=enum_fallback_serializer,
                    )
                )
                session.close()
                data_pydantic = InsertRowsV0Response(
                    main=return_this, affected_count=len(return_this)
                )
                output_content = get_api_output_in_standard_format(
                    message=messages["CREATE_SUCCESSFUL"],
                    data=data_pydantic.model_dump(),
                    as_dict=False,
                )
                return JSONResponse(
                    status_code=status.HTTP_201_CREATED,
                    content=output_content.model_dump(),
                )
            except Exception as e:
                session.rollback()
                session.close()
                output_content = get_api_output_in_standard_format(
                    message=messages["GENERIC_400"], log=str(e)
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=output_content
                )
    except OperationalError as oe:
        global_object_square_logger.logger.error(oe, exc_info=True)
        output_content = get_api_output_in_standard_format(
            message=messages["INCORRECT_DATABASE_NAME"], log=str(oe)
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=output_content
        )
    except Exception:
        raise


@global_object_square_logger.auto_logger()
def util_get_rows_v0(get_rows_model):
    try:
        # Create the database URL
        local_str_database_url = (
            f"postgresql://{config_str_db_username}:{config_str_db_password}@"
            f"{config_str_db_ip}:{str(config_int_db_port)}/{get_rows_model.database_name}"
        )
        database_engine = create_engine(local_str_database_url)

        # Connect to the database
        with database_engine.connect() as database_connection:
            # ===========================================

            # check if schema exists
            schema_result = database_connection.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"
                ),
                {"schema": get_rows_model.schema_name},
            ).scalar()

            if not schema_result:
                output_content = get_api_output_in_standard_format(
                    message=messages["INCORRECT_SCHEMA_NAME"]
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=output_content,
                )

            # connect to schema
            database_connection.execute(
                text(f"SET search_path TO {get_rows_model.schema_name}")
            )
            # ===========================================

            # Dynamically import table module and class
            try:
                table_class_name = snake_to_capital_camel(get_rows_model.table_name)
                table_module_path = (
                    f"{config_str_database_module_name}.{get_rows_model.database_name}"
                    f".{get_rows_model.schema_name}.tables"
                )
                table_module = importlib.import_module(table_module_path)
                table_class = getattr(table_module, table_class_name)
            except Exception as e:
                output_content = get_api_output_in_standard_format(
                    message=messages["INCORRECT_TABLE_NAME"], log=str(e)
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=output_content,
                )

            # Session management
            local_object_session = sessionmaker(bind=database_engine)
            session = local_object_session()

            try:

                query = session.query(table_class)

                if get_rows_model.apply_filters:
                    if not get_rows_model.filters.root:
                        output_content = get_api_output_in_standard_format(
                            data={"main": [], "total_count": 0},
                            message=messages["GENERIC_204"],
                        )
                        return JSONResponse(
                            status_code=status.HTTP_200_OK,
                            content=output_content,
                        )

                    query = apply_filters(
                        query, get_rows_model.filters.root, table_class
                    )
                # Count
                total_count = query.count()
                query = apply_order_by(query, get_rows_model.order_by, table_class)
                query = query.limit(get_rows_model.limit).offset(get_rows_model.offset)

                # Fetch results
                filtered_rows = query.all()

                # Format results to JSON-serializable format
                # column filtering logic added manually
                local_list_filtered_rows = [
                    {
                        key: value
                        for key, value in x.__dict__.items()
                        if not key.startswith("_")
                        and (
                            not get_rows_model.columns or key in get_rows_model.columns
                        )
                    }
                    for x in filtered_rows
                ]
                data_pydantic = GetRowsV0Response(
                    main=json.loads(
                        json.dumps(
                            local_list_filtered_rows,
                            default=enum_fallback_serializer,
                        )
                    ),
                    total_count=total_count,
                )
                output_content = get_api_output_in_standard_format(
                    message=messages["READ_SUCCESSFUL"],
                    data=data_pydantic.model_dump(),
                    as_dict=False,
                )
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=output_content.model_dump(),
                )

            except Exception as e:
                output_content = get_api_output_in_standard_format(
                    message=messages["GENERIC_400"], log=str(e)
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=output_content
                )
            finally:
                # Ensure session is closed
                session.close()
    except OperationalError as oe:
        global_object_square_logger.logger.error(oe, exc_info=True)
        output_content = get_api_output_in_standard_format(
            message=messages["INCORRECT_DATABASE_NAME"], log=str(oe)
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=output_content
        )
    except Exception:
        raise


@global_object_square_logger.auto_logger()
def util_edit_rows_v0(edit_rows_model):
    try:
        local_str_database_url = (
            f"postgresql://{config_str_db_username}:{config_str_db_password}@"
            f"{config_str_db_ip}:{str(config_int_db_port)}/{edit_rows_model.database_name}"
        )
        database_engine = create_engine(local_str_database_url)
        # Connect to database
        with database_engine.connect() as database_connection:
            # ===========================================
            # check if schema exists
            schema_result = database_connection.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"
                ),
                {"schema": edit_rows_model.schema_name},
            ).scalar()

            if not schema_result:
                output_content = get_api_output_in_standard_format(
                    message=messages["INCORRECT_SCHEMA_NAME"]
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=output_content,
                )

            # connect to schema
            database_connection.execute(
                text(f"SET search_path TO {edit_rows_model.schema_name}")
            )
            # ===========================================
            try:
                table_class_name = snake_to_capital_camel(edit_rows_model.table_name)
                table_module_path = (
                    f"{config_str_database_module_name}.{edit_rows_model.database_name}"
                    f".{edit_rows_model.schema_name}.tables"
                )
                table_module = importlib.import_module(table_module_path)
                table_class = getattr(table_module, table_class_name)
            except Exception as e:
                output_content = get_api_output_in_standard_format(
                    message=messages["INCORRECT_TABLE_NAME"], log=str(e)
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=output_content,
                )
            # validate the column names in the edit_rows_model.data
            mapper = inspect(table_class)
            valid_column_names = {col.key for col in mapper.columns}
            for key in edit_rows_model.data.keys():
                if key not in valid_column_names:
                    output_content = get_api_output_in_standard_format(
                        message=messages["GENERIC_400"],
                        log=f"Invalid column '{key}' for table '{table_class.__tablename__}'. Valid columns are: {', '.join(valid_column_names)}",
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail=output_content
                    )
            local_object_session = sessionmaker(bind=database_engine)
            session = local_object_session()
            try:
                # Get rows from filters
                query = session.query(table_class)
                if edit_rows_model.apply_filters:
                    if not edit_rows_model.filters.root:
                        filtered_rows = []
                    else:
                        query = apply_filters(
                            query, edit_rows_model.filters.root, table_class
                        )
                        filtered_rows = query.all()
                else:
                    filtered_rows = query.all()
                # ===========================================
                for row in filtered_rows:
                    for key, value in edit_rows_model.data.items():
                        # edit rows
                        setattr(row, key, value)
                        # ===========================================
                session.commit()
                for row in filtered_rows:
                    session.refresh(row)
                local_list_filtered_rows = [
                    {
                        key: value
                        for key, value in x.__dict__.items()
                        if not key.startswith("_")
                    }
                    for x in filtered_rows
                ]
                session.close()
                return_this = json.loads(
                    json.dumps(
                        local_list_filtered_rows, default=enum_fallback_serializer
                    )
                )
                data_pydantic = EditRowsV0Response(
                    main=return_this, affected_count=len(return_this)
                )
                output_content = get_api_output_in_standard_format(
                    message=messages["UPDATE_SUCCESSFUL"],
                    data=data_pydantic.model_dump(),
                    as_dict=False,
                )
                return JSONResponse(
                    status_code=status.HTTP_200_OK, content=output_content.model_dump()
                )
            except Exception as e:
                session.rollback()
                session.close()
                output_content = get_api_output_in_standard_format(
                    message=messages["GENERIC_400"], log=str(e)
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=output_content
                )
    except OperationalError as oe:
        global_object_square_logger.logger.error(oe, exc_info=True)
        output_content = get_api_output_in_standard_format(
            message=messages["INCORRECT_DATABASE_NAME"], log=str(oe)
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=output_content
        )
    except Exception:
        raise


@global_object_square_logger.auto_logger()
def util_delete_rows_v0(delete_rows_model):
    try:
        local_str_database_url = (
            f"postgresql://{config_str_db_username}:{config_str_db_password}@"
            f"{config_str_db_ip}:{str(config_int_db_port)}/{delete_rows_model.database_name}"
        )
        database_engine = create_engine(local_str_database_url)
        # Connect to database
        with database_engine.connect() as database_connection:
            # ===========================================
            # check if schema exists
            schema_result = database_connection.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"
                ),
                {"schema": delete_rows_model.schema_name},
            ).scalar()

            if not schema_result:
                output_content = get_api_output_in_standard_format(
                    message=messages["INCORRECT_SCHEMA_NAME"]
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=output_content,
                )
            # connect to schema
            database_connection.execute(
                text(f"SET search_path TO {delete_rows_model.schema_name}")
            )
            try:
                table_class_name = snake_to_capital_camel(delete_rows_model.table_name)
                table_module_path = (
                    f"{config_str_database_module_name}.{delete_rows_model.database_name}"
                    f".{delete_rows_model.schema_name}.tables"
                )
                table_module = importlib.import_module(table_module_path)
                table_class = getattr(table_module, table_class_name)
            except Exception as e:
                output_content = get_api_output_in_standard_format(
                    message=messages["INCORRECT_TABLE_NAME"], log=str(e)
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=output_content,
                )

            local_object_session = sessionmaker(bind=database_engine)
            session = local_object_session()
            try:
                # Get rows from filters
                query = session.query(table_class)
                if delete_rows_model.apply_filters:
                    if not delete_rows_model.filters.root:
                        filtered_rows = []
                    else:
                        query = apply_filters(
                            query, delete_rows_model.filters.root, table_class
                        )
                        filtered_rows = query.all()
                else:
                    filtered_rows = query.all()
                # ===========================================
                local_list_filtered_rows = [
                    {
                        key: value
                        for key, value in x.__dict__.items()
                        if not key.startswith("_")
                    }
                    for x in filtered_rows
                ]
                # delete all rows at once
                if query:
                    query.delete()
                # ===========================================
                session.commit()
                session.close()
                return_this = json.loads(
                    json.dumps(
                        local_list_filtered_rows, default=enum_fallback_serializer
                    )
                )
                data_pydantic = DeleteRowsV0Response(
                    main=return_this, affected_count=len(return_this)
                )
                output_content = get_api_output_in_standard_format(
                    message=messages["DELETE_SUCCESSFUL"],
                    data=data_pydantic.model_dump(),
                    as_dict=False,
                )
                return JSONResponse(
                    status_code=status.HTTP_200_OK, content=output_content.model_dump()
                )
            except Exception as e:
                # no need for this but kept it anyway :/
                session.rollback()
                session.close()
                output_content = get_api_output_in_standard_format(
                    message=messages["GENERIC_400"], log=str(e)
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=output_content
                )

    except OperationalError as oe:
        global_object_square_logger.logger.error(oe, exc_info=True)
        output_content = get_api_output_in_standard_format(
            message=messages["INCORRECT_DATABASE_NAME"], log=str(oe)
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content=output_content
        )
    except Exception:
        raise
