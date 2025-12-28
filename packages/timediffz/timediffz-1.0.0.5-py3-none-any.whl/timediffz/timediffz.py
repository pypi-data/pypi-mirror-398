import warnings
try: from src.timediffz import td1
except Exception: warnings.warn(f"timediffz 1.0.0.2 (fractions mode) failed to load correctly :(, using any fractions mode related function WOULD give an error and fall because of this, the error")
try: from src.timediffz import td2
except Exception: warnings.warn(f"timediffz 1.0.0.2 (fractionals mode) failed to load correctly :(, using any fractionals mode related function WOULD give an error and fall because of this, the error")
def pdiff (s,e,tz_s=0,tz_e=0,unit_factor=1,count_ls_param=True,UTDLS=False,input_utc=True,output_tt=False):
    """this function give the difference between the two dates(s and e) in unit_factor, fractions version
    S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
    E: is the second date(ending date) and it has same format and data type as S
    tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
    tz_e: is the same as tz_s in everything, but it's for E date
    unit_factor: this is the unit to be used, basically the difference between dates would be done in seconds , so you can if you want to get result in minutes for example
    to do that , make it into 60 and the difference would be divided by 60 leading to result being in the unit of minutes, and it's an integer
    count_ls_param: enabling this would count leap-seconds, boolean
    UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
    input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
    and your dates would be considered as TAI input, boolean
    output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
    """
    return td1._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=unit_factor, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def cdiff (s,e,tz_s=0,tz_e=0,unit_factor=1,count_ls_param=True,UTDLS=False,input_utc=True,output_tt=False):
    """this function give the difference between the two dates(s and e) in unit_factor, fractionals version
    S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
    E: is the second date(ending date) and it has same format and data type as S
    tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
    tz_e: is the same as tz_s in everything, but it's for E date
    unit_factor: this is the unit to be used, basically the difference between dates would be done in seconds , so you can if you want to get result in minutes for example
    to do that , make it into 60 and the difference would be divided by 60 leading to result being in the unit of minutes, and it's an integer
    count_ls_param: enabling this would count leap-seconds, boolean
    UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
    input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
    and your dates would be considered as TAI input, boolean
    output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
    """
    return td2._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=unit_factor, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def pdseconds (s,e,tz_s=0,tz_e=0,count_ls_param=True,UTDLS=False,input_utc=True,output_tt=False):
    """this function give the difference between the two dates(s and e) in seconds, fractions version
    S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
    E: is the second date(ending date) and it has same format and data type as S
    tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
    tz_e: is the same as tz_s in everything, but it's for E date
    count_ls_param: enabling this would count leap-seconds, boolean
    UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
    input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
    and your dates would be considered as TAI input, boolean
    output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
    """
    return td1._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=1, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def cdseconds(s, e, tz_s=0, tz_e=0, count_ls_param=True, UTDLS=False, input_utc=True, output_tt=False):
    """this function give the difference between the two dates(s and e) in seconds, fractionals version
        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
        E: is the second date(ending date) and it has same format and data type as S
        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
        tz_e: is the same as tz_s in everything, but it's for E date
        count_ls_param: enabling this would count leap-seconds, boolean
        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
        and your dates would be considered as TAI input, boolean
        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
        """
    return td2._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=1, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def pdminutes (s,e,tz_s=0,tz_e=0,count_ls_param=True,UTDLS=False,input_utc=True,output_tt=False):
    """this function give the difference between the two dates(s and e) in minutes, fractions version
        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
        E: is the second date(ending date) and it has same format and data type as S
        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
        tz_e: is the same as tz_s in everything, but it's for E date
        count_ls_param: enabling this would count leap-seconds, boolean
        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
        and your dates would be considered as TAI input, boolean
        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
        """
    return td1._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=60, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def cdminutes(s, e, tz_s=0, tz_e=0, count_ls_param=True, UTDLS=False, input_utc=True, output_tt=False):
    """this function give the difference between the two dates(s and e) in minutes, fractionals version
        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
        E: is the second date(ending date) and it has same format and data type as S
        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
        tz_e: is the same as tz_s in everything, but it's for E date
        count_ls_param: enabling this would count leap-seconds, boolean
        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
        and your dates would be considered as TAI input, boolean
        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
        """
    return td2._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=60, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def pdhours (s,e,tz_s=0,tz_e=0,count_ls_param=True,UTDLS=False,input_utc=True,output_tt=False):
    """this function give the difference between the two dates(s and e) in hours, fractions version
        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
        E: is the second date(ending date) and it has same format and data type as S
        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
        tz_e: is the same as tz_s in everything, but it's for E date
        count_ls_param: enabling this would count leap-seconds, boolean
        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
        and your dates would be considered as TAI input, boolean
        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
        """
    return td1._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=3600, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def cdhours(s, e, tz_s=0, tz_e=0, count_ls_param=True, UTDLS=False, input_utc=True, output_tt=False):
    """this function give the difference between the two dates(s and e) in hours, fractionals version
        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
        E: is the second date(ending date) and it has same format and data type as S
        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
        tz_e: is the same as tz_s in everything, but it's for E date
        count_ls_param: enabling this would count leap-seconds, boolean
        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
        and your dates would be considered as TAI input, boolean
        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
        """
    return td2._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=3600, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def pddays (s,e,tz_s=0,tz_e=0,count_ls_param=True,UTDLS=False,input_utc=True,output_tt=False):
    """this function give the difference between the two dates(s and e) in days, fractions version
        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
        E: is the second date(ending date) and it has same format and data type as S
        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
        tz_e: is the same as tz_s in everything, but it's for E date
        count_ls_param: enabling this would count leap-seconds, boolean
        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
        and your dates would be considered as TAI input, boolean
        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
        """
    return td1._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=86400, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def cddays(s, e, tz_s=0, tz_e=0, count_ls_param=True, UTDLS=False, input_utc=True, output_tt=False):
    """this function give the difference between the two dates(s and e) in seconds, fractionals version
        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
        E: is the second date(ending date) and it has same format and data type as S
        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
        tz_e: is the same as tz_s in everything, but it's for E date
        count_ls_param: enabling this would count leap-seconds, boolean
        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
        and your dates would be considered as TAI input, boolean
        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
        """
    return td2._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=86400, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def pdweeks (s,e,tz_s=0,tz_e=0,count_ls_param=True,UTDLS=False,input_utc=True,output_tt=False):
    """this function give the difference between the two dates(s and e) in weeks, fractions version
        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
        E: is the second date(ending date) and it has same format and data type as S
        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
        tz_e: is the same as tz_s in everything, but it's for E date
        count_ls_param: enabling this would count leap-seconds, boolean
        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
        and your dates would be considered as TAI input, boolean
        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
        """
    return td1._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=86400 * 7, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def cdweeks(s, e, tz_s=0, tz_e=0, count_ls_param=True, UTDLS=False, input_utc=True, output_tt=False):
    """this function give the difference between the two dates(s and e) in weeks, fractionals version
        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
        E: is the second date(ending date) and it has same format and data type as S
        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
        tz_e: is the same as tz_s in everything, but it's for E date
        count_ls_param: enabling this would count leap-seconds, boolean
        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
        and your dates would be considered as TAI input, boolean
        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
        """
    return td2._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=86400 * 7, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def pdmonths(s, e, tz_s=0, tz_e=0,month_unit=0, leap_year=False,input_utc=True, output_tt=False,UTDLS=False, count_ls_param=True,use_date_in_leapyears_checking=False,year_for_leapyears_checking=None,reference_year_for_scaling=None):
    """this function give the difference between the two dates(s and e) in months, fractions version
        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
        E: is the second date(ending date) and it has same format and data type as S
        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
        tz_e: is the same as tz_s in everything, but it's for E date
        month_unit: is what month you chose to be your unit, like how many junes or how many octobers, it's value corresponds to month it represents, it's an integer
        leap_year: if the year is a leap yest or not , useful to determine February's value
        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
        and your dates would be considered as TAI input, boolean
        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
        count_ls_param: enabling this would count leap-seconds, boolean
        use_date_in_leap years_checking: it's an integer value, that would be about to use the year given or written as integer value to determine if year is leap year or not
        year_for_leapyears_checking: it's an integer value, that would be used instead of using the year in starting value to know if to consider
        the year as a leap year or a normal one
        reference_year_for_scaling: it's an boolean value, that would be about if or if not to use the date to determine if year to be used or considered
        is a leap year or not
        """
    return td1._months_piecewise(s, e, tz_s=tz_s, tz_e=tz_e, month_unit=month_unit, leap_year=leap_year, input_utc=input_utc, UTDLS=UTDLS, count_ls_param=count_ls_param, output_tt=output_tt, use_date_in_leapyears_checking=use_date_in_leapyears_checking, year_for_leapyears_checking=year_for_leapyears_checking, reference_year_for_scaling=reference_year_for_scaling)
def cdmonths(s, e, tz_s=0, tz_e=0,month_unit=0, leap_year=False,input_utc=True, output_tt=False,UTDLS=False, count_ls_param=True,use_date_in_leapyears_checking=False,year_for_leapyears_checking=None,reference_year_for_scaling=None):
    """this function give the difference between the two dates(s and e) in months, fractionals version
            S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
            E: is the second date(ending date) and it has same format and data type as S
            tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
            tz_e: is the same as tz_s in everything, but it's for E date
            month_unit: is what month you chose to be your unit, like how many junes or how many octobers, it's value corresponds to month it represents, it's an integer
            leap_year: if the year is a leap yest or not , useful to determine February's value
            input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
            and your dates would be considered as TAI input, boolean
            output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
            UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
            count_ls_param: enabling this would count leap-seconds, boolean
            use_date_in_leap years_checking: it's an integer value, that would be about to use the year given or written as integer value to determine if year is leap year or not
            year_for_leapyears_checking: it's an integer value, that would be used instead of using the year in starting value to know if to consider
            the year as a leap year or a normal one
            reference_year_for_scaling: it's an boolean value, that would be about if or if not to use the date to determine if year to be used or considered
            is a leap year or not
            """
    return td2._months_piecewise(s, e, tz_s=tz_s, tz_e=tz_e, month_unit=month_unit, leap_year=leap_year, input_utc=input_utc, UTDLS=UTDLS, count_ls_param=count_ls_param, output_tt=output_tt, use_date_in_leapyears_checking=use_date_in_leapyears_checking, year_for_leapyears_checking=year_for_leapyears_checking, reference_year_for_scaling=reference_year_for_scaling)
def pdyears(s, e, tz_s=0, tz_e=0,leap_year=None, uniform_year=False, tropical_year=False, custom_year=None,input_utc=True, output_tt=False,UTDLS=False, count_ls_param=True,year_for_leapyear_checking=None,lock_range_to_reference_year=False):
    """this function give the difference between the two dates(s and e) in years, fractions version
                S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
                E: is the second date(ending date) and it has same format and data type as S
                tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
                tz_e: is the same as tz_s in everything, but it's for E date
                leap_year: if the year unit is a leap yest or not , boolean value
                uniform_year: if the year unit is a continuous scale Gregorian year, boolean value
                tropical_year: if the year unit is a tropical years, boolean vale
                custom_year: if not none it would use a custom made year unit, integer value
                input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
                and your dates would be considered as TAI input, boolean
                output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
                UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
                count_ls_param: enabling this would count leap-seconds, boolean
                years_for_leapyear_checking: if to use or not use the year in the date to determine if year is a leap year or not, boolean value
                lock_range_to_reference_year: if true no in between years making the added value to pure difference as zero, while default is max(0, E[0] - S[0] - 1)
                """
    return td1._years_piecewise(s, e, tz_s=tz_s, tz_e=tz_e, input_utc=input_utc, UTDLS=UTDLS, count_ls_param=count_ls_param, output_tt=output_tt, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year, leap_year=leap_year, year_for_leapyear_checking=year_for_leapyear_checking, lock_range_to_reference_year=lock_range_to_reference_year)
def cdyears(s, e, tz_s=0, tz_e=0,leap_year=None, uniform_year=False, tropical_year=False, custom_year=None,input_utc=True, output_tt=False,UTDLS=False, count_ls_param=True,year_for_leapyear_checking=None,lock_range_to_reference_year=False):
    """this function give the difference between the two dates(s and e) in years, fractionals version
                S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
                E: is the second date(ending date) and it has same format and data type as S
                tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
                tz_e: is the same as tz_s in everything, but it's for E date
                leap_year: if the year unit is a leap yest or not , boolean value
                uniform_year: if the year unit is a continuous scale Gregorian year, boolean value
                tropical_year: if the year unit is a tropical years, boolean vale
                custom_year: if not none it would use a custom made year unit, integer value
                input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
                and your dates would be considered as TAI input, boolean
                output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
                UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
                count_ls_param: enabling this would count leap-seconds, boolean
                years_for_leapyear_checking: if to use or not use the year in the date to determine if year is a leap year or not, boolean value
                lock_range_to_reference_year: if true no in between years making the added value to pure difference as zero, while default is max(0, E[0] - S[0] - 1)
                """
    return td2._years_piecewise(s, e, tz_s=tz_s, tz_e=tz_e, input_utc=input_utc, UTDLS=UTDLS, count_ls_param=count_ls_param, output_tt=output_tt, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year, leap_year=leap_year, year_for_leapyear_checking=year_for_leapyear_checking, lock_range_to_reference_year=lock_range_to_reference_year)
def pddecades(s, e, tz_s=0, tz_e=0,leap_year=None, uniform_year=False, tropical_year=False, custom_year=None,input_utc=True, output_tt=False,UTDLS=False, count_ls_param=True,year_for_leapyear_checking=None,lock_range_to_reference_year=False):
    """this function give the difference between the two dates(s and e) in decades, fractions version
                    S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
                    E: is the second date(ending date) and it has same format and data type as S
                    tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
                    tz_e: is the same as tz_s in everything, but it's for E date
                    leap_year: if the year unit is a leap yest or not , boolean value
                    uniform_year: if the year unit is a continuous scale Gregorian year, boolean value
                    tropical_year: if the year unit is a tropical years, boolean vale
                    custom_year: if not none it would use a custom made year unit, integer value
                    input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
                    and your dates would be considered as TAI input, boolean
                    output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
                    UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
                    count_ls_param: enabling this would count leap-seconds, boolean
                    years_for_leapyear_checking: if to use or not use the year in the date to determine if year is a leap year or not, boolean value
                    lock_range_to_reference_year: if true no in between years making the added value to pure difference as zero, while default is max(0, E[0] - S[0] - 1)
                    """
    return td1._years_piecewise(s, e, tz_s=tz_s, tz_e=tz_e, input_utc=input_utc, UTDLS=UTDLS, count_ls_param=count_ls_param, output_tt=output_tt, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year, leap_year=leap_year, year_for_leapyear_checking=year_for_leapyear_checking, lock_range_to_reference_year=lock_range_to_reference_year)/10
def cddecades(s, e, tz_s=0, tz_e=0,leap_year=None, uniform_year=False, tropical_year=False, custom_year=None,input_utc=True, output_tt=False,UTDLS=False, count_ls_param=True,year_for_leapyear_checking=None,lock_range_to_reference_year=False):
    """this function give the difference between the two dates(s and e) in decades, fractionals version
                    S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
                    E: is the second date(ending date) and it has same format and data type as S
                    tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
                    tz_e: is the same as tz_s in everything, but it's for E date
                    leap_year: if the year unit is a leap yest or not , boolean value
                    uniform_year: if the year unit is a continuous scale Gregorian year, boolean value
                    tropical_year: if the year unit is a tropical years, boolean vale
                    custom_year: if not none it would use a custom made year unit, integer value
                    input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
                    and your dates would be considered as TAI input, boolean
                    output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
                    UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
                    count_ls_param: enabling this would count leap-seconds, boolean
                    years_for_leapyear_checking: if to use or not use the year in the date to determine if year is a leap year or not, boolean value
                    lock_range_to_reference_year: if true no in between years making the added value to pure difference as zero, while default is max(0, E[0] - S[0] - 1)
                    """
    return td2._years_piecewise(s, e, tz_s=tz_s, tz_e=tz_e, input_utc=input_utc, UTDLS=UTDLS, count_ls_param=count_ls_param, output_tt=output_tt, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year, leap_year=leap_year, year_for_leapyear_checking=year_for_leapyear_checking, lock_range_to_reference_year=lock_range_to_reference_year)/10
def pdcenturies(s, e, tz_s=0, tz_e=0,leap_year=None, uniform_year=False, tropical_year=False, custom_year=None,input_utc=True, output_tt=False,UTDLS=False, count_ls_param=True,year_for_leapyear_checking=None,lock_range_to_reference_year=False):
    """this function give the difference between the two dates(s and e) in centuries, fractions version
                    S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
                    E: is the second date(ending date) and it has same format and data type as S
                    tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
                    tz_e: is the same as tz_s in everything, but it's for E date
                    leap_year: if the year unit is a leap yest or not , boolean value
                    uniform_year: if the year unit is a continuous scale Gregorian year, boolean value
                    tropical_year: if the year unit is a tropical years, boolean vale
                    custom_year: if not none it would use a custom made year unit, integer value
                    input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
                    and your dates would be considered as TAI input, boolean
                    output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
                    UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
                    count_ls_param: enabling this would count leap-seconds, boolean
                    years_for_leapyear_checking: if to use or not use the year in the date to determine if year is a leap year or not, boolean value
                    lock_range_to_reference_year: if true no in between years making the added value to pure difference as zero, while default is max(0, E[0] - S[0] - 1)
                    """
    return td1._years_piecewise(s, e, tz_s=tz_s, tz_e=tz_e, input_utc=input_utc, UTDLS=UTDLS, count_ls_param=count_ls_param, output_tt=output_tt, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year, leap_year=leap_year, year_for_leapyear_checking=year_for_leapyear_checking, lock_range_to_reference_year=lock_range_to_reference_year)/100
def cdcenturies(s, e, tz_s=0, tz_e=0,leap_year=None, uniform_year=False, tropical_year=False, custom_year=None,input_utc=True, output_tt=False,UTDLS=False, count_ls_param=True,year_for_leapyear_checking=None,lock_range_to_reference_year=False):
    """this function give the difference between the two dates(s and e) in centuries, fractionals version
                    S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
                    E: is the second date(ending date) and it has same format and data type as S
                    tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
                    tz_e: is the same as tz_s in everything, but it's for E date
                    leap_year: if the year unit is a leap yest or not , boolean value
                    uniform_year: if the year unit is a continuous scale Gregorian year, boolean value
                    tropical_year: if the year unit is a tropical years, boolean vale
                    custom_year: if not none it would use a custom made year unit, integer value
                    input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
                    and your dates would be considered as TAI input, boolean
                    output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
                    UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
                    count_ls_param: enabling this would count leap-seconds, boolean
                    years_for_leapyear_checking: if to use or not use the year in the date to determine if year is a leap year or not, boolean value
                    lock_range_to_reference_year: if true no in between years making the added value to pure difference as zero, while default is max(0, E[0] - S[0] - 1)
                    """
    return td2._years_piecewise(s, e, tz_s=tz_s, tz_e=tz_e, input_utc=input_utc, UTDLS=UTDLS, count_ls_param=count_ls_param, output_tt=output_tt, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year, leap_year=leap_year, year_for_leapyear_checking=year_for_leapyear_checking, lock_range_to_reference_year=lock_range_to_reference_year)/100
def pdmillennia(s, e, tz_s=0, tz_e=0,leap_year=None, uniform_year=False, tropical_year=False, custom_year=None,input_utc=True, output_tt=False,UTDLS=False, count_ls_param=True,year_for_leapyear_checking=None,lock_range_to_reference_year=False):
    """this function give the difference between the two dates(s and e) in millennia, fractions version
                        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
                        E: is the second date(ending date) and it has same format and data type as S
                        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
                        tz_e: is the same as tz_s in everything, but it's for E date
                        leap_year: if the year unit is a leap yest or not , boolean value
                        uniform_year: if the year unit is a continuous scale Gregorian year, boolean value
                        tropical_year: if the year unit is a tropical years, boolean vale
                        custom_year: if not none it would use a custom made year unit, integer value
                        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
                        and your dates would be considered as TAI input, boolean
                        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
                        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
                        count_ls_param: enabling this would count leap-seconds, boolean
                        years_for_leapyear_checking: if to use or not use the year in the date to determine if year is a leap year or not, boolean value
                        lock_range_to_reference_year: if true no in between years making the added value to pure difference as zero, while default is max(0, E[0] - S[0] - 1)
                        """
    return td1._years_piecewise(s, e, tz_s=tz_s, tz_e=tz_e, input_utc=input_utc, UTDLS=UTDLS, count_ls_param=count_ls_param, output_tt=output_tt, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year, leap_year=leap_year, year_for_leapyear_checking=year_for_leapyear_checking, lock_range_to_reference_year=lock_range_to_reference_year)/1000
def cdmillennia(s, e, tz_s=0, tz_e=0,leap_year=None, uniform_year=False, tropical_year=False, custom_year=None,input_utc=True, output_tt=False,UTDLS=False, count_ls_param=True,year_for_leapyear_checking=None,lock_range_to_reference_year=False):
    """this function give the difference between the two dates(s and e) in millennia, fractionals version
                        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
                        E: is the second date(ending date) and it has same format and data type as S
                        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
                        tz_e: is the same as tz_s in everything, but it's for E date
                        leap_year: if the year unit is a leap yest or not , boolean value
                        uniform_year: if the year unit is a continuous scale Gregorian year, boolean value
                        tropical_year: if the year unit is a tropical years, boolean vale
                        custom_year: if not none it would use a custom made year unit, integer value
                        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
                        and your dates would be considered as TAI input, boolean
                        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
                        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
                        count_ls_param: enabling this would count leap-seconds, boolean
                        years_for_leapyear_checking: if to use or not use the year in the date to determine if year is a leap year or not, boolean value
                        lock_range_to_reference_year: if true no in between years making the added value to pure difference as zero, while default is max(0, E[0] - S[0] - 1)
                        """
    return td2._years_piecewise(s, e, tz_s=tz_s, tz_e=tz_e, input_utc=input_utc, UTDLS=UTDLS, count_ls_param=count_ls_param, output_tt=output_tt, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year, leap_year=leap_year, year_for_leapyear_checking=year_for_leapyear_checking, lock_range_to_reference_year=lock_range_to_reference_year)/1000
def pdsubseconds(s,e,tz_s=0,tz_e=0,subunit=10**6,count_ls_param=True,UTDLS=False,input_utc=True,output_tt=False):
    """this function give the difference between the two dates(s and e) in subseconds, fractions version
        S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
        E: is the second date(ending date) and it has same format and data type as S
        tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
        tz_e: is the same as tz_s in everything, but it's for E date
        subunit: basically is the number that seconds would be divided upon to get difference in as specific unit like 10**6 for micro or 10**9 nano seconds, the default is 10**6 and it's an
        count_ls_param: enabling this would count leap-seconds, boolean
        UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
        input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
        and your dates would be considered as TAI input, boolean
        output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
        """
    return td1._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=subunit, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def cdsubseconds(s,e,tz_s=0,tz_e=0,subunit=10**6,count_ls_param=True,UTDLS=False,input_utc=True,output_tt=False):
    """this function give the difference between the two dates(s and e) in subseconds, fractionals version
            S: is the first date(starting date) and it's a list made off: [Y(year),M(month),D(day),H(hour),MI(minute),S(second),SS(sub-seconds)] and all of these items integers
            E: is the second date(ending date) and it has same format and data type as S
            tz_s: is the timezone where the S date was measured in by default library is set to use greenwich(england) time, and it's an integer value
            tz_e: is the same as tz_s in everything, but it's for E date
            subunit: basically is the number that seconds would be divided upon to get difference in as specific unit like 10**6 for micro or 10**9 nano seconds, the default is 10**6 and it's an
            count_ls_param: enabling this would count leap-seconds, boolean
            UTDLS: enabling this is useless in all cases except when count_ls_param is True, and it would fetch a list of updated leap seconds from the internet, boolean
            input_utc: this one is by default true, which is when your input is in the UTC system, if it's not make this parameter false
            and your dates would be considered as TAI input, boolean
            output_tt: this one is by default false, which is when you wanna your output to be in TT, boolean
            """
    return td2._time_difference(s, e, tz_s=tz_s, tz_e=tz_e, unit_factor=subunit, input_utc=input_utc, count_ls_param=count_ls_param, UTDLS=UTDLS, output_tt=output_tt)
def ptseconds(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td1._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)
def ctseconds(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td2._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)
def ptimestamp(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td1._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)
def ctimestamp(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td2._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)
def ptminutes(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td1._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)/60
def ctminutes(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td2._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)/60
def pthours(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td1._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)/3600
def cthours(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td2._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)/3600
def pcdays(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td1._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)/86400
def ctdays(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td2._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)/86400
def ptweeks(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td1._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)/(86400 * 7)
def ctweeks(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td2._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)/(86400 * 7)
def ptmonths(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False,month_unit=0,use_date_in_leapyears_checking=False,leap_year=False,year_for_leapyears_checking=None): return td1._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt) / td1._get_month_seconds(d[0], d[1], month_unit, td1.is_leap((d[0] if use_date_in_leapyears_checking else year_for_leapyears_checking), leap_year))
def ctmonths(d,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False,month_unit=0,use_date_in_leapyears_checking=False,leap_year=False,year_for_leapyears_checking=None): return td2._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt) / td2._get_month_seconds(d[0], d[1], month_unit, td2.is_leap((d[0] if use_date_in_leapyears_checking else year_for_leapyears_checking), leap_year))
def ptyears(d, count_ls_param=True, UTDLS=False, input_utc=True, unix_epoch=False, custom_epoch_as_utc=True, custom_epoch_as_tt=False,custom_epoch=None, input_tt=False, output_tt=False,uniform_year=False, tropical_year=False, custom_year=None, year_for_leapyear_checking=None): return td1._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)/ td1._seconds_in_year(d[0] if year_for_leapyear_checking is None else year_for_leapyear_checking, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year)
def ctyears(d, count_ls_param=True, UTDLS=False, input_utc=True, unix_epoch=False, custom_epoch_as_utc=True, custom_epoch_as_tt=False,custom_epoch=None, input_tt=False, output_tt=False,uniform_year=False, tropical_year=False, custom_year=None, year_for_leapyear_checking=None): return td2._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)/ td2._seconds_in_year(d[0] if year_for_leapyear_checking is None else year_for_leapyear_checking, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year)
def ptdecades(d, count_ls_param=True, UTDLS=False, input_utc=True, unix_epoch=False, custom_epoch_as_utc=True, custom_epoch_as_tt=False,custom_epoch=None, input_tt=False, output_tt=False,uniform_year=False, tropical_year=False, custom_year=None, year_for_leapyear_checking=None): return (
            td1._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt) / td1._seconds_in_year(d[0] if year_for_leapyear_checking is None else year_for_leapyear_checking, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year))/10
def ctdecades(d, count_ls_param=True, UTDLS=False, input_utc=True, unix_epoch=False, custom_epoch_as_utc=True, custom_epoch_as_tt=False,custom_epoch=None, input_tt=False, output_tt=False,uniform_year=False, tropical_year=False, custom_year=None, year_for_leapyear_checking=None): return (
            td2._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt) / td2._seconds_in_year(d[0] if year_for_leapyear_checking is None else year_for_leapyear_checking, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year))/10
def ptcenturies(d, count_ls_param=True, UTDLS=False, input_utc=True, unix_epoch=False, custom_epoch_as_utc=True, custom_epoch_as_tt=False,custom_epoch=None, input_tt=False, output_tt=False,uniform_year=False, tropical_year=False, custom_year=None, year_for_leapyear_checking=None): return (
            td1._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt) / td1._seconds_in_year(d[0] if year_for_leapyear_checking is None else year_for_leapyear_checking, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year))/100
def ctcenturies(d, count_ls_param=True, UTDLS=False, input_utc=True, unix_epoch=False, custom_epoch_as_utc=True, custom_epoch_as_tt=False,custom_epoch=None, input_tt=False, output_tt=False,uniform_year=False, tropical_year=False, custom_year=None, year_for_leapyear_checking=None): return (
            td2._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt) / td2._seconds_in_year(d[0] if year_for_leapyear_checking is None else year_for_leapyear_checking, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year))/100
def ptmillennia(d, count_ls_param=True, UTDLS=False, input_utc=True, unix_epoch=False, custom_epoch_as_utc=True, custom_epoch_as_tt=False,custom_epoch=None, input_tt=False, output_tt=False,uniform_year=False, tropical_year=False, custom_year=None, year_for_leapyear_checking=None): return (
            td1._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt) / td1._seconds_in_year(d[0] if year_for_leapyear_checking is None else year_for_leapyear_checking, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year))/1000
def ctmillennia(d, count_ls_param=True, UTDLS=False, input_utc=True, unix_epoch=False, custom_epoch_as_utc=True, custom_epoch_as_tt=False,custom_epoch=None, input_tt=False, output_tt=False,uniform_year=False, tropical_year=False, custom_year=None, year_for_leapyear_checking=None): return (
            td2._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt) / td2._seconds_in_year(d[0] if year_for_leapyear_checking is None else year_for_leapyear_checking, uniform_year=uniform_year, tropical_year=tropical_year, custom_year=custom_year))/1000
def ptsubseconds(d,subunit=10**6,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td1._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)/(1 / subunit)
def ctsubseconds(d,subunit=10**6,count_ls_param=True, UTDLS=False, input_utc=True,unix_epoch=False,custom_epoch_as_utc=True,custom_epoch_as_tt=False,custom_epoch=None,input_tt=False,output_tt=False): return td2._timestampinner(*d, count_ls_param=count_ls_param, UTDLS=UTDLS, input_utc=input_utc, unix_epoch=unix_epoch, custom_epoch_as_utc=custom_epoch_as_utc, custom_epoch_as_tt=custom_epoch_as_tt, custom_epoch=custom_epoch, input_tt=input_tt, output_tt=output_tt)/(1 / subunit)
def pmonthscal(s,e): return  td1._monthscalner(s, e)
def cmonthscal(s,e): return  td2._monthscalner(s, e)
def pyearscal(s,e): return  td1._yearscalner(s, e)
def cyearscal(s,e): return  td2._yearscalner(s, e)