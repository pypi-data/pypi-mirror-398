import re
from datetime import datetime, timedelta, time

from dateutil.relativedelta import relativedelta
from ovos_number_parser.numbers_en import extract_number_en, numbers_to_digits_en, pronounce_number_en
from ovos_number_parser.util import is_numeric
from ovos_utils.time import now_local, DAYS_IN_1_YEAR, DAYS_IN_1_MONTH


def nice_time_en(dt, speech=True, use_24hour=False, use_ampm=False):
    """
    Format a time to a comfortable human format
    For example, generate 'five thirty' for speech or '5:30' for
    text display.
    Args:
        dt (datetime): date to format (assumes already in local timezone)
        speech (bool): format for speech (default/True) or display (False)=Fal
        use_24hour (bool): output in 24-hour/military or 12-hour format
        use_ampm (bool): include the am/pm for 12-hour format
    Returns:
        (str): The formatted time string
    """
    if use_24hour:
        # e.g. "03:01" or "14:22"
        string = dt.strftime("%H:%M")
    else:
        if use_ampm:
            # e.g. "3:01 AM" or "2:22 PM"
            string = dt.strftime("%I:%M %p")
        else:
            # e.g. "3:01" or "2:22"
            string = dt.strftime("%I:%M")
        if string[0] == '0':
            string = string[1:]  # strip leading zeros

    if not speech:
        return string

    # Generate a speakable version of the time
    if use_24hour:
        speak = ""

        # Either "0 8 hundred" or "13 hundred"
        if string[0] == '0':
            speak += pronounce_number_en(int(string[0])) + " "
            speak += pronounce_number_en(int(string[1]))
        else:
            speak = pronounce_number_en(int(string[0:2]))

        speak += " "
        if string[3:5] == '00':
            speak += "hundred"
        else:
            if string[3] == '0':
                speak += pronounce_number_en(0) + " "
                speak += pronounce_number_en(int(string[4]))
            else:
                speak += pronounce_number_en(int(string[3:5]))
        return speak
    else:
        if dt.hour == 0 and dt.minute == 0:
            return "midnight"
        elif dt.hour == 12 and dt.minute == 0:
            return "noon"

        hour = dt.hour % 12 or 12  # 12 hour clock and 0 is spoken as 12
        if dt.minute == 15:
            speak = "quarter past " + pronounce_number_en(hour)
        elif dt.minute == 30:
            speak = "half past " + pronounce_number_en(hour)
        elif dt.minute == 45:
            next_hour = (dt.hour + 1) % 12 or 12
            speak = "quarter to " + pronounce_number_en(next_hour)
        else:
            speak = pronounce_number_en(hour)

            if dt.minute == 0:
                if not use_ampm:
                    return speak + " o'clock"
            else:
                if dt.minute < 10:
                    speak += " oh"
                speak += " " + pronounce_number_en(dt.minute)

        if use_ampm:
            if dt.hour > 11:
                speak += " p.m."
            else:
                speak += " a.m."

        return speak


def extract_duration_en(text):
    """
    Convert an english phrase into a number of seconds

    Convert things like:
        "10 minute"
        "2 and a half hours"
        "3 days 8 hours 10 minutes and 49 seconds"
    into an int, representing the total number of seconds.

    The words used in the duration will be consumed, and
    the remainder returned.

    As an example, "set a timer for 5 minutes" would return
    (300, "set a timer for").

    Args:
        text (str): string containing a duration

    Returns:
        (timedelta, str):
                    A tuple containing the duration and the remaining text
                    not consumed in the parsing. The first value will
                    be None if no duration is found. The text returned
                    will have whitespace stripped from the ends.
    """
    if not text:
        return None

    time_units = {
        'microseconds': 0,
        'milliseconds': 0,
        'seconds': 0,
        'minutes': 0,
        'hours': 0,
        'days': 0,
        'weeks': 0
    }
    # NOTE: these are spelled wrong on purpose because of the loop below that strips the s
    units = ['months', 'years', 'decades', 'centurys', 'millenniums'] + \
            list(time_units.keys())

    pattern = r"(?P<value>\d+(?:\.?\d+)?)(?:\s+|\-){unit}s?"
    text = numbers_to_digits_en(text)
    text = text.replace("centuries", "century").replace("millenia", "millennium")
    for word in ('day', 'month', 'year', 'decade', 'century', 'millennium'):
        text = text.replace(f'a {word}', f'1 {word}')

    for unit_en in units:
        unit_pattern = pattern.format(unit=unit_en[:-1])  # remove 's' from unit

        def repl(match):
            time_units[unit_en] += float(match.group(1))
            return ''

        def repl_non_std(match):
            val = float(match.group(1))
            if unit_en == "months":
                val = DAYS_IN_1_MONTH * val
            if unit_en == "years":
                val = DAYS_IN_1_YEAR * val
            if unit_en == "decades":
                val = 10 * DAYS_IN_1_YEAR * val
            if unit_en == "centurys":
                val = 100 * DAYS_IN_1_YEAR * val
            if unit_en == "millenniums":
                val = 1000 * DAYS_IN_1_YEAR * val
            time_units["days"] += val
            return ''

        if unit_en not in time_units:
            text = re.sub(unit_pattern, repl_non_std, text)
        else:
            text = re.sub(unit_pattern, repl, text)

    text = text.strip()
    duration = timedelta(**time_units) if any(time_units.values()) else None

    return (duration, text)


def extract_datetime_en(text, anchorDate=None, default_time=None):
    """ Convert a human date reference into an exact datetime

    Convert things like
        "today"
        "tomorrow afternoon"
        "next Tuesday at 4pm"
        "August 3rd"
    into a datetime.  If a reference date is not provided, the current
    local time is used.  Also consumes the words used to define the date
    returning the remaining string.  For example, the string
       "what is Tuesday's weather forecast"
    returns the date for the forthcoming Tuesday relative to the reference
    date and the remainder string
       "what is weather forecast".

    The "next" instance of a day or weekend is considered to be no earlier than
    48 hours in the future. On Friday, "next Monday" would be in 3 days.
    On Saturday, "next Monday" would be in 9 days.

    Args:
        text (str): string containing date words
        anchorDate (datetime): A reference date/time for "tommorrow", etc
        default_time (time): Time to set if no time was found in the string

    Returns:
        [datetime, str]: An array containing the datetime and the remaining
                         text not consumed in the parsing, or None if no
                         date or time related text was found.
    """

    def clean_string(s):
        # normalize and lowercase utt  (replaces words with numbers)
        s = numbers_to_digits_en(s, ordinals=None)
        # clean unneeded punctuation and capitalization among other things.
        s = s.lower().replace('?', '').replace(',', '') \
            .replace(' the ', ' ').replace(' a ', ' ').replace(' an ', ' ') \
            .replace("o' clock", "o'clock").replace("o clock", "o'clock") \
            .replace("o ' clock", "o'clock").replace("o 'clock", "o'clock") \
            .replace("oclock", "o'clock").replace("couple", "2") \
            .replace("centuries", "century").replace("decades", "decade") \
            .replace("millenniums", "millennium")

        wordList = s.split()
        for idx, word in enumerate(wordList):
            word = word.replace("'s", "")

            ordinals = ["rd", "st", "nd", "th"]
            if word[0].isdigit():
                for ordinal in ordinals:
                    # "second" is the only case we should not do this
                    if ordinal in word and "second" not in word:
                        word = word.replace(ordinal, "")
            wordList[idx] = word

        return wordList

    def date_found():
        return found or \
            (
                    datestr != "" or
                    yearOffset != 0 or monthOffset != 0 or
                    dayOffset is True or hrOffset != 0 or
                    hrAbs or minOffset != 0 or
                    minAbs or secOffset != 0
            )

    if not anchorDate:
        anchorDate = now_local()

    if text == "":
        return None
    default_time = default_time or time(0, 0, 0)
    found = False
    daySpecified = False
    dayOffset = False
    monthOffset = 0
    yearOffset = 0
    today = anchorDate.strftime("%w")
    wkday = anchorDate.weekday()  # 0 - monday
    currentYear = anchorDate.strftime("%Y")
    fromFlag = False
    datestr = ""
    hasYear = False
    timeQualifier = ""

    timeQualifiersAM = ['morning']
    timeQualifiersPM = ['afternoon', 'evening', 'night', 'tonight']
    timeQualifiersList = set(timeQualifiersAM + timeQualifiersPM)
    year_markers = ['in', 'on', 'of']
    past_markers = ["last", "past"]
    earlier_markers = ["ago", "earlier"]
    later_markers = ["after", "later"]
    future_markers = ["in", "within"]  # in a month -> + 1 month timedelta
    future_1st_markers = ["next"]  # next month -> day 1 of next month
    markers = year_markers + ['at', 'by', 'this', 'around', 'for', "within"]
    days = ['monday', 'tuesday', 'wednesday',
            'thursday', 'friday', 'saturday', 'sunday']
    months = ['january', 'february', 'march', 'april', 'may', 'june',
              'july', 'august', 'september', 'october', 'november',
              'december']
    recur_markers = days + [d + 's' for d in days] + ['weekend', 'weekday',
                                                      'weekends', 'weekdays']
    monthsShort = ['jan', 'feb', 'mar', 'apr', 'may', 'june', 'july', 'aug',
                   'sept', 'oct', 'nov', 'dec']
    year_multiples = ["decade", "century", "millennium"]
    day_multiples = ["weeks", "months", "years"]
    past_markers = ["was", "last", "past"]

    words = clean_string(text)

    for idx, word in enumerate(words):
        if word == "":
            continue
        wordPrevPrev = words[idx - 2] if idx > 1 else ""
        wordPrev = words[idx - 1] if idx > 0 else ""
        wordNext = words[idx + 1] if idx + 1 < len(words) else ""
        wordNextNext = words[idx + 2] if idx + 2 < len(words) else ""

        # this isn't in clean string because I don't want to save back to words
        word = word.rstrip('s')
        start = idx
        used = 0
        # save timequalifier for later
        if word in earlier_markers and dayOffset:
            dayOffset = - dayOffset
            used += 1
        elif word == "now" and not datestr:
            resultStr = " ".join(words[idx + 1:])
            resultStr = ' '.join(resultStr.split())
            extractedDate = anchorDate.replace(microsecond=0)
            return [extractedDate, resultStr]
        elif wordNext in year_multiples:
            multiplier = None
            if is_numeric(word):
                try:
                    multiplier = float(word)
                except:
                    multiplier = extract_number_en(word)
            multiplier = multiplier or 1
            _leftover = "0"
            if int(multiplier) != multiplier:
                multiplier, _leftover = str(multiplier).split(".")
            multiplier = int(multiplier)

            used += 2
            if wordNext == "decade":
                yearOffset = multiplier * 10 + int(_leftover[:1])
            elif wordNext == "century":
                yearOffset = multiplier * 100 + int(_leftover[:2]) * 10
            elif wordNext == "millennium":
                yearOffset = multiplier * 1000 + int(_leftover[:3]) * 100

            if wordNextNext in earlier_markers:
                yearOffset = yearOffset * -1
                used += 1
            elif word in past_markers:
                yearOffset = yearOffset * -1
            elif wordPrev in past_markers:
                yearOffset = yearOffset * -1
                start -= 1
                used += 1

        elif word in year_markers and wordNext.isdigit() and len(wordNext) == 4:
            yearOffset = int(wordNext) - int(currentYear)
            used += 2
            hasYear = True
        # couple of
        elif word == "2" and wordNext == "of" and \
                wordNextNext in year_multiples:
            multiplier = 2
            used += 3
            if wordNextNext == "decade":
                yearOffset = multiplier * 10
            elif wordNextNext == "century":
                yearOffset = multiplier * 100
            elif wordNextNext == "millennium":
                yearOffset = multiplier * 1000
        elif word == "2" and wordNext == "of" and \
                wordNextNext in day_multiples:
            multiplier = 2
            used += 3
            if wordNextNext == "years":
                yearOffset = multiplier
            elif wordNextNext == "months":
                monthOffset = multiplier
            elif wordNextNext == "weeks":
                dayOffset = multiplier * 7
        elif word in timeQualifiersList:
            timeQualifier = word
        # parse today, tomorrow, day after tomorrow
        elif word == "today" and not fromFlag:
            dayOffset = 0
            used += 1
        elif word == "tomorrow" and not fromFlag:
            dayOffset = 1
            used += 1
        elif word == "day" and wordNext == "before" and wordNextNext == "yesterday" and not fromFlag:
            dayOffset = -2
            used += 3
        elif word == "before" and wordNext == "yesterday" and not fromFlag:
            dayOffset = -2
            used += 2
        elif word == "yesterday" and not fromFlag:
            dayOffset = -1
            used += 1
        elif (word == "day" and
              wordNext == "after" and
              wordNextNext == "tomorrow" and
              not fromFlag and
              (not wordPrev or not wordPrev[0].isdigit())):
            dayOffset = 2
            used = 3
            if wordPrev == "the":
                start -= 1
                used += 1
        # parse 5 days, 10 weeks, last week, next week
        elif word == "day" and wordNext not in earlier_markers:
            if wordPrev and wordPrev[0].isdigit():
                dayOffset += int(wordPrev)
                start -= 1
                used = 2
                if wordPrevPrev in past_markers:
                    dayOffset = dayOffset * -1
                    start -= 1
                    used += 1

            # next day
            # normalize step makes "in a day" -> "in day"
            elif wordPrev and wordPrev in future_markers + future_1st_markers:
                dayOffset += 1
                start -= 1
                used = 2
            elif wordPrev in past_markers:
                dayOffset = -1
                start -= 1
                used = 2
        # parse X days ago
        elif word == "day" and wordNext in earlier_markers:
            if wordPrev and wordPrev[0].isdigit():
                dayOffset -= int(wordPrev)
                start -= 1
                used = 3
            else:
                dayOffset -= 1
                used = 2
        # parse last/past/next week and in/after X weeks
        elif word == "week" and not fromFlag and wordPrev and wordNext not in earlier_markers:
            if wordPrev[0].isdigit():
                dayOffset += int(wordPrev) * 7
                start -= 1
                used = 2
                if wordPrevPrev in past_markers:
                    dayOffset = dayOffset * -1
                    start -= 1
                    used += 1
            # next week -> next monday
            elif wordPrev in future_1st_markers:
                dayOffset = 7 - wkday
                start -= 1
                used = 2
            # normalize step makes "in a week" -> "in week"
            elif wordPrev in future_markers:
                dayOffset = 7
                start -= 1
                used = 2
            elif wordPrev in past_markers:
                dayOffset = -7
                start -= 1
                used = 2
        # parse X weeks ago
        elif word == "week" and not fromFlag and wordNext in earlier_markers:
            if wordPrev[0].isdigit():
                dayOffset -= int(wordPrev) * 7
                start -= 1
                used = 3
            else:
                dayOffset -= 7
                used = 2
        # parse last/past/next weekend and in/after X weekends
        elif word == "weekend" and not fromFlag and wordPrev and wordNext not in earlier_markers:
            # in/after X weekends
            if wordPrev[0].isdigit():
                n = int(wordPrev)
                dayOffset += 7 - wkday  # next monday -> 1 weekend
                n -= 1
                dayOffset += n * 7
                start -= 1
                used = 2
                if wordPrevPrev in past_markers:
                    dayOffset = dayOffset * -1
                    start -= 1
                    used += 1
            # next weekend -> next saturday
            elif wordPrev in future_1st_markers:
                if wkday < 5:
                    dayOffset = 5 - wkday
                elif wkday == 5:
                    dayOffset = 7
                else:
                    dayOffset = 6
                start -= 1
                used = 2
            # normalize step makes "in a weekend" -> "in weekend" (next monday)
            elif wordPrev in future_markers:
                dayOffset += 7 - wkday  # next monday
                start -= 1
                used = 2
            # last/past weekend -> last/past saturday
            elif wordPrev in past_markers:
                dayOffset -= wkday + 2
                start -= 1
                used = 2
        # parse X weekends ago
        elif word == "weekend" and not fromFlag and wordNext in earlier_markers:
            dayOffset -= wkday + 3  # past friday "one weekend ago"
            used = 2
            # X weekends ago
            if wordPrev and wordPrev[0].isdigit():
                n = int(wordPrev) - 1
                dayOffset -= n * 7
                start -= 1
                used = 3
        # parse 10 months, next month, last month
        elif word == "month" and not fromFlag and wordPrev and wordNext not in earlier_markers:
            if wordPrev[0].isdigit():
                monthOffset = int(wordPrev)
                start -= 1
                used = 2
                if wordPrevPrev in past_markers:
                    monthOffset = monthOffset * -1
                    start -= 1
                    used += 1
            # next month -> day 1
            elif wordPrev in future_1st_markers:
                next_dt = (anchorDate.replace(day=1) + timedelta(days=32)).replace(day=1)
                dayOffset = (next_dt - anchorDate).days
                start -= 1
                used = 2
            # normalize step makes "in a month" -> "in month"
            elif wordPrev in future_markers:
                monthOffset = 1
                start -= 1
                used = 2
            elif wordPrev in past_markers:
                monthOffset = -1
                start -= 1
                used = 2
        elif word == "month" and wordNext in earlier_markers:
            if wordPrev and wordPrev[0].isdigit():
                monthOffset -= int(wordPrev)
                start -= 1
                used = 3
            else:
                monthOffset -= 1
                used = 2
        # parse 5 years, next year, last year
        elif word == "year" and not fromFlag and wordPrev and wordNext not in earlier_markers:
            if wordPrev[0].isdigit():
                yearOffset = int(wordPrev)
                start -= 1
                used = 2
                if wordPrevPrev in past_markers:
                    yearOffset = yearOffset * -1
                    start -= 1
                    used += 1
            # next year -> day 1
            elif wordPrev in future_1st_markers:
                next_dt = anchorDate.replace(day=1, month=1, year=anchorDate.year + 1)
                dayOffset = (next_dt - anchorDate).days
                start -= 1
                used = 2
            # normalize step makes "in a year" -> "in year"
            elif wordPrev in future_markers:
                yearOffset = 1
                start -= 1
                used = 2
            elif wordPrev in past_markers:
                yearOffset = -1
                start -= 1
                used = 2
        elif word == "year" and wordNext in earlier_markers:
            if wordPrev and wordPrev[0].isdigit():
                yearOffset -= int(wordPrev)
                start -= 1
                used = 3
            else:
                yearOffset -= 1
                used = 2

        # parse Monday, Tuesday, etc., and next Monday,
        # last Tuesday, etc.
        elif word in days and not fromFlag:
            d = days.index(word)
            dayOffset = (d + 1) - int(today)
            used = 1
            if dayOffset < 0:
                dayOffset += 7
            if wordPrev == "next":
                if dayOffset <= 2:
                    dayOffset += 7
                used += 1
                start -= 1
            elif wordPrev in past_markers:
                dayOffset -= 7
                used += 1
                start -= 1
        # parse 15 of July, June 20th, Feb 18, 19 of February
        elif word in months or word in monthsShort and not fromFlag:
            try:
                m = months.index(word)
            except ValueError:
                m = monthsShort.index(word)
            used += 1
            datestr = months[m]
            if wordPrev and (wordPrev[0].isdigit() or
                             (wordPrev == "of" and wordPrevPrev[0].isdigit())):
                if wordPrev == "of" and wordPrevPrev[0].isdigit():
                    datestr += " " + words[idx - 2]
                    used += 1
                    start -= 1
                else:
                    datestr += " " + wordPrev
                start -= 1
                used += 1
                if wordNext and wordNext[0].isdigit():
                    datestr += " " + wordNext
                    used += 1
                    hasYear = True
                else:
                    hasYear = False

            elif wordNext and wordNext[0].isdigit():
                datestr += " " + wordNext
                used += 1
                if wordNextNext and wordNextNext[0].isdigit():
                    datestr += " " + wordNextNext
                    used += 1
                    hasYear = True
                else:
                    hasYear = False
            # if no date indicators found, it may not be the month of May
            # may "i/we" ...
            # "... may be"
            elif word == 'may' and wordNext in ['i', 'we', 'be']:
                datestr = ""
            # when was MONTH
            elif not hasYear and wordPrev in past_markers:
                if anchorDate.month > m:
                    datestr += f" {anchorDate.year}"
                else:
                    datestr += f" {anchorDate.year - 1}"
                hasYear = True
            # when is MONTH
            elif not hasYear:
                if anchorDate.month > m:
                    datestr += f" {anchorDate.year + 1}"
                else:
                    datestr += f" {anchorDate.year}"
                hasYear = True
        # parse 5 days from tomorrow, 10 weeks from next thursday,
        # 2 months from July
        validFollowups = days + months + monthsShort
        validFollowups.append("today")
        validFollowups.append("tomorrow")
        validFollowups.append("yesterday")
        validFollowups.append("next")
        validFollowups.append("last")
        validFollowups.append("past")
        validFollowups.append("now")
        validFollowups.append("this")
        if (word == "from" or word == "after") and wordNext in validFollowups:
            used = 2
            fromFlag = True
            if wordNext == "tomorrow":
                dayOffset += 1
            elif wordNext == "yesterday":
                dayOffset -= 1
            elif wordNext in days:
                d = days.index(wordNext)
                tmpOffset = (d + 1) - int(today)
                used = 2
                if tmpOffset < 0:
                    tmpOffset += 7
                dayOffset += tmpOffset
            elif wordNextNext and wordNextNext in days:
                d = days.index(wordNextNext)
                tmpOffset = (d + 1) - int(today)
                used = 3
                if wordNext in future_1st_markers:
                    if dayOffset <= 2:
                        tmpOffset += 7
                    used += 1
                    start -= 1
                elif wordNext in past_markers:
                    tmpOffset -= 7
                    used += 1
                    start -= 1
                dayOffset += tmpOffset
        if used > 0:
            if start - 1 > 0 and words[start - 1] == "this":
                start -= 1
                used += 1

            for i in range(0, used):
                words[i + start] = ""

            if start - 1 >= 0 and words[start - 1] in markers:
                words[start - 1] = ""
            found = True
            daySpecified = True

    # parse time
    hrOffset = 0
    minOffset = 0
    secOffset = 0
    hrAbs = None
    minAbs = None
    military = False

    for idx, word in enumerate(words):
        if word == "":
            continue

        wordPrevPrev = words[idx - 2] if idx > 1 else ""
        wordPrev = words[idx - 1] if idx > 0 else ""
        wordNext = words[idx + 1] if idx + 1 < len(words) else ""
        wordNextNext = words[idx + 2] if idx + 2 < len(words) else ""
        # parse noon, midnight, morning, afternoon, evening
        used = 0
        if word == "noon":
            hrAbs = 12
            used += 1
        elif word == "midnight":
            hrAbs = 0
            used += 1
        elif word == "morning":
            if hrAbs is None:
                hrAbs = 8
            used += 1
        elif word == "afternoon":
            if hrAbs is None:
                hrAbs = 15
            used += 1
        elif word == "evening":
            if hrAbs is None:
                hrAbs = 19
            used += 1
        elif word == "tonight" or word == "night":
            if hrAbs is None:
                hrAbs = 22
            # used += 1 ## NOTE this breaks other tests, TODO refactor me!

        # couple of time_unit
        elif word == "2" and wordNext == "of" and \
                wordNextNext in ["hours", "minutes", "seconds"]:
            used += 3
            if wordNextNext == "hours":
                hrOffset = 2
            elif wordNextNext == "minutes":
                minOffset = 2
            elif wordNextNext == "seconds":
                secOffset = 2
        # parse in a/next second/minute/hour
        elif wordNext == "hour" and word in future_markers + future_1st_markers:
            used += 2
            hrOffset = 1
        elif wordNext == "minute" and word in future_markers + future_1st_markers:
            used += 2
            minOffset = 1
        elif wordNext == "second" and word in future_markers + future_1st_markers:
            used += 2
            secOffset = 1
        # parse last/past  second/minute/hour
        elif wordNext == "hour" and word in past_markers:
            used += 2
            hrOffset = - 1
        elif wordNext == "minute" and word in past_markers:
            used += 2
            minOffset = - 1
        elif wordNext == "second" and word in past_markers:
            used += 2
            secOffset = - 1
        # parse half an hour, quarter hour
        elif word == "hour" and \
                (wordPrev in markers or wordPrevPrev in markers):
            if wordPrev == "half":
                minOffset = 30
            elif wordPrev == "quarter":
                minOffset = 15
            elif wordPrevPrev == "quarter":
                minOffset = 15
                if idx > 2 and words[idx - 3] in markers:
                    words[idx - 3] = ""
                words[idx - 2] = ""
            elif wordPrev == "within":
                hrOffset = 1
            else:
                hrOffset = 1
            if wordPrevPrev in markers:
                words[idx - 2] = ""
                if wordPrevPrev == "this":
                    daySpecified = True
            words[idx - 1] = ""
            used += 1
            hrAbs = -1
            minAbs = -1
        # parse 5:00 am, 12:00 p.m., etc
        elif word[0].isdigit():
            isTime = True
            strHH = ""
            strMM = ""
            remainder = ""
            wordNextNextNext = words[idx + 3] \
                if idx + 3 < len(words) else ""
            if wordNext == "tonight" or wordNextNext == "tonight" or \
                    wordPrev == "tonight" or wordPrevPrev == "tonight" or \
                    wordNextNextNext == "tonight":
                remainder = "pm"
                used += 1
                if wordPrev == "tonight":
                    words[idx - 1] = ""
                if wordPrevPrev == "tonight":
                    words[idx - 2] = ""
                if wordNextNext == "tonight":
                    used += 1
                if wordNextNextNext == "tonight":
                    used += 1

            if ':' in word:
                # parse colons
                # "3:00 in the morning"
                stage = 0
                length = len(word)
                for i in range(length):
                    if stage == 0:
                        if word[i].isdigit():
                            strHH += word[i]
                        elif word[i] == ":":
                            stage = 1
                        else:
                            stage = 2
                            i -= 1
                    elif stage == 1:
                        if word[i].isdigit():
                            strMM += word[i]
                        else:
                            stage = 2
                            i -= 1
                    elif stage == 2:
                        remainder = word[i:].replace(".", "")
                        break
                if remainder == "":
                    nextWord = wordNext.replace(".", "")
                    if nextWord == "am" or nextWord == "pm":
                        remainder = nextWord
                        used += 1

                    elif wordNext == "in" and wordNextNext == "the" and \
                            words[idx + 3] == "morning":
                        remainder = "am"
                        used += 3
                    elif wordNext == "in" and wordNextNext == "the" and \
                            words[idx + 3] == "afternoon":
                        remainder = "pm"
                        used += 3
                    elif wordNext == "in" and wordNextNext == "the" and \
                            words[idx + 3] == "evening":
                        remainder = "pm"
                        used += 3
                    elif wordNext == "in" and wordNextNext == "morning":
                        remainder = "am"
                        used += 2
                    elif wordNext == "in" and wordNextNext == "afternoon":
                        remainder = "pm"
                        used += 2
                    elif wordNext == "in" and wordNextNext == "evening":
                        remainder = "pm"
                        used += 2
                    elif wordNext == "this" and wordNextNext == "morning":
                        remainder = "am"
                        used = 2
                        daySpecified = True
                    elif wordNext == "this" and wordNextNext == "afternoon":
                        remainder = "pm"
                        used = 2
                        daySpecified = True
                    elif wordNext == "this" and wordNextNext == "evening":
                        remainder = "pm"
                        used = 2
                        daySpecified = True
                    elif wordNext == "at" and wordNextNext == "night":
                        if strHH and int(strHH) > 5:
                            remainder = "pm"
                        else:
                            remainder = "am"
                        used += 2

                    else:
                        if timeQualifier != "":
                            military = True
                            if strHH and int(strHH) <= 12 and \
                                    (timeQualifier in timeQualifiersPM):
                                strHH += str(int(strHH) + 12)

            else:
                # try to parse numbers without colons
                # 5 hours, 10 minutes etc.
                length = len(word)
                strNum = ""
                remainder = ""
                for i in range(length):
                    if word[i].isdigit():
                        strNum += word[i]
                    else:
                        remainder += word[i]

                if remainder == "":
                    remainder = wordNext.replace(".", "").lstrip().rstrip()
                if (
                        remainder == "pm" or
                        wordNext == "pm" or
                        remainder == "p.m." or
                        wordNext == "p.m."):
                    strHH = strNum
                    remainder = "pm"
                    used = 1
                elif (
                        remainder == "am" or
                        wordNext == "am" or
                        remainder == "a.m." or
                        wordNext == "a.m."):
                    strHH = strNum
                    remainder = "am"
                    used = 1
                elif (
                        remainder in recur_markers or
                        wordNext in recur_markers or
                        wordNextNext in recur_markers):
                    # Ex: "7 on mondays" or "3 this friday"
                    # Set strHH so that isTime == True
                    # when am or pm is not specified
                    strHH = strNum
                    used = 1
                else:
                    if (
                            int(strNum) > 100 and
                            (
                                    wordPrev == "o" or
                                    wordPrev == "oh"
                            )):
                        # 0800 hours (pronounced oh-eight-hundred)
                        strHH = str(int(strNum) // 100)
                        strMM = str(int(strNum) % 100)
                        military = True
                        if wordNext == "hours":
                            used += 1
                    elif (
                            (wordNext == "hours" or wordNext == "hour" or
                             remainder == "hours" or remainder == "hour") and
                            word[0] != '0' and
                            (int(strNum) < 100 or int(strNum) > 2400 or wordPrev in past_markers)):
                        # ignores military time
                        # "in 3 hours"
                        hrOffset = int(strNum)
                        used = 2
                        isTime = False
                        hrAbs = -1
                        minAbs = -1
                        # in last N hours
                        if wordPrev in past_markers:
                            start -= 1
                            used += 1
                            hrOffset = hrOffset * -1

                    elif wordNext == "minutes" or wordNext == "minute" or \
                            remainder == "minutes" or remainder == "minute":
                        # "in 10 minutes"
                        minOffset = int(strNum)
                        used = 2
                        isTime = False
                        hrAbs = -1
                        minAbs = -1
                        # in last N minutes
                        if wordPrev in past_markers:
                            start -= 1
                            used += 1
                            minOffset = minOffset * -1
                    elif wordNext == "seconds" or wordNext == "second" \
                            or remainder == "seconds" or remainder == "second":
                        # in 5 seconds
                        secOffset = int(strNum)
                        used = 2
                        isTime = False
                        hrAbs = -1
                        minAbs = -1
                        # in last N seconds
                        if wordPrev in past_markers:
                            start -= 1
                            used += 1
                            secOffset = secOffset * -1
                    elif int(strNum) > 100:
                        # military time, eg. "3300 hours"
                        strHH = str(int(strNum) // 100)
                        strMM = str(int(strNum) % 100)
                        military = True
                        if wordNext == "hours" or wordNext == "hour" or \
                                remainder == "hours" or remainder == "hour":
                            used += 1
                    elif wordNext and wordNext[0].isdigit():
                        # military time, e.g. "04 38 hours"
                        strHH = strNum
                        strMM = wordNext
                        military = True
                        used += 1
                        if (wordNextNext == "hours" or
                                wordNextNext == "hour" or
                                remainder == "hours" or remainder == "hour"):
                            used += 1
                    elif (wordNext == ""
                          or wordNext == "o'clock"
                          or (wordNext == "in" and (wordNextNext == "the" or wordNextNext == timeQualifier))
                          or wordNext == 'tonight'
                          or wordNextNext == 'tonight'):
                        strHH = strNum
                        strMM = "00"
                        if wordNext == "o'clock":
                            used += 1

                        if wordNext == "in" or wordNextNext == "in":
                            used += (1 if wordNext == "in" else 2)
                            wordNextNextNext = words[idx + 3] \
                                if idx + 3 < len(words) else ""

                            if (wordNextNext and
                                    (wordNextNext in timeQualifier or
                                     wordNextNextNext in timeQualifier)):
                                if (wordNextNext in timeQualifiersPM or
                                        wordNextNextNext in timeQualifiersPM):
                                    remainder = "pm"
                                    used += 1
                                if (wordNextNext in timeQualifiersAM or
                                        wordNextNextNext in timeQualifiersAM):
                                    remainder = "am"
                                    used += 1

                        if timeQualifier != "":
                            if timeQualifier in timeQualifiersPM:
                                remainder = "pm"
                                used += 1

                            elif timeQualifier in timeQualifiersAM:
                                remainder = "am"
                                used += 1
                            else:
                                # TODO: Unsure if this is 100% accurate
                                used += 1
                                military = True
                    else:
                        isTime = False

            HH = int(strHH) if strHH else 0
            MM = int(strMM) if strMM else 0
            HH = HH + 12 if remainder == "pm" and HH < 12 else HH
            HH = HH - 12 if remainder == "am" and HH >= 12 else HH

            if (not military and
                    remainder not in ['am', 'pm', 'hours', 'minutes',
                                      "second", "seconds",
                                      "hour", "minute"] and
                    ((not daySpecified) or 0 <= dayOffset < 1)):

                # ambiguous time, detect whether they mean this evening or
                # the next morning based on whether it has already passed
                if anchorDate.hour < HH or (anchorDate.hour == HH and
                                            anchorDate.minute < MM):
                    pass  # No modification needed
                elif anchorDate.hour < HH + 12:
                    HH += 12
                else:
                    # has passed, assume the next morning
                    dayOffset += 1

            if timeQualifier in timeQualifiersPM and HH < 12:
                HH += 12

            if HH > 24 or MM > 59:
                isTime = False
                used = 0
            if isTime:
                hrAbs = HH
                minAbs = MM
                used += 1

        if used > 0:
            # removed parsed words from the sentence
            for i in range(used):
                if idx + i >= len(words):
                    break
                words[idx + i] = ""

            if wordPrev == "o" or wordPrev == "oh":
                words[words.index(wordPrev)] = ""

            if wordPrev == "early":
                hrOffset = -1
                words[idx - 1] = ""
                idx -= 1
            elif wordPrev == "late":
                hrOffset = 1
                words[idx - 1] = ""
                idx -= 1
            if idx > 0 and wordPrev in markers:
                words[idx - 1] = ""
                if wordPrev == "this":
                    daySpecified = True
            if idx > 1 and wordPrevPrev in markers:
                words[idx - 2] = ""
                if wordPrevPrev == "this":
                    daySpecified = True

            idx += used - 1
            found = True

    # check that we found a date
    if not date_found():
        return None

    if dayOffset is False:
        dayOffset = 0

    # perform date manipulation

    extractedDate = anchorDate.replace(microsecond=0)

    if datestr != "":
        # date included an explicit date, e.g. "june 5" or "june 2, 2017"
        try:
            temp = datetime.strptime(datestr, "%B %d")
        except ValueError:
            # Try again, allowing the year
            try:
                temp = datetime.strptime(datestr, "%B %d %Y")
            except ValueError:
                # Try again, without day
                try:
                    temp = datetime.strptime(datestr, "%B %Y")
                except ValueError:
                    # Try again, with only month
                    temp = datetime.strptime(datestr, "%B")
        extractedDate = extractedDate.replace(hour=0, minute=0, second=0)
        if not hasYear:
            temp = temp.replace(year=extractedDate.year,
                                tzinfo=extractedDate.tzinfo)
            if extractedDate < temp:
                extractedDate = extractedDate.replace(
                    year=int(currentYear),
                    month=int(temp.strftime("%m")),
                    day=int(temp.strftime("%d")),
                    tzinfo=extractedDate.tzinfo)
            else:
                extractedDate = extractedDate.replace(
                    year=int(currentYear) + 1,
                    month=int(temp.strftime("%m")),
                    day=int(temp.strftime("%d")),
                    tzinfo=extractedDate.tzinfo)
        else:
            extractedDate = extractedDate.replace(
                year=int(temp.strftime("%Y")),
                month=int(temp.strftime("%m")),
                day=int(temp.strftime("%d")),
                tzinfo=extractedDate.tzinfo)
    else:
        # ignore the current HH:MM:SS if relative using days or greater
        if hrOffset == 0 and minOffset == 0 and secOffset == 0:
            extractedDate = extractedDate.replace(hour=default_time.hour,
                                                  minute=default_time.minute,
                                                  second=default_time.second)

    if yearOffset != 0:
        extractedDate = extractedDate + relativedelta(years=yearOffset)
    if monthOffset != 0:
        extractedDate = extractedDate + relativedelta(months=monthOffset)
    if dayOffset != 0:
        extractedDate = extractedDate + relativedelta(days=dayOffset)
    if hrOffset != 0:
        extractedDate = extractedDate + relativedelta(hours=hrOffset)
    if minOffset != 0:
        extractedDate = extractedDate + relativedelta(minutes=minOffset)
    if secOffset != 0:
        extractedDate = extractedDate + relativedelta(seconds=secOffset)

    if hrAbs != -1 and minAbs != -1 and not hrOffset and not minOffset and not secOffset:
        # If no time was supplied in the string set the time to default
        # time if it's available
        if hrAbs is None and minAbs is None and default_time is not None:
            hrAbs, minAbs = default_time.hour, default_time.minute
        else:
            hrAbs = hrAbs or 0
            minAbs = minAbs or 0

        extractedDate = extractedDate.replace(hour=hrAbs,
                                              minute=minAbs)

        if (hrAbs != 0 or minAbs != 0) and datestr == "":
            if not daySpecified and anchorDate > extractedDate:
                extractedDate = extractedDate + relativedelta(days=1)

    for idx, word in enumerate(words):
        if words[idx] == "and" and \
                words[idx - 1] == "" and words[idx + 1] == "":
            words[idx] = ""

    resultStr = " ".join(words)
    resultStr = ' '.join(resultStr.split())
    return [extractedDate, resultStr]
