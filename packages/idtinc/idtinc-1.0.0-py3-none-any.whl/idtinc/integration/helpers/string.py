import re


def decode_unicode_escape(cls, text) -> str:
    if isinstance(text, str):
        try:
            if "\\u" in text:
                return text.encode("utf-8").decode("unicode_escape")
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass

    return text or ""


def remove_vietnamese_accents(cls, text: str) -> str:
    if not isinstance(text, str) or not text:
        return text or ""

    translation_table = str.maketrans(
        "áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựíìỉĩịýỳỷỹỵđ"
        "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÍÌỈĨỊÝỲỶỸỴĐ",
        "aaaaaaaaaaaaaaaaaeeeeeeeeeeeooooooooooooooooouuuuuuuuuuuiiiiiyyyyyd"
        "AAAAAAAAAAAAAAAAAEEEEEEEEEEEOOOOOOOOOOOOOOOOOUUUUUUUUUUUIIIIIYYYYYD",
    )
    return text.translate(translation_table)


def slugify_vietnamese(cls, text: str) -> str:
    text = re.sub(r"[àáạảãâầấậẩẫăằắặẳẵ]", "a", text)
    text = re.sub(r"[èéẹẻẽêềếệểễ]", "e", text)
    text = re.sub(r"[ìíịỉĩ]", "i", text)
    text = re.sub(r"[òóọỏõôồốộổỗơờớợởỡ]", "o", text)
    text = re.sub(r"[ùúụủũưừứựửữ]", "u", text)
    text = re.sub(r"[ỳýỵỷỹ]", "y", text)
    text = re.sub(r"[đ]", "d", text)
    text = re.sub(r"[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]", "A", text)
    text = re.sub(r"[ÈÉẸẺẼÊỀẾỆỂỄ]", "E", text)
    text = re.sub(r"[ÌÍỊỈĨ]", "I", text)
    text = re.sub(r"[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]", "O", text)
    text = re.sub(r"[ÙÚỤỦŨƯỪỨỰỬỮ]", "U", text)
    text = re.sub(r"[ỲÝỴỶỸ]", "Y", text)
    text = re.sub(r"[Đ]", "D", text)
    text = re.sub(r"[\u0300\u0301\u0303\u0309\u0323]", "", text)
    text = re.sub(r"[\u02C6\u0306\u031B]", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip()


def capitalize_first_letter(cls, text: str) -> str:
    if not isinstance(text, str) or not text:
        return text or ""

    return str(text[0].upper() + text[1:]).strip()
