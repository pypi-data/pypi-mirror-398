"""
Este módulo reúne seletores utilizados pela classe principal (WhatsApp).

Atualizado em: 12 de dezembro de 2025
"""


class Elements:
    """Classe utilitária que concentra os seletores do WhatsApp Web."""

    SEND_BUTTON = "//*[contains(@aria-label,'Enviar')]"
    ATTACHMENT_BUTTON = '//*[@data-icon="plus-rounded"]'
    IMAGE_INPUT_FILE = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
    ALL_INPUT_FILE = "//input[@accept='*']"
    DATA_PROFILE_BUTTON = "//div[@title='Dados do perfil']"
    MEDIA_DOCS = "//span[text()='Mídia, links e docs']"
    DOWNLOAD_BUTTON = "//button[@aria-label='Baixar']"
    INPUT_MESSAGE = "//div[@aria-placeholder='Digite uma mensagem']"
    SENDING_MESSAGE_CLOCK = '//*[@id="main"]//*[@data-icon="msg-time"]'
    THIS_MONTH = "//div[text()='Neste mês']"
    FIRST_IMAGE = "//div[contains(@aria-label,'Imagem')][1]"
    NEXT_IMAGE_BUTTON = "//*[@id='app']/div/div/span[3]/div/div/div[1]/div/div[2]/div[1]/div/span/button"
    IMAGE_LIST = (
        "(//div[contains(@aria-label, 'Lista de mídias')]/div[@role='listitem'])"
    )
    HAS_TODAY = "//div[contains(text(), 'Hoje às')]"
    DOCUMENT_BUTTON = '//*[text()="Documento"]'
    CLOSE_BUTTON = "//button[@aria-label='Fechar']"
    CONVERSATIONS_BUTTON = "//button[@aria-label='Conversas']"
    SEARCH_BOX = "(//*[@role='textbox'])[1]"
    SEARCH_BOX_EDIT = '(//div[@contenteditable="true" and @role="textbox"])[1]'
    MORE_OPTIONS_BUTTON = "//button[@title='Mais opções']"
    CLEAN_CHAT = "//span[text()='Limpar conversa']"
    CONFIRM_CLEAN_CHAT = "//div[text()='Limpar conversa']"
    IMAGE_SELECTOR = '//div[contains(@aria-label,"Imagem")]'
    NR_NOT_FOUND = (
        '//*[@id="app"]/div/span[2]/div/span/div/div/div/div/div/div[2]/div/div'
    )
    IMAGE_BUTTON = '//*[contains(text(),"Fotos")]'
