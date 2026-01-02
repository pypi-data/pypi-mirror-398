# CQCalendar v1.1.0
CQCalendar is a lightweight, tick-based time and calendar system for Python games and simulations.

It is designed for RPGs, sandbox sims, and systemic games, where time drives world behavior rather than just displaying a UI clock.

***
## Features
* Tick-based and absolute time progression
* Gregorian calendar with leap year support
* Weekday tracking
* Synodic lunar cycle (moon phases & illumination)
* Event callbacks for hour/day/month/year changes
* Designed for decoupled, systemic game logic
* No external dependencies

***
## Installation
You can install CQCalendar using [pip](https://pypi.org/project/cqcalendar/).

```
pip install cqcalendar
```
***

## How to Create a Calendar for Your Game
```
import cqcalendar

calendar = cqcalendar.CQCalendar(
  hour=9,
  minute=0,
  is_pm=False,
  minutes_per_tick=1,
  day=1,
  month=1,
  year=1,
  weekday=0,
  moon_age_days=0.0,
  moon_phase=None,
  debug_callbacks=False,
)
```

***
## Time

### How to Display Current Time
```
print(calendar.time_string())
```

### How to Change Time
```
calendar.set_time(hour=12, minute=0, is_pm=True)
```

### How to Increment Time
```
calendar.update(ticks=10)
```

***
## Date

### How to Display Current Date
```
print(calendar.date_string())
```

### How to Change Date
```
calendar.set_date(day=31, month=12, year=1)
```
***

## Absolute Time Advancement
You can advance time directly without ticks.

```
calendar.add_minutes(30)
calendar.add_hours(6)
calendar.add_days(1)
calendar.add_months(1)
calendar.add_years(1)
```

Or you can do it in a single method.

```
calendar.add(days=3, hours=4)
```

***
## Weekdays
Weekdays are zero-indexed (0 = Monday, 6 = Sunday).

### How to Display Weekday
```
print(calendar.weekday_name())
```

### How to Change Weekday
```
calendar.set_weekday(weekday=1)
```

***
## Lunar Cycle
CQCalendar includes a synodic lunar cycle (approximately 29.53 days)

### How to Display Moon Phase
```
print(calendar.moon_phase_name())
```

### How to Set Moon Phase
```
calendar.set_moon_phase("Waning Crescent")
```

The above is an alternative to using ```moon_age_days```:
```
# Precise numeric control still supported
calendar = CQCalendar(moon_age_days=14.77) # Full Moon
```

If both ```moon_phase``` and ```moon_age_days``` are provided, ```moon_phase``` takes priority.

### How to Get Moon Illumination
```
print(calendar.moon_illumination())
```

Useful for:
* werewolf systems
* rituals
* night visibility
* tides or magic strength

***
## Callbacks (Events)
CQCalendar allows systems to react to time changes using callbacks.

Callbacks are triggered when time crosses a boundary (hour/day/month/year), not continuously.

### Hourly Event
```
def restock_shops(calendar):
  if calendar.hour == 6 and not calendar.is_pm:
    print("Shops restocked!")

calendar.on_hour(restock_shops)
```

### Daily Event
```
def payday(calendar):
  if calendar.day == 1:
    print("Rent is due!")

calendar.on_day(payday)
```

Available callbacks:
* on_hour
* on_day
* on_month
* on_year

***
## Misc.

### How to Display Current Date and Time
```
print(calendar.datetime_string())
```

***
## Related Libraries
* [TerraForge](https://github.com/BriannaLadson/TerraForge): A versatile Python toolset for procedural map generation.
