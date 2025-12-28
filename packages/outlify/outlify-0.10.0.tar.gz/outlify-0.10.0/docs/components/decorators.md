# Decorators

The **Decorators** module in **Outlify** provides a collection of decorators
designed to extend the capabilities of features, preserving the original
feature signatures and metadata and adding useful behavior.

To view the demo for the **Decorators** module use:

```sh
python -m outlify.decorators
```

<div class="result" markdown>

```
    @timer()
    def dummy_func(a: int, b: int) -> int:
        return a + b
    
Function 'dummy_func' took 00:00:00.123

Continued...
```

</div>

---

## timer
Use the timer decorator to time the execution of the function

```python
import time
from outlify.decorators import timer

@timer()
def dummy():
    time.sleep(1)

dummy()
```

<div class="result" markdown>

```
Function 'dummy' took 00:00:01.000
```

</div>

### `label`
To set a custom label for a function, use:

```python
import time
from outlify.decorators import timer

@timer(label='Custom name')
def dummy():
    time.sleep(1)

dummy()
```

<div class="result" markdown>

```
Custom name took 00:00:01.000
```

</div>

### `label_style`
To set a colors / styles for label of a function, use:

```python
import time
from outlify.decorators import timer
from outlify.style import Colors

@timer(label_style=[Colors.red])
def dummy():
    time.sleep(1)

dummy()
```

For details on styling, see [Styles](style.md).

### `connector`
Word or phrase used to connect the label and the measured duration in the output message (e.g. "took", "in", "completed in")

```python
import time
from outlify.decorators import timer

@timer(connector='in')
def dummy():
    time.sleep(1)

dummy()
```

<div class="result" markdown>

```
Function 'dummy' in 00:00:01.000
```

</div>

### `time_format`
Specifies the format string used to display the function's execution duration.

```python
import time
from outlify.decorators import timer

@timer(time_format='{h} hours {m:02} minutes {s:02} seconds')
def dummy():
    time.sleep(1)

dummy()
```

<div class="result" markdown>

```
Function 'dummy' took 0 hours 00 minutes 01 seconds
```

</div>

The string should use Python’s standard `str.format` syntax and supports
the following placeholders:

* `{h}` - hours
* `{m}` - minutes (0–59)
* `{s}` - seconds (0–59)
* `{ms}` - milliseconds (0–999)

You can fully customize the output format using any combination
of these placeholders along with Python formatting options.

#### Examples

* Default format: `"{h:02}:{m:02}:{s:02}.{ms:03}"` → `00:01:23.456`
* Human-readable format: `"{m} min {s} sec"` → `1 min 23 sec`
* Minimal format: `"{m}:{s}"` → `1:23`

If the format string contains any invalid key, e.g., `{minutes}` instead of `{m}`,
a `KeyError` will be raised, indicating the allowed keys.

### `time_style`
To set a colors / styles for function runtime, use:

```python
import time
from outlify.decorators import timer
from outlify.style import Colors, Styles

@timer(time_style=[Colors.crimson, Styles.underline])
def dummy():
    time.sleep(1)

dummy()
```

For details on styling, see [Styles](style.md).

### `output_func`
Specifies the function that will be used to output the final timing message.

```python
import logging
import time
from outlify.decorators import timer

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

@timer(output_func=logger.info)
def dummy():
    time.sleep(1)

dummy()
```

<div class="result" markdown>

```
INFO:root:Function 'dummy' took 00:00:01.000
```

</div>