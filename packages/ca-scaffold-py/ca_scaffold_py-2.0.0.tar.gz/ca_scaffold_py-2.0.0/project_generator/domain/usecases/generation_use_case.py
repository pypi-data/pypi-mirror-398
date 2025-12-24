from project_generator.domain.models.project_models import ProjectRequest, GeneratedProjectInfo, ProjectGeneratorGateway

class GenerateProjectUseCase:
    """
    Use case that orchestrates the generation of a project.
    """
    def __init__(self, generator_adapter: ProjectGeneratorGateway):
        self._generator_adapter = generator_adapter

    def execute(self, project_data: ProjectRequest, no_zip: bool = False) -> GeneratedProjectInfo:
        """
        Executes the project generation flow.

        Args:
            project_data: The data required to generate the project.
            no_zip: If True, generates files directly instead of a zip archive.

        Returns:
            Information about the generated project, including the path to the ZIP file.
        """
        return self._generator_adapter.generate(project_data, no_zip)
