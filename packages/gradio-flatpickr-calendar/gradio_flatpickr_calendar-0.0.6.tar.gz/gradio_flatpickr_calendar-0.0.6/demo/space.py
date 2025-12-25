
import gradio as gr
from app import demo as app
import os

_docs = {'Calendar': {'description': 'A calendar component that allows users to select a date or a range of dates.\n\ndepending on the value of the type parameter.\n\n\n    value: The default date value, formatted as YYYY-MM-DD. Can be either a string or datetime.datetime object.\n    type: The type of the value to pass to the python function. Either "string" or "datetime".\n    mode: The mode of the value to pass to the python function. Either "date" for single dates or "range" for ranges.\n    label: The label for the component.\n    info: Extra text to render below the component.\n    show_label: Whether to show the label for the component.\n    container: Whether to show the component in a container.\n    scale: The relative size of the component compared to other components in the same row.\n    min_width: The minimum width of the component.\n    interactive: Whether to allow the user to interact with the component.\n    visible: Whether to show the component.\n    elem_id: The id of the component. Useful for custom js or css.\n    elem_classes: The classes of the component. Useful for custom js or css.\n    render: Whether to render the component in the parent Blocks scope.\n    load_fn: A function to run when the component is first loaded onto the page to set the intial value.\n    every: Whether load_fn should be run on a fixed time interval.\n    date_format: The date format to use when using "string" type.', 'members': {'__init__': {'value': {'type': 'str | datetime.datetime', 'default': 'None', 'description': None}, 'type': {'type': '"string" | "datetime"', 'default': '"datetime"', 'description': None}, 'mode': {'type': '"date" | "range"', 'default': '"date"', 'description': None}, 'label': {'type': 'str | None', 'default': 'None', 'description': None}, 'info': {'type': 'str | None', 'default': 'None', 'description': None}, 'show_label': {'type': 'bool | None', 'default': 'None', 'description': None}, 'container': {'type': 'bool', 'default': 'True', 'description': None}, 'scale': {'type': 'int | None', 'default': 'None', 'description': None}, 'min_width': {'type': 'int | None', 'default': 'None', 'description': None}, 'interactive': {'type': 'bool | None', 'default': 'None', 'description': None}, 'visible': {'type': 'bool', 'default': 'True', 'description': None}, 'elem_id': {'type': 'str | None', 'default': 'None', 'description': None}, 'elem_classes': {'type': 'list[str] | str | None', 'default': 'None', 'description': None}, 'render': {'type': 'bool', 'default': 'True', 'description': None}, 'load_fn': {'type': 'typing.Optional[typing.Callable[..., typing.Any]][\n    typing.Callable[..., typing.Any][Ellipsis, typing.Any],\n    None,\n]', 'default': 'None', 'description': None}, 'every': {'type': 'float | None', 'default': 'None', 'description': None}, 'date_format': {'type': 'str', 'default': '"%Y-%m-%d"', 'description': None}}, 'postprocess': {'value': {'type': 'str\n    | datetime.datetime\n    | tuple[str, str]\n    | tuple[datetime.datetime, datetime.datetime]\n    | None', 'description': "The output data received by the component from the user's function in the backend."}}, 'preprocess': {'return': {'type': 'str\n    | datetime.datetime\n    | tuple[str, str]\n    | tuple[datetime.datetime, datetime.datetime]\n    | None', 'description': "The preprocessed input data sent to the user's function in the backend."}, 'value': None}}, 'events': {'change': {'type': None, 'default': None, 'description': ''}, 'input': {'type': None, 'default': None, 'description': ''}, 'submit': {'type': None, 'default': None, 'description': ''}}}, '__meta__': {'additional_interfaces': {}, 'user_fn_refs': {'Calendar': []}}}

abs_path = os.path.join(os.path.dirname(__file__), "css.css")

with gr.Blocks(
    css=abs_path,
    theme=gr.themes.Default(
        font_mono=[
            gr.themes.GoogleFont("Inconsolata"),
            "monospace",
        ],
    ),
) as demo:
    gr.Markdown(
"""
# `gradio_flatpickr_calendar`

<div style="display: flex; gap: 7px;">
<a href="https://pypi.org/project/gradio_flatpickr_calendar/" target="_blank"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/gradio_flatpickr_calendar"></a> <a href="https://github.com/Florian-BACHO/gradio-flatpickr-calendar/issues" target="_blank"><img alt="Static Badge" src="https://img.shields.io/badge/Issues-white?logo=github&logoColor=black"></a> 
</div>

Gradio component for selecting dates or ranges of dates with a Flatpickr calendar 📆
""", elem_classes=["md-custom"], header_links=True)
    app.render()
    gr.Markdown(
"""
## Installation

```bash
pip install gradio_flatpickr_calendar
```

## Usage

```python
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

```
""", elem_classes=["md-custom"], header_links=True)


    gr.Markdown("""
## `Calendar`

### Initialization
""", elem_classes=["md-custom"], header_links=True)

    gr.ParamViewer(value=_docs["Calendar"]["members"]["__init__"], linkify=[])


    gr.Markdown("### Events")
    gr.ParamViewer(value=_docs["Calendar"]["events"], linkify=['Event'])




    gr.Markdown("""

### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As input:** Is passed, the preprocessed input data sent to the user's function in the backend.
- **As output:** Should return, the output data received by the component from the user's function in the backend.

 ```python
def predict(
    value: str
    | datetime.datetime
    | tuple[str, str]
    | tuple[datetime.datetime, datetime.datetime]
    | None
) -> str
    | datetime.datetime
    | tuple[str, str]
    | tuple[datetime.datetime, datetime.datetime]
    | None:
    return value
```
""", elem_classes=["md-custom", "Calendar-user-fn"], header_links=True)




    demo.load(None, js=r"""function() {
    const refs = {};
    const user_fn_refs = {
          Calendar: [], };
    requestAnimationFrame(() => {

        Object.entries(user_fn_refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}-user-fn`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })

        Object.entries(refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })
    })
}

""")

demo.launch()
