import math
from models import Location


def calculate_distance(location1: Location, location2: Location) -> float:
    R = 6378137

    # Convert degrees to radians
    phi1 = math.radians(location1.latitude)
    phi2 = math.radians(location2.latitude)
    delta_phi = math.radians(location2.latitude - location1.latitude)
    delta_lambda = math.radians(location2.longitude - location1.longitude)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance
