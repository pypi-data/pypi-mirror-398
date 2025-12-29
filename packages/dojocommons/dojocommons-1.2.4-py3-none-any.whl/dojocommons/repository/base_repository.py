from typing import Generic, List, Optional, Type, TypeVar
import threading
from dojocommons.model.app_configuration import AppConfiguration
from dojocommons.service.db_service import DbService

# Define um TypeVar para representar o tipo genérico
T = TypeVar("T")

_id_generation_lock = threading.Lock()

class BaseRepository(Generic[T]):
    """
    BaseRepository
    ==============

    Uma classe genérica para manipulação de entidades em um banco de dados.
     Esta classe utiliza o `DbService` para executar operações no
      banco de dados e é projetada para trabalhar com modelos que seguem
       o padrão de validação do Pydantic.

    Classes
    -------
    BaseRepository
        Classe genérica para operações CRUD em um banco de dados.

    Parâmetros
    ----------
    cfg : AppConfiguration
        Configuração da aplicação, utilizada para inicializar o serviço de
         banco de dados.
    model : Type[T]
        O modelo da entidade que será manipulado. Deve ser uma classe que
         segue o padrão de validação do Pydantic.
    table_name : str
        O nome da tabela no banco de dados onde as entidades serão armazenadas.

    Métodos
    -------
    create(entity: T) -> T
        Insere uma nova entidade no banco de dados.
    find_by_id(entity_id: int) -> Optional[T]
        Busca uma entidade pelo ID.
    find_all() -> List[T]
        Retorna todas as entidades cadastradas no banco de dados.
    update(entity_id: int, updates: dict) -> Optional[T]
        Atualiza uma entidade pelo ID com os valores fornecidos.
    delete(entity_id: int) -> None
        Deleta uma entidade pelo ID.

    Exemplo de Uso
    --------------
    .. code-block:: python

        from typing import Optional
        from pydantic import BaseModel
        from dojocommons.model.app_configuration import AppConfiguration
        from dojocommons.repository.base_repository import BaseRepository

        # Definição do modelo
        class User(BaseModel):
            id: Optional[int] = None  # ✅ ID opcional (será gerado automaticamente)
            name: str
            email: str

        # Definição do repositório
        class UserRepository(BaseRepository[User]):
            def __init__(self, cfg: AppConfiguration):
                super().__init__(cfg, User, "users")

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

        # Instanciação do repositório
        user_repository = Go.pRepository(cfg=app_cfg)

        # Criação de um novo usuário
        new_user = User(name="John Doe", email="john.doe@example.com")
        user_repository.create(new_user)

        # Busca de um usuário pelo ID
        user = user_repository.find_by_id(1)
        if user:
            print(f"Usuário encontrado: {user.name} - {user.email}")

        # Atualização de um usuário
        updated_user = user_repository.update(1, {"name": "John Smith"})
        if updated_user:
            print(f"Usuário atualizado: {updated_user.name}")

        # Listagem de todos os usuários
        all_users = user_repository.find_all()
        for user in all_users:
            print(f"{user.id}: {user.name} - {user.email}")

        # Deleção de um usuário
        user_repository.delete(1)
    """

    def __init__(self, cfg: AppConfiguration, model: Type[T], table_name: str):
        self._db = DbService(cfg)
        self._model = model
        self._table_name = table_name
        print(f"[DEBUG][BaseRepository] table_name: {self._table_name}")
        print(f"[DEBUG][BaseRepository] cfg.s3_bucket: {cfg.s3_bucket}, cfg.s3_path: {cfg.s3_path}")
        self._db.create_table(model, table_name)

    def __del__(self):
        """
        Método destrutor para garantir que a conexão com o banco de dados
        seja fechada quando o repositório for destruído.
        """
        self.persist_data()

    def persist_data(self):
        self._db.persist_data(self._table_name)

    def _generate_next_id(self) -> int:
        """
        ✅ Gera o próximo ID disponível de forma thread-safe.
        
        Estratégia: Auto-increment (max_id + 1)
        
        :return: O próximo ID único disponível.
        :rtype: int
        """
        with _id_generation_lock:
            # Busca o maior ID atual
            query = f"SELECT MAX(id) as max_id FROM {self._table_name}"
            result = self._db.execute_query(query).fetchone()
            
            max_id = result[0] if result[0] is not None else 0
            next_id = max_id + 1
            
            print(f"[DEBUG][_generate_next_id] Tabela: {self._table_name}, "
                  f"max_id={max_id}, next_id={next_id}")
            
            return next_id

    def create(self, entity: T) -> T:
        """
        Insere uma nova entidade no banco.

        :param T entity: A entidade a ser inserida no banco de dados.
        :return: A entidade inserida no banco de dados.
        :rtype: T
        """
        # ✅ Gera ID automaticamente se não fornecido
        if not hasattr(entity, 'id') or entity.id is None:
            new_id = self._generate_next_id()
            entity.id = new_id
            print(f"[DEBUG][create] ID gerado automaticamente: {new_id}")
        else:
            # Valida se o ID já existe (evita sobrescrever)
            if self.exists_by_id(entity.id):
                raise ValueError(
                    f"Entidade com id={entity.id} já existe na tabela {self._table_name}. "
                    f"Use update() ao invés de create()."
                )
            print(f"[DEBUG][create] ID fornecido pelo cliente: {entity.id}")

        # Filtra as colunas e valores para ignorar os que são None
        filtered_data = {k: v for k, v in entity.__dict__.items() if v is not None}

        columns = ", ".join(filtered_data.keys())
        placeholders = ", ".join(["?"] * len(filtered_data))
        values = tuple(filtered_data.values())

        query = f"INSERT INTO {self._table_name} ({columns}) VALUES ({placeholders})"
        print(f"[DEBUG][create] Query: {query}")
        print(f"[DEBUG][create] Values: {values}")

        self._db.execute_query(query, values)

        print(f"[INFO][create] Entidade criada com sucesso: id={entity.id}")
        return entity

    def find_by_id(self, entity_id: int) -> Optional[T]:
        """
        Busca uma entidade pelo ID.

        :param int entity_id: O ID da entidade a ser buscada.
        :return: A entidade encontrada ou None se não existir.
        :rtype: Optional[T]
        """
        print(f"[DEBUG][find_by_id] Buscando id={entity_id} na tabela: {self._table_name}")

        cursor = self._db.execute_query(
            f"SELECT * FROM {self._table_name} WHERE id = ?",
            (entity_id,),
        )
        row = cursor.fetchone()
        print(f"[DEBUG][find_by_id] Resultado: {row}")
        
        if row:
            column_names = [description[0] for description in cursor.description]
            row_dict = dict(zip(column_names, row))
            print(f"[DEBUG][find_by_id] row_dict: {row_dict}")
            
            return self._model.model_validate(row_dict)
        
        return None

    def find_all(self, **filters) -> List[T]:
        """
        Retorna todas as entidades cadastradas.

        :return: Uma lista de todas as entidades cadastradas
         no banco de dados.
        :rtype: List[T]
        """
        print(f"[DEBUG][find_all] Lendo todos da tabela: {self._table_name}")
        query = f"SELECT * FROM {self._table_name}"
        if filters:
            where_clauses = [f"{key} = {value}" for key, value in filters.items()]
            print(f"[DEBUG][find_all] Consulta com filtros: {where_clauses}")
            query += f" WHERE {' AND '.join(where_clauses)}"
            values = tuple(filters.values())
            cursor = self._db.execute_query(query, values)
        else:
            cursor = self._db.execute_query(query)
        
        rows = cursor.fetchall()
        print(f"[DEBUG][find_all] Resultado: {rows}")

        # ✅ CORREÇÃO: Pegar os nomes das colunas do cursor
        column_names = [description[0] for description in cursor.description]
        print(f"[DEBUG][find_all] Colunas: {column_names}")

        # ✅ Mapear cada linha para um dict com os nomes corretos das colunas
        result = []
        for row in rows:
            row_dict = dict(zip(column_names, row))
            print(f"[DEBUG][find_all] row_dict: {row_dict}")

            try:
                entity = self._model.model_validate(row_dict)
                result.append(entity)
            except Exception as e:
                print(f"[ERROR][find_all] Erro ao validar entidade: {e}")
                print(f"[ERROR][find_all] row_dict problemático: {row_dict}")
                raise
            
        return result

    def update(self, entity_id: int, updates: dict) -> Optional[T]:
        """
        Atualiza uma entidade pelo ID.

        :param int entity_id: O ID da entidade a ser atualizada.
        :param dict updates: Um dicionário com os campos a serem atualizados
         e seus novos valores.
        :return: A entidade atualizada ou None se não existir.
        :rtype: Optional[T]
        """
        # Filtra as colunas e valores para ignorar os que são None
        filtered_data = {k: v for k, v in updates.items() if v is not None}

        updates_sql = ", ".join([f"{key} = ?" for key in filtered_data.keys()])
        values = list(filtered_data.values()) + [entity_id]

        self._db.execute_query(
            f"UPDATE {self._table_name} SET {updates_sql} WHERE id = ?",
            tuple(values),
        )

        return self.find_by_id(entity_id)

#    def update(self, entity_id: int, updates: dict) -> Optional[T]:
#        """
#        Atualiza uma entidade pelo ID.
#
#        :param int entity_id: O ID da entidade a ser atualizada.
#        :param dict updates: Um dicionário com os campos a serem atualizados
#            e seus novos valores.
#        :return: A entidade atualizada ou None se não existir.
#        :rtype: Optional[T]
#        """
#        # ✅ Não permite atualizar o ID
#        if 'id' in updates:
#            print(f"[WARNING][update] Tentativa de atualizar ID será ignorada")
#            del updates['id']
#
#        # Filtra as colunas e valores para ignorar os que são None
#        filtered_data = {k: v for k, v in updates.items() if v is not None}
#
#        if not filtered_data:
#            print(f"[WARNING][update] Nenhum campo para atualizar")
#            return self.find_by_id(entity_id)
#
#        updates_sql = ", ".join([f"{key} = ?" for key in filtered_data.keys()])
#        values = list(filtered_data.values()) + [entity_id]
#
#        query = f"UPDATE {self._table_name} SET {updates_sql} WHERE id = ?"
#        print(f"[DEBUG][update] Query: {query}")
#        print(f"[DEBUG][update] Values: {values}")
#
#        self._db.execute_query(query, tuple(values))
#        
#        print(f"[INFO][update] Entidade atualizada: id={entity_id}")
#        return self.find_by_id(entity_id)


    def delete(self, entity_id: int) -> None:
        """
        Deleta uma entidade pelo ID.

        :param int entity_id: O ID da entidade a ser deletada.
        """
        self._db.execute_query(
            f"DELETE FROM {self._table_name} WHERE id = ?",
            (entity_id,),
        )

    def exists_by_id(self, id_value: int) -> bool:
        """
        Verifica se um registro com o ID especificado já existe.
        :param id_value: Valor do ID a ser verificado.
        :return: True se existir, False caso contrário.
        """
        query = f"SELECT COUNT(*) as count FROM {self._table_name} WHERE id = ?"
        result = self._db.execute_query(query, (id_value,)).fetchone()
        return result[0] > 0
