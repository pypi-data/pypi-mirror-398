# Styles

The **Style** module allows you to customize text styling and colors,
including in **Outlify** elements.

To view the demo for the **Style** module use:

```sh
python -m outlify.style
```

## `Colors` / `Back`

A classes for managing colors.

* `Colors` for text colors aka foreground.
* `Back` for background.

### Standard color: 8-16 Colors

| Color field | Text color codes | Background color codes | Comments         |
|-------------|:----------------:|:----------------------:|------------------|
| `black`     |       `30`       |          `40`          |
| `red`       |       `31`       |          `41`          |
| `green`     |       `32`       |          `42`          |
| `yellow`    |       `33`       |          `43`          |
| `blue`      |       `34`       |          `44`          |
| `magenta`   |       `35`       |          `45`          |
| `cyan`      |       `36`       |          `46`          |
| `white`     |       `37`       |          `47`          |
| `gray`      |       `90`       |         `100`          | Bright black     |
| `crimson`   |       `91`       |         `101`          | Bright red       |
| `lime`      |       `92`       |         `102`          | Bright green     |
| `gold`      |       `93`       |         `103`          | Bright yellow    |
| `skyblue`   |       `94`       |         `104`          | Bright blue      |
| `violet`    |       `95`       |         `105`          | Bright magenta   |
| `aqua`      |       `96`       |         `106`          | Bright cyan      |
| `snow`      |       `97`       |         `107`          | Bright white     |
| `reset`     |       `39`       |          `39`          | Reset all colors |

## `Styles`

A class for managing text styles.

### Available fields

| Style Field / Reset field           | Text style codes | Reset style codes | Description                                                 |
|-------------------------------------|:----------------:|:-----------------:|-------------------------------------------------------------|
| `bold` / `reset_bold`               |       `1`        |       `22`        | Makes text bold or brighter (depending on terminal support) |
| `dim` / `reset_dim`                 |       `2`        |       `22`        | Makes text dim or less intense                              |
| `italic` / `reset_italic`           |       `3`        |       `23`        | Italic text (not supported in many terminal emulators)      |
| `underline` / `reset_underline`     |       `4`        |       `24`        | Underlines the text                                         |
| `blink` / `reset_blink`             |       `5`        |       `25`        | Makes the text blink (deprecated and rarely supported)      |
| `inverse` / `reset_inverse`         |       `7`        |       `27`        | Inverts foreground and background colors                    |
| `hidden` / `reset_hidden`           |       `8`        |       `28`        | Hides the text (useful for passwords, visible when copied)  |
| `crossed_out` / `reset_crossed_out` |       `9`        |       `29`        | Strikes through the text                                    |
| `reset`                             |       `0`        |                   | Reset all styles include colors/styles                      |

## `AnsiCodes`

This is parent class for `Colors`, `Back`, `Styles`. 
But it can help you in your customization as well. 
Just specify the variable name and its value as a code / sequence of codes,
and it will convert your codes to ansi escape sequences on initialization
like this:

```python
from outlify.style import AnsiCodes

class CustomAnsiCodes(AnsiCodes):
    <name> = <code(s)>

Custom = CustomAnsiCodes()
```

And use it as a **Outlify** styles.

If you do not have enough standard colors, for example, you want to add
a branded color of your instrument, then you can use `AnsiCodes`.

* Colors by IDs: [256 Colors](#256-colors) 
* Colors by RGB: [RGB Colors](#rgb-colors) 

### 256 Colors
The following escape codes tells the terminal to use the given color ID:

| Codes             | Description                   |
|-------------------|-------------------------------|
| `38`, `5`, `{ID}` | Set text color aka foreground |
| `48`, `5`, `{ID}` | Set background color          |

You can find more information at [ANSI Escape Sequences: 256 Colors](https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797#256-colors)

How to create your own colors by IDs using `AnsiCodes`:
```python
from outlify.style import AnsiCodes, Colors

class IDAnsiCodes(AnsiCodes):
    pink   = [38, 5, 207]
    orange = [38, 5, 208]

Custom = IDAnsiCodes()
print(f'{Custom.pink}Colored text{Colors.reset}')
```

### RGB Colors

More modern terminals supports [Truecolor](https://en.wikipedia.org/wiki/Color_depth#True_color_.2824-bit.29) (24-bit RGB), which allows you to set foreground and background colors using RGB.

The following escape codes tells the terminal to use the given RGB color:

| Codes                          | Description                           |
|:-------------------------------|:--------------------------------------|
| `38`, `2`, `{r}`, `{g}`, `{b}` | Set text color aka foreground as RGB. |
| `48`, `2`, `{r}`, `{g}`, `{b}` | Set background color as RGB.          |

You can find more information at [ANSI Escape Sequences: RGB Colors](https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797#rgb-colors)

How to create your own colors by IDs using `AnsiCodes`:
```python
from outlify.style import AnsiCodes, Colors

class RGBAnsiCodes(AnsiCodes):
    pink   = [38, 2, 255, 192, 203]
    orange = [38, 2, 255, 128, 0]

Custom = RGBAnsiCodes()
print(f'{Custom.pink}Colored text{Colors.reset}')
```

## Advanced
### Ansi escape sequences

!!! question

    Why are pre-prepared ansi escape sequences for each style used separately instead of together?
    (`\033[1m\033[30m` instead of `\033[1;30m`)

The difference between terminal processing of the first and second variants
is very small. If we make a convenient class that will process and create
one sequence of ansi characters, it will take more time to process it than
separate ones. Convenience is chosen over hundred-thousandths of a second
of execution time.

To check the processing time of these two options, you can run this code:

```python
import time

def timer(text: str):
    now = time.time()
    print(text)
    return time.time() - now

timer('warp up')
x = timer('\033[31m\033[1m\033[0m')
y = timer('\033[31;1m\033[0m')

print("--- Timing Results ---")
print(f"1. Multiple sequences : {x:.10f} seconds")
print(f"2. Single sequence    : {y:.10f} seconds")
print(f"Ratio (x/y)           : {x / y:.4f} faster")
```

<div class="result" markdown>

```
warp up


--- Timing Results ---
1. Multiple sequences : 0.0000038147 seconds
2. Single sequence    : 0.0000033379 seconds
Ratio (x/y)           : 1.1429 faster
```

</div>