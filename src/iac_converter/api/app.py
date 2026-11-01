from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from iac_converter.compiler import (
    TerraformProjectParseError,
    YAMLProjectParseError,
    parse_terraform_project,
    parse_yaml_project,
)
from iac_converter.compiler.terraform_to_ir import (
    TerraformParseError,
    parse_terraform,
)
from iac_converter.generator import generate_yaml_project
from iac_converter.generator.terraform import (
    TerraformGenerationError,
    TerraformGenerator,
)
from iac_converter.generator.terraform_project import (
    TerraformProjectGenerationError,
    generate_terraform_project,
)
from iac_converter.generator.yaml_project import (
    YAMLProjectGenerationError,
)
from iac_converter.ir import ProjectIR
from iac_converter.project import (
    Project,
    ProjectArchiveError,
    ProjectFile,
    load_project_zip,
    save_project_zip,
)

app = FastAPI(
    title="IaC Converter API",
    description="Bidirectional YAML and Terraform infrastructure converter",
    version="0.1.0",
)


@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a generic response for unexpected internal errors."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
    )


# Maximum uploaded file size: 100 MB
MAX_UPLOAD_SIZE = 100 * 1024 * 1024

# Allow 1 MB for multipart form-data overhead.
MAX_REQUEST_SIZE = MAX_UPLOAD_SIZE + (1024 * 1024)

UPLOAD_ENDPOINTS = {
    "/convert/terraform-to-yaml",
    "/convert/yaml-zip-to-terraform-zip",
    "/convert/terraform-zip-to-yaml-zip",
    "/convert/yaml-file-to-terraform",
    "/convert/terraform-file-to-yaml",
}


class RequestBodyTooLarge(Exception):
    """Raised when an incoming request exceeds its size limit."""


class RequestSizeLimitMiddleware:
    """Limit incoming request bodies before multipart parsing."""

    def __init__(
        self,
        app: ASGIApp,
        max_request_size: int,
        paths: set[str],
    ) -> None:
        self.app = app
        self.max_request_size = max_request_size
        self.paths = paths

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"] not in self.paths:
            await self.app(scope, receive, send)
            return

        content_length = next(
            (value for name, value in scope["headers"] if name.lower() == b"content-length"),
            None,
        )

        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header."},
                )
                await response(scope, receive, send)
                return

            if declared_size < 0:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header."},
                )
                await response(scope, receive, send)
                return

            if declared_size > self.max_request_size:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "Request body exceeds the allowed upload size."},
                )
                await response(scope, receive, send)
                return

        received_size = 0

        async def limited_receive() -> Message:
            nonlocal received_size

            message = await receive()

            if message["type"] == "http.request":
                received_size += len(message.get("body", b""))

                if received_size > self.max_request_size:
                    raise RequestBodyTooLarge()

            return message

        try:
            await self.app(scope, limited_receive, send)

        except RequestBodyTooLarge:
            response = JSONResponse(
                status_code=413,
                content={"detail": "Request body exceeds the allowed upload size."},
            )
            await response(scope, receive, send)


app.add_middleware(
    RequestSizeLimitMiddleware,
    max_request_size=MAX_REQUEST_SIZE,
    paths=UPLOAD_ENDPOINTS,
)


class YAMLConversionRequest(BaseModel):
    content: str = Field(min_length=1)


class TerraformConversionResponse(BaseModel):
    content: str


class YAMLConversionResponse(BaseModel):
    content: str


async def read_limited_upload(file: UploadFile) -> bytes:
    """Read an uploaded file while enforcing the maximum size."""

    content = await file.read(MAX_UPLOAD_SIZE + 1)

    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Uploaded file exceeds the 100 MB limit.",
        )

    return content


def create_zip_response(
    project: Project,
    filename: str,
) -> FileResponse:
    """Create a ZIP archive and stream it as an HTTP response."""

    temp_dir = TemporaryDirectory()

    try:
        archive_path = Path(temp_dir.name) / filename
        save_project_zip(project, archive_path)

        return FileResponse(
            path=archive_path,
            media_type="application/zip",
            filename=filename,
            background=BackgroundTask(temp_dir.cleanup),
        )
    except Exception:
        temp_dir.cleanup()
        raise


def merge_project_ir(
    target: ProjectIR,
    source: ProjectIR,
) -> None:
    """Merge one ProjectIR into another."""

    if source.version != "1":
        target.version = source.version

    target.providers.extend(source.providers)
    target.variables.extend(source.variables)
    target.resources.extend(source.resources)
    target.data_sources.extend(source.data_sources)
    target.outputs.extend(source.outputs)

    target.locals.update(source.locals)
    target.terraform.update(source.terraform)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


# ---------------------------------------------------------
# YAML text -> Terraform text
# ---------------------------------------------------------


@app.post(
    "/convert/yaml-to-terraform",
    response_model=TerraformConversionResponse,
)
def convert_yaml_to_terraform(
    request: YAMLConversionRequest,
) -> TerraformConversionResponse:
    try:
        project_ir = parse_yaml_project(request.content)

        terraform_content = TerraformGenerator().generate(project_ir)

        return TerraformConversionResponse(content=terraform_content)

    except YAMLProjectParseError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except TerraformGenerationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------
# Terraform project ZIP -> YAML text
# ---------------------------------------------------------


@app.post(
    "/convert/terraform-to-yaml",
    response_model=YAMLConversionResponse,
)
async def convert_terraform_to_yaml(
    file: UploadFile = File(...),
) -> YAMLConversionResponse:
    try:
        if not file.filename or not file.filename.lower().endswith(".zip"):
            raise HTTPException(
                status_code=400,
                detail="Please upload a Terraform project ZIP file.",
            )

        content = await read_limited_upload(file)

        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "terraform-project.zip"
            archive_path.write_bytes(content)

            project = load_project_zip(archive_path)

            project_ir = parse_terraform_project(project)

            yaml_content = generate_yaml_project(project_ir)

        return YAMLConversionResponse(content=yaml_content)

    except ProjectArchiveError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except TerraformProjectParseError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except YAMLProjectGenerationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()


# ---------------------------------------------------------
# YAML project ZIP -> Terraform project ZIP
# ---------------------------------------------------------


@app.post("/convert/yaml-zip-to-terraform-zip")
async def convert_yaml_zip_to_terraform_zip(
    file: UploadFile = File(...),
) -> Response:
    try:
        if not file.filename or not file.filename.lower().endswith(".zip"):
            raise HTTPException(
                status_code=400,
                detail="Please upload a YAML project ZIP file.",
            )

        content = await read_limited_upload(file)

        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "yaml-project.zip"
            archive_path.write_bytes(content)

            yaml_project = load_project_zip(archive_path)

        yaml_files = [
            project_file
            for project_file in yaml_project.files
            if project_file.path.lower().endswith((".yaml", ".yml"))
        ]

        if not yaml_files:
            raise HTTPException(
                status_code=422,
                detail="The ZIP archive does not contain any YAML files.",
            )

        merged_ir = ProjectIR()

        for yaml_file in yaml_files:
            try:
                parsed_ir = parse_yaml_project(yaml_file.content)

            except YAMLProjectParseError as exc:
                raise HTTPException(
                    status_code=422,
                    detail=(f"Failed to parse YAML file '{yaml_file.path}': {exc}"),
                ) from exc

            merge_project_ir(merged_ir, parsed_ir)

        terraform_project = generate_terraform_project(merged_ir)

        return create_zip_response(
            terraform_project,
            "terraform-project.zip",
        )

    except ProjectArchiveError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except TerraformProjectGenerationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()


# ---------------------------------------------------------
# Terraform project ZIP -> YAML project ZIP
# ---------------------------------------------------------


@app.post("/convert/terraform-zip-to-yaml-zip")
async def convert_terraform_zip_to_yaml_zip(
    file: UploadFile = File(...),
) -> Response:
    try:
        if not file.filename or not file.filename.lower().endswith(".zip"):
            raise HTTPException(
                status_code=400,
                detail="Please upload a Terraform project ZIP file.",
            )

        content = await read_limited_upload(file)

        with TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "terraform-project.zip"
            archive_path.write_bytes(content)

            terraform_project = load_project_zip(archive_path)

            project_ir = parse_terraform_project(terraform_project)

            yaml_content = generate_yaml_project(project_ir)

        yaml_project = Project(
            files=[
                ProjectFile(
                    path="main.yaml",
                    content=yaml_content,
                )
            ]
        )

        return create_zip_response(
            yaml_project,
            "yaml-project.zip",
        )

    except ProjectArchiveError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except TerraformProjectParseError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except YAMLProjectGenerationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()


# ---------------------------------------------------------
# NEW: Single YAML file -> Terraform file
# ---------------------------------------------------------


@app.post(
    "/convert/yaml-file-to-terraform",
    response_model=TerraformConversionResponse,
)
async def convert_yaml_file_to_terraform(
    file: UploadFile = File(...),
) -> TerraformConversionResponse:
    try:
        if not file.filename or not file.filename.lower().endswith((".yaml", ".yml")):
            raise HTTPException(
                status_code=400,
                detail="Please upload a YAML (.yaml or .yml) file.",
            )

        content = await read_limited_upload(file)

        try:
            yaml_content = content.decode("utf-8")

        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=422,
                detail="YAML file must use UTF-8 encoding.",
            ) from exc

        project_ir = parse_yaml_project(yaml_content)

        terraform_content = TerraformGenerator().generate(project_ir)

        return TerraformConversionResponse(
            content=terraform_content,
        )

    except YAMLProjectParseError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except TerraformGenerationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()


# ---------------------------------------------------------
# NEW: Single Terraform file -> YAML file
# ---------------------------------------------------------


@app.post(
    "/convert/terraform-file-to-yaml",
    response_model=YAMLConversionResponse,
)
async def convert_terraform_file_to_yaml(
    file: UploadFile = File(...),
) -> YAMLConversionResponse:
    try:
        if not file.filename or not file.filename.lower().endswith(".tf"):
            raise HTTPException(
                status_code=400,
                detail="Please upload a Terraform (.tf) file.",
            )

        content = await read_limited_upload(file)

        try:
            terraform_content = content.decode("utf-8")

        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=422,
                detail="Terraform file must use UTF-8 encoding.",
            ) from exc

        project_ir = parse_terraform(terraform_content)

        yaml_content = generate_yaml_project(project_ir)

        return YAMLConversionResponse(
            content=yaml_content,
        )

    except TerraformParseError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except YAMLProjectGenerationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()
