import datetime
import pathlib
from dataclasses import dataclass
from itertools import groupby

import logging
from html.parser import HTMLParser
import httpx

from gyvatukas.exceptions import GyvatukasException
from gyvatukas.internal import get_app_storage_path
from gyvatukas.utils.json_ import get_pretty_json

_logger = logging.getLogger("gyvatukas")


class FormParser(HTMLParser):
    form: dict = {}

    def handle_starttag(self, tag: str, attrs: tuple) -> None:
        if tag != "input":
            return

        self.handle_input_tag(attrs)

    def get(self, attribute: str) -> dict | None:
        if attribute not in self.form:
            return None

        return self.form[attribute]

    def set(self, attribute: str, value: str) -> None:
        self.form[attribute] = value

    def handle_input_tag(self, attrs: tuple) -> None:
        attributes = dict(attrs)

        if "name" in attributes and attributes["name"] in [
            "form_token",
            "form_build_id",
            "form_id",
        ]:
            self.form[attributes["name"]] = attributes["value"]


@dataclass
class ConsumptionRecord:
    dt: datetime.datetime
    kwh: float


@dataclass
class ConsumptionDataset:
    type_key: str
    type: str
    dt: datetime.date
    total_kwh: float
    records: list[ConsumptionRecord]


class ManoEsoLt:
    """ESO data extractor based on https://github.com/algirdasc/hass-eso +rep

    Kai moki daxuja+1 už perdavimą ir etc, pastato naują skaitliuką, bet jo duomenys tik per web'ą
    arba mokamą API ale verslui. Ačiū jums, kad esate, ESO.
    """

    # TODO: Custom exceptions.
    URL_LOGIN = "https://mano.eso.lt/?destination=/consumption"
    URL_CONSUMPTION_DATA = (
        "https://mano.eso.lt/consumption?ajax_form=1&_wrapper_format=drupal_ajax"
    )

    def __init__(self, username: str, password: str, persist_session: bool = True):
        # TODO: Check if session exists, load it if username matches.
        #  Also log that!
        self.username: str = username
        self.password: str = password
        self.persist_session: bool = persist_session
        self.cookies: dict | None = None
        self.special_fields: dict = {}

        self.is_persisted_session: bool = False

    def _extract_special_fields(self, login_response: str) -> None:
        fp = FormParser()
        fp.feed(login_response)

        self.special_fields["form_build_id"] = fp.get("form_build_id")
        self.special_fields["form_token"] = fp.get("form_token")
        self.special_fields["form_id"] = fp.get("form_id")

    def _save_session(self) -> None:
        """Saves session to disk for reuse."""
        path = pathlib.Path(get_app_storage_path(), "mano_eso_lt.json")

        data = {
            "username": self.username,
            "cookies": self.cookies,
            "special_fields": self.special_fields,
        }

        path.write_text(get_pretty_json(data))

    def login(self) -> None:
        with httpx.post(
            url=self.URL_LOGIN,
            data={
                "name": self.username,
                "pass": self.password,
                "login_type": 1,
                "form_id": "user_login_form",
            },
            allow_redirects=True,
            timeout=30,
        ) as response:
            if response.status_code != 200:
                raise GyvatukasException("Failed mano.eso.lt login!")

            self.cookies = httpx.utils.dict_from_cookiejar(response.cookies)
            self._extract_special_fields(response.text)

            if self.persist_session:
                self._save_session()

    def get_day_stats(
        self, eso_object_id: str, date: datetime.date | datetime.datetime
    ) -> list[ConsumptionDataset]:
        """Return daily consumption stats."""
        raise NotImplementedError()

    def get_week_stats(
        self, eso_object_id: str, date: datetime.date | datetime.datetime
    ) -> list[ConsumptionDataset]:
        """Return weekly consumption stats.

        🚨 Will always return date - 1 stats.
        """
        # TODO: handle if session expired!
        # TODO: handle historical data!

        if not self.cookies:
            raise Exception("Cookies are empty. Check your credentials.")

        if self.special_fields.get("form_id") != "eso_consumption_history_form":
            raise GyvatukasException("Form ID not found. Check your credentials.")

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }

        data = {
            "objects[]": eso_object_id,
            "objects_mock": "",
            "display_type": "hourly",
            "period": "week",
            # day_period, other_start, other_end
            "energy_type": "general",
            "scales": "total",
            "active_date_value": date.strftime("%Y-%m-%d+00:00"),
            "made_energy_status": 1,
            # back_button_value, next_button_value
            "visible_scales_field": 0,
            "visible_last_year_comparison_field": 0,
            "last_year_comparison": 1,
            "total_monthly_consumption": 1,
            "_drupal_ajax": "1",
            "_triggering_element_name": "display_type",
            **self.special_fields,
        }

        with httpx.post(
            url=self.URL_CONSUMPTION_DATA,
            data=data,
            headers=headers,
            cookies=self.cookies,
            allow_redirects=False,
            timeout=90,
        ) as response:
            if response.status_code != 200:
                raise GyvatukasException("Failed mano.eso.lt consumption data request!")

            data = response.json()

            # Find dataset with key `settings.eso_consumption_history_form`
            wanted_data = None
            for d in data:
                try:
                    wanted_data = d["settings"]["eso_consumption_history_form"][
                        "graphics_data"
                    ]
                except (KeyError, TypeError):
                    continue

            # Do initial processing of all data.
            result = []
            for dataset in wanted_data["datasets"]:
                parsed_records = []

                for record in dataset["record"]:
                    ts = datetime.datetime.strptime(record["date"], "%Y%m%d%H%M%S")
                    # TODO: Set tz to lithuania.
                    kwh = (
                        abs(float(record["value"]))
                        if record["value"] is not None
                        else 0.0
                    )
                    parsed_records.append(
                        ConsumptionRecord(
                            dt=ts,
                            kwh=kwh,
                        )
                    )

                # Group records by day and create consumption dataset for each day.
                parsed_records.sort(key=lambda x: x.dt.date())
                grouped_parsed_records = groupby(
                    parsed_records, key=lambda x: x.dt.date()
                )

                for key, group in grouped_parsed_records:
                    day_records = []
                    total_kwh = 0.0
                    for hourly_parsed_record in group:
                        day_records.append(hourly_parsed_record)
                        total_kwh += hourly_parsed_record.kwh

                    cd = ConsumptionDataset(
                        type_key=dataset["key"],
                        type=dataset["label"],
                        total_kwh=total_kwh,
                        dt=key,
                        records=day_records,
                    )
                    result.append(cd)

            return result
