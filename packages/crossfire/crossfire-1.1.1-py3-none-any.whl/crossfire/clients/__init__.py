from asyncio import get_event_loop
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from decouple import UndefinedValueError, config
from nest_asyncio import apply

from crossfire.clients.occurrences import Occurrences
from crossfire.errors import CrossfireError, RetryAfterError
from crossfire.parser import parse_response


class CredentialsNotFoundError(CrossfireError):
    def __init__(self, key):
        message = f"There's no environment variable `{key}` condigured."
        super().__init__(message)


class IncorrectCredentialsError(CrossfireError):
    pass


class Token:
    def __init__(self, value, expires_in):
        self.value = value
        self.valid_until = datetime.now() + timedelta(seconds=expires_in)

    def is_valid(self):
        return datetime.now() < self.valid_until


class AsyncClient:
    URL = "https://api-service.fogocruzado.org.br/api/v2"

    def __init__(self, email=None, password=None, max_parallel_requests=None):
        try:
            email = email or config("FOGOCRUZADO_EMAIL")
        except UndefinedValueError:
            raise CredentialsNotFoundError("FOGOCRUZADO_EMAIL")

        try:
            password = password or config("FOGOCRUZADO_PASSWORD")
        except UndefinedValueError:
            raise CredentialsNotFoundError("FOGOCRUZADO_PASSWORD")

        self.max_parallel_requests = max_parallel_requests
        self.client = httpx.AsyncClient(default_encoding="utf-8")
        self.credentials = {"email": email, "password": password}
        self.cached_token = None

    async def token(self):
        if self.cached_token and self.cached_token.is_valid():
            return self.cached_token.value

        resp = await self.client.post(
            f"{self.URL}/auth/login", json=self.credentials
        )

        if resp.status_code == 401:
            data = resp.json()
            raise IncorrectCredentialsError(data.get("msg"))

        if resp.status_code != 201:
            resp.raise_for_status()

        data = resp.json()
        self.cached_token = Token(
            data["data"]["accessToken"], data["data"]["expiresIn"]
        )
        return self.cached_token.value

    async def get(self, *args, **kwargs):
        """Wraps `httpx.get` to inject the authorization header. Also, accepts the
        `format` argument consumed by the `parse_response` decorator."""
        format = kwargs.pop("format", None)
        token = await self.token()
        auth = {"Authorization": f"Bearer {token}"}

        if "headers" not in kwargs:
            kwargs["headers"] = auth
        else:
            kwargs["headers"].update(auth)

        response = await self.client.get(*args, **kwargs)
        if response.status_code == 429:
            try:
                wait = int(response.headers.get("retry-after") or 1)
            except ValueError:
                wait = 1
            raise RetryAfterError(wait)

        response.raise_for_status()
        return parse_response(response, format=format)

    async def states(self, format=None):
        return await self.get(f"{self.URL}/states", format=format)

    async def cities(
        self, city_id=None, city_name=None, state_id=None, format=None
    ):
        params = {"cityId": city_id, "cityName": city_name, "stateId": state_id}
        cleaned = urlencode(
            {key: value for key, value in params.items() if value}
        )
        return await self.get(f"{self.URL}/cities?{cleaned}", format=format)

    async def occurrences(
        self,
        id_state,
        id_cities=None,
        type_occurrence="all",
        initial_date=None,
        final_date=None,
        max_parallel_requests=None,
        format=None,
        flat=False,
    ):
        occurrences = Occurrences(
            self,
            id_state,
            id_cities=id_cities,
            type_occurrence=type_occurrence,
            initial_date=initial_date,
            final_date=final_date,
            max_parallel_requests=max_parallel_requests
            or self.max_parallel_requests,
            format=format,
            flat=flat,
        )
        return await occurrences()


class Client(AsyncClient):
    def __init__(self, email=None, password=None, max_parallel_requests=None):
        super().__init__(
            email=email,
            password=password,
            max_parallel_requests=max_parallel_requests,
        )
        apply()

    def states(self, format=None):
        loop = get_event_loop()
        states, _ = loop.run_until_complete(super().states(format=format))
        return states

    def cities(self, city_id=None, city_name=None, state_id=None, format=None):
        loop = get_event_loop()
        cities, _ = loop.run_until_complete(
            super().cities(
                city_id=city_id,
                city_name=city_name,
                state_id=state_id,
                format=format,
            )
        )
        return cities

    def occurrences(
        self,
        id_state,
        id_cities=None,
        type_occurrence="all",
        initial_date=None,
        final_date=None,
        max_parallel_requests=None,
        format=None,
        flat=False,
    ):
        loop = get_event_loop()
        occurrences = loop.run_until_complete(
            super().occurrences(
                id_state=id_state,
                id_cities=id_cities,
                type_occurrence=type_occurrence,
                initial_date=initial_date,
                final_date=final_date,
                max_parallel_requests=max_parallel_requests,
                format=format,
                flat=flat,
            )
        )
        return occurrences
