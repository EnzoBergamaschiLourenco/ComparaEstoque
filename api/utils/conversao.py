"""Utilitários de conversão e formatação"""


def string_to_float(value) -> float:
    """Converte strings com vírgula (ex: '1,50') para float."""
    try:
        return float(str(value).replace(',', '.'))
    except (ValueError, AttributeError):
        return 0.0


def safe_float(val) -> float:
    """Converte valor para float com segurança"""
    if val is None or str(val).strip() == '':
        return 0.0
    try:
        return float(str(val).replace(',', '.'))
    except:
        return 0.0
