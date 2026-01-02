__version__ = "1.1.0"

class CQCalendar:
	def __init__(
		self, 
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
		debug_callbacks=False
	):
		self.minutes_per_tick = max(1, int(minutes_per_tick))
		
		self.months = [
			("January", 31),
			("February", 28),
			("March", 31),
			("April", 30),
			("May", 31),
			("June", 30),
			("July", 31),
			("August", 31),
			("September", 30),
			("October", 31),
			("November", 30),
			("December", 31),
		]
		
		self.weekdays = [
			"Monday",
			"Tuesday",
			"Wednesday",
			"Thursday",
			"Friday",
			"Saturday",
			"Sunday",
		]
		
		self._on_hour = []
		self._on_day = []
		self._on_month = []
		self._on_year = []
		
		self.synodic_month_days = 29.530588
		
		self.moon_age_days = float(moon_age_days) % self.synodic_month_days
		
		if moon_phase is not None:
			self.set_moon_phase(moon_phase)
			
		else:
			self.moon_age_days = float(moon_age_days) % self.synodic_month_days
		
		self.set_time(hour=hour, minute=minute, is_pm=is_pm)
		self.set_date(day=day, month=month, year=year)
		self.set_weekday(weekday)
		
		self.debug_callbacks = bool(debug_callbacks)
		
	def __repr__(self):
		return f"<CQCalendar {self.date_string()} {self.time_string()}>"
		
	def on_hour(self, callback):
		self._on_hour.append(callback)
		
		return callback
		
	def on_day(self, callback):
		self._on_day.append(callback)
		
		return callback
		
	def on_month(self, callback):
		self._on_month.append(callback)
		
		return callback
		
	def on_year(self, callback):
		self._on_year.append(callback)
		
		return callback
		
	def off_hour(self, callback):
		if callback in self._on_hour:
			self._on_hour.remove(callback)
			
	def off_day(self, callback):
		if callback in self._on_day:
			self._on_day.remove(callback)

	def off_month(self, callback):
		if callback in self._on_month:
			self._on_month.remove(callback)
			
	def off_year(self, callback):
		if callback in self._on_year:
			self._on_year.remove(callback)
			
	def _emit(self, callbacks):
		for cb in list(callbacks):
			try:
				cb(self)
				
			except Exception as e:
				if self.debug_callbacks:
					raise
		
	def set_time(self, hour=9, minute=0, is_pm=False):
		hour = int(hour)
		minute = int(minute)
		
		if hour < 1: hour = 1
		if hour > 12: hour = 12
		
		if minute < 0: minute = 0
		if minute > 59: minute = 59
		
		self.hour = hour
		self.minute = minute
		self.is_pm = bool(is_pm)
		
	def set_date(self, day=1, month=1, year=1):
		month = int(month)
		day = int(day)
		year = int(year)
		
		month = max(1, min(month, len(self.months)))
		year = max(1, year)
		
		days_in_month = self.days_in_month(month, year)
		day = max(1, min(day, days_in_month))
		
		self.day = day
		self.month = month
		self.year = year
		
	def update(self, ticks=1):
		self.add_minutes(int(ticks) * self.minutes_per_tick)
		
	def add_minutes(self, minutes: int):
		minutes = int(minutes)
		
		if minutes == 0:
			return
			
		if minutes < 0:
			raise ValueError("add_minutes does not support negative values.")
			
		self.advance_moon_by_minutes(minutes)	
			
		self.minute += minutes
		
		while self.minute >= 60:
			self.minute -= 60
			self.advance_hour()
			
	def add_hours(self, hours: int):
		hours = int(hours)
		
		if hours == 0:
			return
			
		if hours < 0:
			raise ValueError("add_hours does not support negative values.")
			
		self.add_minutes(hours * 60)
		
	def add_days(self, days: int):
		days = int(days)
		
		if days == 0:
			return
			
		if days < 0:
			raise ValueError("add_days does not support negative values.")
			
		for _ in range(days):
			self.advance_day()
			
	def add_months(self, months: int):
		months = int(months)
		
		if months == 0:
			return
			
		if months < 0:
			raise ValueError("add_months does not support negative values.")
			
		for _ in range(months):
			self.advance_month()
			
		self.clamp_day_to_month()
			
	def add_years(self, years: int):
		years = int(years)
		
		if years == 0:
			return
			
		if years < 0:
			raise ValueError("add_years does not support negative values.")
			
		self.year += years
		
		self.clamp_day_to_month()
		
	def add(self, minutes=0, hours=0, days=0, months=0, years=0):
		if years: self.add_years(years)
		if months: self.add_months(months)
		if days: self.add_days(days)
		if hours: self.add_hours(hours)
		if minutes: self.add_minutes(minutes)
			
	def advance_hour(self):
		if self.hour == 11:
			self.hour = 12
			
			self.is_pm = not self.is_pm
			
			if not self.is_pm:
				self.advance_day()
			
		elif self.hour == 12:
			self.hour = 1
			
		else:
			self.hour += 1
			
		self._emit(self._on_hour)
			
	def advance_day(self):
		days_in_month = self.days_in_month(self.month, self.year)
		
		self.day += 1
		
		self.moon_age_days = (self.moon_age_days + 1.0) % self.synodic_month_days
		
		if self.day > days_in_month:
			self.day = 1
			self.advance_month()
			
		self.weekday = (self.weekday + 1) % 7
			
		self._emit(self._on_day)	
			
	def advance_month(self):
		self.month += 1
		
		if self.month > len(self.months):
			self.month = 1
			self.advance_year()
			
		self.clamp_day_to_month()
		
		self._emit(self._on_month)
		
	def advance_year(self):
		self.year += 1
		
		self._emit(self._on_year)
		
	def advance_moon_by_minutes(self, minutes: int):
		days = minutes / (60.0 * 24.0)
		
		self.moon_age_days = (self.moon_age_days + days) % self.synodic_month_days
			
	def is_leap_year(self, year=None) -> bool:
		if year is None:
			year = self.year
			
		year = int(year)
		
		if year % 400 == 0:
			return True
			
		if year % 100 == 0:
			return False
			
		return year % 4 == 0
		
	def days_in_month(self, month=None, year=None) -> int:
		if month is None:
			month = self.month
			
		if year is None:
			year = self.year
			
		month = int(month)
		year = int(year)
		
		if month == 2:
			return 29 if self.is_leap_year(year) else 28
			
		_, base_days = self.months[month - 1]
		
		return base_days
		
	def clamp_day_to_month(self):
		dim = self.days_in_month(self.month, self.year)
		
		if self.day > dim:
			self.day = dim
			
	def set_weekday(self, weekday=0):
		if weekday is None:
			weekday = 0
			
		self.weekday = int(weekday) % 7
	
	def weekday_name(self):
		return self.weekdays[self.weekday]
		
	def moon_phase_name(self):
		phase = self.moon_age_days / self.synodic_month_days
		
		index = int((phase * 8) + 0.5) % 8
		
		return [
			"New Moon",
			"Waxing Crescent",
			"First Quarter",
			"Waxing Gibbous",
			"Full Moon",
			"Waning Gibbous",
			"Last Quarter",
			"Waning Crescent",
		][index]
		
	def moon_illumination(self):
		import math
		
		phase_angle = (self.moon_age_days / self.synodic_month_days) * 2.0 * math.pi
		
		return 0.5 * (1.0 - math.cos(phase_angle))
		
	def set_moon_phase(self, phase_name):
		phases = [
			"New Moon",
			"Waxing Crescent",
			"First Quarter",
			"Waxing Gibbous",
			"Full Moon",
			"Waning Gibbous",
			"Last Quarter",
			"Waning Crescent",
		]
		
		if isinstance(phase_name, str):
			phase_name = phase_name.strip().title()
			
			if phase_name not in phases:
				raise ValueError(f"Invalid phase name: {phase_name}")
				
			index = phases.index(phase_name)
			
		else:
			index = int(phase_name) % 8
			
		self.moon_age_days = (index / 8) * self.synodic_month_days
		
		return self.moon_age_days
			
	def time_string(self):
		return f"{self.hour}:{self.minute:02d} {'PM' if self.is_pm else 'AM'}"
		
	def date_string(self):
		month_name, _ = self.months[self.month - 1]
		return f"{self.weekday_name()}, {month_name} {self.day}, Year {self.year}"
		
	def datetime_string(self):
		return f"{self.date_string()} at {self.time_string()}"
		
if __name__ == "__main__":
	calendar = CQCalendar(day=31, month=1, year=2024, weekday=0, moon_phase="Full Moon")
	
	def restock_shops(calendar):
		if calendar.hour == 6 and not calendar.is_pm:
			print("[EVENT] Shops restocked!")
			
	def payday(calendar):
		if calendar.day == 1:
			print("[EVENT] Rent due!")
			
	calendar.on_hour(restock_shops)
	calendar.on_day(payday)
	
	for i in range(48):
		print(calendar.datetime_string(), calendar.moon_phase_name(), round(calendar.moon_illumination(), 2))
		calendar.add_hours(1)