class AeroNavXError(Exception):
    pass


class AirportNotFoundError(AeroNavXError):
    pass


class InvalidAirportCodeError(AeroNavXError):
    pass


class DataLoadError(AeroNavXError):
    pass


class RoutingError(AeroNavXError):
    pass


class WeatherDataError(AeroNavXError):
    pass
