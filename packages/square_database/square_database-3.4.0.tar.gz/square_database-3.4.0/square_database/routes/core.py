from fastapi import status, APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from square_commons import get_api_output_in_standard_format
from square_commons.api_utils import StandardResponse

from square_database.configuration import (
    global_object_square_logger,
)
from square_database.messages import messages
from square_database.models.core import (
    DeleteRowsV0,
    EditRowsV0,
    GetRowsV0,
    InsertRowsV0,
    InsertRowsV0Response,
    GetRowsV0Response,
    EditRowsV0Response,
    DeleteRowsV0Response,
)
from square_database.utils.routes.core import (
    util_insert_rows_v0,
    util_get_rows_v0,
    util_edit_rows_v0,
    util_delete_rows_v0,
)

router = APIRouter(
    tags=["core"],
)


@router.post(
    "/insert_rows/v0",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[InsertRowsV0Response],
)
@global_object_square_logger.auto_logger()
async def insert_rows_v0(insert_rows_model: InsertRowsV0):
    try:
        return util_insert_rows_v0(insert_rows_model)
    except HTTPException as he:
        global_object_square_logger.logger.error(he, exc_info=True)
        return JSONResponse(status_code=he.status_code, content=he.detail)
    except Exception as e:
        global_object_square_logger.logger.error(e, exc_info=True)
        output_content = get_api_output_in_standard_format(
            message=messages["GENERIC_500"], log=str(e)
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=output_content
        )


@router.post(
    "/get_rows/v0",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[GetRowsV0Response],
)
@global_object_square_logger.auto_logger()
async def get_rows_v0(get_rows_model: GetRowsV0):
    try:
        return util_get_rows_v0(get_rows_model)
    except HTTPException as he:
        global_object_square_logger.logger.error(he, exc_info=True)
        return JSONResponse(status_code=he.status_code, content=he.detail)
    except Exception as e:
        global_object_square_logger.logger.error(e, exc_info=True)
        output_content = get_api_output_in_standard_format(
            message=messages["GENERIC_500"], log=str(e)
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=output_content
        )


@router.patch(
    "/edit_rows/v0",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[EditRowsV0Response],
)
@global_object_square_logger.auto_logger()
async def edit_rows_v0(edit_rows_model: EditRowsV0):
    try:
        return util_edit_rows_v0(edit_rows_model)
    except HTTPException as he:
        global_object_square_logger.logger.error(he, exc_info=True)
        return JSONResponse(status_code=he.status_code, content=he.detail)
    except Exception as e:
        global_object_square_logger.logger.error(e, exc_info=True)
        output_content = get_api_output_in_standard_format(
            message=messages["GENERIC_500"], log=str(e)
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=output_content
        )


@router.post(
    "/delete_rows/v0",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[DeleteRowsV0Response],
)
@global_object_square_logger.auto_logger()
async def delete_rows_v0(delete_rows_model: DeleteRowsV0):
    try:
        return util_delete_rows_v0(delete_rows_model)
    except HTTPException as he:
        global_object_square_logger.logger.error(he, exc_info=True)
        return JSONResponse(status_code=he.status_code, content=he.detail)
    except Exception as e:
        global_object_square_logger.logger.error(e, exc_info=True)
        output_content = get_api_output_in_standard_format(
            message=messages["GENERIC_500"], log=str(e)
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=output_content
        )
