import re
from typing import Literal

re_chemistry = re.compile(".+-appb-C[0-9]+")
re_figure = re.compile(".+-(appb|jpdrab)-D[0-9]+")
re_math = re.compile(".+-appb-M[0-9]+")
re_table = re.compile(".+-appb-T[0-9]+")
re_appb_image = re.compile(".+-appb-I[0-9]+")
re_jpbibl = re.compile(".+-jpbibl-I[0-9]+")
re_jpfolb = re.compile(".+-jpfolb-I[0-9]+")
re_power_of_attorney = re.compile("JPOXMLDOC[0-9]+-poat-I[0-9]+")
re_bio = re.compile("JPOXMLDOC[0-9]+-biod-I[0-9]+")
re_lack_sign = re.compile("JPOXMLDOC[0-9]+-lacs-I[0-9]+")
re_jpothd = re.compile("JPOXMLDOC[0-9]+-jpothd-I[0-9]+")
re_offline_jpseql = re.compile("[0-9]-jpseql-I[0-9]+")
re_online_jpseql = re.compile("JPOXMLDOC01-jpseql-I[0-9]+")
re_online_jpatta = re.compile("JPOXMLDOC01-jpatta-I[0-9]+")
re_jpntce = re.compile("[0-9]+-jpntce-I[0-9]+")


def detect_image_kind(
    image_name: str,
) -> Literal["chemistry", "figure", "math", "table", "image", "unknown"]:
    """detect image kind from image name

    Args:
        image_name (str): image name"""
    if re_chemistry.match(image_name):
        return "chemistry"
    elif re_figure.match(image_name):
        return "figure"
    elif re_math.match(image_name):
        return "math"
    elif re_table.match(image_name):
        return "table"
    elif (
        re_appb_image.match(image_name)
        or re_jpbibl.match(image_name)
        or re_jpfolb.match(image_name)
        or re_power_of_attorney.match(image_name)
        or re_bio.match(image_name)
        or re_lack_sign.match(image_name)
        or re_jpothd.match(image_name)
        or re_offline_jpseql.match(image_name)
        or re_online_jpseql.match(image_name)
        or re_online_jpatta.match(image_name)
        or re_jpntce.match(image_name)
    ):
        return "image"
    else:
        return "unknown"
