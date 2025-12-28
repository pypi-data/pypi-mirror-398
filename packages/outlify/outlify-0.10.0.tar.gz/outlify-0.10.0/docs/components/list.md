# List

The **List** module in **Outlify** helps structure list information, improving
readability and visual organization when displaying grouped data in
terminal applications. It is especially useful for presenting collections,
options, or summaries in a clean and consistent format.

To view the demo for the **List** module use:

```sh
python -m outlify.list
```

<div class="result" markdown>

```
Outlify helps you create list output in a beautiful format

The first one is the simplest: a titled list
Packages (4): ruff@1.0.0  pytest@1.2.3  mkdocs@3.2.1  mike@0.0.1

Continued...
```

</div>

---

## TitledList
If you need a simple titled list in structured output, you can use `TitledList`.

```python
from outlify.list import TitledList

packages = ['first', 'second', 'third']
print(TitledList(packages))
```

<div class="result" markdown>

```
Content (3): first  second  third
```

</div>

### `title`
Customize the title prefix of the list. The count will be automatically appended.

```python
from outlify.list import TitledList

packages = ['first-package-1.0.0', 'second-package-1.2.3']
print(TitledList(packages, title='Packages'))
```

<div class="result" markdown>

```
Packages (2): first-package-1.0.0  second-package-1.2.3
```

</div>

### `title_separator`
Sets the string separating the title from the list content.
Default is `": "`. Useful for placing items on a new line or changing title formatting.

```python
from outlify.list import TitledList

fruits = ['apple', 'banana', 'orange']
print(TitledList(fruits, title_separator=':\n'))
```

<div class="result" markdown>

```
Content (3):
apple  banana  orange
```

</div>


### `separator`
Change how items are separated in the output. Default is two spaces.

```python
from outlify.list import TitledList

fruits = ['apple', 'banana', 'orange']
print(TitledList(fruits, separator=', '))
```

<div class="result" markdown>

```
Content (3): apple, banana, orange
```

</div>

### `title_style`

You can also style title with the list, for example, 
paint them <span style="color: red;">red</span>, make **bold** or 
<span style="text-decoration: underline;">underlining</span> the text.

You can pass a style like this:

```python
from outlify.list import TitledList
from outlify.style import Colors, Styles

elements = ['elem1', 'elem2']
print(TitledList(elements, title_style=[Colors.red, Styles.bold]))
```

For details on styling, see [Styles](style.md).

### Combining `title_separator` and `separator`
You can combine `title_separator` and `separator` to fully control the layout.
For example, to print each item on a new line with a dash:

```
from outlify.list import TitledList

fruits = ['apple', 'banana', 'orange']
print(TitledList(fruits, title_separator=':\n- ', separator='\n- '))
```

<div class="result" markdown>

```
Content (3):
- apple
- banana
- orange
```

</div>