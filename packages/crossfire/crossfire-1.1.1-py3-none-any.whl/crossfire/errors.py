class CrossfireError(Exception):
    pass


class RetryAfterError(CrossfireError):
    def __init__(self, retry_after):
        self.retry_after = retry_after
        message = (
            "Got HTTP Status 429 Too Many Requests. "
            f"Retry after {self.retry_after} seconds"
        )
        super().__init__(message)


class DateIntervalError(CrossfireError):
    def __init__(self, initial_date, final_date):
        message = (
            f"initial_date `{initial_date}` is greater than final_date "
            f"`{final_date}`"
        )
        super().__init__(message)


class DateFormatError(CrossfireError):
    def __init__(self, date):
        message = f"Date `{date}` does not match format YYYYMMDD, YYYY-MM-DD, or YYYY/MM/DD"
        super().__init__(message)


class NestedColumnError(CrossfireError):
    def __init__(self, nested_columns):
        message = f"Invalid `nested_columns` value: {nested_columns}"
        super().__init__(message)
