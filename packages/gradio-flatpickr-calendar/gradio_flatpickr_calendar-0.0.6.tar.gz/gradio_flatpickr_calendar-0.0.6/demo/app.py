import gradio as gr
from gradio_flatpickr_calendar import Calendar
import datetime


def predict(date: datetime.datetime | tuple[datetime.datetime, datetime.datetime]) \
        -> datetime.datetime | tuple[datetime.datetime, datetime.datetime]:
    return date


demo = gr.Interface(fn=predict,
                    inputs=[Calendar(label="Select a date or a range of dates",
                                     info="Click to bring up the calendar.",
                                     mode="range", type="datetime")],
                    outputs=Calendar(label="Selected date(s)", info="Here are the date(s) you selected:"),
                    examples=["2023-01-01", ("2023-01-01", "2023-12-11")],
                    cache_examples=True,
                    title="Choose a date")

if __name__ == "__main__":
    demo.launch()
