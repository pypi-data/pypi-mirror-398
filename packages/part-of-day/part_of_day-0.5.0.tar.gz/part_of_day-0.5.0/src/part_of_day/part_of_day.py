from datetime import datetime, timezone
from enum import Enum

from astral import Observer
from astral.sun import sun

from part_of_day.exceptions import PartOfDayCalculationError, TwilightsNotIncludedError


class PartOfDay(str, Enum):
    DAY = "Day"
    NIGHT = "Night"
    DAWN = "Dawn"
    DUSK = "Dusk"


class PartOfDayCalculator:
    def __init__(self, latitude: int | float, longitude: int | float, include_twilights=False) -> None:
        self.observer = Observer(latitude=latitude, longitude=longitude)
        self.include_twilights = include_twilights
        if include_twilights:
            self.get_part_of_day = self._get_part_of_day_with_twilights
        else:
            self.get_part_of_day = self._get_part_of_day

    def _get_part_of_day(self, dt: datetime | None = None) -> PartOfDay:
        if dt is None:
            dt = datetime.now(timezone.utc)

        try:
            times_of_day = sun(self.observer, dt)
        except ValueError as e:
            if len(e.args) > 0:
                if e.args[0] == "Sun never reaches 6 degrees below the horizon, at this location.":
                    return PartOfDay.DAY
                elif e.args[0] == "Sun is always below the horizon on this day, at this location.":
                    return PartOfDay.NIGHT
            raise

        current_time = dt.time()

        if times_of_day["sunrise"].time() <= current_time and current_time <= times_of_day["sunset"].time():
            return PartOfDay.DAY
        elif current_time <= times_of_day["sunrise"] or times_of_day["sunset"] <= current_time:
            return PartOfDay.NIGHT

        raise PartOfDayCalculationError

    def _get_part_of_day_with_twilights(self, dt: datetime | None = None) -> PartOfDay:
        if dt is None:
            dt = datetime.now(timezone.utc)

        try:
            times_of_day = sun(self.observer, dt)
        except ValueError as e:
            if len(e.args) > 0:
                if e.args[0] == "Sun never reaches 6 degrees below the horizon, at this location.":
                    return PartOfDay.DAY
                elif e.args[0] == "Sun is always below the horizon on this day, at this location.":
                    return PartOfDay.NIGHT
            raise

        current_time = dt.time()

        if current_time <= times_of_day["dawn"].time() or times_of_day["dusk"].time() <= current_time:
            return PartOfDay.NIGHT
        elif times_of_day["dawn"].time() <= current_time <= times_of_day["sunrise"].time():
            return PartOfDay.DAWN
        elif times_of_day["sunrise"].time() <= current_time <= times_of_day["sunset"].time():
            return PartOfDay.DAY
        elif times_of_day["sunset"].time() <= current_time <= times_of_day["dusk"].time():
            return PartOfDay.DUSK

        raise PartOfDayCalculationError

    def is_it_day(self, dt: datetime | None = None) -> bool:
        if dt is None:
            dt = datetime.now(timezone.utc)

        return self.get_part_of_day(dt) == PartOfDay.DAY

    def is_it_night(self, dt: datetime | None = None) -> bool:
        if dt is None:
            dt = datetime.now(timezone.utc)

        return self.get_part_of_day(dt) == PartOfDay.NIGHT

    def is_it_dawn(self, dt: datetime | None = None) -> bool:
        if not self.include_twilights:
            raise TwilightsNotIncludedError

        if dt is None:
            dt = datetime.now(timezone.utc)

        return self.get_part_of_day(dt) == PartOfDay.DAWN

    def is_it_dusk(self, dt: datetime | None = None) -> bool:
        if not self.include_twilights:
            raise TwilightsNotIncludedError

        if dt is None:
            dt = datetime.now(timezone.utc)

        return self.get_part_of_day(dt) == PartOfDay.DUSK
