import re
from datetime import datetime
from datetime import timedelta

from ovos_number_parser.numbers_gl import pronounce_number_gl
from ovos_utils.time import now_local

WEEKDAYS_GL = {
    0: "luns",
    1: "martes",
    2: "mércores",
    3: "xoves",
    4: "venres",
    5: "sábado",
    6: "domingo"
}
MONTHS_GL = {
    1: "xaneiro",
    2: "febreiro",
    3: "marzo",
    4: "abril",
    5: "maio",
    6: "xuño",
    7: "xullo",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "decembro"
}


def nice_year_gl(dt, bc=False):
    """
        Formatea un ano nunha forma pronunciable.

        Por exemplo, xera 'mil novecentos oitenta e catro' para o ano 1984.

        Args:
            dt (datetime): data a formatar (asúmise que xa está na zona horaria local)
            bc (bool): engade a.C. despois do ano (Python non soporta datas a.C. en datetime)
        Returns:
            (str): O ano formatado como cadea
    """
    year = pronounce_number_gl(dt.year)
    if bc:
        return f"{year} a.C."
    return year


def nice_weekday_gl(dt):
    weekday = WEEKDAYS_GL[dt.weekday()]
    return weekday.capitalize()


def nice_month_gl(dt):
    month = MONTHS_GL[dt.month]
    return month.capitalize()


def nice_day_gl(dt, date_format='DMY', include_month=True):
    if include_month:
        month = nice_month_gl(dt)
        if date_format == 'MDY':
            return "{} {}".format(month, dt.strftime("%d").lstrip("0"))
        else:
            return "{} {}".format(dt.strftime("%d").lstrip("0"), month)
    return dt.strftime("%d").lstrip("0")


def nice_date_time_gl(dt, now=None, use_24hour=False, use_ampm=False):
    """
        Formatea unha data e hora de maneira pronunciable.

        Por exemplo, xera 'martes, cinco de xuño de 2018 ás cinco e media'.

        Args:
            dt (datetime): data a formatar (asúmise que xa está na zona horaria local)
            now (datetime): Data actual. Se se proporciona, a data devolta acurtarase en consecuencia:
                Non se devolve o ano se now está no mesmo ano que `dt`, non se devolve o mes
                se now está no mesmo mes que `dt`. Se `now` e `dt` son o mesmo día, devélvese 'hoxe'.
            use_24hour (bool): saída en formato de 24 horas/militar ou 12 horas
            use_ampm (bool): incluír o am/pm en formato de 12 horas
        Returns:
            (str): A cadea de data e hora formatada
    """
    now = now or now_local()
    return f"{nice_date_gl(dt, now)} ás {nice_time_gl(dt, use_24hour=use_24hour, use_ampm=use_ampm)}"


def nice_date_gl(dt: datetime, now: datetime = None, include_weekday=True):
    """
    Formatea unha data nunha forma pronunciable.

    Por exemplo, xera 'martes, cinco de xuño de 2018'.

    Args:
        dt (datetime): data a formatar (asúmise que xa está na zona horaria local)
        now (datetime): Data actual. Se se proporciona, a data devolta acurtarase en consecuencia:
            Non se devolve o ano se now está no mesmo ano que `dt`, non se devolve o mes
            se now está no mesmo mes que `dt`. Se `now` e `dt` son o mesmo día, devélvese 'hoxe'.
        include_weekday (bool, optional): Whether to prepend the weekday name to the formatted date. Defaults to True.

    Returns:
        (str): A cadea de data formatada
    """
    day = pronounce_number_gl(dt.day)
    if now is not None:
        nice = day
        if dt.day == now.day:
            return "hoxe"
        if dt.day == now.day + 1:
            return "mañá"
        if dt.day == now.day - 1:
            return "onte"
        if dt.month != now.month:
            nice = nice + " de " + nice_month_gl(dt)
        if dt.year != now.year:
            nice = nice + ", " + nice_year_gl(dt)
    else:
        nice = f"{day} de {nice_month_gl(dt)}, {nice_year_gl(dt)}"

    if include_weekday:
        weekday = nice_weekday_gl(dt)
        nice = f"{weekday}, {nice}"
    return nice


def nice_time_gl(dt, speech=True, use_24hour=False, use_ampm=False):
    """
    Formatea unha hora nun formato humano comprensible

    Por exemplo, xera 'cinco e media' para fala ou '5:30' para visualización en texto.

    Args:
        dt (datetime): data a formatar (asume que xa está na zona horaria local)
        speech (bool): formato para fala (True, por defecto) ou para visualización en texto (False)
        use_24hour (bool): saída en formato de 24 horas/militar ou en formato de 12 horas
        use_ampm (bool): incluír am/pm para o formato de 12 horas
    Returns:
        (str): A cadea de texto coa hora formatada
    """
    if use_24hour:
        # ex.: "03:01" ou "14:22"
        string = dt.strftime("%H:%M")
    else:
        if use_ampm:
            # ex.: "3:01 AM" ou "2:22 PM"
            string = dt.strftime("%I:%M %p")
        else:
            # ex.: "3:01" ou "2:22"
            string = dt.strftime("%I:%M")
        if string[0] == '0':
            string = string[1:]  # eliminar ceros á esquerda

    if not speech:
        return string

    # Xerar unha versión falada da hora
    speak = ""
    if use_24hour:
        if dt.hour == 1:
            speak += "a unha"
        else:
            speak += "as " + pronounce_number_gl(dt.hour)

        if dt.minute < 10:
            speak += " cero " + pronounce_number_gl(dt.minute)
        else:
            speak += " " + pronounce_number_gl(dt.minute)

    else:
        if dt.minute == 35:
            minute = -25
            hour = dt.hour + 1
        elif dt.minute == 40:
            minute = -20
            hour = dt.hour + 1
        elif dt.minute == 45:
            minute = -15
            hour = dt.hour + 1
        elif dt.minute == 50:
            minute = -10
            hour = dt.hour + 1
        elif dt.minute == 55:
            minute = -5
            hour = dt.hour + 1
        else:
            minute = dt.minute
            hour = dt.hour

        if hour == 0 or hour == 12:
            speak += "as doce"
        elif hour == 1 or hour == 13:
            speak += "a unha"
        elif hour < 13:
            speak = "as " + pronounce_number_gl(hour)
        else:
            speak = "as " + pronounce_number_gl(hour - 12)

        if minute != 0:
            if minute == 15:
                speak += " e cuarto"
            elif minute == 30:
                speak += " e media"
            elif minute == -15:
                speak += " menos cuarto"
            else:
                if minute > 0:
                    speak += " e " + pronounce_number_gl(minute)
                else:
                    speak += " " + pronounce_number_gl(minute)

        if minute == 0 and not use_ampm:
            speak += " en punto"

        if use_ampm:
            if hour >= 0 and hour < 6:
                speak += " da madrugada"
            elif hour >= 6 and hour < 13:
                speak += " da mañá"
            elif hour >= 13 and hour < 21:
                speak += " da tarde"
            else:
                speak += " da noite"
    return speak


def extract_duration_gl(text):
    """
    Converte unha frase en galego nun número de segundos.
    Converte cousas como:
        "10 minutos"
        "3 días 8 horas 10 minutos e 49 segundos"
    nun número enteiro que representa o total de segundos.
    As palabras empregadas na duración serán consumidas,
    devolvéndose o texto restante.
    Por exemplo, "pon un temporizador de 5 minutos" devolvería
    (300, "pon un temporizador de").

    Args:
        text (str): cadea de texto que contén unha duración

    Returns:
        (timedelta, str):
            Unha tupla co tempo total e o texto restante
            non consumido no análise. O primeiro valor será
            None se non se atopa ningunha duración. O texto devolto
            terá os espazos en branco eliminados nos extremos.
    """
    if not text:
        return None, text

    text = text.lower().replace("í", "i").replace("é", "e").replace("ñ", "n").replace("meses", "mes")

    unidades_tempo = {
        'microseconds': 'microsegundos',
        'milliseconds': 'milisegundos',
        'seconds': 'segundos',
        'minutes': 'minutos',
        'hours': 'horas',
        'days': 'dias',
        'weeks': 'semanas'
    }

    unidades_non_estandar = {
        "months": "mes",
        "years": "anos",
        'decades': "decadas",
        'centuries': "seculos",
        'millenniums': "milenios"
    }

    patron = r"(?P<value>\d+(?:\.?\d+)?)(?:\s+|\-){unit}[s]?"

    for (unit_en, unit_gl) in unidades_tempo.items():
        patron_unidade = patron.format(unit=unit_gl[:-1])  # eliminar 's' da unidade
        unidades_tempo[unit_en] = 0

        def substitucion(match):
            unidades_tempo[unit_en] += float(match.group("value"))
            return ''

        text = re.sub(patron_unidade, substitucion, text)

    for (unit_en, unit_gl) in unidades_non_estandar.items():
        patron_unidade = patron.format(unit=unit_gl[:-1])  # eliminar 's' da unidade

        def substitucion_non_estandar(match):
            val = float(match.group("value"))
            if unit_en == "months":
                val = 30 * val  # aproximación dun mes en días
            elif unit_en == "years":
                val = 365 * val  # aproximación dun ano en días
            elif unit_en == "decades":
                val = 10 * 365 * val
            elif unit_en == "centuries":
                val = 100 * 365 * val
            elif unit_en == "millenniums":
                val = 1000 * 365 * val
            unidades_tempo["days"] += val
            return ''

        text = re.sub(patron_unidade, substitucion_non_estandar, text)

    text = text.strip()
    duracion = timedelta(**unidades_tempo) if any(unidades_tempo.values()) else None

    return duracion, text
