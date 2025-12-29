from typing import Generic, List, Type, TypeVar

from dojocommons.model.app_configuration import AppConfiguration
from dojocommons.repository.base_repository import BaseRepository
from dojocommons.exception.business_exception import BusinessException

# Define um TypeVar para representar o tipo genérico T
T = TypeVar("T")


class BaseService(Generic[T]):
    """
    BaseService
    ===========

    Uma classe genérica para manipulação de entidades utilizando um repositório base.
    Esta classe fornece métodos para operações CRUD (Create, Read, Update, Delete) em entidades.

    Classes
    -------

    BaseService
        Classe genérica para operações de serviço em entidades.

    Parâmetros
    ----------

    cfg : AppConfiguration
        Configuração da aplicação, utilizada para inicializar o repositório.

    repository_class : Type[BaseRepository[T]]
        A classe do repositório que será utilizada para manipular as entidades.

    Métodos
    -------

    .. py:method:: create(entity: T) -> T
        Cria uma nova entidade.

        :param entity: A entidade que será criada.
        :type entity: T
        :return: A entidade criada.
        :rtype: T

    .. py:method:: get_by_id(entity_id: int) -> T
        Obtém uma entidade pelo ID.

        :param entity_id: O ID da entidade que será buscada.
        :type entity_id: int
        :return: A entidade encontrada.
        :rtype: T

    .. py:method:: list_all() -> List[T]
        Lista todas as entidades.

        :return: Uma lista contendo todas as entidades.
        :rtype: List[T]

    .. py:method:: update(entity: T) -> T
        Atualiza uma entidade.

        :param entity: A entidade que será atualizada.
        :type entity: T
        :return: A entidade atualizada.
        :rtype: T

    .. py:method:: delete(entity_id: int) -> None
        Deleta uma entidade pelo ID.

        :param entity_id: O ID da entidade que será deletada.
        :type entity_id: int
        :return: Este método não retorna nenhum valor.
        :rtype: None

    Exemplo de Uso
    --------------

    .. code-block:: python

        from typing import Optional
        from pydantic import BaseModel
        from dojocommons.model.app_configuration import AppConfiguration
        from dojocommons.repository.base_repository import BaseRepository
        from dojocommons.service.base_service import BaseService

        # Definição do modelo
        class User(BaseModel):
            id: Optional[int]
            name: str
            email: str

        # Definição do repositório
        class UserRepository(BaseRepository[User]):
            def __init__(self, cfg: AppConfiguration):
                super().__init__(cfg, User, "users")

        # Definição do serviço
        class UserService(BaseService[User]):
            def __init__(self, cfg: AppConfiguration):
                super().__init__(cfg, UserRepository)

        # Configuração da aplicação
        app_cfg = AppConfiguration(
            app_name="MyApp",
            app_version="1.0.0",
            s3_bucket="my-bucket",
            s3_path="db",
            aws_region="us-east-1",
            aws_endpoint="http://localhost:9000",
            aws_access_key_id="my-access-key",
            aws_secret_access_key="my-secret-key",
        )

        # Instanciação do serviço
        user_service = UserService(cfg=app_cfg)

        # Criação de um novo usuário
        new_user = User(name="John Doe", email="john.doe@example.com")
        user_service.create(new_user)

        # Busca de um usuário pelo ID
        user = user_service.get_by_id(1)
        if user:
            print(f"Usuário encontrado: {user.name} - {user.email}")

        # Atualização de um usuário
        updated_user = user_service.update(User(id=1, name="John Smith", email="john.smith@example.com"))
        if updated_user:
            print(f"Usuário atualizado: {updated_user.name}")

        # Listagem de todos os usuários
        all_users = user_service.list_all()
        for user in all_users:
            print(f"{user.id}: {user.name} - {user.email}")

        # Deleção de um usuário
        user_service.delete(1)
    """

    def __init__(
        self, cfg: AppConfiguration, repository_class: Type[BaseRepository[T]]
    ):
        self._repository = repository_class(cfg)  # type: ignore

    def _validate_unique_id(self, entity):
        """
        Valida se o ID é único antes de criar.
        :param entity: Entidade a ser validada.
        :raises BusinessException: Se o ID já existir.
        """
        if hasattr(entity, 'id') and entity.id is not None:
            if self._repository.exists_by_id(entity.id):
                raise BusinessException(
                    f"Já existe um registro com o ID {entity.id}",
                    status_code=409  # Conflict
                )
    
    def create(self, entity: T) -> T:
        self._validate_unique_id(entity)
        """Cria uma nova entidade."""
        return self._repository.create(entity)

    def get_by_id(self, entity_id: int) -> T:
        """Obtém uma entidade pelo ID."""
        return self._repository.find_by_id(entity_id)

    def list_all(self, **filters) -> List[T]:
        """Lista todas as entidades."""
        print("[DEBUG][Service] Chamando find_all")
        if not filters:
            print("[DEBUG][Service] Sem filtros, chamando find_all sem parâmetros")
            return self._repository.find_all()
        print(f"[DEBUG][Service] Com filtros: {filters}, chamando find_all com parâmetros")
        return self._repository.find_all(**filters)

    def update(self, entity: T) -> T:
        """Atualiza uma entidade."""
        return self._repository.update(entity.id, entity.model_dump())

    def delete(self, entity_id: int) -> None:
        """Deleta uma entidade pelo ID."""
        self._repository.delete(entity_id)

    def persist(self):
        self._repository.persist_data()
