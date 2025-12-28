class TwilightsNotIncludedError(Exception):
    def __init__(self):
        super().__init__(
            'you must set "include_twilights" flag in PartOfDayCalculator initialization in order to get dusk and dawn times',
        )


class PartOfDayCalculationError(Exception):
    def __init__(self):
        super().__init__("Part of day could not be calculated")
