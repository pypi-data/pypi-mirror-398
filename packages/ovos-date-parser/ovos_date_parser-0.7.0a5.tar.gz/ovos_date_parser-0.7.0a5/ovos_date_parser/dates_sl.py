
from ovos_number_parser.numbers_sl import pronounce_number_sl


def nice_time_sl(dt, speech=True, use_24hour=False, use_ampm=False):
    """
    Format a time to a comfortable human format
    For example, generate 'pet trideset' for speech or '5:30' for
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

    def _hour_declension(hour):
        speak = pronounce_number_sl(hour)

        if hour == 1:
            return speak[:-1] + "ih"
        elif hour == 2 or hour == 4:
            return speak + "h"
        elif hour == 3:
            return speak[:-1] + "eh"
        elif hour == 7 or hour == 8:
            return speak[:-2] + "mih"
        else:
            return speak + "ih"

    # Generate a speakable version of the time
    if use_24hour:
        # "13 nič nič"
        speak = pronounce_number_sl(int(string[0:2]))

        speak += " "
        if string[3:5] == '00':
            speak += "nič nič"
        else:
            if string[3] == '0':
                speak += pronounce_number_sl(0) + " "
                speak += pronounce_number_sl(int(string[4]))
            else:
                speak += pronounce_number_sl(int(string[3:5]))
        return speak
    else:
        if dt.hour == 0 and dt.minute == 0:
            return "polnoč"
        elif dt.hour == 12 and dt.minute == 0:
            return "poldne"

        hour = dt.hour % 12 or 12  # 12 hour clock and 0 is spoken as 12
        if dt.minute == 0:
            speak = pronounce_number_sl(hour)
        elif dt.minute < 30:
            speak = pronounce_number_sl(
                dt.minute) + " čez " + pronounce_number_sl(hour)
        elif dt.minute == 30:
            next_hour = (dt.hour + 1) % 12 or 12
            speak = "pol " + _hour_declension(next_hour)
        elif dt.minute > 30:
            next_hour = (dt.hour + 1) % 12 or 12
            speak = pronounce_number_sl(
                60 - dt.minute) + " do " + _hour_declension(next_hour)

        if use_ampm:
            if dt.hour > 11:
                speak += " p.m."
            else:
                speak += " a.m."

        return speak
