
# `gradio_flatpickr_calendar`
<a href="https://pypi.org/project/gradio_flatpickr_calendar/" target="_blank"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/gradio_flatpickr_calendar"></a> <a href="https://github.com/Florian-BACHO/gradio-flatpickr-calendar/issues" target="_blank"><img alt="Static Badge" src="https://img.shields.io/badge/Issues-white?logo=github&logoColor=black"></a> 

Gradio component for selecting dates or ranges of dates with a Flatpickr calendar 📆

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

## `Calendar`

### Initialization

<table>
<thead>
<tr>
<th align="left">name</th>
<th align="left" style="width: 25%;">type</th>
<th align="left">default</th>
<th align="left">description</th>
</tr>
</thead>
<tbody>
<tr>
<td align="left"><code>value</code></td>
<td align="left" style="width: 25%;">

```python
str | datetime.datetime
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>type</code></td>
<td align="left" style="width: 25%;">

```python
"string" | "datetime"
```

</td>
<td align="left"><code>"datetime"</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>mode</code></td>
<td align="left" style="width: 25%;">

```python
"date" | "range"
```

</td>
<td align="left"><code>"date"</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>label</code></td>
<td align="left" style="width: 25%;">

```python
str | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>info</code></td>
<td align="left" style="width: 25%;">

```python
str | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>show_label</code></td>
<td align="left" style="width: 25%;">

```python
bool | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>container</code></td>
<td align="left" style="width: 25%;">

```python
bool
```

</td>
<td align="left"><code>True</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>scale</code></td>
<td align="left" style="width: 25%;">

```python
int | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>min_width</code></td>
<td align="left" style="width: 25%;">

```python
int | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>interactive</code></td>
<td align="left" style="width: 25%;">

```python
bool | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>visible</code></td>
<td align="left" style="width: 25%;">

```python
bool
```

</td>
<td align="left"><code>True</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>elem_id</code></td>
<td align="left" style="width: 25%;">

```python
str | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>elem_classes</code></td>
<td align="left" style="width: 25%;">

```python
list[str] | str | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>render</code></td>
<td align="left" style="width: 25%;">

```python
bool
```

</td>
<td align="left"><code>True</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>load_fn</code></td>
<td align="left" style="width: 25%;">

```python
typing.Optional[typing.Callable[..., typing.Any]][
    typing.Callable[..., typing.Any][Ellipsis, typing.Any],
    None,
]
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>every</code></td>
<td align="left" style="width: 25%;">

```python
float | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">None</td>
</tr>

<tr>
<td align="left"><code>date_format</code></td>
<td align="left" style="width: 25%;">

```python
str
```

</td>
<td align="left"><code>"%Y-%m-%d"</code></td>
<td align="left">None</td>
</tr>
</tbody></table>


### Events

| name | description |
|:-----|:------------|
| `change` |  |
| `input` |  |
| `submit` |  |



### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As output:** Is passed, the preprocessed input data sent to the user's function in the backend.
- **As input:** Should return, the output data received by the component from the user's function in the backend.

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
 
