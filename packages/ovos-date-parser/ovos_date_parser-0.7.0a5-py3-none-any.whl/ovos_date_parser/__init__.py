import json
import os
import re
from collections import namedtuple
from datetime import datetime, timedelta, time
from typing import Optional, Tuple, Union

import dateparser # fallback parser
from dateparser.search import search_dates
from ovos_config import Configuration
from ovos_utils.log import LOG
from ovos_utils.time import now_local

from ovos_date_parser.common import nice_duration_generic, nice_relative_time_generic
from ovos_date_parser.dates_az import (
    extract_datetime_az, extract_duration_az, nice_duration_az, nice_time_az,
)
from ovos_date_parser.dates_ca import (
    TimeVariantCA, extract_datetime_ca, nice_time_ca, extract_duration_ca
)
from ovos_date_parser.dates_cs import (
    extract_duration_cs, extract_datetime_cs, nice_time_cs
)
from ovos_date_parser.dates_da import (
    extract_datetime_da, extract_duration_da, nice_time_da,
)
from ovos_date_parser.dates_de import (
    extract_datetime_de, extract_duration_de, nice_time_de,
)
from ovos_date_parser.dates_en import (
    extract_datetime_en, extract_duration_en, nice_time_en
)
from ovos_date_parser.dates_es import (
    extract_datetime_es, extract_duration_es, nice_time_es, nice_date_time_es, nice_date_es,
    nice_weekday_es, nice_day_es, nice_year_es, nice_month_es
)
from ovos_date_parser.dates_eu import (
    extract_datetime_eu, nice_time_eu, nice_relative_time_eu,
)
from ovos_date_parser.dates_fa import (
    extract_datetime_fa, nice_time_fa, extract_duration_fa,
)
from ovos_date_parser.dates_fr import (
    extract_datetime_fr, nice_time_fr
)
from ovos_date_parser.dates_gl import (
    extract_duration_gl, nice_year_gl, nice_weekday_gl, nice_month_gl,
    nice_day_gl, nice_date_time_gl, nice_date_gl, nice_time_gl
)
from ovos_date_parser.dates_hu import nice_time_hu
from ovos_date_parser.dates_it import (
    extract_datetime_it, nice_time_it
)
from ovos_date_parser.dates_nl import (
    extract_datetime_nl, nice_part_of_day_nl, extract_duration_nl, nice_time_nl
)
from ovos_date_parser.dates_pl import (
    extract_datetime_pl, extract_duration_pl, nice_time_pl, nice_duration_pl
)
from ovos_date_parser.dates_pt import (
    extract_datetime_pt, extract_duration_pt, nice_time_pt, nice_date_pt, nice_year_pt, nice_date_time_pt,
    nice_month_pt, nice_weekday_pt, nice_day_pt
)
from ovos_date_parser.dates_ru import (
    extract_datetime_ru, extract_duration_ru, nice_time_ru, nice_duration_ru
)
from ovos_date_parser.dates_sl import (
    nice_time_sl
)
from ovos_date_parser.dates_sv import (
    extract_datetime_sv, extract_duration_sv, nice_time_sv
)
from ovos_date_parser.dates_uk import (
    extract_datetime_uk, extract_duration_uk, nice_time_uk, nice_duration_uk
)


def nice_time(
        dt: datetime,
        lang: str,
        speech: bool = True,
        use_24hour: bool = False,
        use_ampm: bool = False,
        variant: Optional[TimeVariantCA] = None,
) -> str:
    """
    Format a time to a comfortable human format.

    Args:
        dt: date to format (assumes already in local timezone).
        lang: A BCP-47 language code.
        speech: Format for speech (default is True) or display (False).
        use_24hour: Output in 24-hour/military or 12-hour format.
        use_ampm: Include the am/pm for 12-hour format.
        variant: Optional variant for Catalan (ca).

    Returns:
        The formatted time string.
    """
    if lang.startswith("az"):
        return nice_time_az(dt, speech, use_24hour, use_ampm)
    if lang.startswith("gl"):
        return nice_time_gl(dt, speech, use_24hour, use_ampm)
    if lang.startswith("ca"):
        return nice_time_ca(dt, speech, use_24hour, use_ampm, variant=variant)
    if lang.startswith("cs"):
        return nice_time_cs(dt, speech, use_24hour, use_ampm)
    if lang.startswith("da"):
        return nice_time_da(dt, speech, use_24hour, use_ampm)
    if lang.startswith("de"):
        return nice_time_de(dt, speech, use_24hour, use_ampm)
    if lang.startswith("en"):
        return nice_time_en(dt, speech, use_24hour, use_ampm)
    if lang.startswith("es"):
        return nice_time_es(dt, speech, use_24hour, use_ampm)
    if lang.startswith("eu"):
        return nice_time_eu(dt, speech, use_24hour, use_ampm)
    if lang.startswith("fa"):
        return nice_time_fa(dt, speech, use_24hour, use_ampm)
    if lang.startswith("fr"):
        return nice_time_fr(dt, speech, use_24hour, use_ampm)
    if lang.startswith("hu"):
        return nice_time_hu(dt, speech, use_24hour, use_ampm)
    if lang.startswith("it"):
        return nice_time_it(dt, speech, use_24hour, use_ampm)
    if lang.startswith("nl"):
        return nice_time_nl(dt, speech, use_24hour, use_ampm)
    if lang.startswith("pl"):
        return nice_time_pl(dt, speech, use_24hour, use_ampm)
    if lang.startswith("pt"):
        return nice_time_pt(dt, speech, use_24hour, use_ampm)
    if lang.startswith("ru"):
        return nice_time_ru(dt, speech, use_24hour, use_ampm)
    if lang.startswith("sv"):
        return nice_time_sv(dt, speech, use_24hour, use_ampm)
    if lang.startswith("sl"):
        return nice_time_sl(dt, speech, use_24hour, use_ampm)
    if lang.startswith("uk"):
        return nice_time_uk(dt, speech, use_24hour, use_ampm)
    raise NotImplementedError(f"Unsupported language: {lang}")


def nice_relative_time(when, relative_to, lang):
    """Create a relative phrase to roughly describe a datetime

    Examples are "25 seconds", "tomorrow", "7 days".

    Args:
        when (datetime): Local timezone
        relative_to (datetime): Baseline for relative time, default is now()
        lang (str, optional): Defaults to "en-us".
    Returns:
        str: Relative description of the given time
    """
    if lang.startswith("eu"):
        return nice_relative_time_eu(when, relative_to)
    return nice_relative_time_generic(lang, when, relative_to)


def nice_duration(
        duration: Union[int, float], lang: str, speech: bool = True
) -> str:
    """
    Convert duration in seconds to a nice spoken timespan.

    Args:
        duration: Time in seconds.
        lang: A BCP-47 language code.
        speech: Format for speech (True) or display (False).

    Returns:
        Timespan as a string.
    """
    if lang.startswith("az"):
        return nice_duration_az(duration, speech)
    if lang.startswith("pl"):
        return nice_duration_pl(duration, speech)
    if lang.startswith("ru"):
        return nice_duration_ru(duration, speech)
    if lang.startswith("uk"):
        return nice_duration_uk(duration, speech)
    return nice_duration_generic(lang, duration, speech)


def extract_duration(
        text: str, lang: str
) -> Tuple[Optional[timedelta], str]:
    """
    Convert a phrase into a number of seconds and return the remainder text.

    Args:
        text: String containing a duration.
        lang: A BCP-47 language code.

    Returns:
        A tuple containing the duration as timedelta and the remaining text.
    """
    if lang.startswith("az"):
        return extract_duration_az(text)
    if lang.startswith("ca"):
        return extract_duration_ca(text)
    if lang.startswith("cs"):
        return extract_duration_cs(text)
    if lang.startswith("da"):
        return extract_duration_da(text)
    if lang.startswith("de"):
        return extract_duration_de(text)
    if lang.startswith("en"):
        return extract_duration_en(text)
    if lang.startswith("es"):
        return extract_duration_es(text)
    if lang.startswith("gl"):
        return extract_duration_gl(text)
    if lang.startswith("fa"):
        return extract_duration_fa(text)
    if lang.startswith("nl"):
        return extract_duration_nl(text)
    if lang.startswith("pl"):
        return extract_duration_pl(text)
    if lang.startswith("pt"):
        return extract_duration_pt(text)
    if lang.startswith("ru"):
        return extract_duration_ru(text)
    if lang.startswith("sv"):
        return extract_duration_sv(text)
    if lang.startswith("uk"):
        return extract_duration_uk(text)
    raise NotImplementedError(f"Unsupported language: {lang}")


def extract_datetime(
        text: str,
        lang: str,
        anchorDate: Optional[datetime] = None,
        default_time: Optional[time] = None,
) -> Optional[Tuple[datetime, str]]:
    """
    Extract date and time information from a sentence.

    Args:
        text: The text to be interpreted.
        lang: The BCP-47 code for the language to use.
        anchorDate: Date to use for relative dating.
        default_time: Time to use if none was found in the input string.

    Returns:
        A tuple with the extracted date as datetime and the leftover string,
        or None if no date or time related text is found.
    """
    if lang.startswith("az"):
        return extract_datetime_az(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("ca"):
        return extract_datetime_ca(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("cs"):
        return extract_datetime_cs(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("da"):
        return extract_datetime_da(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("de"):
        return extract_datetime_de(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("en"):
        return extract_datetime_en(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("es"):
        return extract_datetime_es(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("fa"):
        return extract_datetime_fa(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("fr"):
        return extract_datetime_fr(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("it"):
        return extract_datetime_it(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("nl"):
        return extract_datetime_nl(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("pl"):
        return extract_datetime_pl(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("pt"):
        return extract_datetime_pt(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("ru"):
        return extract_datetime_ru(text, anchor_date=anchorDate, default_time=default_time)
    if lang.startswith("sv"):
        return extract_datetime_sv(text, anchorDate=anchorDate, default_time=default_time)
    if lang.startswith("uk"):
        return extract_datetime_uk(text, anchor_date=anchorDate, default_time=default_time)

    # fallback parser
    LOG.warning(f"{lang} is not implemented! attempting to use fallback date parser")

    tzstr = Configuration()["location"]["timezone"]["code"]
    fmt = Configuration().get("date_format", 'DMY')
    settings = {'RELATIVE_BASE': anchorDate or now_local(),
                'TIMEZONE': tzstr,
                'RETURN_AS_TIMEZONE_AWARE': True,
                'TO_TIMEZONE': tzstr,
                'DATE_ORDER': fmt}

    try:  # assume full text is a date with no leftover
        date = dateparser.parse(text,
                                languages=[lang.split("-")[0]],
                                settings=settings)
        if date:
            return date, ""
    except Exception as e:
        pass

    # less accurate substring search
    try:
        dates = search_dates(text,
                             languages=[lang.split("-")[0]],
                             settings=settings)
        if dates:
            date_txt, date = dates[0]
            return date, text.replace(date_txt, "")
    except:
        pass

    raise NotImplementedError(f"Unsupported language: {lang}")


NUMBER_TUPLE = namedtuple(
    'number',
    ('x, xx, x0, x_in_x0, xxx, x00, x_in_x00, xx00, xx_in_xx00, x000, ' +
     'x_in_x000, x0_in_x000, x_in_0x00'))


class DateTimeFormat:
    """resource file based regex date formatter
    NOTE: this is optional, can be implemented as code if desired"""

    def __init__(self, config_path):
        self.lang_config = {}
        self.config_path = config_path

    def cache(self, lang):
        lang = lang.split("-")[0]
        # TODO - find closest lang code
        if lang not in self.lang_config:
            path = self.config_path + '/' + lang + '/date_time.json'
            if not os.path.isfile(path):
                LOG.warning(f"could not find '{path}'")
                return
            with open(self.config_path + '/' + lang + '/date_time.json',
                      'r', encoding='utf8') as lang_config_file:
                self.lang_config[lang] = json.loads(
                    lang_config_file.read())

            for x in ['decade_format', 'hundreds_format', 'thousand_format',
                      'year_format']:
                i = 1
                while self.lang_config[lang][x].get(str(i)):
                    self.lang_config[lang][x][str(i)]['re'] = (
                        re.compile(self.lang_config[lang][x][str(i)]['match']
                                   ))
                    i = i + 1

    def _number_strings(self, number, lang):
        lang = lang.split("-")[0]
        x = (self.lang_config[lang]['number'].get(str(number % 10)) or
             str(number % 10))
        xx = (self.lang_config[lang]['number'].get(str(number % 100)) or
              str(number % 100))
        x_in_x0 = self.lang_config[lang]['number'].get(
            str(int(number % 100 / 10))) or str(int(number % 100 / 10))
        x0 = (self.lang_config[lang]['number'].get(
            str(int(number % 100 / 10) * 10)) or
              str(int(number % 100 / 10) * 10))
        xxx = (self.lang_config[lang]['number'].get(str(number % 1000)) or
               str(number % 1000))
        x00 = (self.lang_config[lang]['number'].get(str(int(
            number % 1000 / 100) * 100)) or
               str(int(number % 1000 / 100) * 100))
        x_in_x00 = self.lang_config[lang]['number'].get(str(int(
            number % 1000 / 100))) or str(int(number % 1000 / 100))
        xx00 = self.lang_config[lang]['number'].get(str(int(
            number % 10000 / 100) * 100)) or str(int(number % 10000 / 100) *
                                                 100)
        xx_in_xx00 = self.lang_config[lang]['number'].get(str(int(
            number % 10000 / 100))) or str(int(number % 10000 / 100))
        x000 = (self.lang_config[lang]['number'].get(str(int(
            number % 10000 / 1000) * 1000)) or
                str(int(number % 10000 / 1000) * 1000))
        x_in_x000 = self.lang_config[lang]['number'].get(str(int(
            number % 10000 / 1000))) or str(int(number % 10000 / 1000))
        x0_in_x000 = self.lang_config[lang]['number'].get(str(int(
            number % 10000 / 1000) * 10)) or str(int(number % 10000 / 1000) * 10)
        x_in_0x00 = self.lang_config[lang]['number'].get(str(int(
            number % 1000 / 100)) or str(int(number % 1000 / 100)))

        return NUMBER_TUPLE(
            x, xx, x0, x_in_x0, xxx, x00, x_in_x00, xx00, xx_in_xx00, x000,
            x_in_x000, x0_in_x000, x_in_0x00)

    def _format_string(self, number, format_section, lang):
        lang = lang.split("-")[0]
        s = self.lang_config[lang][format_section]['default']
        i = 1
        while self.lang_config[lang][format_section].get(str(i)):
            e = self.lang_config[lang][format_section][str(i)]
            if e['re'].match(str(number)):
                return e['format']
            i = i + 1
        return s

    def _decade_format(self, number, number_tuple, lang):
        s = self._format_string(number % 100, 'decade_format', lang)
        return s.format(x=number_tuple.x, xx=number_tuple.xx,
                        x0=number_tuple.x0, x_in_x0=number_tuple.x_in_x0,
                        number=str(number % 100))

    def _number_format_hundreds(self, number, number_tuple, lang,
                                formatted_decade):
        s = self._format_string(number % 1000, 'hundreds_format', lang)
        return s.format(xxx=number_tuple.xxx, x00=number_tuple.x00,
                        x_in_x00=number_tuple.x_in_x00,
                        formatted_decade=formatted_decade,
                        number=str(number % 1000))

    def _number_format_thousand(self, number, number_tuple, lang,
                                formatted_decade, formatted_hundreds):
        """
        Format the thousands part of a year using language-specific templates.

        Parameters:
            number (int): The year value to format.
            number_tuple: A named tuple containing precomputed string representations of number components.
            lang (str): Language code for localization.
            formatted_decade (str): Preformatted decade string.
            formatted_hundreds (str): Preformatted hundreds string.

        Returns:
            str: The formatted thousands part of the year as a localized string.
        """
        s = self._format_string(number % 10000, 'thousand_format', lang)
        return s.format(x_in_x00=number_tuple.x_in_x00,
                        xx00=number_tuple.xx00,
                        xx_in_xx00=number_tuple.xx_in_xx00,
                        x000=number_tuple.x000,
                        x_in_x000=number_tuple.x_in_x000,
                        x0_in_x000=number_tuple.x0_in_x000,
                        x_in_0x00=number_tuple.x_in_0x00,
                        formatted_decade=formatted_decade,
                        formatted_hundreds=formatted_hundreds,
                        number=str(number % 10000))

    def date_format(self, dt, lang, now, include_weekday=True):
        """
        Format a datetime object as a localized date string according to language-specific templates.
        
        Parameters:
            dt (datetime): The date to format.
            lang (str): Language code for localization.
            now (datetime): Reference date for relative formatting (e.g., today, tomorrow).
            include_weekday (bool): If True, includes the weekday name in the output.
        
        Returns:
            str: The formatted date string, localized and optionally including the weekday.
        """
        format_str = 'date_full'
        lang = lang.split("-")[0]
        if now:
            if dt.year == now.year:
                format_str = 'date_full_no_year'
                if dt.month == now.month and dt.day > now.day:
                    format_str = 'date_full_no_year_month'

            tomorrow = now + timedelta(days=1)
            yesterday = now - timedelta(days=1)
            if tomorrow.date() == dt.date():
                format_str = 'tomorrow'
            elif now.date() == dt.date():
                format_str = 'today'
            elif yesterday.date() == dt.date():
                format_str = 'yesterday'

        unformatted = self.lang_config[lang]['date_format'][format_str]
        args = dict(
                month=self.lang_config[lang]['month'][str(dt.month)],
                day=self.lang_config[lang]['date'][str(dt.day)],
                formatted_year=self.year_format(dt, lang, False)
        )
        if include_weekday:
            args["weekday"] = self.lang_config[lang]['weekday'][str(dt.weekday())]
        else:
            unformatted = re.sub(r"{weekday}\s*,?\s*", "", unformatted).strip(", ")
        return unformatted.format(**args)

    def date_time_format(self, dt, lang, now, use_24hour, use_ampm):
        lang = lang.split("-")[0]
        date_str = self.date_format(dt, lang, now)
        time_str = nice_time(dt, lang, use_24hour=use_24hour,
                             use_ampm=use_ampm)
        return self.lang_config[lang]['date_time_format']['date_time'].format(
            formatted_date=date_str, formatted_time=time_str)

    def year_format(self, dt, lang, bc):
        lang = lang.split("-")[0]
        number_tuple = self._number_strings(dt.year, lang)
        formatted_bc = (
            self.lang_config[lang]['year_format']['bc'] if bc else '')
        formatted_decade = self._decade_format(
            dt.year, number_tuple, lang)
        formatted_hundreds = self._number_format_hundreds(
            dt.year, number_tuple, lang, formatted_decade)
        formatted_thousand = self._number_format_thousand(
            dt.year, number_tuple, lang, formatted_decade, formatted_hundreds)

        s = self._format_string(dt.year, 'year_format', lang)
        return re.sub(' +', ' ',
                      s.format(
                          year=str(dt.year),
                          century=str(int(dt.year / 100)),
                          decade=str(dt.year % 100),
                          formatted_hundreds=formatted_hundreds,
                          formatted_decade=formatted_decade,
                          formatted_thousand=formatted_thousand,
                          bc=formatted_bc)).strip()


date_time_format = DateTimeFormat(os.path.join(os.path.dirname(__file__), 'res'))


def nice_date(dt, lang, now=None, include_weekday=True):
    """
    Format a datetime to a pronounceable date

    For example, generates 'tuesday, june the fifth, 2018'

    Args:
        dt (datetime): date to format (assumes already in local timezone)
        lang (str, optional): an optional BCP-47 language code, if omitted
                              the default language will be used.
        now (datetime): Current date. If provided, the returned date for speech
            will be shortened accordingly: No year is returned if now is in the
            same year as td, no month is returned if now is in the same month
            as td. If now and td is the same day, 'today' is returned.
        include_weekday (bool, optional): Whether to include the weekday name in the output. Defaults to True.

    Returns:
        (str): The formatted date string
    """
    lang = lang.lower().split("-")[0]
    if lang.startswith("pt"):
        return nice_date_pt(dt, now, include_weekday)
    if lang.startswith("es"):
        return nice_date_es(dt, now, include_weekday)
    if lang.startswith("gl"):
        return nice_date_gl(dt, now, include_weekday)
    date_time_format.cache(lang)
    return date_time_format.date_format(dt, lang, now, include_weekday)


def nice_date_time(dt, lang, now=None, use_24hour=False,
                   use_ampm=False):
    """
        Format a datetime to a pronounceable date and time

        For example, generate 'tuesday, june the fifth, 2018 at five thirty'

        Args:
            dt (datetime): date to format (assumes already in local timezone)
            lang (str, optional): an optional BCP-47 language code, if omitted
                                  the default language will be used.
            now (datetime): Current date. If provided, the returned date for
                speech will be shortened accordingly: No year is returned if
                now is in the same year as td, no month is returned if now is
                in the same month as td. If now and td is the same day, 'today'
                is returned.
            use_24hour (bool): output in 24-hour/military or 12-hour format
            use_ampm (bool): include the am/pm for 12-hour format
        Returns:
            (str): The formatted date time string
    """
    lang = lang.lower().split("-")[0]
    if lang.startswith("pt"):
        return nice_date_time_pt(dt, now, use_24hour, use_ampm)
    if lang.startswith("es"):
        return nice_date_time_es(dt, now, use_24hour, use_ampm)
    if lang.startswith("gl"):
        return nice_date_time_gl(dt, now, use_24hour, use_ampm)
    date_time_format.cache(lang)
    return date_time_format.date_time_format(dt, lang, now, use_24hour, use_ampm)


def nice_day(dt, lang, date_format='DMY', include_month=True):
    if lang.startswith("pt"):
        return nice_day_pt(dt, date_format, include_month)
    if lang.startswith("es"):
        return nice_day_es(dt, date_format, include_month)
    if lang.startswith("gl"):
        return nice_day_gl(dt, date_format, include_month)
    if include_month:
        month = nice_month(dt, lang, date_format)
        if date_format == 'MDY':
            return "{} {}".format(month, dt.strftime("%d"))
        else:
            return "{} {}".format(dt.strftime("%d"), month)
    return dt.strftime("%d")


def nice_weekday(dt, lang):
    lang = lang.lower().split("-")[0]
    if lang.startswith("pt"):
        return nice_weekday_pt(dt)
    if lang.startswith("es"):
        return nice_weekday_es(dt)
    if lang.startswith("gl"):
        return nice_weekday_gl(dt)
    date_time_format.cache(lang)

    if lang in date_time_format.lang_config.keys():
        localized_day_names = list(
            date_time_format.lang_config[lang]['weekday'].values())
        weekday = localized_day_names[dt.weekday()]
    else:
        weekday = dt.strftime("%A")
    return weekday.capitalize()


def nice_month(dt, lang, date_format='MDY'):
    lang = lang.lower().split("-")[0]
    if lang.startswith("pt"):
        return nice_month_pt(dt)
    if lang.startswith("es"):
        return nice_month_es(dt)
    if lang.startswith("gl"):
        return nice_month_gl(dt)
    date_time_format.cache(lang)
    if lang in date_time_format.lang_config.keys():
        localized_month_names = date_time_format.lang_config[lang]['month']
        month = localized_month_names[str(int(dt.strftime("%m")))]
    else:
        month = dt.strftime("%B")
    return month.capitalize()


def nice_year(dt, lang, bc=False):
    """
        Format a datetime to a pronounceable year

        For example, generate 'nineteen-hundred and eighty-four' for year 1984

        Args:
            dt (datetime): date to format (assumes already in local timezone)
            lang (str, optional): an optional BCP-47 language code, if omitted
                                  the default language will be used.
            bc (bool) pust B.C. after the year (python does not support dates
                B.C. in datetime)
        Returns:
            (str): The formatted year string
    """
    lang = lang.lower().split("-")[0]
    if lang.startswith("pt"):
        return nice_year_pt(dt, bc)
    if lang.startswith("es"):
        return nice_year_es(dt, bc)
    if lang.startswith("gl"):
        return nice_year_gl(dt, bc)
    date_time_format.cache(lang)
    return date_time_format.year_format(dt, lang, bc)


def get_date_strings(dt, lang, date_format='DMY', time_format="full"):
    lang = lang.lower().split("-")[0]
    timestr = nice_time(dt, lang, speech=False,
                        use_24hour=time_format == "full")
    monthstr = nice_month(dt, lang, date_format)
    weekdaystr = nice_weekday(dt, lang)
    yearstr = dt.strftime("%Y")
    daystr = nice_day(dt, date_format=date_format, include_month=False, lang=lang)
    if date_format == 'MDY':
        dtstr = dt.strftime("%-m/%-d/%Y")
    elif date_format == 'DMY':
        dtstr = dt.strftime("%d/%-m/%-Y")
    elif date_format == 'YMD':
        dtstr = dt.strftime("%Y/%-m/%-d")
    else:
        raise ValueError("invalid date_format")
    return {
        "date_string": dtstr,
        "time_string": timestr,
        "month_string": monthstr,
        "day_string": daystr,
        'year_string': yearstr,
        "weekday_string": weekdaystr
    }
