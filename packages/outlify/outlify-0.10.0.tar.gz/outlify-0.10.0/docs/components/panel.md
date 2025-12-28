# Panels

The **Panel** module in **Outlify** provides a way to display content within structured, 
visually distinct panels. This is especially useful for emphasizing important information
in your cli outputs. Panels can have titles, borders, and various formatting styles,
making them perfect for logging warnings, errors, or key messages.

To view the demo for the **Panel** module use:

```sh
python -m outlify.panel
```

<div class="result" markdown>

```
╭─ Welcome to Outlify ───────────────────────────────╮
│ Outlify helps you render beautiful command-line    │
│ panels.                                            │
│ You can customize borders, alignment, etc.         │
│                                                    │
│ This is just a simple text panel.                  │
╰───────────────────────────────────Text Panel Demo──╯

Continued...
```

</div>

---

## Panel
For normal text output without any customization you can just pass the text inside `Panel`:
```python
from outlify.panel import Panel

print(Panel('A very important text'))
```

For details on customizing the Panel, see [Common customization](#common-customization).

## ParamsPanel
If you want to display parameters, environment variables or anything else, `ParamsPanel` is perfect for you.

Unlike a regular `Panel`, in a `ParamPanel` you do not pass plain text, but a key-value structure:

```python
from outlify.panel import ParamsPanel

parameters = {'parameter1': 'value1', 'parameter2': 'value2'}
print(ParamsPanel(parameters, title='Startup Parameters'))
```

### `hidden`
To hide sensitive data you can use `hidden` argument:

```python
from outlify.panel import ParamsPanel

parameters = {
    'parameter1': 'value1', 
    'parameter2': 'value2', 
    'token': 'fake-token'
}
print(ParamsPanel(parameters))
```

<div class="result" markdown>

```
╭──────────────────────────────────────╮
│ parameter1 = value1                  │
│ parameter2 = value2                  │
│ token      = *****                   │
╰──────────────────────────────────────╯
```
</div>

Keys to hide can be passed as regex: 

1. a string to be compiled into regex
2. an already precompiled regex. The default is patterns: `.*password.*`, `.*token.*`

!!! tip

    If you don't want to mask anything, pass an empty list.

!!! note

    `hidden` works in such a way that if a value is passed to it
    and it needs to be masked, it will output `*****` instead of the value,
    if it is empty, it will output the result of the masking too.

### `separator`
The default is ` = ` between the key and the value, but this can be overridden using `separator` argument to,
for example, `: `:

```python
from outlify.panel import ParamsPanel

parameters = {'parameter1': 'value1', 'parameter2': 'value2'}
print(ParamsPanel(parameters, separator=': '))
```

<div class="result" markdown>

```
╭──────────────────────────────────────╮
│ parameter1: value1                   │
│ parameter2: value2                   │
╰──────────────────────────────────────╯
```
</div>

### `params_style`
if you want to style variable names in parameters, you can use `params_style`.
This works the same way as [`title_style` / `subtitle_style` / `border_style`](#title_style-subtitle_style-border_style) 

### In addition
Also a feature of `ParamsPanel` is that values are aligned to the `separator` if they are too large, for example:

```python
from outlify.panel import ParamsPanel

parameters = {
    'parameter1': 'This is a fake value to show you how Outlify can wrap text in the Parameters Panel', 
    'parameter2': 'value2'
}
print(ParamsPanel(parameters, separator=': '))
```

<div class="result" markdown>

```
╭──────────────────────────────────────╮
│ parameter1: This is a fake value to  │
│             show you how Outlify can │
│              wrap text in the        │
│             Parameters Panel         │
│ parameter2: value2                   │
╰──────────────────────────────────────╯
```
</div>

For details on customizing the Panel, see [Common customization](#common-customization).

## Common customization
In any Panel you can customize Panel width, titles, its aligns and borders and.

### `width`
You can specify `width` like this:

```python
from outlify.panel import Panel

text = 'My text'
print(Panel(text, width=len(text) + 4))
```

<div class="result" markdown>

```
╭─────────╮
│ My text │
╰─────────╯
```

</div>

If you don't specify a size, it will automatically adjust for the terminal size. 

!!! note

    For CI systems it is not possible to calculate the size and the Panel will be size 80

### `title` / `subtitle`
You can specify titles using `title` (for header title) or `subtitle` (for footer title) like this:


```python
from outlify.panel import Panel

print(Panel('My text', title='Header title', subtitle='Footer title'))
```

<div class="result" markdown>

```
╭─────────────Header title─────────────╮
│ My text                              │
╰─────────────Footer title─────────────╯
```

</div>

### `title_align` / `subtitle_align`
By default, the title is placed in the `center` of the Panel, 
but you can move it to the `left` or `right` by specifying:

```python
from outlify.panel import Panel

print(Panel('My text', title='Header title', title_align='left'))
```

<div class="result" markdown>

```
╭──Header title────────────────────────╮
│ My text                              │
╰──────────────────────────────────────╯
```

</div>

Works the same way for `subtitle`.

You can also use the `Align` enum from `outlify.styles` to do this:

```python
from outlify.style import Align
from outlify.panel import Panel

print(Panel('My text', title='Header title', title_align=Align.left))
```

<div class="result" markdown>

```
╭──Header title────────────────────────╮
│ My text                              │
╰──────────────────────────────────────╯
```

</div>

### `title_conns` / `subtitle_conns`
You can add connectors to your title / subtitle

```python
from outlify.panel import Panel

print(Panel('My text', title='Title', title_conns='<<>>'))
```

<div class="result" markdown>

```
╭──────────────<<Title>>───────────────╮
│ My text                              │
╰──────────────────────────────────────╯
```

</div>

Works the same way for `subtitle`.

### `border`
You can replace the default borders using `border` like this:

```python
from outlify.panel import Panel

print(Panel('My text', border='╔╗╚╝═║'))
```

<div class="result" markdown>

```
╔══════════════════════════════════════╗
║ My text                              ║
╚══════════════════════════════════════╝
```

</div>

or to make it clearer in the code, use `BorderStyle`:

```python
from outlify.style import BorderStyle
from outlify.panel import Panel

border = BorderStyle(
    lt='╔', rt='╗',
    lb='╚', rb='╝',
    headers='═', sides='║'
)
print(Panel('My text', border=border))
```

<div class="result" markdown>

```
╔══════════════════════════════════════╗
║ My text                              ║
╚══════════════════════════════════════╝
```

</div>

Here `lt`, `rt` are the top left and right corners, 
`lb`, `rb` are the bottom corners. 
`headers` are the symbols for the "caps" at the top and bottom, 
and `siders` are the side symbols.

The `siders` deserve special attention. If you specify it as an empty string, 
or in case of using not `BorderStyle` but a `str`, specify five characters instead of six, 
the text inside Panel will not wrap, it will stretch to the full width of the terminal.

```python
from outlify.panel import Panel

long_text = (
        "In a world where CLI tools are often boring and unstructured, "
        "Outlify brings beauty and structure to your terminal output. "
        "It allows developers to create elegant panels with customizable "
        "borders, titles, subtitles, and aligned content — all directly "
        "in the terminal.\n\n"
        "Outlify is lightweight and dependency-free — it uses only Python’s "
        "standard libraries, so you can easily integrate it into any "
        "project without worrying about bloat or compatibility issues.\n\n"
        "Whether you're building debugging tools, reporting pipelines, or "
        "just want to print data in a cleaner way, "
        "Outlify helps you do it with style."
    )
print(Panel(long_text, border='╔╗╚╝═'))
```

<div class="result" markdown>

```
╔══════════════════════════════════════╗
 In a world where CLI tools are often boring and unstructured, Outlify brings beauty and structure to your terminal output. It allows developers to create elegant panels with customizable borders, titles, subtitles, and aligned content — all directly in the terminal.
                                     
 Outlify is lightweight and dependency-free — it uses only Python’s standard libraries, so you can easily integrate it into any project without worrying about bloat or compatibility issues.
                                     
 Whether you're building debugging tools, reporting pipelines, or just want to print data in a cleaner way, Outlify helps you do it with style.
╚══════════════════════════════════════╝
```

</div>

### `title_style` / `subtitle_style` / `border_style`

You can also style title with the list, for example, 
paint them <span style="color: red;">red</span>, make **bold** or 
<span style="text-decoration: underline;">underlining</span> the text.

You can pass a style like this:

```python
from outlify.panel import Panel
from outlify.style import Colors, Styles

print(Panel('Text', title_style=[Colors.red], border_style=[Styles.bold]))
```

For details on styling, see [Styles](style.md).
