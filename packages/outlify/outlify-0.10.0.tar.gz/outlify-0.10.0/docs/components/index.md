# Components
This contains all the Outlify components you can use. 
To view a demo to quickly see the functionality of a particular component, use:
```bash
python -m outlify.<component>
```

For example, to view the demo for the [**Panel**](panel.md) module:
```bash
python -m outlify.panel
```

## Quicklinks
### Panels
<div class="grid" markdown>
[**Panel**](panel.md#panel)

Used for displaying plain text content inside a customizable Panel.
</div>

---

<div class="grid" markdown>
[**ParamsPanel**](panel.md#paramspanel)

Specialized Panel for displaying key-value pairs, often used for configuration settings or parameterized data.
</div>

---

<div class="grid" markdown>
[**Common customization**](panel.md#common-customization)

General Panel customization that does not depend on a specific Panel.
</div>

---

### Lists
<div class="grid" markdown>
[**TitledList**](list.md#titledlist)

Used to output a simple list of headings in a structured form.
</div>

---

### Style
<div class="grid" markdown>
[**Colors / Back**](style.md#colors-back)

A classes for managing colors. 
`Colors` for text colors aka foreground. 
`Back` for background.
</div>

---

<div class="grid" markdown>
[**Styles**](style.md#styles_1)

A class for managing text styles.
</div>

---

<div class="grid" markdown>
[**AnsiCodes**](style.md#ansicodes)

This is parent class for `Colors`, `Back`, `Styles`. 
But it can help you in your customization as well. 
</div>

---