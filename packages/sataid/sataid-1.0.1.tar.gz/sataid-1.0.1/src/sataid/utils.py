from datetime import datetime, timedelta

def etim_to_datetime(etim):
    """
    Convert a SATAID time tuple into a Python datetime object.

    SATAID stores time in 8 integers; here only the first 6 are used:
        etim = (yy, yy, month, day, hour, minute, ...)
    """
    if not etim:
        return None
        
    try:
        tahun = int(str(etim[0]) + str(etim[1]))
        bulan = etim[2]
        hari = etim[3]
        jam = etim[4]
        menit = etim[5]

        dt = datetime(tahun, bulan, hari, jam, menit)
        
        # Round up to the next 10 minutes
        remainder = menit % 10
        if remainder > 0:
            dt = dt + timedelta(minutes=(10 - remainder))
        
        return dt
    except Exception:
        return None
