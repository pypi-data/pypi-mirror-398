"""Tests for RecurrenceManager and recurrence pattern handling."""

import pytest
from datetime import date, datetime, timedelta

from todo_cli.models import RecurrencePattern, RecurrenceRule
from todo_cli.recurrence import RecurrenceManager, ParsedPattern


class TestParsePattern:
    """Tests for RecurrenceManager.parse_pattern()."""

    @pytest.fixture
    def manager(self) -> RecurrenceManager:
        return RecurrenceManager()

    # Simple patterns
    def test_parse_daily(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("daily")
        assert result.pattern == RecurrencePattern.DAILY
        assert result.interval == 1

    def test_parse_weekly(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("weekly")
        assert result.pattern == RecurrencePattern.WEEKLY
        assert result.interval == 1

    def test_parse_monthly(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("monthly")
        assert result.pattern == RecurrencePattern.MONTHLY
        assert result.interval == 1

    def test_parse_yearly(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("yearly")
        assert result.pattern == RecurrencePattern.YEARLY
        assert result.interval == 1

    # Case insensitivity
    def test_parse_case_insensitive(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("DAILY")
        assert result.pattern == RecurrencePattern.DAILY

        result = manager.parse_pattern("Weekly")
        assert result.pattern == RecurrencePattern.WEEKLY

    def test_parse_with_whitespace(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("  daily  ")
        assert result.pattern == RecurrencePattern.DAILY

    # Interval patterns
    def test_parse_every_n_days(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("every 3 days")
        assert result.pattern == RecurrencePattern.DAILY
        assert result.interval == 3

    def test_parse_every_1_day(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("every 1 day")
        assert result.pattern == RecurrencePattern.DAILY
        assert result.interval == 1

    def test_parse_every_n_weeks(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("every 2 weeks")
        assert result.pattern == RecurrencePattern.WEEKLY
        assert result.interval == 2

    def test_parse_every_1_week(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("every 1 week")
        assert result.pattern == RecurrencePattern.WEEKLY
        assert result.interval == 1

    def test_parse_every_n_months(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("every 6 months")
        assert result.pattern == RecurrencePattern.MONTHLY
        assert result.interval == 6

    def test_parse_every_n_years(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("every 5 years")
        assert result.pattern == RecurrencePattern.YEARLY
        assert result.interval == 5

    # Days of week patterns
    def test_parse_specific_days(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("every mon,wed,fri")
        assert result.pattern == RecurrencePattern.CUSTOM
        assert result.days_of_week == ['mon', 'wed', 'fri']

    def test_parse_single_day(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("every mon")
        assert result.pattern == RecurrencePattern.CUSTOM
        assert result.days_of_week == ['mon']

    def test_parse_full_day_names(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("every monday,wednesday")
        assert result.pattern == RecurrencePattern.CUSTOM
        assert result.days_of_week == ['mon', 'wed']

    def test_parse_weekend(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("every sat,sun")
        assert result.pattern == RecurrencePattern.CUSTOM
        assert result.days_of_week == ['sat', 'sun']

    def test_parse_days_sorted(self, manager: RecurrenceManager) -> None:
        # Days should be sorted by weekday order
        result = manager.parse_pattern("every fri,mon,wed")
        assert result.days_of_week == ['mon', 'wed', 'fri']

    def test_parse_days_deduplicated(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("every mon,mon,tue")
        assert result.days_of_week == ['mon', 'tue']

    # Monthly on specific day
    def test_parse_monthly_on_day(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("monthly on 15")
        assert result.pattern == RecurrencePattern.MONTHLY
        assert result.day_of_month == 15

    def test_parse_monthly_on_first(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("monthly on 1")
        assert result.pattern == RecurrencePattern.MONTHLY
        assert result.day_of_month == 1

    def test_parse_monthly_on_last_day(self, manager: RecurrenceManager) -> None:
        result = manager.parse_pattern("monthly on 31")
        assert result.pattern == RecurrencePattern.MONTHLY
        assert result.day_of_month == 31

    # Error cases
    def test_parse_invalid_pattern(self, manager: RecurrenceManager) -> None:
        with pytest.raises(ValueError, match="Cannot parse"):
            manager.parse_pattern("invalid pattern")

    def test_parse_invalid_day_name(self, manager: RecurrenceManager) -> None:
        with pytest.raises(ValueError, match="Invalid day name"):
            manager.parse_pattern("every xyz")

    def test_parse_monthly_invalid_day(self, manager: RecurrenceManager) -> None:
        with pytest.raises(ValueError, match="Invalid day of month"):
            manager.parse_pattern("monthly on 32")

    def test_parse_monthly_day_zero(self, manager: RecurrenceManager) -> None:
        with pytest.raises(ValueError, match="Invalid day of month"):
            manager.parse_pattern("monthly on 0")


class TestGetNextOccurrence:
    """Tests for RecurrenceManager.get_next_occurrence()."""

    @pytest.fixture
    def manager(self) -> RecurrenceManager:
        return RecurrenceManager()

    def _make_rule(
        self,
        pattern: RecurrencePattern,
        interval: int = 1,
        days_of_week: list[str] | None = None,
        day_of_month: int | None = None,
        end_date: datetime | None = None,
        max_occurrences: int | None = None,
        occurrences_created: int = 0
    ) -> RecurrenceRule:
        return RecurrenceRule(
            id=1,
            task_id=1,
            pattern=pattern,
            interval=interval,
            days_of_week=days_of_week,
            day_of_month=day_of_month,
            end_date=end_date,
            max_occurrences=max_occurrences,
            occurrences_created=occurrences_created
        )

    # Daily patterns
    def test_daily_next_occurrence(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.DAILY)
        from_date = date(2025, 1, 15)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 1, 16)

    def test_daily_interval_3(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.DAILY, interval=3)
        from_date = date(2025, 1, 15)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 1, 18)

    # Weekly patterns
    def test_weekly_next_occurrence(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.WEEKLY)
        from_date = date(2025, 1, 15)  # Wednesday
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 1, 22)

    def test_weekly_interval_2(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.WEEKLY, interval=2)
        from_date = date(2025, 1, 15)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 1, 29)

    # Monthly patterns
    def test_monthly_next_occurrence(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.MONTHLY)
        from_date = date(2025, 1, 15)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 2, 15)

    def test_monthly_on_specific_day(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.MONTHLY, day_of_month=20)
        from_date = date(2025, 1, 15)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 2, 20)

    def test_monthly_end_of_month_edge_case(self, manager: RecurrenceManager) -> None:
        # Jan 31 -> Feb should be Feb 28 (or 29 in leap year)
        rule = self._make_rule(RecurrencePattern.MONTHLY)
        from_date = date(2025, 1, 31)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 2, 28)

    def test_monthly_february_leap_year(self, manager: RecurrenceManager) -> None:
        # 2024 is a leap year
        rule = self._make_rule(RecurrencePattern.MONTHLY)
        from_date = date(2024, 1, 31)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2024, 2, 29)

    def test_monthly_day_31_to_30_day_month(self, manager: RecurrenceManager) -> None:
        # Day 31 in month with 30 days -> 30
        rule = self._make_rule(RecurrencePattern.MONTHLY, day_of_month=31)
        from_date = date(2025, 3, 15)  # Next is April (30 days)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 4, 30)

    def test_monthly_interval_3(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.MONTHLY, interval=3)
        from_date = date(2025, 1, 15)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 4, 15)

    def test_monthly_crosses_year(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.MONTHLY)
        from_date = date(2025, 12, 15)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2026, 1, 15)

    # Yearly patterns
    def test_yearly_next_occurrence(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.YEARLY)
        from_date = date(2025, 6, 15)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2026, 6, 15)

    def test_yearly_leap_day(self, manager: RecurrenceManager) -> None:
        # Feb 29 in leap year -> Feb 28 in non-leap year
        rule = self._make_rule(RecurrencePattern.YEARLY)
        from_date = date(2024, 2, 29)  # 2024 is leap year
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 2, 28)  # 2025 is not leap year

    def test_yearly_leap_day_to_leap_year(self, manager: RecurrenceManager) -> None:
        # Feb 29 -> next leap year Feb 29
        rule = self._make_rule(RecurrencePattern.YEARLY, interval=4)
        from_date = date(2024, 2, 29)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2028, 2, 29)

    def test_yearly_interval_5(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.YEARLY, interval=5)
        from_date = date(2025, 6, 15)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2030, 6, 15)

    # Custom patterns (days of week)
    def test_custom_mon_wed_fri(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(
            RecurrencePattern.CUSTOM,
            days_of_week=['mon', 'wed', 'fri']
        )
        # Monday Jan 13 -> next is Wednesday Jan 15
        from_date = date(2025, 1, 13)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 1, 15)  # Wednesday

    def test_custom_friday_to_monday(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(
            RecurrencePattern.CUSTOM,
            days_of_week=['mon', 'wed', 'fri']
        )
        # Friday Jan 17 -> next is Monday Jan 20
        from_date = date(2025, 1, 17)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 1, 20)  # Monday

    def test_custom_single_day(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(
            RecurrencePattern.CUSTOM,
            days_of_week=['tue']
        )
        # Monday Jan 13 -> next Tuesday Jan 14
        from_date = date(2025, 1, 13)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 1, 14)

    def test_custom_same_day_goes_to_next_week(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(
            RecurrencePattern.CUSTOM,
            days_of_week=['mon']
        )
        # Monday Jan 13 -> next Monday Jan 20
        from_date = date(2025, 1, 13)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 1, 20)

    def test_custom_empty_days(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(
            RecurrencePattern.CUSTOM,
            days_of_week=[]
        )
        from_date = date(2025, 1, 15)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 1, 16)  # Fallback to next day

    # End date limits
    def test_end_date_not_exceeded(self, manager: RecurrenceManager) -> None:
        # Use future dates relative to test execution
        future_end = datetime.now() + timedelta(days=30)
        from_date = date.today()
        rule = self._make_rule(
            RecurrencePattern.DAILY,
            end_date=future_end
        )
        result = manager.get_next_occurrence(rule, from_date)
        expected = from_date + timedelta(days=1)
        assert result == expected

    def test_end_date_exceeded(self, manager: RecurrenceManager) -> None:
        # Use past end date to trigger expiration
        past_end = datetime.now() - timedelta(days=1)
        rule = self._make_rule(
            RecurrencePattern.DAILY,
            end_date=past_end
        )
        from_date = date.today()
        result = manager.get_next_occurrence(rule, from_date)
        assert result is None

    # Occurrence limits
    def test_max_occurrences_not_reached(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(
            RecurrencePattern.DAILY,
            max_occurrences=10,
            occurrences_created=5
        )
        from_date = date(2025, 1, 15)
        result = manager.get_next_occurrence(rule, from_date)
        assert result == date(2025, 1, 16)

    def test_max_occurrences_reached(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(
            RecurrencePattern.DAILY,
            max_occurrences=10,
            occurrences_created=10
        )
        from_date = date(2025, 1, 15)
        result = manager.get_next_occurrence(rule, from_date)
        assert result is None

    # Default from_date
    def test_default_from_date(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.DAILY)
        result = manager.get_next_occurrence(rule)
        expected = date.today() + timedelta(days=1)
        assert result == expected


class TestShouldCreateOccurrence:
    """Tests for RecurrenceManager.should_create_occurrence()."""

    @pytest.fixture
    def manager(self) -> RecurrenceManager:
        return RecurrenceManager()

    def _make_rule(
        self,
        max_occurrences: int | None = None,
        occurrences_created: int = 0,
        end_date: datetime | None = None
    ) -> RecurrenceRule:
        return RecurrenceRule(
            id=1,
            task_id=1,
            pattern=RecurrencePattern.DAILY,
            max_occurrences=max_occurrences,
            occurrences_created=occurrences_created,
            end_date=end_date
        )

    def test_should_create_no_limits(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule()
        assert manager.should_create_occurrence(rule) is True

    def test_should_create_under_max(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(max_occurrences=10, occurrences_created=5)
        assert manager.should_create_occurrence(rule) is True

    def test_should_not_create_at_max(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(max_occurrences=10, occurrences_created=10)
        assert manager.should_create_occurrence(rule) is False

    def test_should_not_create_over_max(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(max_occurrences=10, occurrences_created=15)
        assert manager.should_create_occurrence(rule) is False

    def test_should_create_before_end_date(self, manager: RecurrenceManager) -> None:
        future = datetime.now() + timedelta(days=30)
        rule = self._make_rule(end_date=future)
        assert manager.should_create_occurrence(rule) is True

    def test_should_not_create_after_end_date(self, manager: RecurrenceManager) -> None:
        past = datetime.now() - timedelta(days=1)
        rule = self._make_rule(end_date=past)
        assert manager.should_create_occurrence(rule) is False


class TestFormatPattern:
    """Tests for RecurrenceManager.format_pattern()."""

    @pytest.fixture
    def manager(self) -> RecurrenceManager:
        return RecurrenceManager()

    def _make_rule(
        self,
        pattern: RecurrencePattern,
        interval: int = 1,
        days_of_week: list[str] | None = None,
        day_of_month: int | None = None
    ) -> RecurrenceRule:
        return RecurrenceRule(
            id=1,
            task_id=1,
            pattern=pattern,
            interval=interval,
            days_of_week=days_of_week,
            day_of_month=day_of_month
        )

    def test_format_daily(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.DAILY)
        assert manager.format_pattern(rule) == "daily"

    def test_format_daily_interval(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.DAILY, interval=3)
        assert manager.format_pattern(rule) == "every 3 days"

    def test_format_weekly(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.WEEKLY)
        assert manager.format_pattern(rule) == "weekly"

    def test_format_weekly_interval(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.WEEKLY, interval=2)
        assert manager.format_pattern(rule) == "every 2 weeks"

    def test_format_monthly(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.MONTHLY)
        assert manager.format_pattern(rule) == "monthly"

    def test_format_monthly_on_day(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.MONTHLY, day_of_month=15)
        assert manager.format_pattern(rule) == "monthly on 15"

    def test_format_monthly_interval_on_day(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(
            RecurrencePattern.MONTHLY, interval=3, day_of_month=15
        )
        assert manager.format_pattern(rule) == "every 3 months on 15"

    def test_format_monthly_interval(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.MONTHLY, interval=6)
        assert manager.format_pattern(rule) == "every 6 months"

    def test_format_yearly(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.YEARLY)
        assert manager.format_pattern(rule) == "yearly"

    def test_format_yearly_interval(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.YEARLY, interval=5)
        assert manager.format_pattern(rule) == "every 5 years"

    def test_format_custom_days(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(
            RecurrencePattern.CUSTOM,
            days_of_week=['mon', 'wed', 'fri']
        )
        assert manager.format_pattern(rule) == "every mon,wed,fri"

    def test_format_custom_no_days(self, manager: RecurrenceManager) -> None:
        rule = self._make_rule(RecurrencePattern.CUSTOM)
        assert manager.format_pattern(rule) == "custom"


class TestSerializeDaysOfWeek:
    """Tests for days_of_week serialization."""

    @pytest.fixture
    def manager(self) -> RecurrenceManager:
        return RecurrenceManager()

    def test_serialize_days(self, manager: RecurrenceManager) -> None:
        days = ['mon', 'wed', 'fri']
        result = manager.serialize_days_of_week(days)
        assert result == '["mon", "wed", "fri"]'

    def test_deserialize_days(self, manager: RecurrenceManager) -> None:
        data = '["mon", "wed", "fri"]'
        result = manager.deserialize_days_of_week(data)
        assert result == ['mon', 'wed', 'fri']

    def test_deserialize_none(self, manager: RecurrenceManager) -> None:
        result = manager.deserialize_days_of_week(None)
        assert result is None

    def test_deserialize_empty_string(self, manager: RecurrenceManager) -> None:
        result = manager.deserialize_days_of_week("")
        assert result is None

    def test_roundtrip(self, manager: RecurrenceManager) -> None:
        original = ['tue', 'thu', 'sat']
        serialized = manager.serialize_days_of_week(original)
        result = manager.deserialize_days_of_week(serialized)
        assert result == original


class TestRecurrenceRuleModel:
    """Tests for RecurrenceRule dataclass properties."""

    def test_has_reached_limit_false(self) -> None:
        rule = RecurrenceRule(
            id=1,
            task_id=1,
            pattern=RecurrencePattern.DAILY,
            max_occurrences=10,
            occurrences_created=5
        )
        assert rule.has_reached_limit is False

    def test_has_reached_limit_true(self) -> None:
        rule = RecurrenceRule(
            id=1,
            task_id=1,
            pattern=RecurrencePattern.DAILY,
            max_occurrences=10,
            occurrences_created=10
        )
        assert rule.has_reached_limit is True

    def test_has_reached_limit_no_max(self) -> None:
        rule = RecurrenceRule(
            id=1,
            task_id=1,
            pattern=RecurrencePattern.DAILY,
            occurrences_created=100
        )
        assert rule.has_reached_limit is False

    def test_has_expired_false(self) -> None:
        future = datetime.now() + timedelta(days=30)
        rule = RecurrenceRule(
            id=1,
            task_id=1,
            pattern=RecurrencePattern.DAILY,
            end_date=future
        )
        assert rule.has_expired is False

    def test_has_expired_true(self) -> None:
        past = datetime.now() - timedelta(days=1)
        rule = RecurrenceRule(
            id=1,
            task_id=1,
            pattern=RecurrencePattern.DAILY,
            end_date=past
        )
        assert rule.has_expired is True

    def test_has_expired_no_end_date(self) -> None:
        rule = RecurrenceRule(
            id=1,
            task_id=1,
            pattern=RecurrencePattern.DAILY
        )
        assert rule.has_expired is False

    def test_is_active_true(self) -> None:
        rule = RecurrenceRule(
            id=1,
            task_id=1,
            pattern=RecurrencePattern.DAILY
        )
        assert rule.is_active is True

    def test_is_active_false_limit_reached(self) -> None:
        rule = RecurrenceRule(
            id=1,
            task_id=1,
            pattern=RecurrencePattern.DAILY,
            max_occurrences=5,
            occurrences_created=5
        )
        assert rule.is_active is False

    def test_is_active_false_expired(self) -> None:
        past = datetime.now() - timedelta(days=1)
        rule = RecurrenceRule(
            id=1,
            task_id=1,
            pattern=RecurrencePattern.DAILY,
            end_date=past
        )
        assert rule.is_active is False


class TestRecurrencePatternEnum:
    """Tests for RecurrencePattern enum."""

    def test_pattern_values(self) -> None:
        assert RecurrencePattern.DAILY.value == "daily"
        assert RecurrencePattern.WEEKLY.value == "weekly"
        assert RecurrencePattern.MONTHLY.value == "monthly"
        assert RecurrencePattern.YEARLY.value == "yearly"
        assert RecurrencePattern.CUSTOM.value == "custom"

    def test_pattern_str(self) -> None:
        assert str(RecurrencePattern.DAILY) == "daily"
        assert str(RecurrencePattern.CUSTOM) == "custom"


class TestCreateOccurrence:
    """Tests for RecurrenceManager.create_occurrence() - Story 5.4."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database for testing."""
        from todo_cli.database import Database
        db_path = tmp_path / "test.db"
        return Database(db_path)

    @pytest.fixture
    def manager(self) -> RecurrenceManager:
        return RecurrenceManager()

    def test_create_occurrence_basic(self, temp_db, manager) -> None:
        """Test basic occurrence creation from a recurring task."""
        # Create a recurring task
        task = temp_db.add("Daily standup", due_date=datetime(2025, 1, 15))
        temp_db.add_recurrence_rule(
            task_id=task.id,
            pattern=RecurrencePattern.DAILY
        )

        # Create next occurrence
        new_task = manager.create_occurrence(temp_db, task.id)

        assert new_task is not None
        assert new_task.id != task.id
        assert new_task.task == "Daily standup"
        assert new_task.due_date is not None
        assert new_task.due_date.date() == date(2025, 1, 16)

    def test_create_occurrence_inherits_properties(self, temp_db, manager) -> None:
        """Test that new occurrence inherits priority, project, tags."""
        from todo_cli.models import Priority

        # Create project first
        from todo_cli.projects import ProjectManager
        pm = ProjectManager(temp_db.db_path)
        project = pm.create_project("work")

        # Create a recurring task with all properties
        task = temp_db.add(
            "Weekly review",
            priority=Priority.P1,
            project_id=project.id,
            tags=["important", "review"],
            due_date=datetime(2025, 1, 15)
        )
        temp_db.add_recurrence_rule(
            task_id=task.id,
            pattern=RecurrencePattern.WEEKLY
        )

        # Create next occurrence
        new_task = manager.create_occurrence(temp_db, task.id)

        assert new_task is not None
        assert new_task.priority == Priority.P1
        assert new_task.project_id == project.id
        assert set(new_task.tags) == {"important", "review"}
        assert new_task.due_date.date() == date(2025, 1, 22)

    def test_create_occurrence_respects_max_occurrences(self, temp_db, manager) -> None:
        """Test that occurrence creation stops at max_occurrences."""
        task = temp_db.add("Limited task", due_date=datetime(2025, 1, 15))
        rule = temp_db.add_recurrence_rule(
            task_id=task.id,
            pattern=RecurrencePattern.DAILY,
            max_occurrences=3
        )

        # Create 3 occurrences
        for i in range(3):
            new_task = manager.create_occurrence(temp_db, task.id)
            assert new_task is not None

        # 4th occurrence should fail
        new_task = manager.create_occurrence(temp_db, task.id)
        assert new_task is None

        # Verify count
        updated_rule = temp_db.get_recurrence_rule(rule.id)
        assert updated_rule.occurrences_created == 3

    def test_create_occurrence_respects_end_date(self, temp_db, manager) -> None:
        """Test that occurrence creation stops after end_date."""
        task = temp_db.add("Ends soon", due_date=datetime(2025, 1, 15))
        temp_db.add_recurrence_rule(
            task_id=task.id,
            pattern=RecurrencePattern.WEEKLY,
            end_date=datetime(2025, 1, 20)  # Only allows one more week
        )

        # First occurrence should work (Jan 22 > Jan 20 end_date)
        # Actually, the next occurrence from Jan 15 is Jan 22, which exceeds end_date
        new_task = manager.create_occurrence(temp_db, task.id)
        assert new_task is None  # Jan 22 > Jan 20 end_date

    def test_create_occurrence_nonexistent_task(self, temp_db, manager) -> None:
        """Test that create_occurrence returns None for nonexistent task."""
        result = manager.create_occurrence(temp_db, 99999)
        assert result is None

    def test_create_occurrence_no_rule(self, temp_db, manager) -> None:
        """Test that create_occurrence returns None for task without rule."""
        task = temp_db.add("Regular task")
        result = manager.create_occurrence(temp_db, task.id)
        assert result is None

    def test_create_occurrence_updates_occurrence_count(self, temp_db, manager) -> None:
        """Test that occurrence count is properly incremented."""
        task = temp_db.add("Counted task", due_date=datetime(2025, 1, 15))
        rule = temp_db.add_recurrence_rule(
            task_id=task.id,
            pattern=RecurrencePattern.DAILY
        )

        assert rule.occurrences_created == 0

        manager.create_occurrence(temp_db, task.id)
        updated_rule = temp_db.get_recurrence_rule(rule.id)
        assert updated_rule.occurrences_created == 1

        manager.create_occurrence(temp_db, task.id)
        updated_rule = temp_db.get_recurrence_rule(rule.id)
        assert updated_rule.occurrences_created == 2

    def test_create_occurrence_monthly_pattern(self, temp_db, manager) -> None:
        """Test monthly recurrence pattern."""
        task = temp_db.add("Monthly report", due_date=datetime(2025, 1, 15))
        temp_db.add_recurrence_rule(
            task_id=task.id,
            pattern=RecurrencePattern.MONTHLY,
            day_of_month=15
        )

        new_task = manager.create_occurrence(temp_db, task.id)

        assert new_task is not None
        assert new_task.due_date.date() == date(2025, 2, 15)

    def test_create_occurrence_custom_days(self, temp_db, manager) -> None:
        """Test custom days of week pattern."""
        # Monday, January 13, 2025
        task = temp_db.add("Exercise", due_date=datetime(2025, 1, 13))
        temp_db.add_recurrence_rule(
            task_id=task.id,
            pattern=RecurrencePattern.CUSTOM,
            days_of_week=["mon", "wed", "fri"]
        )

        new_task = manager.create_occurrence(temp_db, task.id)

        assert new_task is not None
        # Next occurrence from Monday should be Wednesday
        assert new_task.due_date.date() == date(2025, 1, 15)

    def test_create_occurrence_without_due_date(self, temp_db, manager) -> None:
        """Test occurrence creation from task without due date uses today."""
        task = temp_db.add("No due date task")
        temp_db.add_recurrence_rule(
            task_id=task.id,
            pattern=RecurrencePattern.DAILY
        )

        new_task = manager.create_occurrence(temp_db, task.id)

        assert new_task is not None
        assert new_task.due_date is not None
        # Should be tomorrow
        expected = date.today() + timedelta(days=1)
        assert new_task.due_date.date() == expected
