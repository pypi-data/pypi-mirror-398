import importlib


def test_import_root() -> None:
    module = importlib.import_module("kensho")
    assert hasattr(module, "PRODUCT_NAME")
