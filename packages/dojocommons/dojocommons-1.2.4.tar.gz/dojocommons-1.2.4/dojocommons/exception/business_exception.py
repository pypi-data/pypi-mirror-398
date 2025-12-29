class BusinessException(Exception):
    """
    Exceção para erros de lógica de negócio.
    
    :param message: Mensagem de erro descritiva.
    :param status_code: Código HTTP a ser retornado (padrão: 400).
    """
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)