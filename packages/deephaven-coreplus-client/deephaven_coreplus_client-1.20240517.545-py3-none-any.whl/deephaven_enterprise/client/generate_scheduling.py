from typing import List

class GenerateScheduling:
    """
    GenerateScheduling contains helper methods to generate scheduling arrays for use in persistent queries.
    """

    @staticmethod
    def _create_standard_parameters(scheduler_type: str,
                                   start_time: str,
                                   stop_time: str,
                                   time_zone: str,
                                   calendar: str,
                                   overnight: bool,
                                   repeat_enabled: bool,
                                   repeat_interval: int,
                                   skip_if_unsuccessful: bool,
                                   stop_time_disabled: bool,
                                   restart_error_count: int,
                                   restart_error_delay_minutes: int,
                                   restart_when_running: str):
        """
        Internal function to generate a base scheduler array with basic values. This array is not sufficient to create a valid
        scheduler by itself.

        :return: a base scheduling definition array that should be appended to create a valid scheduler.
        """
        if restart_when_running != "Yes" and restart_when_running != "No":
            raise ValueError("'restart_when_running' must be 'Yes' or 'No'")

        if repeat_enabled and repeat_interval < 1:
            raise ValueError("'repeat_interval' must be greater than zero when repeat is enabled")

        scheduling = []
        scheduling.append("SchedulerType=" + scheduler_type)
        if start_time is not None:
            scheduling.append("StartTime=" + start_time)
        if stop_time is not None:
            scheduling.append("StopTime=" + stop_time)
        scheduling.append("TimeZone=" + time_zone)
        if calendar is not None:
            scheduling.append("Calendar=" + calendar)
        scheduling.append("SkipIfUnsuccessful=" + str(skip_if_unsuccessful).lower())
        scheduling.append("StopTimeDisabled=" + str(stop_time_disabled).lower())
        scheduling.append("Overnight=" + str(overnight).lower())
        scheduling.append("RepeatEnabled=" + str(repeat_enabled).lower())
        if repeat_enabled:
            scheduling.append("RepeatInterval=" + str(repeat_interval))
        scheduling.append("RestartErrorCount=" + str(restart_error_count))
        scheduling.append("RestartErrorDelay=" + str(restart_error_delay_minutes))
        scheduling.append("RestartWhenRunning=" + restart_when_running)
        scheduling.append("SchedulingDisabled=false")

        return scheduling

    @staticmethod
    def generate_disabled_scheduler() -> List[str]:
        """
        Generates a scheduler array for a persistent query with scheduling disabled.

        :return: a scheduling definition array that can be passed to the controller when adding or updating a persistent query
        """
        scheduling = []
        scheduling.append(
            "SchedulerType=com.illumon.iris.controller.IrisQuerySchedulerDaily")
        scheduling.append(
            "Calendar=USNYSE")
        scheduling.append("BusinessDays=false")
        scheduling.append("Days=true=true=true=true=true=true=true")
        scheduling.append("StartTime=00:00:00")
        scheduling.append("StopTime=23:59:59")
        scheduling.append("TimeZone=America/New_York")
        scheduling.append("SchedulingDisabled=true")
        return scheduling

    @staticmethod
    def generate_daily_scheduler(start_time: str,
                                 stop_time: str,
                                 time_zone: str = "America/New_York",
                                 business_days: bool = False,
                                 calendar: str = "USNYSE",
                                 days: List[bool] = [True, True, True, True, True, True, True],
                                 overnight: bool = False,
                                 repeat_enabled: bool = False,
                                 repeat_interval: int = 0,
                                 skip_if_unsuccessful: bool = False,
                                 stop_time_disabled: bool = False,
                                 restart_error_count: int = 0,
                                 restart_error_delay_minutes: int = 0,
                                 restart_when_running: str = "Yes") -> List[str]:
        """
        Generate a scheduler array for a persistent query that has daily scheduling.

        :param start_time: the query's starting time in HH:MM:SS format
        :param stop_time: the query's stop time in HH:MM:SS format
        :param time_zone: the time zone, such as 'America/New_York' or 'Europe/London'
        :param business_days: if changed to True, only run on business days
        :param calendar: if business_days is True, the business calendar to use
        :param days: a list of bool values representing the days to run the persistent query, from Monday through Sunday
        :param overnight: if True, the query runs overnight
        :param repeat_enabled: for batch-style queries, if True, the persistent query will be restarted at the repeat_interval interval
        :param repeat_interval: if repeat_enabled is True, the interval in minutes between restarts
        :param skip_if_unsuccessful: for repeating queries, skip if the previous run failed when this is True
        :param stop_time_disabled: if True, the persistent query does not need a stop time (for example, non-repeating batch queries)
        :param restart_error_count: the number of times a failing query will attempt to be restarted within its run window
        :param restart_error_delay_minutes: the delay in minutes between attempting to restart a failed query
        :param restart_when_running: if 'Yes' then the query will be restarted when running at its start time, if 'No' it will be left running
        :return: a scheduling definition array that can be passed to the controller when adding or updating a persistent query
        """

        if len(days) != 7:
            raise ValueError("'days' must contain exactly 7 elements")

        scheduling = GenerateScheduling._create_standard_parameters("com.illumon.iris.controller.IrisQuerySchedulerDaily",
            start_time, stop_time, time_zone, calendar, overnight, repeat_enabled, repeat_interval, skip_if_unsuccessful,
            stop_time_disabled, restart_error_count, restart_error_delay_minutes, restart_when_running)
        scheduling.append("BusinessDays=" + str(business_days).lower())
        scheduling.append("Days=" + "=".join(str(item).lower() for item in days))

        return scheduling

    @staticmethod
    def generate_monthly_scheduler(start_time: str,
                                  stop_time: str,
                                  time_zone: str = "America/New_York",
                                  business_days: bool = False,
                                  calendar: str = "USNYSE",
                                  first_business_day: bool = False,
                                  last_business_day: bool = False,
                                  months: List[bool] = [True, True, True, True, True, True, True, True, True, True, True, True],
                                  days: List[int] = None,
                                  overnight: bool = False,
                                  repeat_enabled: bool = False,
                                  repeat_interval: int = 0,
                                  skip_if_unsuccessful: bool = False,
                                  stop_time_disabled: bool = False,
                                  restart_error_count: int = 0,
                                  restart_error_delay_minutes: int = 0,
                                  restart_when_running: str = "Yes") -> List[str]:
        """
        Generate a scheduler array for a persistent query that has monthly scheduling.

        :param start_time: the query's starting time in HH:MM:SS format
        :param stop_time: the query's stop time in HH:MM:SS format
        :param time_zone: the time zone, such as 'America/New_York' or 'Europe/London'
        :param business_days: if changed to True, only run on business days
        :param calendar: if business_days is True, the business calendar to use
        :param first_business_day: if True, then run the query on the first business day of the month
        :param last_business_day: if True, then run the query on the last business day of the month
        :param months: a List of the months on which the persistent query will be started, starting with January
        :param days: a list of specific days (from 1 to 31) to run the persistent query for each month, or None if this is not needed
        :param overnight: if True, the query runs overnight
        :param repeat_enabled: for batch-style queries, if True, the persistent query will be restarted at the repeat_interval interval
        :param repeat_interval: if repeat_enabled is True, the interval in minutes between restarts
        :param skip_if_unsuccessful: for repeating queries, skip if the previous run failed when this is True
        :param stop_time_disabled: if True, the persistent query does not need a stop time (for example, non-repeating batch queries)
        :param restart_error_count: the number of times a failing query will attempt to be restarted within its run window
        :param restart_error_delay_minutes: the delay in minutes between attempting to restart a failed query
        :param restart_when_running: if 'Yes' then the query will be restarted when running at its start time, if 'No' it will be left running
        :return: a scheduling definition array that can be passed to the controller when adding or updating a persistent query
        """

        if len(months) != 12:
            raise ValueError("'months' must contain exactly 12 elements")

        if days is not None and len(days) > 31:
            raise ValueError("'days' must contain 31 or fewer elements")

        scheduling = GenerateScheduling._create_standard_parameters("com.illumon.iris.controller.IrisQuerySchedulerMonthly",
            start_time, stop_time, time_zone, calendar, overnight, repeat_enabled, repeat_interval, skip_if_unsuccessful,
            stop_time_disabled, restart_error_count, restart_error_delay_minutes, restart_when_running)

        scheduling.append("BusinessDays=" + str(business_days).lower())
        scheduling.append("FirstBusinessDay=" + str(first_business_day).lower())
        scheduling.append("LastBusinessDay=" + str(last_business_day).lower())
        scheduling.append("Months=" + "=".join(str(item).lower() for item in months))

        if days is not None:
            scheduling.append("SpecificDays=true")
            # Generate a list with all values set to False, then overwrite the specified days with True
            day_list = []
            for i in range(31):
                day_list.append(False)

            for day in days:
                day_list[day-1] = True

            scheduling.append("Days=" + "=".join(str(item).lower() for item in day_list))
        else:
            scheduling.append("SpecificDays=false")

        return scheduling


    @staticmethod
    def generate_continuous_scheduler(start_time: str,
                                      time_zone: str = "America/New_York",
                                      restart_daily: bool = False,
                                      restart_error_count: int = 0,
                                      restart_error_delay_minutes: int = 0) -> List[str]:
        """
        Generate a scheduler array for a persistent query that has continuous scheduling.

        :param start_time: the query's restart time in HH:MM:SS format
        :param time_zone: the time zone, such as 'America/New_York' or 'Europe/London'
        :param restart_daily: if True, then the query should be restarted every day at the defined start_time
        :param restart_error_count: the number of times a failing query will attempt to be restarted within its run window
        :param restart_error_delay_minutes: the delay in minutes between attempting to restart a failed query
        :return: a scheduling definition array that can be passed to the controller when adding or updating a persistent query
        """

        if not restart_daily and start_time is None:
            start_time = "00:00:00"

        if restart_daily and start_time is None:
            raise ValueError("start_time must be provided when restart_daily is True")

        scheduling = GenerateScheduling._create_standard_parameters("com.illumon.iris.controller.IrisQuerySchedulerContinuous",
            start_time, None, time_zone, None, False, False, 0, False,
            True, restart_error_count, restart_error_delay_minutes, "Yes")
        scheduling.append("DailyRestart=" + str(restart_daily).lower())

        return scheduling


    @staticmethod
    def generate_range_scheduler(start_time: str,
                                 stop_time: str,
                                 start_date: str,
                                 end_date: str,
                                 time_zone: str = "America/New_York",
                                 repeat_enabled: bool = False,
                                 repeat_interval: int = 0,
                                 skip_if_unsuccessful: bool = False,
                                 restart_error_count: int = 0,
                                 restart_error_delay_minutes: int = 0,
                                 restart_when_running: str = "Yes") -> List[str]:
        """
        Generate a scheduler array for a persistent query that has range scheduling.

        :param start_time: the query's starting time in HH:MM:SS format, or None if no start date/time will be used
        :param stop_time: the query's stop time in HH:MM:SS format, or None if no stop date/time will be used
        :param start_date: the query's start date in YYYY-MM-DD format, or None if no start date/time will be used
        :param end_date: the query's end date in YYYY-MM-DD format, or None if no stop date/time will be used
        :param time_zone: the time zone, such as 'America/New_York' or 'Europe/London'
        :param repeat_enabled: for batch-style queries, if True, the persistent query will be restarted at the repeat_interval interval
        :param repeat_interval: if repeat_enabled is True, the interval in minutes between restarts
        :param skip_if_unsuccessful: for repeating queries, skip if the previous run failed when this is True
        :param restart_error_count: the number of times a failing query will attempt to be restarted within its run window
        :param restart_error_delay_minutes: the delay in minutes between attempting to restart a failed query
        :param restart_when_running: if 'Yes' then the query will be restarted when running at its start time, if 'No' it will be left running
        :return: a scheduling definition array that can be passed to the controller when adding or updating a persistent query
        """

        if start_time is not None and start_date is None:
            raise ValueError("if start_time is defined then start_date must be defined")

        if stop_time is not None and end_date is None:
            raise ValueError("if stop_time is defined then end_date must be defined")

        scheduling = GenerateScheduling._create_standard_parameters("com.illumon.iris.controller.IrisQuerySchedulerRange",
            start_time, stop_time, time_zone, None, False, repeat_enabled, repeat_interval, False,
            not repeat_enabled, restart_error_count, restart_error_delay_minutes, restart_when_running)

        if start_time is not None:
            scheduling.append("StartDate=" + start_date)
            scheduling.append("UseStartDateTime=true")
        else:
            scheduling.append("UseStartDateTime=false")

        if stop_time is not None:
            scheduling.append("StopDate=" + end_date)
            scheduling.append("UseStopDateTime=true")
        else:
            scheduling.append("UseStopDateTime=false")

        return scheduling


    @staticmethod
    def generate_temporary_scheduler(queue_name: str = "DefaultTemporaryQueue",
                                     restart_error_count: int = 0,
                                     restart_error_delay_minutes: int = 0,
                                     auto_delete: bool = True,
                                     expiration_time_minutes: int = 1440,
                                     dependent_query_serial: int = None) -> List[str]:
        """
        Generate a scheduler array for a persistent query that has temporary scheduling.

        :param queue_name: the temporary queue name
        :param restart_error_count: the number of times a failing query will attempt to be restarted within its run window
        :param restart_error_delay_minutes: the delay in minutes between attempting to restart a failed query
        :param auto_delete: if True, automatically delete the PQ after it's completed
        :param expiration_time_minutes: the time in minutes after which the temporary query will automatically be deleted (defaults to 1 day)
        :param dependent_query_serial: a single optional query on which the temporary query is dependent
        :return: a scheduling definition array that can be passed to the controller when adding or updating a persistent query
        """

        scheduling = GenerateScheduling._create_standard_parameters("com.illumon.iris.controller.IrisQuerySchedulerTemporary",
            "00:00:00", None, "America/New_York", None, False, False, 0, False,
            True, restart_error_count, restart_error_delay_minutes, "Yes")
        scheduling.append("TemporaryQueueName=" + queue_name)
        scheduling.append("TemporaryAutoDelete=" + str(auto_delete).lower())
        scheduling.append("TemporaryExpirationTimeMillis=" + str(expiration_time_minutes * 60000))
        if dependent_query_serial is not None:
            scheduling.append("TemporaryDependentQuerySerial=" + str(dependent_query_serial))

        return scheduling


    @staticmethod
    def generate_dependent_scheduler(start_time: str,
                                     stop_time: str,
                                     time_zone: str = "America/New_York",
                                     dependent_query_serials: List[int] = None,
                                     run_on_failure: bool = False,
                                     restart_on_condition: bool = False,
                                     run_on_any_dependency_met: bool = False,
                                     use_minimum_start_time: bool = False,
                                     run_each_time: bool = False,
                                     deadline_start: str = "00:00:00",
                                     deadline_end: str = "23:59:59",
                                     overnight: bool = False,
                                     repeat_enabled: bool = False,
                                     repeat_interval: int = 0,
                                     skip_if_unsuccessful: bool = False,
                                     stop_time_disabled: bool = False,
                                     restart_error_count: int = 0,
                                     restart_error_delay_minutes: int = 0,
                                     restart_when_running: str = "Yes") -> List[str]:
        """
        Generate a scheduler array for a persistent query that has dependent scheduling.

        :param start_time: the query's starting time in HH:MM:SS format
        :param stop_time: the query's stop time in HH:MM:SS format
        :param time_zone: the time zone, such as 'America/New_York' or 'Europe/London'
        :param dependent_query_serials: a list of serials on which the query is dependent
        :param run_on_failure: if True, run when dependencies fail (rather than succeed)
        :param restart_on_condition: if True, restart when conditions are met even if the query is running at the time
        :param run_on_any_dependency_met: if True, run when any dependency is met, otherwise all dependencies must be met
        :param use_minimum_start_time: if True, delay start of query after dependencies are met until the specified start_time
        :param run_each_time: if True, run every time dependencies are met, otherwise run once each day
        :param deadline_start: the start of the time at which the query should respond to dependency changes, in HH:MM:SS format
        :param deadline_end: the end of the time at which the query should respond to dependency changes, in HH:MM:SS format
        :param overnight: if True, the query runs overnight
        :param repeat_enabled: for batch-style queries, if True, the persistent query will be restarted at the repeat_interval interval
        :param repeat_interval: if repeat_enabled is True, the interval in minutes between restarts
        :param skip_if_unsuccessful: for repeating queries, skip if the previous run failed when this is True
        :param stop_time_disabled: if True, the persistent query does not need a stop time (for example, non-repeating batch queries)
        :param restart_error_count: the number of times a failing query will attempt to be restarted within its run window
        :param restart_error_delay_minutes: the delay in minutes between attempting to restart a failed query
        :param restart_when_running: if 'Yes' then the query will be restarted when running at its start time, if 'No' it will be left running
        :return: a scheduling definition array that can be passed to the controller when adding or updating a persistent query
        """

        if dependent_query_serials is None:
            raise ValueError("'dependent_query_serials' must be provided")

        if len(dependent_query_serials) < 1:
            raise ValueError("'dependent_query_serials' must contain at least one element")

        scheduling = GenerateScheduling._create_standard_parameters("com.illumon.iris.controller.IrisQuerySchedulerDependent",
            start_time, stop_time, time_zone, None, overnight, repeat_enabled, repeat_interval, skip_if_unsuccessful,
            stop_time_disabled, restart_error_count, restart_error_delay_minutes, restart_when_running)
        scheduling.append("DependentQuerySerial=" + ";".join(str(item) for item in dependent_query_serials))
        scheduling.append("RunOnFailure=" + str(run_on_failure).lower())
        scheduling.append("RestartOnCondition=" + str(restart_on_condition).lower())
        scheduling.append("RunOnAny=" + str(run_on_any_dependency_met).lower())
        scheduling.append("UseMinStartTime=" + str(use_minimum_start_time).lower())
        scheduling.append("RunEachTime=" + str(run_each_time).lower())
        scheduling.append("DeadlineStart=" + deadline_start)
        scheduling.append("DeadlineEnd=" + deadline_end)

        return scheduling