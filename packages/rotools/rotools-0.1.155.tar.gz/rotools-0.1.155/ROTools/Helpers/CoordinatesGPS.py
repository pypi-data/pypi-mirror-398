class CoordinatesGPS:
    def __init__(self, latitude, longitude):
        self.latitude = float(latitude)
        self.longitude = float(longitude)

    def __str__(self):
        return f"({self.latitude}, {self.longitude})"

    def __repr__(self):
        return self.__str__()
