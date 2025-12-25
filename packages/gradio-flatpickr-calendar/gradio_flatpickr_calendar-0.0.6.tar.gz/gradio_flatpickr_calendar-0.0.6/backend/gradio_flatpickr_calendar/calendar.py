from __future__ import annotations
from typing import Any, Callable, Literal
from gradio.components.base import Component
import datetime


class Calendar(Component):
    """
    A calendar component that allows users to select a date or a range of dates.

    Preprocessing: The date passed to the python function will be a string formatted as YYYY-MM-DD or a datetime.datetime object
    depending on the value of the type parameter.

    Postprocessing: The value returned from the function can be a string, a datetime.datetime object or tuples for ranges.

    Parameters:
        value: The default date value, formatted as YYYY-MM-DD. Can be either a string or datetime.datetime object.
        type: The type of the value to pass to the python function. Either "string" or "datetime".
        mode: The mode of the value to pass to the python function. Either "date" for single dates or "range" for ranges.
        label: The label for the component.
        info: Extra text to render below the component.
        show_label: Whether to show the label for the component.
        container: Whether to show the component in a container.
        scale: The relative size of the component compared to other components in the same row.
        min_width: The minimum width of the component.
        interactive: Whether to allow the user to interact with the component.
        visible: Whether to show the component.
        elem_id: The id of the component. Useful for custom js or css.
        elem_classes: The classes of the component. Useful for custom js or css.
        render: Whether to render the component in the parent Blocks scope.
        load_fn: A function to run when the component is first loaded onto the page to set the intial value.
        every: Whether load_fn should be run on a fixed time interval.
        date_format: The date format to use when using "string" type.
    """

    EVENTS = ["change", "input", "submit"]

    def __init__(self, value: str | datetime.datetime = None, *,
                 type: Literal["string", "datetime"] = "datetime",
                 mode: Literal["date", "range"] = "date",
                 label: str | None = None, info: str | None = None,
                 show_label: bool | None = None, container: bool = True, scale: int | None = None,
                 min_width: int | None = None, interactive: bool | None = None, visible: bool = True,
                 elem_id: str | None = None, elem_classes: list[str] | str | None = None,
                 render: bool = True,
                 load_fn: Callable[..., Any] | None = None, every: float | None = None,
                 date_format: str = "%Y-%m-%d"):
        self.date_format = date_format
        self.type = type
        self.mode = mode

        super().__init__(value, label=label, info=info, show_label=show_label, container=container,
                         scale=scale, min_width=min_width, interactive=interactive, visible=visible,
                         elem_id=elem_id, elem_classes=elem_classes, render=render,
                         load_fn=load_fn, every=every)

    def preprocess(self, payload: str | None) -> (str | datetime.datetime | tuple[str, str] |
                                                  tuple[datetime.datetime, datetime.datetime] | None):
        if payload is None:
            return None

        if "to" in payload:
            start_date, end_date = payload.split(" to ")
            if self.type == "string":
                return start_date, end_date
            else:
                return (datetime.datetime.strptime(start_date, self.date_format),
                        datetime.datetime.strptime(end_date, self.date_format))
        else:
            if self.type == "string":
                return payload if self.mode == "date" else (payload, payload)
            else:
                date = datetime.datetime.strptime(payload, self.date_format)
                return date if self.mode == "date" else (date, date)

    def postprocess(self, value: str | datetime.datetime | tuple[str, str] |
                                 tuple[datetime.datetime, datetime.datetime] | None) -> str | None:
        if not value:
            return None

        if isinstance(value, tuple):
            return (f"{v.strftime(self.date_format) if isinstance(v := value[0], datetime.datetime) else v} to "  # type: ignore
                    f"{v.strftime(self.date_format) if isinstance(v := value[1], datetime.datetime) else v}")  # type: ignore
        elif isinstance(value, str):
            return datetime.datetime.strptime(value, self.date_format).strftime(self.date_format)
        elif isinstance(value, datetime.datetime):
            return value.strftime(self.date_format)

        return None

    def example_inputs(self):
        return "2023-01-01"

    def api_info(self):
        return {"type": "string", "description": f"Date string or date range formatted as YYYY-MM-DD."}
