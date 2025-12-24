from dependency_injector import containers, providers
from arxiv import Client

from src.domain.usecase.paper_usecase import PaperUseCase
from src.domain.usecase.resource_usecase import ResourceUseCase
from src.domain.usecase.prompt_usecase import PromptUseCase
from src.domain.usecase.sum_usecase import SumUseCase
from src.domain.usecase.retrieve_personal_data_use_case import (
    RetrievePersonalDataUseCase
)

# ANCHOR_CONTAINER_IMPORT (no borrar)

from src.infrastructure.driven_adapters.http_client.arxiv_papers import (
    ArxivPaper
)
from src.infrastructure.driven_adapters.local_files.local_papers import (
    LocalPaper
)
from src.infrastructure.driven_adapters.prompts.papers import PromptPaper
from src.infrastructure.driven_adapters.api_connect_adapter import (
    ApiConnectAdapter,
    PersonalDataApiAdapter
)

# ANCHOR_CONTAINER_ADAPTER_IMPORT (no borrar)

from src.infrastructure.driven_adapters.aio_http_adapter import (
    AiohttpAdapter
)
from src.infrastructure.driven_adapters.secret_manager_adapter import (
    SecretManagerAdapter
)

PAPER_DIR = "arXiv-papers"


class Container(containers.DeclarativeContainer):

    config = providers.Configuration()

    secret_manager = providers.Singleton(
        SecretManagerAdapter,
        aws_config=config.aws
    )

    http_adapter = providers.Singleton(AiohttpAdapter)

    api_connect_adapter = providers.Singleton(
        ApiConnectAdapter,
        config=config.provided,
        http_adapter=http_adapter,
        secret_manager=secret_manager
    )

    paper_adapter = providers.Singleton(
        ArxivPaper,
        client=Client(),
        paper_dir=PAPER_DIR
    )

    resource_adapter = providers.Singleton(
        LocalPaper
    )

    prompt_adapter = providers.Singleton(
        PromptPaper
    )

    personal_data_adapter = providers.Singleton(
        PersonalDataApiAdapter,
        config=config.provided,
        api_adapter=api_connect_adapter
    )

    # ANCHOR_CONTAINER_ADAPTER (no borrar)

    paper_usecase = providers.Singleton(
        PaperUseCase,
        paper_repository=paper_adapter
    )

    resource_usecase = providers.Singleton(
        ResourceUseCase,
        resource_repository=resource_adapter
    )

    prompt_usecase = providers.Singleton(
        PromptUseCase,
        prompt_repository=prompt_adapter
    )

    sum_usecase = providers.Factory(
        SumUseCase
    )

    personal_data_usecase = providers.Singleton(
        RetrievePersonalDataUseCase,
        personal_data_adapter=personal_data_adapter
    )

    # ANCHOR_CONTAINER_USE_CASE (no borrar)
