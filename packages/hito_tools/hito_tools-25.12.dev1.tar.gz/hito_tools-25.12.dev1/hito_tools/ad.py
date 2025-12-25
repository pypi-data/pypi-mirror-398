import datetime


def convert_ad_datetime(timestamp):
    """
    Convert an AD timestamp to a standard one

    :param timestamp: AD timestamp
    :return: standard timestamp
    """
    return datetime.datetime(1601, 1, 1) + datetime.timedelta(seconds=int(timestamp) / 10000000)
