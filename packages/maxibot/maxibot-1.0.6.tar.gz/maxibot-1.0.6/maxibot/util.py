from io import BytesIO
from typing import Union

try:
    # noinspection PyPackageRequirements
    from PIL import Image
    pil_imported = True
except ImportError:
    pil_imported = False


def is_command(text: str) -> bool:
    """
    Проверка, является ли строка командой

    :param text: строка
    :type text: str
    :return: Флаг, является ли строка командой
    :rtype: bool
    """
    if text is None:
        return False
    return text.startswith('/')


def extract_command(text: str) -> Union[str, None]:
    """
    Вытаскивает команду из текста сообщения

    :param text: Description
    :type text: str
    :return: Description
    :rtype: Union[str, None]
    """
    if text is None:
        return None
    return text.split()[0].split('@')[0][1:] if is_command(text) else None


def is_pil_image(var) -> bool:
    """
    Returns True if the given object is a PIL.Image.Image object.

    :param var: object to be checked
    :type var: :obj:`object`

    :return: True if the given object is a PIL.Image.Image object.
    :rtype: :obj:`bool`
    """
    return pil_imported and isinstance(var, Image.Image)


def pil_image_to_bytes(image, extension='JPEG', quality='web_low') -> bool:
    """
    Returns True if the given object is a PIL.Image.Image object.

    :param var: object to be checked
    :type var: :obj:`object`

    :return: True if the given object is a PIL.Image.Image object.
    :rtype: :obj:`bool`
    """
    if pil_imported:
        photoBuffer = BytesIO()
        image.convert('RGB').save(photoBuffer, extension, quality=quality)
        photoBuffer.seek(0)
        return photoBuffer
    else:
        raise RuntimeError('PIL module is not imported')


def get_text(media):
    """
    Метод получения текста из media

    :param media: Объект медиа
    """
    try:
        text = media.caption
    except Exception:
        text = None
    finally:
        return text


def get_parse_mode(media, parse_mode: str):
    """
    Метод получения parce_mode из media

    :param media: Объект медиа
    :param parse_mode: Тип парсинга раметки
    """
    try:
        parse_mode_res = media.parse_mode.lower()
    except Exception:
        parse_mode_res = parse_mode.lower()
    finally:
        return parse_mode_res
