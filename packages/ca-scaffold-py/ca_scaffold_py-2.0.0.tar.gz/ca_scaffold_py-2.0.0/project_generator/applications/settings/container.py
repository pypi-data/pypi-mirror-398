from dependency_injector import containers, providers
from project_generator.domain.usecases.generation_use_case import GenerateProjectUseCase
from project_generator.infrastructure.driven_adapters.cookiecutter_adapter import CookiecutterAdapter

from project_generator.domain.usecases.update_use_case import UpdateProjectUseCase
from project_generator.infrastructure.driven_adapters.project_analyzer_adapter import ProjectAnalyzerAdapter
from project_generator.infrastructure.driven_adapters.code_injector_adapter import CodeInjectorAdapter
from project_generator.domain.usecases.restore_use_case import RestoreBackupUseCase

class Container(containers.DeclarativeContainer):
    """Dependency Injection Container."""
    cookiecutter_adapter = providers.Singleton(CookiecutterAdapter)
    restore_backup_use_case = providers.Singleton(RestoreBackupUseCase)
    generation_use_case = providers.Singleton(
        GenerateProjectUseCase,
        generator_adapter=cookiecutter_adapter
    )

    project_analyzer_adapter = providers.Singleton(ProjectAnalyzerAdapter)
    code_injector_adapter = providers.Singleton(CodeInjectorAdapter)
    update_project_use_case = providers.Singleton(
        UpdateProjectUseCase,
        analyzer=project_analyzer_adapter,
        injector=code_injector_adapter
    )

container = Container()