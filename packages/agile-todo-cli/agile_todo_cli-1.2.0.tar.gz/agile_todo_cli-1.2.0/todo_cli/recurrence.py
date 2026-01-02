"""Recurrence management for recurring tasks.

Handles parsing recurrence patterns, calculating next occurrences,
and managing recurring task lifecycle.
"""

import calendar
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from .models import RecurrencePattern, RecurrenceRule


@dataclass
class ParsedPattern:
    """Result of parsing a recurrence pattern string."""
    pattern: RecurrencePattern
    interval: int = 1
    days_of_week: Optional[list[str]] = None
    day_of_month: Optional[int] = None


# Day name mappings
DAY_NAMES = {
    'mon': 0, 'monday': 0,
    'tue': 1, 'tuesday': 1,
    'wed': 2, 'wednesday': 2,
    'thu': 3, 'thursday': 3,
    'fri': 4, 'friday': 4,
    'sat': 5, 'saturday': 5,
    'sun': 6, 'sunday': 6,
}

# Short day names for storage
SHORT_DAY_NAMES = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


class RecurrenceManager:
    """Manages recurrence patterns and occurrence generation.

    Handles parsing user-friendly recurrence patterns, calculating
    next occurrence dates, and determining when new occurrences
    should be created.
    """

    def parse_pattern(self, pattern_str: str) -> ParsedPattern:
        """Parse a recurrence pattern string into structured data.

        Supported patterns:
        - "daily" - Every day
        - "weekly" - Every week (same day)
        - "monthly" - Every month (same day of month)
        - "yearly" - Every year (same date)
        - "every N days" - Every N days
        - "every N weeks" - Every N weeks
        - "every mon,wed,fri" - Specific days of week
        - "every 2 weeks" - Every 2 weeks
        - "monthly on 15" - Monthly on the 15th

        Args:
            pattern_str: User-friendly pattern string

        Returns:
            ParsedPattern with structured recurrence data

        Raises:
            ValueError: If pattern cannot be parsed
        """
        pattern_str = pattern_str.lower().strip()

        # Simple patterns
        if pattern_str == 'daily':
            return ParsedPattern(pattern=RecurrencePattern.DAILY)

        if pattern_str == 'weekly':
            return ParsedPattern(pattern=RecurrencePattern.WEEKLY)

        if pattern_str == 'monthly':
            return ParsedPattern(pattern=RecurrencePattern.MONTHLY)

        if pattern_str == 'yearly':
            return ParsedPattern(pattern=RecurrencePattern.YEARLY)

        # "every N days/weeks/months/years"
        interval_match = re.match(
            r'every\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)$',
            pattern_str
        )
        if interval_match:
            interval = int(interval_match.group(1))
            unit = interval_match.group(2).rstrip('s')  # Normalize to singular

            pattern_map = {
                'day': RecurrencePattern.DAILY,
                'week': RecurrencePattern.WEEKLY,
                'month': RecurrencePattern.MONTHLY,
                'year': RecurrencePattern.YEARLY,
            }
            return ParsedPattern(
                pattern=pattern_map[unit],
                interval=interval
            )

        # "every mon,wed,fri" - specific days of week
        days_match = re.match(r'every\s+([a-z,]+)$', pattern_str)
        if days_match:
            days_str = days_match.group(1)
            days = [d.strip() for d in days_str.split(',')]

            # Validate all days
            parsed_days = []
            for day in days:
                if day not in DAY_NAMES:
                    raise ValueError(f"Invalid day name: {day}")
                # Store as short name
                parsed_days.append(SHORT_DAY_NAMES[DAY_NAMES[day]])

            if not parsed_days:
                raise ValueError("No valid days specified")

            return ParsedPattern(
                pattern=RecurrencePattern.CUSTOM,
                days_of_week=sorted(set(parsed_days), key=lambda d: DAY_NAMES[d])
            )

        # "monthly on N" - specific day of month
        monthly_match = re.match(r'monthly\s+on\s+(\d+)$', pattern_str)
        if monthly_match:
            day = int(monthly_match.group(1))
            if day < 1 or day > 31:
                raise ValueError(f"Invalid day of month: {day}")
            return ParsedPattern(
                pattern=RecurrencePattern.MONTHLY,
                day_of_month=day
            )

        raise ValueError(f"Cannot parse recurrence pattern: {pattern_str}")

    def get_next_occurrence(
        self,
        rule: RecurrenceRule,
        from_date: Optional[date] = None
    ) -> Optional[date]:
        """Calculate the next occurrence date for a recurrence rule.

        Args:
            rule: The recurrence rule
            from_date: Date to calculate from (defaults to today)

        Returns:
            Next occurrence date, or None if recurrence has ended
        """
        if not rule.is_active:
            return None

        if from_date is None:
            from_date = date.today()

        next_date = self._calculate_next_date(rule, from_date)

        # Check if next date exceeds end_date
        if rule.end_date and next_date:
            end_date_only = rule.end_date.date() if isinstance(rule.end_date, datetime) else rule.end_date
            if next_date > end_date_only:
                return None

        return next_date

    def _calculate_next_date(self, rule: RecurrenceRule, from_date: date) -> date:
        """Calculate raw next date without checking limits.

        Args:
            rule: The recurrence rule
            from_date: Date to calculate from

        Returns:
            Next occurrence date
        """
        if rule.pattern == RecurrencePattern.DAILY:
            return from_date + timedelta(days=rule.interval)

        if rule.pattern == RecurrencePattern.WEEKLY:
            return from_date + timedelta(weeks=rule.interval)

        if rule.pattern == RecurrencePattern.MONTHLY:
            return self._add_months(from_date, rule.interval, rule.day_of_month)

        if rule.pattern == RecurrencePattern.YEARLY:
            return self._add_years(from_date, rule.interval)

        if rule.pattern == RecurrencePattern.CUSTOM:
            return self._next_matching_day(from_date, rule.days_of_week or [])

        # Fallback
        return from_date + timedelta(days=1)

    def _add_months(
        self,
        from_date: date,
        months: int,
        target_day: Optional[int] = None
    ) -> date:
        """Add months to a date, handling month-end edge cases.

        Args:
            from_date: Starting date
            months: Number of months to add
            target_day: Specific day of month (or use from_date's day)

        Returns:
            New date with months added
        """
        target_day = target_day or from_date.day

        # Calculate target month and year
        month = from_date.month + months
        year = from_date.year

        while month > 12:
            month -= 12
            year += 1

        while month < 1:
            month += 12
            year -= 1

        # Handle days that don't exist in target month (e.g., Jan 31 -> Feb 28)
        max_day = calendar.monthrange(year, month)[1]
        day = min(target_day, max_day)

        return date(year, month, day)

    def _add_years(self, from_date: date, years: int) -> date:
        """Add years to a date, handling leap year edge cases.

        Args:
            from_date: Starting date
            years: Number of years to add

        Returns:
            New date with years added
        """
        target_year = from_date.year + years

        # Handle Feb 29 on non-leap years
        if from_date.month == 2 and from_date.day == 29:
            if not calendar.isleap(target_year):
                return date(target_year, 2, 28)

        return date(target_year, from_date.month, from_date.day)

    def _next_matching_day(
        self,
        from_date: date,
        days_of_week: list[str]
    ) -> date:
        """Find the next date matching one of the specified weekdays.

        Args:
            from_date: Starting date
            days_of_week: List of day names (e.g., ['mon', 'wed', 'fri'])

        Returns:
            Next matching date
        """
        if not days_of_week:
            return from_date + timedelta(days=1)

        # Convert day names to weekday numbers (0=Monday)
        target_weekdays = {DAY_NAMES[day] for day in days_of_week}

        # Start from tomorrow
        check_date = from_date + timedelta(days=1)

        # Find next matching day (max 7 days ahead)
        for _ in range(7):
            if check_date.weekday() in target_weekdays:
                return check_date
            check_date += timedelta(days=1)

        # Should never reach here if days_of_week is valid
        return from_date + timedelta(days=1)

    def should_create_occurrence(self, rule: RecurrenceRule) -> bool:
        """Check if a new occurrence should be created.

        Args:
            rule: The recurrence rule to check

        Returns:
            True if a new occurrence should be created
        """
        # Check limits
        if rule.has_reached_limit:
            return False

        if rule.has_expired:
            return False

        return True

    def format_pattern(self, rule: RecurrenceRule) -> str:
        """Format a recurrence rule as a human-readable string.

        Args:
            rule: The recurrence rule

        Returns:
            Human-readable pattern description
        """
        if rule.pattern == RecurrencePattern.DAILY:
            if rule.interval == 1:
                return "daily"
            return f"every {rule.interval} days"

        if rule.pattern == RecurrencePattern.WEEKLY:
            if rule.interval == 1:
                return "weekly"
            return f"every {rule.interval} weeks"

        if rule.pattern == RecurrencePattern.MONTHLY:
            if rule.day_of_month:
                if rule.interval == 1:
                    return f"monthly on {rule.day_of_month}"
                return f"every {rule.interval} months on {rule.day_of_month}"
            if rule.interval == 1:
                return "monthly"
            return f"every {rule.interval} months"

        if rule.pattern == RecurrencePattern.YEARLY:
            if rule.interval == 1:
                return "yearly"
            return f"every {rule.interval} years"

        if rule.pattern == RecurrencePattern.CUSTOM:
            if rule.days_of_week:
                days = ','.join(rule.days_of_week)
                return f"every {days}"
            return "custom"

        return str(rule.pattern)

    def serialize_days_of_week(self, days: list[str]) -> str:
        """Serialize days of week list to JSON for storage.

        Args:
            days: List of day names

        Returns:
            JSON string
        """
        return json.dumps(days)

    def deserialize_days_of_week(self, data: Optional[str]) -> Optional[list[str]]:
        """Deserialize days of week from JSON storage.

        Args:
            data: JSON string or None

        Returns:
            List of day names or None
        """
        if not data:
            return None
        return json.loads(data)

    def create_occurrence(
        self,
        db,  # Database instance (avoid circular import)
        task_id: int,
        from_date: Optional[date] = None
    ) -> Optional['Todo']:
        """Create the next occurrence of a recurring task.

        This method creates a new task instance based on a recurring task's
        template and its recurrence rule. The new task inherits properties
        from the original (priority, project, tags) and gets a calculated
        due date based on the recurrence pattern.

        Args:
            db: Database instance for creating the new task
            task_id: ID of the recurring task to generate from
            from_date: Date to calculate next occurrence from (defaults to today)

        Returns:
            The newly created Todo, or None if:
            - Task doesn't exist
            - Task has no recurrence rule
            - Recurrence has reached its limit (max_occurrences)
            - Recurrence has expired (end_date passed)
        """
        from .models import Todo  # Import here to avoid circular

        # Get the template task
        template_task = db.get(task_id)
        if not template_task:
            return None

        # Get the recurrence rule
        rule = db.get_recurrence_rule_by_task(task_id)
        if not rule:
            return None

        # Check if we should create a new occurrence
        if not self.should_create_occurrence(rule):
            return None

        # Calculate next due date
        base_date = from_date or date.today()
        if template_task.due_date:
            # Use task's due date if it exists
            base_date = template_task.due_date.date() if isinstance(
                template_task.due_date, datetime
            ) else template_task.due_date

        next_due_date = self.get_next_occurrence(rule, base_date)
        if not next_due_date:
            return None

        # Convert date to datetime for storage
        next_due_datetime = datetime.combine(next_due_date, datetime.min.time())

        # Create the new occurrence with same properties
        new_task = db.add(
            task=template_task.task,
            priority=template_task.priority,
            project=template_task.project,
            project_id=template_task.project_id,
            tags=template_task.tags.copy() if template_task.tags else [],
            due_date=next_due_datetime
        )

        # Update the recurrence rule's occurrence count
        rule.occurrences_created += 1
        db.update_recurrence_rule(rule)

        return new_task
