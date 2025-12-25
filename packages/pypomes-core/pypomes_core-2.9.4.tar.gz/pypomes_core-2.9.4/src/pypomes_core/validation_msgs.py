from typing import Final, Literal

__ERR_MSGS: Final[dict[int, dict[str, str]]] = {
    # omits the attribute 'code'
    100: {
        "en": "{}",
        "pt": "{}",
    },
    101: {
        "en": "{}",
        "pt": "{}",
    },
    102: {
        "en": "Unexpected error: {}",
        "pt": "Erro inesperado: {}",
    },
    103: {
        "en": "Invalid operation {}",
        "pt": "Operação {} inválida",
    },
    104: {
        "en": "The operation {} returned the error {}",
        "pt": "A operação {} retornou o erro {}",
    },
    105: {
        "en": "Error invoking service {}: {}",
        "pt": "Erro na invocação do serviço {}: {}",
    },
    106: {
        "en": "No records matching the provided criteria found",
        "pt": "Não foram encontrados registros para os critérios fornecidos",
    },
    107: {
        "en": "No files matching the provided criteria found",
        "pt": "Não foram encontrados arquivos para os critérios fornecidos",
    },
    111: {
        "en": "File {} not found",
        "pt": "Arquivo {} não encontrado",
    },
    112: {
        "en": "Environment variable {} not defined",
        "pt": "Variável de ambiente {} não definida",
    },
    121: {
        "en": "Required attribute",
        "pt": "Atributo obrigatório",
    },
    122: {
        "en": "Attribute is unknown or invalid in this context",
        "pt": "Atributo desconhecido ou inválido para o contexto",
    },
    123: {
        "en": "Attribute not applicable for {}",
        "pt": "Atributo não se aplica a {}",
    },
    124: {
        "en": "Attribute applicable only for {}",
        "pt": "Atributo se aplica apenas a {}",
    },
    125: {
        "en": "A value has not been assigned",
        "pt": "Valor não foi atribuído",
    },
    126: {
        "en": "Value {} cannot be assigned for attributes {} at the same time",
        "pt": "Valor {} não pode ser especificado aos atributos {} ao mesmo tempo",
    },
    127: {
        "en": "Attributes {} cannot be assigned values at the same time",
        "pt": "Atributos {} não podem ter valores especificados ao mesmo tempo",
    },
    141: {
        "en": "Invalid value {}",
        "pt": "Valor {} inválido",
    },
    142: {
        "en": "Invalid value {}: {}",
        "pt": "Valor {} inválido: {}",
    },
    143: {
        "en": "Invalid value {}: must be less than {}",
        "pt": "Valor {} inválido: deve ser menor que {}",
    },
    144: {
        "en": "Invalid value {}: must be greater than {}",
        "pt": "Valor {} inválido: deve ser maior que {}",
    },
    145: {
        "en": "Invalid, inconsistent, or missing arguments",
        "pt": "Argumento(s) inválido(s), inconsistente(s) ou não fornecido(s)",
    },
    146: {
        "en": "Invalid value {}: length must be {}",
        "pt": "Valor {} inválido: comprimento deve ser {}",
    },
    147: {
        "en": "Invalid value {}: length shorter than {}",
        "pt": "Valor {} inválido: comprimento menor que {}",
    },
    148: {
        "en": "Invalid value {}: length longer than {}",
        "pt": "Valor {} inválido: comprimento maior que {}",
    },
    149: {
        "en": "Invalid value {}: must be {}",
        "pt": "Valor {} inválido: deve ser {}",
    },
    150: {
        "en": "Invalid value {}: must be one of {}",
        "pt": "Valor {} inválido: deve ser um de {}",
    },
    151: {
        "en": "Invalid value {}: must be in the range {}",
        "pt": "Valor {} inválido: deve estar no intervalo {}",
    },
    152: {
        "en": "Invalid value {}: must be type {}",
        "pt": "Valor {} inválido: deve ser do tipo {}",
    },
    153: {
        "en": "Invalid value {}: date is later than the current date",
        "pt": "Valor {} inválido: data posterior à data atual",
    },
    154: {
        "en": "Value {} not a valid date",
        "pt": "Valor {} não é uma data válida"
    },
    171: {
        "en": "Error receiving attachment: {}",
        "pt": "Erro no recebimento de documento anexado: {}",
    },
    172: {
        "en": "Invalid attachment type {}: {}",
        "pt": "Tipo de documento anexado {} inválido: {}",
    },
    173: {
        "en": "Unable to receive attachment {}",
        "pt": "Não foi possível receber o documento anexado {}",
    },
    201: {
        "en": "Error accessing the DB in {}: {}",
        "pt": "Erro na interação com o BD em {}: {}",
    },
    202: {
        "en": "No record found on DB in {}, for {}",
        "pt": "Nenhum registro encontrado no BD, em {} para {}",
    },
    203: {
        "en": "Error accessing the object store: {}",
        "pt": "Erro na interação com o armazenador de objetos: {}",
    },
    204: {
        "en": "Unable to retrieve document {} from the object store",
        "pt": "Não foi possível recuperar o documento {} no armazenador de objetos",
    },
    205: {
        "en": "Error accessing the message queue manager: {}",
        "pt": "Erro na interação com o gerenciador de mensagens: {}",
    },
    206: {
        "en": "Record already exists on DB in {}, for {}",
        "pt": "Registro já existe no BD, em {} para {}",
    },
    207: {
        "en": "More than one record exists on DB in {}, for {}",
        "pt": "Mais de um registro existente no BD, em {} para {}",
    },
    211: {
        "en": "Error accessing the job scheduler: {}",
        "pt": "Erro na interação com o gerenciador de tarefas: {}",
    },
    212: {
        "en": "Unable to access the entry point {} for the job {}: {}",
        "pt": "Não foi possível acesso ao ponto de entrada {} para a tarefa {}: {}",
    },
    213: {
        "en": "Invalid CRON expression {}",
        "pt": "Expressão CRON {} inválida",
    },
    221: {
        "en": "Error accessing the SOAP service: {}",
        "pt": "Erro na interação com o serviço SOAP: {}",
    },
    222: {
        "en": "SOAP envelope {} has invalid content: {}",
        "pt": "Envelope SOAP {} com conteúdo inválido: {}",
    },
    231: {
        "en": "Token not provided",
        "pt": "Token não fornecido",
    },
    232: {
        "en": "Invalid token",
        "pt": "Token inválido",
    },
    233: {
        "en": "User not provided",
        "pt": "Usuário não fornecido",
    },
    234: {
        "en": "Invalid user {}",
        "pt": "Usuário {} inválido",
    },
    235: {
        "en": "User/password not provided",
        "pt": "Usuário/senha não fornecido",
    },
    236: {
        "en": "Invalid user/password",
        "pt": "Usuário/senha inválido",
    },
    237: {
        "en": "Value {} does not meet the formation rules",
        "pt": "Valor {} não atende as regras de formação"
    },
    241: {
        "en": "Error accessing the digital signing service at {}: {}",
        "pt": "Erro no acesso ao serviço de assinaturas em {}: {}",
    },
    242: {
        "en": "Failed to verify the digital signature of document {}: {}",
        "pt": "Erro na verificação da assinatura digital do documento {}:{}",
    },
    243: {
        "en": "Failed to verify the digest for document {}: {}",
        "pt": "Erro na verificação do digesto do documento {}: {}",
    },
    244: {
        "en": "Document {} is not digitally signed",
        "pt": "Documento {} não contem assinatura digital",
    },
    245: {
        "en": "Invalid digital signature in document {}: {}",
        "pt": "A assinatura digital no documento {} é inválida: {}",
    },
    246: {
        "en": "Document {} was modified after being digitally signed",
        "pt": "Documento {} modificado após assinatura digital",
    },
    247: {
        "en": "Document {} has invalid digest",
        "pt": "Digesto do documento {} inválido",
    },
    248: {
        "en": "Document {} has already been filed",
        "pt": "Documento {} já cadastrado",
    }
}

_ERR_MSGS_EN: dict[int, str] = {}
for key, value in __ERR_MSGS.items():
    _ERR_MSGS_EN[key] = value["en"]

_ERR_MSGS_PT: dict[int, str] = {}
for key, value in __ERR_MSGS.items():
    _ERR_MSGS_PT[key] = value["pt"]


def validate_set_msgs(msgs: dict[int, str],
                      lang: Literal["en", "pt"] = "en") -> None:
    """
    Set  the standard validation messages list for language *lang* to the coded messages in *msgs*.

    If applicable, this operation should be performed at the start of the application importing this module,
    before any attempt to read from *_ERR_MSGS_EN* or *_ERR_MSGS_PT*.

    :param msgs: list of coded messages to set the standard validation messages to
    :param lang: the reference language
    """
    global _ERR_MSGS_EN, _ERR_MSGS_PT

    match lang:
        case "en":
            _ERR_MSGS_EN = msgs
        case "pt":
            _ERR_MSGS_PT = msgs


def validate_update_msgs(msgs: dict[int, str],
                         lang: Literal["en", "pt"] = "en") -> None:
    """
    Update the messages in the standard validation messages list with *msgs*, for language *lang*.

    If applicable, this operation should be performed at the start of the application importing this module,
    before any attempt to read from *_ERR_MSGS_EN* or *_ERR_MSGS_PT*.

    :param msgs: list of coded messages to update the standard validation messages with
    :param lang: the reference language
    """
    match lang:
        case "en":
            _ERR_MSGS_EN.update(msgs)
        case "pt":
            _ERR_MSGS_PT.update(msgs)
