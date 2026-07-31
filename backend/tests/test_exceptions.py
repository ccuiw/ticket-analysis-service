"""领域异常层次结构测试。"""

from app.domain.exceptions import (
    DomainError,
    AnalysisError,
    ValidationError,
    RepairFailedError,
    PromptNotFoundError,
)


class TestExceptionHierarchy:
    def test_analysis_error_is_domain_error(self):
        assert issubclass(AnalysisError, DomainError)

    def test_validation_error_is_domain_error(self):
        assert issubclass(ValidationError, DomainError)

    def test_repair_failed_error_is_domain_error(self):
        assert issubclass(RepairFailedError, DomainError)

    def test_prompt_not_found_error_is_domain_error(self):
        assert issubclass(PromptNotFoundError, DomainError)

    def test_exception_message(self):
        error = AnalysisError("测试错误消息")
        assert str(error) == "测试错误消息"
        assert "测试" in repr(error)

    def test_domain_error_not_direct_fastapi_import(self):
        """domain 层不应导入 FastAPI。"""
        import inspect
        import app.domain.exceptions as mod
        for _name, obj in inspect.getmembers(mod):
            if inspect.ismodule(obj):
                assert not obj.__name__.startswith("fastapi"), \
                    f"domain.exceptions imports {obj.__name__}"
