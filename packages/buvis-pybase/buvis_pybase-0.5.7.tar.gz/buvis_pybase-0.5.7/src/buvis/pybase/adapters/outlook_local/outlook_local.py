from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

import tzlocal
from buvis.pybase.adapters.outlook_local.exceptions import (
    OutlookAppointmentCreationFailedError,
)

if os.name == "nt":
    import win32com.client
else:
    msg = f"OS {os.name} not supported by OutlookLocalAdapter"
    raise OSError(msg)

from buvis.pybase.adapters import console


class OutlookLocalAdapter:
    def __init__(self: OutlookLocalAdapter) -> None:
        try:
            self.app = win32com.client.Dispatch("Outlook.Application")
            self.api = self.app.GetNamespace("MAPI")
            self.calendar = self.api.GetDefaultFolder(9)
        except Exception as e:  # noqa: BLE001
            console.panic(f"Outook connection failed:\n{e}")

    def create_timeblock(
        self: OutlookLocalAdapter,
        appointment_input: dict,
    ) -> None:
        try:
            appointment = self.app.CreateItem(1)  # 1 represents AppointmentItem
            if appointment_input.get("start") and isinstance(
                appointment_input["start"],
                datetime,
            ):
                start = appointment_input["start"]
            else:
                start = datetime.now(tzlocal.get_localzone()).replace(
                    minute=0,
                    second=0,
                )
            appointment.Start = start
            appointment.Subject = appointment_input["subject"]
            appointment.Body = appointment_input["body"]
            appointment.Duration = appointment_input["duration"]
            appointment.Location = appointment_input["location"]
            appointment.Categories = appointment_input["categories"]
            appointment.Save()
        except Exception as e:  # noqa: BLE001
            msg = f"Appointment creation failed:\n{e}"
            raise OutlookAppointmentCreationFailedError(msg) from e

    def get_all_appointments(self: OutlookLocalAdapter) -> list:
        appointments: Any = self.calendar.Items
        appointments.IncludeRecurrences = True
        appointments.Sort("[Start]")
        return appointments

    def get_day_appointments(
        self: OutlookLocalAdapter,
        appointments: Any,  # noqa: ANN401 (The win32com.client library dynamically creates Python wrappers for COM objects, which means the exact type of the object can vary and is not known at compile time.)
        date: datetime,
    ) -> list:
        restrict_from = date.strftime("%Y-%d-%m")
        restrict_to = date + timedelta(days=1)
        restrict_to = restrict_to.strftime("%Y-%d-%m")
        restrict_query = f"[Start] >= '{restrict_from}' AND [End] <= '{restrict_to}'"
        appointments = appointments.Restrict(restrict_query)
        return [
            appointment
            for appointment in appointments
            if (
                appointment.Start.year == date.year
                and appointment.Start.month == date.month
                and appointment.Start.day == date.day
            )
        ]

    def get_conflicting_appointment(
        self: OutlookLocalAdapter,
        desired_start: datetime,
        desired_duration: int,
        debug_level: int = 0,
    ) -> Any | None:  # noqa: ANN401 (The win32com.client library dynamically creates Python wrappers for COM objects, which means the exact type of the object can vary and is not known at compile time.)
        appointments = self.get_day_appointments(
            self.get_all_appointments(),
            desired_start,
        )
        desired_start_time = desired_start.replace(second=0)
        desired_end_time = desired_start_time + timedelta(minutes=desired_duration)

        for appointment in appointments:
            appointment_start_time = appointment.Start.replace(tzinfo=None)
            appointment_end_time = appointment.End.replace(tzinfo=None)

            if debug_level > 0:
                console.print(
                    f"Checking if desired block ({desired_start_time} - {desired_end_time}) "
                    f"collides with appointment {appointment.Subject} ({appointment_start_time} - {appointment_end_time})",
                )

            if (
                appointment_start_time >= desired_end_time
            ):  # appointnments are sorted by Start, so it is safe to end early
                break

            if _is_colliding(
                appointment_start_time,
                appointment_end_time,
                desired_start_time,
                desired_end_time,
            ):
                return appointment


def _is_colliding(
    this_start: datetime,
    this_end: datetime,
    other_start: datetime,
    other_end: datetime,
) -> bool:
    return this_start <= other_start < this_end or this_start < other_end <= this_end
