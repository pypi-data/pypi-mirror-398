import re
from asyncio import Semaphore, gather, sleep
from datetime import date, datetime
from urllib.parse import urlencode

from httpx import ReadTimeout
from tqdm import tqdm

from crossfire.errors import NestedColumnError

try:
    from pandas import DataFrame, Series, concat

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


try:
    from geopandas import GeoDataFrame

    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False

from crossfire.errors import (
    CrossfireError,
    DateFormatError,
    DateIntervalError,
    RetryAfterError,
)
from crossfire.logger import Logger

logger = Logger(__name__)

TYPE_OCCURRENCES = {"all", "withVictim", "withoutVictim"}
NOT_NUMBER = re.compile("\D")
NESTED_COLUMNS = {
    "contextInfo",
    "state",
    "region",
    "city",
    "neighborhood",
    "locality",
}


def date_formatter(date_parameter):
    if isinstance(date_parameter, datetime):
        return date_parameter.date()
    elif isinstance(date_parameter, date):
        return date_parameter
    date_cleaned = re.sub(NOT_NUMBER, "", date_parameter)
    try:
        date_cleaned = datetime.strptime(date_cleaned, "%Y%m%d").date()
    except ValueError:
        raise DateFormatError(date_parameter)
    return date_cleaned


class UnknownTypeOccurrenceError(CrossfireError):
    def __init__(self, type_occurrence):
        message = (
            f"Unknown type_occurrence `{type_occurrence}`. "
            f"Valid formats are: {', '.join(TYPE_OCCURRENCES)}"
        )
        super().__init__(message)


class Occurrences:
    MAX_PARALLEL_REQUESTS = 16

    def __init__(
        self,
        client,
        id_state,
        id_cities=None,
        type_occurrence="all",
        initial_date=None,
        final_date=None,
        max_parallel_requests=None,
        format=None,
        flat=False,
    ):
        if type_occurrence not in TYPE_OCCURRENCES:
            raise UnknownTypeOccurrenceError(type_occurrence)

        self.client = client
        self.format = format
        self.flat = flat
        self.params = {"idState": id_state, "typeOccurrence": type_occurrence}
        if id_cities:
            self.params["idCities"] = id_cities
        if initial_date:
            initial_date = date_formatter(initial_date)
            self.params["initialdate"] = initial_date
        if final_date:
            final_date = date_formatter(final_date)
            self.params["finaldate"] = final_date
        if initial_date and final_date and initial_date > final_date:
            raise DateIntervalError(initial_date, final_date)

        self.semaphore = Semaphore(
            max_parallel_requests or self.MAX_PARALLEL_REQUESTS
        )
        self.total_pages = None
        self.progress_bar = None

    async def page(self, number):
        params = self.params.copy()
        params["page"] = number
        query = urlencode(params, doseq=True)
        url = f"{self.client.URL}/occurrences?{query}"

        failed = False
        async with self.semaphore:
            try:
                occurrences, metadata = await self.client.get(
                    url, format=self.format
                )
            except (ReadTimeout, RetryAfterError) as err:
                failed = True
                wait = getattr(err, "retry_after", 1)

        if failed:
            logger.debug(
                f"Too many requests. Waiting {wait}s before retrying page {number}"
            )
            await sleep(wait)
            return await self.page(number)

        if not self.total_pages:
            self.total_pages = metadata.page_count
            self.progress_bar.total = metadata.page_count

        self.progress_bar.update(1)
        return occurrences

    async def __call__(self):
        self.progress_bar = tqdm(desc="Loading pages", unit="page")

        data = Accumulator()
        data.merge(await self.page(1))

        if self.total_pages > 1:
            requests = tuple(
                self.page(n) for n in range(2, self.total_pages + 1)
            )
            pages = await gather(*requests)
            data.merge(*pages)

        if self.flat:
            return flatten(data())
        return data()


class Accumulator:
    def __init__(self):
        self.data = None
        self.is_gdf = False

    def save_first(self, *pages):
        self.data, *remaining = pages
        if HAS_GEOPANDAS and isinstance(self.data, GeoDataFrame):
            self.is_gdf = True
        return self if not remaining else self.merge(remaining)

    def merge(self, *pages):
        if self.data is None:
            return self.save_first(*pages)

        if isinstance(self.data, list):
            for page in pages:
                self.data.extend(page)
            return self

        dfs = [self.data] + list(pages)
        self.data = concat(dfs, ignore_index=True)
        return self

    def __call__(self):
        if self.is_gdf:
            return GeoDataFrame(self.data)

        return self.data


def _flatten_df(data, nested_columns):
    def _flatten_col(row, column_name):
        column_data = row[column_name]
        if not column_data:
            return Series()

        flatenned_series = Series(
            {
                f"{column_name}_{key}": value
                for key, value in column_data.items()
            }
        )
        for key, value in column_data.items():
            if isinstance(value, dict):
                flatenned_series = concat(
                    [
                        flatenned_series,
                        Series(
                            {
                                f"{column_name}_{key}_{subkey}": v
                                for subkey, v in value.items()
                            },
                        ),
                    ],
                    axis=0,
                )
        return flatenned_series

    keys = set(data.columns) & nested_columns
    if not keys:
        return data
    for key in keys:
        data = concat(
            [
                data,
                data.apply(_flatten_col, args=(key,), axis=1),
            ],
            axis=1,
        )
    return data


def _flatten_list(data, nested_columns):
    keys = set(data[0].keys()) & nested_columns
    for item in data:
        for key in keys:
            if key not in item:
                return data
            value = item.get(key)
            if not value:
                return data

            item.update({f"{key}_{k}": v for k, v in value.items() if v})
            for k, v in value.items():
                if isinstance(v, dict):
                    item.update(
                        {
                            f"{key}_{k}_{subkey}": v
                            for subkey, v in v.items()
                            if v
                        }
                    )
    return data


def is_empty(data):
    if HAS_PANDAS and isinstance(data, DataFrame):
        return data.empty
    return not data


def flatten(data, nested_columns=None):
    nested_columns = set(nested_columns or NESTED_COLUMNS)
    if not nested_columns.issubset(NESTED_COLUMNS):
        raise NestedColumnError(nested_columns)
    if is_empty(data):
        return data
    if HAS_PANDAS and isinstance(data, DataFrame):
        data = _flatten_df(data, nested_columns)
        return data

    data = _flatten_list(data, nested_columns)
    return data
