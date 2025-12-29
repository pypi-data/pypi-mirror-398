from datetime import datetime, timedelta, timezone
from typing import Union
from zoneinfo import ZoneInfo

COUNTRY_TIMEZONES = {
    "VN": "Asia/Ho_Chi_Minh",
    "US": "America/New_York",
    "UK": "Europe/London",
    "JP": "Asia/Tokyo",
    "KR": "Asia/Seoul",
    "CN": "Asia/Shanghai",
    "IN": "Asia/Kolkata",
    "TH": "Asia/Bangkok",
    "SG": "Asia/Singapore",
    "MY": "Asia/Kuala_Lumpur",
    "ID": "Asia/Jakarta",
    "PH": "Asia/Manila",
    "AU": "Australia/Sydney",
    "DE": "Europe/Berlin",
    "FR": "Europe/Paris",
    "IT": "Europe/Rome",
    "ES": "Europe/Madrid",
    "RU": "Europe/Moscow",
    "BR": "America/Sao_Paulo",
    "CA": "America/Toronto",
    "MX": "America/Mexico_City",
    "AR": "America/Argentina/Buenos_Aires",
    "ZA": "Africa/Johannesburg",
    "EG": "Africa/Cairo",
    "NG": "Africa/Lagos",
    "KE": "Africa/Nairobi",
    "MA": "Africa/Casablanca",
    "TN": "Africa/Tunis",
    "DZ": "Africa/Algiers",
    "LY": "Africa/Tripoli",
    "SD": "Africa/Khartoum",
    "ET": "Africa/Addis_Ababa",
    "GH": "Africa/Accra",
    "UG": "Africa/Kampala",
    "TZ": "Africa/Dar_es_Salaam",
    "ZM": "Africa/Lusaka",
    "ZW": "Africa/Harare",
    "BW": "Africa/Gaborone",
    "NA": "Africa/Windhoek",
    "MW": "Africa/Blantyre",
    "MZ": "Africa/Maputo",
    "MG": "Indian/Antananarivo",
    "MU": "Indian/Mauritius",
    "SC": "Indian/Mahe",
    "RE": "Indian/Reunion",
    "YT": "Indian/Mayotte",
    "KM": "Indian/Comoro",
    "DJ": "Africa/Djibouti",
    "SO": "Africa/Mogadishu",
    "ER": "Africa/Asmara",
    "SS": "Africa/Juba",
    "CF": "Africa/Bangui",
    "TD": "Africa/Ndjamena",
    "NE": "Africa/Niamey",
    "ML": "Africa/Bamako",
    "BF": "Africa/Ouagadougou",
    "CI": "Africa/Abidjan",
    "SN": "Africa/Dakar",
    "GM": "Africa/Banjul",
    "GN": "Africa/Conakry",
    "SL": "Africa/Freetown",
    "LR": "Africa/Monrovia",
    "CV": "Atlantic/Cape_Verde",
    "ST": "Africa/Sao_Tome",
    "GQ": "Africa/Malabo",
    "GA": "Africa/Libreville",
    "CG": "Africa/Brazzaville",
    "CD": "Africa/Kinshasa",
    "AO": "Africa/Luanda",
    "CM": "Africa/Douala",
}


def get_timezone_by_country(country_code: str):
    return COUNTRY_TIMEZONES.get(country_code.upper())


def get_available_countries():
    return list(COUNTRY_TIMEZONES.keys())


def get_timezone_info(timezone_name: str):
    try:
        tz = ZoneInfo(timezone_name)
        now = datetime.now(tz)
        return {
            "timezone": timezone_name,
            "utc_offset": now.utcoffset().total_seconds() / 3600,
            "dst_offset": now.dst().total_seconds() / 3600 if now.dst() else 0,
            "is_dst": now.dst() != timedelta(0),
            "abbreviation": now.tzname(),
            "current_time": now.isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def convert_datetime(dt: Union[datetime, str], from_tz: str, to_tz: str):
    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        dt = dt.astimezone(ZoneInfo(from_tz))
        return dt.astimezone(ZoneInfo(to_tz))

    except Exception as e:
        print(f"Error converting datetime: {e}")
        return None


def get_current_time_in_timezone(timezone_name: str):
    try:
        return datetime.now(ZoneInfo(timezone_name))
    except Exception as e:
        print(f"Error getting current time: {e}")
        return None


def get_current_time_by_country(country_code: str):
    if tz_name := get_timezone_by_country(country_code):
        return get_current_time_in_timezone(tz_name)
    return None


def format_datetime_for_timezone(
    dt: Union[datetime, str],
    timezone_name: str,
    format_str: str = "%Y-%m-%d %H:%M:%S %Z",
):
    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        localized_dt = dt.astimezone(ZoneInfo(timezone_name))
        return localized_dt.strftime(format_str)

    except Exception as e:
        print(f"Error formatting datetime: {e}")
        return None


def get_timezone_offset(timezone_name: str):
    try:
        now = datetime.now(ZoneInfo(timezone_name))
        return now.utcoffset().total_seconds() / 3600
    except Exception as e:
        print(f"Error getting timezone offset: {e}")
        return None


def is_dst_active(timezone_name: str):
    try:
        now = datetime.now(ZoneInfo(timezone_name))
        return now.dst() != timedelta(0)
    except Exception as e:
        print(f"Error checking DST: {e}")
        return None


def get_timezone_abbreviation(timezone_name: str):
    try:
        now = datetime.now(ZoneInfo(timezone_name))
        return now.tzname()
    except Exception as e:
        print(f"Error getting timezone abbreviation: {e}")
        return None


def get_all_timezones():
    from zoneinfo import available_timezones

    return sorted(list(available_timezones()))


def search_timezones(query: str):
    return [tz for tz in get_all_timezones() if query.lower() in tz.lower()]


def get_common_timezones():
    return {
        "UTC": "UTC (Coordinated Universal Time)",
        "Asia/Ho_Chi_Minh": "Vietnam (ICT)",
        "America/New_York": "United States - New York (EST/EDT)",
        "America/Los_Angeles": "United States - Los Angeles (PST/PDT)",
        "Europe/London": "United Kingdom (GMT/BST)",
        "Europe/Paris": "France (CET/CEST)",
        "Asia/Tokyo": "Japan (JST)",
        "Asia/Seoul": "South Korea (KST)",
        "Asia/Shanghai": "China (CST)",
        "Asia/Kolkata": "India (IST)",
        "Asia/Bangkok": "Thailand (ICT)",
        "Asia/Singapore": "Singapore (SGT)",
        "Australia/Sydney": "Australia - Sydney (AEST/AEDT)",
    }
