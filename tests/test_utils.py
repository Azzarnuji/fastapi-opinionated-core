
import pytest
from fastapi_opinionated.utils.import_string import import_string
from fastapi_opinionated.shared.publish_metadata import PublishMetadata

from fastapi_opinionated.utils.html_view import html_content

class MyClass:
    pass

def test_import_string_success():
    # Import self to test
    cls = import_string("tests.test_utils.MyClass")
    assert cls is MyClass

def test_import_string_module_error():
    with pytest.raises(ImportError):
        import_string("non_existent_module.Class")

def test_import_string_class_error():
    with pytest.raises(AttributeError):
        import_string("tests.test_utils.NonExistentClass")

@pytest.mark.asyncio
async def test_publish_metadata():
    pm = PublishMetadata(domain="test")
    assert pm.domain == "test"
    assert pm.overwrite is False
    
    # Coverage for pass methods
    await pm.pre_publish()
    await pm.post_publish()


from unittest.mock import patch, mock_open
from fastapi_opinionated.utils.html_view import html_content

@pytest.mark.asyncio
async def test_html_content_success():
    m = mock_open(read_data="<html></html>")
    with patch("builtins.open", m):
        content = await html_content("user/page.html")
        assert content == "<html></html>"
        m.assert_called_with("app/domains/user/page.html", "r", encoding="utf-8")

    
