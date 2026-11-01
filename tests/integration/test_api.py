import asyncio
from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile

from fastapi.testclient import TestClient

from iac_converter.api.app import (
    RequestSizeLimitMiddleware,
    app,
)

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_yaml_to_terraform_endpoint():
    yaml_content = """
version: "1"
resources:
  - type: aws_s3_bucket
    name: example
    properties:
      bucket: my-example-bucket
"""

    response = client.post(
        "/convert/yaml-to-terraform",
        json={"content": yaml_content},
    )

    assert response.status_code == 200
    assert 'resource "aws_s3_bucket" "example"' in response.json()["content"]
    assert 'bucket = "my-example-bucket"' in response.json()["content"]


def test_terraform_to_yaml_endpoint():
    buffer = BytesIO()

    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "main.tf",
            """
resource "aws_s3_bucket" "example" {
  bucket = "my-example-bucket"
}
""",
        )

    buffer.seek(0)

    response = client.post(
        "/convert/terraform-to-yaml",
        files={
            "file": (
                "terraform-project.zip",
                buffer.getvalue(),
                "application/zip",
            )
        },
    )

    assert response.status_code == 200

    content = response.json()["content"]

    assert "aws_s3_bucket" in content
    assert "my-example-bucket" in content


def test_yaml_to_terraform_rejects_invalid_yaml():
    response = client.post(
        "/convert/yaml-to-terraform",
        json={"content": "resources: [invalid"},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_terraform_to_yaml_rejects_invalid_zip():
    response = client.post(
        "/convert/terraform-to-yaml",
        files={
            "file": (
                "invalid.zip",
                b"This is not a ZIP archive",
                "application/zip",
            )
        },
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_yaml_zip_to_terraform_zip_endpoint():
    yaml_content = """
version: "1"
resources:
  - type: aws_s3_bucket
    name: example
    properties:
      bucket: my-example-bucket
"""

    input_buffer = BytesIO()

    with ZipFile(input_buffer, "w") as archive:
        archive.writestr("config.yaml", yaml_content)

    input_buffer.seek(0)

    response = client.post(
        "/convert/yaml-zip-to-terraform-zip",
        files={
            "file": (
                "yaml-project.zip",
                input_buffer.getvalue(),
                "application/zip",
            )
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    output_buffer = BytesIO(response.content)

    with ZipFile(output_buffer, "r") as archive:
        filenames = archive.namelist()

        assert "main.tf" in filenames

        terraform_content = archive.read("main.tf").decode("utf-8")

        assert 'resource "aws_s3_bucket" "example"' in terraform_content
        assert 'bucket = "my-example-bucket"' in terraform_content


def test_terraform_zip_to_yaml_zip_endpoint():
    terraform_content = """
resource "aws_s3_bucket" "example" {
  bucket = "my-example-bucket"
}
"""

    input_buffer = BytesIO()

    with ZipFile(input_buffer, "w") as archive:
        archive.writestr("main.tf", terraform_content)

    input_buffer.seek(0)

    response = client.post(
        "/convert/terraform-zip-to-yaml-zip",
        files={
            "file": (
                "terraform-project.zip",
                input_buffer.getvalue(),
                "application/zip",
            )
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    output_buffer = BytesIO(response.content)

    with ZipFile(output_buffer, "r") as archive:
        filenames = archive.namelist()

        assert "main.yaml" in filenames

        yaml_content = archive.read("main.yaml").decode("utf-8")

        assert "aws_s3_bucket" in yaml_content
        assert "my-example-bucket" in yaml_content


def test_request_middleware_rejects_oversized_content_length():
    async def dummy_app(scope, receive, send):
        raise AssertionError("Application should not receive this request")

    middleware = RequestSizeLimitMiddleware(
        app=dummy_app,
        max_request_size=4,
        paths={"/upload"},
    )

    messages = []

    async def receive():
        return {
            "type": "http.request",
            "body": b"",
            "more_body": False,
        }

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/upload",
        "headers": [(b"content-length", b"5")],
    }

    asyncio.run(middleware(scope, receive, send))

    assert messages[0]["status"] == 413


def test_request_middleware_rejects_oversized_body_without_content_length():
    async def dummy_app(scope, receive, send):
        while True:
            message = await receive()

            if message["type"] == "http.request" and not message.get("more_body", False):
                break

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            }
        )

        await send(
            {
                "type": "http.response.body",
                "body": b"ok",
            }
        )

    middleware = RequestSizeLimitMiddleware(
        app=dummy_app,
        max_request_size=4,
        paths={"/upload"},
    )

    messages = []
    request_chunks = [
        {
            "type": "http.request",
            "body": b"abc",
            "more_body": True,
        },
        {
            "type": "http.request",
            "body": b"def",
            "more_body": False,
        },
    ]

    async def receive():
        return request_chunks.pop(0)

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/upload",
        "headers": [],
    }

    asyncio.run(middleware(scope, receive, send))

    assert messages[0]["status"] == 413


def test_yaml_file_to_terraform_endpoint():
    yaml_content = b"""
version: "1"
resources:
  - type: aws_s3_bucket
    name: example
    properties:
      bucket: my-example-bucket
"""

    response = client.post(
        "/convert/yaml-file-to-terraform",
        files={
            "file": (
                "config.yaml",
                yaml_content,
                "application/yaml",
            )
        },
    )

    assert response.status_code == 200

    content = response.json()["content"]

    assert 'resource "aws_s3_bucket" "example"' in content
    assert 'bucket = "my-example-bucket"' in content


def test_terraform_file_to_yaml_endpoint():
    terraform_content = b"""
resource "aws_s3_bucket" "example" {
  bucket = "my-example-bucket"
}
"""

    response = client.post(
        "/convert/terraform-file-to-yaml",
        files={
            "file": (
                "main.tf",
                terraform_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    content = response.json()["content"]

    assert "aws_s3_bucket" in content
    assert "my-example-bucket" in content


def test_yaml_file_to_terraform_rejects_invalid_extension():
    response = client.post(
        "/convert/yaml-file-to-terraform",
        files={
            "file": (
                "config.txt",
                b"resources: []",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert "detail" in response.json()


def test_terraform_file_to_yaml_rejects_invalid_extension():
    response = client.post(
        "/convert/terraform-file-to-yaml",
        files={
            "file": (
                "main.txt",
                b'resource "aws_s3_bucket" "example" {}',
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert "detail" in response.json()


def test_yaml_to_terraform_hides_unexpected_internal_errors():
    with patch(
        "iac_converter.api.app.parse_yaml_project",
        side_effect=RuntimeError("Sensitive internal implementation detail"),
    ):
        test_client = TestClient(
            app,
            raise_server_exceptions=False,
        )

        response = test_client.post(
            "/convert/yaml-to-terraform",
            json={
                "content": """
version: "1"
resources: []
"""
            },
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error."}
    assert "Sensitive internal implementation detail" not in response.text


def test_yaml_file_to_terraform_hides_unexpected_internal_errors():
    with patch(
        "iac_converter.api.app.parse_yaml_project",
        side_effect=RuntimeError("Sensitive internal implementation detail"),
    ):
        test_client = TestClient(
            app,
            raise_server_exceptions=False,
        )

        response = test_client.post(
            "/convert/yaml-file-to-terraform",
            files={
                "file": (
                    "config.yaml",
                    b'version: "1"\nresources: []',
                    "application/yaml",
                )
            },
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error."}
    assert "Sensitive internal implementation detail" not in response.text
