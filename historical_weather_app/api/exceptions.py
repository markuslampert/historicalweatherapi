
class NoDbEntriesForRequestException404(Exception):
    pass


class StartDateAfterEndDateException400(Exception):
    pass


class MoreThan10WeatherStationsException400(Exception):
    pass


class WrongParameterException400(Exception):
    pass
