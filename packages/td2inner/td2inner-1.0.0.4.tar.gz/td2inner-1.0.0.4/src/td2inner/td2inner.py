#THIS IS timediffz (fractionals mode) - made by wedu_official
import sys
# noinspection PyUnresolvedReferences
try: from td2inner.fractionals import Fraction #cython
except: raise ImportError('you need to setup fractionals via this command "cd (full path of folder where setupfractionals.py is in, found in the library files)" and then "python(3 or nothing) setupfractionals.py build_ext --inplace"')
import requests, bisect
sys.set_int_max_str_digits(0)
TT_TAI_OFFSET_SECONDS = Fraction(32184, 1000)

_LEAP_SECOND_DAYNUMS = [Fraction(4882999, 2), Fraction(4883367, 2), Fraction(4884097, 2), Fraction(4884827, 2), Fraction(4885557, 2), Fraction(4886289, 2), Fraction(4887019, 2), Fraction(4887749, 2), Fraction(4888479, 2), Fraction(4889573, 2), Fraction(4890303, 2), Fraction(4891033, 2), Fraction(4892495, 2), Fraction(4894323, 2), Fraction(4895785, 2), Fraction(4896515, 2), Fraction(4897609, 2), Fraction(4898339, 2), Fraction(4899069, 2), Fraction(4900167, 2), Fraction(4901261, 2), Fraction(4902359, 2), Fraction(4907473, 2), Fraction(4909665, 2), Fraction(4912219, 2), Fraction(4914409, 2), Fraction(4915509, 2)]
_MONTH_MAP = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
def _day_number(y, m, d, h=0, mi=0, s=0, sub_seconds=0, sub_unit_depth=10**6):
    # Compute Julian day number for date
    a = (14 - m) // 12
    y_adj = y + 4800 - a
    m_adj = m + 12*a - 3
    jd_integer = d + ((153 * m_adj + 2) // 5) + 365 * y_adj + y_adj // 4 - y_adj // 100 + y_adj // 400
    jd = Fraction(jd_integer) - Fraction(64091, 2)  # Equivalent to 32045.5
    # Add fractional day
    frac_day = Fraction(h*3600 + mi*60 + s, 86400) + Fraction(sub_seconds, sub_unit_depth * 86400) - Fraction(1,2)
    return Fraction(jd) + frac_day
def _get_online_daynums():
    try:
        r = requests.get("https://data.iana.org/time-zones/tzdb/leap-seconds.list", timeout=10)
        r.raise_for_status()
    except requests.RequestException: return None
    daynums = []
    for line in r.text.splitlines():
        if line and line[0].isdigit():
            parts = line.split()
            if len(parts) >= 6:
                day = int(parts[3])
                month_str = parts[4]
                year = int(parts[5])
                if month_str in _MONTH_MAP:
                    month = _MONTH_MAP[month_str]
                    dn = _day_number(year, month, day)
                    bisect.insort_right(daynums, dn)
    print(daynums[1:])
    return daynums[1:]
def _count_ls(y, m, d, UTDLS=False):
    dn = _day_number(y, m, d)
    if UTDLS:
        daynums = _get_online_daynums()
        # Fallback to hardcoded list if online fetch fails
        if daynums is None or not daynums:   # Check for None or an empty list
            daynums = _LEAP_SECOND_DAYNUMS
    else:
        daynums = _LEAP_SECOND_DAYNUMS
    return bisect.bisect_right(daynums, dn)
def _utc_to_tai_offset_seconds(y, m, d, UTDLS=False): return int(_count_ls(y, m, d, UTDLS=UTDLS) + 10)
def _tt_minus_tai_seconds(): return TT_TAI_OFFSET_SECONDS
def _tai_to_otherformats(count_ls_param=False, output_tt=False, count_ls_param_pra=None):
    if count_ls_param_pra is None: count_ls_param_pra = [0, 0, 0, True]
    if count_ls_param: return - (_count_ls(count_ls_param_pra[0], count_ls_param_pra[1], count_ls_param_pra[2], UTDLS=count_ls_param_pra[3]) + 10)  # add this to TAI to get UTC (integer)
    elif output_tt:
        return TT_TAI_OFFSET_SECONDS  # Fraction to add to TAI to get TT
    else: return 0
def _timestampinner(y, m, d, h=0, mi=0, s=0, sub_seconds=0, sub_unit_depth=10**6,
                    count_ls_param=True, UTDLS=False,
                    input_utc=True, input_tt=False, output_tt=False,
                    unix_epoch=False, custom_epoch_as_utc=True,custom_epoch_as_tt=False, custom_epoch=None):
    jd_input = Fraction(_day_number(y, m, d, h, mi, s, sub_seconds, sub_unit_depth))
    if unix_epoch: jd_epoch = Fraction(_day_number(1970, 1, 1))
    elif custom_epoch is not None: jd_epoch = Fraction(_day_number(*custom_epoch))
    else: jd_epoch = Fraction(0)
    base_seconds = (jd_input - jd_epoch) * 86400  # Fraction
    if input_utc and input_tt:
        raise ValueError("invaild input, it's impossible to decide if the input is utc or tt")
    if custom_epoch_as_utc and custom_epoch_as_tt:
        raise ValueError("invaild input, it's impossible to decide if the custom epoch is utc or tt")
    if count_ls_param and output_tt:
        raise ValueError("invaild input, it's impossible to decide if the output must be utc or tt")
    if input_utc: input_offset = Fraction(_utc_to_tai_offset_seconds(y, m, d, UTDLS=UTDLS))
    elif input_tt:input_offset = _tt_minus_tai_seconds()*-1
    else: input_offset = Fraction(0)
    epoch_offset = Fraction(0)
    if custom_epoch is not None:
        if custom_epoch_as_utc: epoch_offset = Fraction(_utc_to_tai_offset_seconds(custom_epoch[0], custom_epoch[1], custom_epoch[2], UTDLS=UTDLS))
        elif custom_epoch_as_tt: epoch_offset = Fraction(_utc_to_tai_offset_seconds(custom_epoch[0], custom_epoch[1], custom_epoch[2], UTDLS=UTDLS))
    tai_seconds = base_seconds + input_offset - epoch_offset
    out_offset = Fraction(_tai_to_otherformats(count_ls_param=count_ls_param, output_tt=output_tt, count_ls_param_pra=[y, m, d, UTDLS]))
    result_seconds = tai_seconds + out_offset
    return result_seconds
def _days_in_month(y, m):
    if m == 2:
        is_leap = (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)
        return 29 if is_leap else 28
    elif m in (4, 6, 9, 11):
        return 30
    else:
        return 31
def _monthscalner(s, e):
    is_negative = False
    if (s[0], s[1], s[2]) > (e[0], e[1], e[2]):
        is_negative = True
        s, e = e, s
    total_months = (e[0] - s[0]) * 12 + (e[1] - s[1])
    # Adjust if the end day is before the start day
    if e[2] < s[2]:
        total_months -= 1
        days_in_end_month = _days_in_month(e[0], e[1])
        day_fraction = Fraction(e[2] + (days_in_end_month - s[2]), days_in_end_month)
    else:
        # The fraction is simply the difference in days over the total days in the start month
        days_in_start_month = _days_in_month(s[0], s[1])
        day_fraction = Fraction(e[2] - s[2], days_in_start_month)
    result = Fraction(total_months) + day_fraction
    if is_negative:
        result *= -1
    return result
def _yearscalner(s, e):
    is_negative = False
    if (s[0], s[1], s[2]) > (e[0], e[1], e[2]):
        is_negative = True
        s, e = e, s
    total_years = e[0] - s[0]
    if (e[1], e[2]) < (s[1], s[2]): total_years -= 1
    total_months = (e[0] - s[0]) * 12 + (e[1] - s[1])
    remaining_months = total_months % 12
    if e[2] < s[2]: remaining_months -= 1
    days_in_start_month = _days_in_month(s[0], s[1])
    day_fraction_of_month = Fraction(e[2] - s[2], days_in_start_month)
    fractional_months = remaining_months + day_fraction_of_month
    result = Fraction(total_years) + Fraction(fractional_months, 12)
    if is_negative:
        result *= -1
    return result
def _time_difference(start, end, unit_factor, tz_s=0, tz_e=0, input_utc=True,output_tt=False,count_ls_param=True, UTDLS=False):
    start_tai = _timestampinner(*start, count_ls_param=count_ls_param, input_utc=input_utc,input_tt=False,output_tt=False, UTDLS=UTDLS)
    end_tai   = _timestampinner(*end, count_ls_param=count_ls_param, input_utc=input_utc,input_tt=False,output_tt=False, UTDLS=UTDLS)
    delta = Fraction(end_tai - start_tai - (tz_e - tz_s) * 3600)
    if output_tt: delta = delta + TT_TAI_OFFSET_SECONDS
    return delta / Fraction(1,unit_factor)
def _seconds_in_year(y=None, custom_year=None, leap_year=None,uniform_year=False,tropical_year=False):
    if tropical_year: return Fraction(Fraction(3652421896698,10000000000) * 86400)
    if custom_year is not None: return custom_year
    if uniform_year: return Fraction(Fraction(3652425,10000) * 86400)
    if leap_year is None:
        if y is None: raise ValueError("Need year y or leap_year/custom_year/tropical_year/preleptic to compute seconds")
        leap_year = (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0))
    return (366 if leap_year else 365) * 86400
def _get_year_seconds(y, leap_year=None, uniform_year=False, tropical_year=False, custom_year=None):
    return _seconds_in_year(y=y, leap_year=leap_year, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year)
def _seconds_in_month(y, m):
    start = _timestampinner(y, m, 1, 0, 0, 0) # Assuming 0,0,0 as standard start time
    end = _timestampinner(y, m, _days_in_month(y, m), 23, 59, 59) # End of last second of the month,
    return end - start
def _get_month_seconds(y, m, month_unit=0, leap_year=False):
    if month_unit == 0:
        return _seconds_in_month(y, m)
    else:
        ref_month = month_unit
        ref_year = 3  # arbitrary reference year
        if leap_year:
            ref_year = 4
        return _seconds_in_month(ref_year, ref_month)
def is_leap(year, leap_year=False):
    if year is not None:
        return ((year % 4 == 0 and year % 100 != 0) or (year % 400 == 0))
    else:
        return leap_year
def _months_piecewise(s, e, tz_s=0, tz_e=0,
                      month_unit=0, leap_year=False,
                      input_utc=True, output_tt=False,
                      UTDLS=False, count_ls_param=True,
                      use_date_in_leapyears_checking=False,
                      year_for_leapyears_checking=None,
                      reference_year_for_scaling=None):
    """Compute difference between two timestamps in months (piecewise), fully continuous (first, mid, last)."""

    neg = False
    if s > e:
        s, e = e, s
        tz_s, tz_e = tz_e, tz_s
        neg = True

    # Same month → direct fraction
    if (s[0], s[1]) == (e[0], e[1]):
        denom = _get_month_seconds(
            s[0], s[1], month_unit,
            is_leap(
                year=(s[0] if use_date_in_leapyears_checking else year_for_leapyears_checking),
                leap_year=leap_year
            )
        )
        num = _time_difference(
            s, e, unit_factor=1,
            tz_s=tz_s, tz_e=tz_e,
            input_utc=input_utc, output_tt=output_tt,
            count_ls_param=count_ls_param, UTDLS=UTDLS
        )
        return -num / denom if neg else num / denom

    # === First segment (from s → end of its month) ===
    end_s = (s[0], s[1], _days_in_month(s[0], s[1]), 23, 59, 59)
    denom_first = _get_month_seconds(
        s[0], s[1], month_unit,
        is_leap(
            year=(s[0] if use_date_in_leapyears_checking else year_for_leapyears_checking),
            leap_year=leap_year
        )
    )
    first_part = _time_difference(
        s, end_s, unit_factor=1,
        tz_s=tz_s, tz_e=tz_s,
        input_utc=input_utc, output_tt=output_tt,
        count_ls_param=count_ls_param, UTDLS=UTDLS
    ) / denom_first

    # === Last segment (from start of its month → e) ===
    start_e = (e[0], e[1], 1, 0, 0, 0)
    denom_last = _get_month_seconds(
        e[0], e[1], month_unit,
        is_leap(
            year=(e[0] if use_date_in_leapyears_checking else year_for_leapyears_checking),
            leap_year=leap_year
        )
    )
    last_part = _time_difference(
        start_e, e, unit_factor=1,
        tz_s=tz_e, tz_e=tz_e,
        input_utc=input_utc, output_tt=output_tt,
        count_ls_param=count_ls_param, UTDLS=UTDLS
    ) / denom_last
    if s[1] == 12:
        mid_start = (s[0] + 1, 1, 1, 0, 0, 0)
    else:
        mid_start = (s[0], s[1] + 1, 1, 0, 0, 0)
    mid_end = (e[0], e[1], 1, 0, 0, 0)
    mid_part = Fraction(0)
    leap_correction = Fraction(0)
    if mid_start < mid_end:
        full_months = (mid_end[0] - mid_start[0]) * 12 + (mid_end[1] - mid_start[1])
        mid_part = Fraction(full_months)
        feb29_count = 0
        if full_months > 0 and not leap_year:  # Only count if using actual leap years
            def count_leap_years(start, end):
                """Count leap years from start to end inclusive."""
                def leaps_before(year):
                    return year // 4 - year // 100 + year // 400
                return leaps_before(end) - leaps_before(start - 1)
            start_year, start_month = mid_start[0], mid_start[1]
            end_year, end_month = mid_end[0], mid_end[1]
            # Adjust range based on month boundaries
            effective_start = start_year if start_month <= 2 else start_year + 1
            effective_end = end_year if end_month >= 2 else end_year - 1
            if effective_start <= effective_end:
                feb29_count = count_leap_years(effective_start, effective_end)
        if feb29_count:
            # reference month to convert days -> months (same logic you used previously)
            ref_y = reference_year_for_scaling if reference_year_for_scaling is not None else s[0]
            ref_m = month_unit if month_unit != 0 else s[1]
            # compute correct leap/ reference-year logic as you intend:
            year_to_check_for_ref = ref_y if not use_date_in_leapyears_checking else (
                        year_for_leapyears_checking or ref_y)
            denom_ref = _get_month_seconds(
                ref_y, ref_m, month_unit,
                is_leap(year=year_to_check_for_ref, leap_year=leap_year))
            # each Feb-29 is 86400 seconds; convert to months using denom_ref
            leap_correction = Fraction((feb29_count * 86400) / Fraction(denom_ref))
    # finally: mid_part + leap_correction
    mid_part = Fraction(mid_part) + Fraction(leap_correction)
    result = Fraction(first_part) + Fraction(mid_part) + Fraction(last_part)
    return result*-1 if neg else result


def _years_piecewise(s, e, tz_s=0, tz_e=0,
                     leap_year=None, uniform_year=False, tropical_year=False, custom_year=None,
                     input_utc=True, output_tt=False,
                     UTDLS=False, count_ls_param=True,year_for_leapyear_checking=None,lock_range_to_reference_year=False):
    neg = False
    if s > e:
        s, e = e, s
        tz_s, tz_e = tz_e, tz_s
        neg = True
    # Same year
    if s[0] == e[0]:
        denom = _get_year_seconds(s[0] if year_for_leapyear_checking is None else year_for_leapyear_checking, leap_year=leap_year, uniform_year=uniform_year,
                                  tropical_year=tropical_year, custom_year=custom_year)
        num = _time_difference(s, e, unit_factor=1, tz_s=tz_s, tz_e=tz_e,
                               input_utc=input_utc, output_tt=output_tt,
                               count_ls_param=count_ls_param, UTDLS=UTDLS)
        return -num / denom if neg else num / denom
    # Fraction of first year
    end_s = (s[0], 12, 31, 23, 59, 60)
    denom_first = _get_year_seconds(s[0] if year_for_leapyear_checking is None else year_for_leapyear_checking, leap_year=leap_year, uniform_year=uniform_year,
                                    tropical_year=tropical_year, custom_year=custom_year)
    first_part = _time_difference(s, end_s, unit_factor=1, tz_s=tz_s, tz_e=tz_s,
                                  input_utc=input_utc, output_tt=output_tt,
                                  count_ls_param=count_ls_param, UTDLS=UTDLS) / denom_first
    # Fraction of last year
    start_e = (e[0], 1, 1, 0, 0, 0)
    denom_last = _get_year_seconds(e[0] if year_for_leapyear_checking is None else year_for_leapyear_checking, leap_year=leap_year, uniform_year=uniform_year,
                                   tropical_year=tropical_year, custom_year=custom_year)
    last_part = _time_difference(start_e, e, unit_factor=1, tz_s=tz_e, tz_e=tz_e,
                                 input_utc=input_utc, output_tt=output_tt,
                                 count_ls_param=count_ls_param, UTDLS=UTDLS) / denom_last
    if lock_range_to_reference_year:
        full = 0  # When locked to reference year, no full years in between
    else:
        full = max(0, e[0] - s[0] - 1)  # Full years between (exclusive)
    result = first_part + full + last_part
    return result*-1 if neg else result