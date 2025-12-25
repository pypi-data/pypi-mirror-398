# Part of Day

This is an astral package wrapper, that uses it's calculations to give the part of day, instead of giving time intervals for spesific parts.

## Installation
To install, run the following command

```
pip install part-of-day
```

## Usage
```python
from part_of_day import PartOfDayCalculator

from datetime import datetime, timezone

pod = PartOfDayCalculator(latitude=15.33, longitude=-7)

# following methods gives results related to now, if a datetime is not given
pod.is_it_day()
# True
pod.is_it_night()
# False
pod.get_part_of_day()
# <PartOfDay.DAY: 'Day'>

# or they can be used with a datetime
dt = datetime(2025, 3, 12, 6, 13, 25, 0, timezone.utc)

pod.is_it_day(dt)
# False
pod.is_it_night(dt)
# True
pod.get_part_of_day(dt)
# <PartOfDay.NIGHT: 'Night'>
```

### Including twilights
By settings `include_twilights` flag in calculator's init, you can enable calculations for dusk and dawn (normally, both counts as night). Note that, if you do it, you should use `PartOfDayWithTwilights` enum in equality checks, and vice versa, in order to avoid incorrect equalities.
```python
from part_of_day import PartOfDayCalculator, PartOfDayWithTwilights, PartOfDay

from datetime import datetime, timezone

pod = PartOfDayCalculator(latitude=15.33, longitude=-7, include_twilights=True)

# following methods gives results related to now, if a datetime is not given
pod.is_it_day()
# True
pod.is_it_night()
# False
pod.is_it_dawn()
# False
pod.is_it_dusk()
# False
pod.get_part_of_day()
# <PartOfDayWithTwilights.DAY: 'Day'>
pod.get_part_of_day() == PartOfDayWithTwilights.NIGHT
# False
pod.get_part_of_day()==PartOfDay.NIGHT
# part_of_day.exceptions.MixedPartOfDayError: Checking equality between <PartOfDay> and <PartOfDayWithTwilights> enums could cause miscalculations. Please use <PartOfDayWithTwilights> enum if "include_twilights" is enabled
```