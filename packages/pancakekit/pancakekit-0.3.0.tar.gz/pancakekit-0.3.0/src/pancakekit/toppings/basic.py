import os, ast
import traceback
from typing import Optional, Union, Any, Iterable
from ..pancakekit import Topping, Tag, Arrangement, GroupContainer
from ..utils import get_number, pk_wrapped_dict


class Button(Topping):
    def __init__(self, title:str, style: dict=None, **kwargs):
        super().__init__(title, style, **kwargs)

    def prepare(self, title, style):
        self.value = title
        properties = {
            "type": "button",
            "variant": "brand",
            "appearance": "filled-outlined",
        }

        base_style = {}
        if style is not None:
            base_style.update(style)
        # Use Web Awesome's default button appearance.
        self.button = Tag("wa-button", properties, style=base_style, value_ref=self)
        
    def html(self):
        if self.pressed:
            initial_event = "onclick" if self.clicked else "pressed"
            self.button.set_click_response(pressable=True, initial_event=initial_event)
        else:
            self.button.set_click_response()
        return self.button.render()

    def event_preprocessor(self, event):
        if event.event_type in ("onclick", "pressed"):
            return self.value
    
    def set_title(self, title):
        self.value = title

    @property
    def title(self):
        return self.value
    
    @title.setter
    def title(self, value):
        self.set_title(value)

class Label(Topping):
    def __init__(self, text: str="", style: dict=None, **kwargs):
        super().__init__(text, style, **kwargs)

    def prepare(self, text: str, style: dict):
        if style is None:
            style = {}
        self.value = text
        self.label = Tag("label", style=style, value_ref=self)
        
    def html(self):
        return self.label.render()

class Text(Topping):
    def __init__(self, text="", align: str=None, shadow: int=None, shadow_blur: int=None, style: dict=None, **kwargs):
        super().__init__(text, align, shadow, shadow_blur, style, **kwargs)

    def prepare(self, text="", align=None, shadow=None, shadow_blur=None, style=None):
        self.value = text
        if style is None:
            style = {}
        if align is not None:
            style["text-align"] = align
        if shadow is not None:
            shadow_blur = shadow if shadow_blur is None else shadow_blur
            style["text-shadow"] = f"{shadow}px {shadow}px {shadow_blur}px #bbb"
        self.div = Tag("div", style=style, value_ref=self)
        
    def html(self):
        return self.div.render()

class Paragraph(Topping):
    def __init__(self, text: str="", style: dict=None, **kwargs):
        super().__init__(text, style, **kwargs)

    def prepare(self, text: str, style: dict):
        if style is None:
            style = {}
        self.value = text
        self.p = Tag("p", style=style)

    def html(self):
        return self.p.render()
    

class Input(Topping):
    def __init__(self, label: Optional[str]=None, default: Union[str, int, float]=None, placeholder: Any=None, **kwargs):
        super().__init__(label=label, default=default, placeholder=placeholder, **kwargs)

    def prepare(self, label, default, placeholder):
        self.value_type = type(default)
        self.label = label
        self.value = default if default is not None else ""
        if placeholder is None:
            placeholder = default
        style = {"max-width": "12em", "min-width": "10em"}
        input_type = "text"
        if self.value_type in (int, float):
            input_type = "number"
        properties = {"type": input_type, "placeholder": placeholder}
        if self.label is not None:
            properties["label"] = self.label
        # Use Web Awesome's default input appearance.
        self.user_input = Tag("wa-input", properties, style=style, value_ref=self)

    def html(self):
        return self.user_input.render()
    
    def value_getter(self):
        if self.value_type is type(None):
            return get_number(self._value)
        try:
            return self.value_type(self._value)
        except:
            pass
        return self._value


def _normalize_choice_options(options: Any) -> list[dict[str, Any]]:
    """Normalize choice options into a list of dicts with stable string keys.

    Supported input forms:
      - dict: treated as {label: value}
      - iterable of values: labels are str(value)
      - iterable of 2-tuples: (label, value) or (value, label) (heuristic)
    """
    if options is None:
        return []

    pairs: list[tuple[str, Any]] = []
    if isinstance(options, dict):
        for label, value in options.items():
            pairs.append((str(label), value))
    elif isinstance(options, Iterable) and not isinstance(options, (str, bytes)):
        for item in options:
            if isinstance(item, (tuple, list)) and len(item) == 2:
                a, b = item
                # Common patterns:
                #   ("Label", value) or (value, "Label")
                if isinstance(a, str) and not isinstance(b, str):
                    label, value = a, b
                elif not isinstance(a, str) and isinstance(b, str):
                    value, label = a, b
                else:
                    label, value = a, b
                pairs.append((str(label), value))
            else:
                pairs.append((str(item), item))
    else:
        raise TypeError("options must be a dict or an iterable of values/2-tuples")

    normalized: list[dict[str, Any]] = []
    for index, (label, value) in enumerate(pairs):
        normalized.append({"key": str(index), "label": label, "value": value})
    return normalized


class Select(Topping):
    def __init__(
        self,
        label: Optional[str],
        options: Any,
        value: Any = None,
        placeholder: Any = None,
        *,
        with_clear: bool = False,
        allow_none: bool | None = None,
        disabled: bool = False,
        **kwargs,
    ):
        super().__init__(
            label=label,
            options=options,
            value=value,
            placeholder=placeholder,
            with_clear=with_clear,
            allow_none=allow_none,
            disabled=disabled,
            **kwargs,
        )

    def prepare(
        self,
        label: Optional[str],
        options: Any,
        value: Any = None,
        placeholder: Any = None,
        with_clear: bool = False,
        allow_none: bool | None = None,
        disabled: bool = False,
    ):
        self.label = label
        self._options = _normalize_choice_options(options)
        self._key_to_value = {opt["key"]: opt["value"] for opt in self._options}
        self._allow_none = bool(with_clear) if allow_none is None else bool(allow_none)

        # Use Web Awesome's default select appearance.
        style = {"max-width": "16em", "min-width": "12em"}
        properties: dict[str, Any] = {}
        if placeholder is not None:
            properties["placeholder"] = placeholder
        if self.label is not None:
            properties["label"] = self.label
        if with_clear:
            properties["with-clear"] = None
        if disabled:
            properties["disabled"] = None

        self.user_input = Tag("wa-select", properties, style=style, value_ref=self)
        for opt in self._options:
            option = self.user_input.add("wa-option", {"value": opt["key"]})
            option.add_html(opt["label"])

        if value is None and not self._allow_none and len(self._options) > 0:
            value = self._options[0]["value"]
        self.value = value

    def html(self):
        return self.user_input.render()

    def html_value(self, tag_name=None):
        if self._value is None:
            return ""
        if isinstance(self._value, str) and self._value in self._key_to_value:
            return self._value
        for opt in self._options:
            if opt["value"] == self._value:
                return opt["key"]
        return ""

    def web_value_proprocessor(self, tag: Tag, value: Any):
        if value is None:
            return None if self._allow_none else (self._options[0]["value"] if len(self._options) > 0 else None)
        key = str(value)
        if key == "":
            return None if self._allow_none else (self._options[0]["value"] if len(self._options) > 0 else None)
        if key in self._key_to_value:
            return self._key_to_value[key]
        return self._value

    def value_preprocessor(self, value: Any):
        if value is None or value == "":
            return None if self._allow_none else (self._options[0]["value"] if len(self._options) > 0 else None)
        if isinstance(value, str) and value in self._key_to_value:
            return self._key_to_value[value]
        for opt in self._options:
            if opt["value"] == value:
                return opt["value"]
        return self._value


class Switch(Topping):
    def __init__(
        self,
        label: str = "",
        value: bool = False,
        *,
        disabled: bool = False,
        **kwargs,
    ):
        super().__init__(label=label, value=value, disabled=disabled, **kwargs)

    def prepare(self, label: str = "", value: bool = False, disabled: bool = False):
        self.label = label
        properties: dict[str, Any] = {}
        if disabled:
            properties["disabled"] = None
        if bool(value):
            properties["checked"] = None

        # Use Web Awesome's default switch appearance.
        self.user_input = Tag("wa-switch", properties, value_ref=self)
        if self.label:
            self.user_input.add_html(self.label)

        self.value = value

    def html(self):
        return self.user_input.render()

    def web_value_proprocessor(self, tag: Tag, value: Any):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("1", "true", "t", "yes", "y", "on"):
                return True
            if v in ("0", "false", "f", "no", "n", "off", ""):
                return False
        return bool(value)

    def value_preprocessor(self, value):
        return bool(value)


class RadioGroup(Topping):
    def __init__(
        self,
        label: Optional[str],
        options: Any,
        value: Any = None,
        *,
        orientation: str = "vertical",
        appearance: Optional[str] = None,
        allow_none: bool = False,
        disabled: bool = False,
        **kwargs,
    ):
        super().__init__(
            label=label,
            options=options,
            value=value,
            orientation=orientation,
            appearance=appearance,
            allow_none=allow_none,
            disabled=disabled,
            **kwargs,
        )

    def prepare(
        self,
        label: Optional[str],
        options: Any,
        value: Any = None,
        orientation: str = "vertical",
        appearance: Optional[str] = None,
        allow_none: bool = False,
        disabled: bool = False,
    ):
        self.label = label
        self._options = _normalize_choice_options(options)
        self._key_to_value = {opt["key"]: opt["value"] for opt in self._options}
        self._allow_none = bool(allow_none)
        self.orientation = "horizontal" if str(orientation).lower().startswith("h") else "vertical"
        self.appearance = appearance

        properties: dict[str, Any] = {"orientation": self.orientation}
        if self.label is not None:
            properties["label"] = self.label
        if disabled:
            properties["disabled"] = None

        self.user_input = Tag("wa-radio-group", properties, value_ref=self)
        for opt in self._options:
            radio_props: dict[str, Any] = {"value": opt["key"]}
            if self.appearance is not None:
                radio_props["appearance"] = self.appearance
            radio = self.user_input.add("wa-radio", radio_props)
            radio.add_html(opt["label"])

        if value is None and not self._allow_none and len(self._options) > 0:
            value = self._options[0]["value"]
        self.value = value

    def html(self):
        return self.user_input.render()

    def html_value(self, tag_name=None):
        if self._value is None:
            return ""
        if isinstance(self._value, str) and self._value in self._key_to_value:
            return self._value
        for opt in self._options:
            if opt["value"] == self._value:
                return opt["key"]
        return ""

    def web_value_proprocessor(self, tag: Tag, value: Any):
        if value is None:
            return None if self._allow_none else (self._options[0]["value"] if len(self._options) > 0 else None)
        key = str(value)
        if key == "":
            return None if self._allow_none else (self._options[0]["value"] if len(self._options) > 0 else None)
        if key in self._key_to_value:
            return self._key_to_value[key]
        return self._value

    def value_preprocessor(self, value: Any):
        if value is None or value == "":
            return None if self._allow_none else (self._options[0]["value"] if len(self._options) > 0 else None)
        if isinstance(value, str) and value in self._key_to_value:
            return self._key_to_value[value]
        for opt in self._options:
            if opt["value"] == value:
                return opt["value"]
        return self._value


class ProgressBar(Topping):
    def __init__(
        self,
        value: float = 0,
        *,
        label: Optional[str] = None,
        max_value: float = 100,
        show_value: bool = True,
        **kwargs,
    ):
        super().__init__(value=value, label=label, max_value=max_value, show_value=show_value, **kwargs)

    def prepare(self, value: float = 0, label: Optional[str] = None, max_value: float = 100, show_value: bool = True):
        self.label = label
        self.max_value = max_value if max_value is not None else 100
        self.show_value = bool(show_value)

        label_style = {
            "font-size": "var(--wa-font-size-s)",
            "color": "var(--wa-color-text-quiet)",
            "margin-bottom": "4px",
        }
        self._label_tag = Tag("div", properties={"class": "pk-progress__label"}, style=label_style, value_ref=self, name="label")
        self._progress_tag = Tag(
            "progress",
            properties={"class": "pk-progress", "max": self.max_value},
            style={"width": "100%"},
            value_ref=self,
            name="progress",
        )

        self.value = value

    def html_value(self, tag_name=None):
        if tag_name == "label":
            return self._format_label()
        if tag_name == "progress":
            return self._clamp_value(self._value)
        return self._clamp_value(self._value)

    def _clamp_value(self, value):
        try:
            value = float(value)
        except Exception:
            return 0
        if self.max_value is None:
            return value
        try:
            max_value = float(self.max_value)
        except Exception:
            max_value = 100
        if max_value <= 0:
            return 0
        return max(0.0, min(value, max_value))

    def _format_label(self) -> str:
        if not self.show_value and not self.label:
            return ""
        current = self._clamp_value(self._value)
        try:
            max_value = float(self.max_value)
        except Exception:
            max_value = 100.0
        if max_value <= 0:
            pct = 0
        else:
            pct = int(round(current / max_value * 100))
        prefix = f"{self.label}: " if self.label else ""
        if self.show_value:
            return f"{prefix}{pct}%"
        return prefix.rstrip()

    def html(self):
        container = Tag("div", style={"width": "100%", "max-width": "32em"})
        container.add(self._label_tag)
        container.add(self._progress_tag)
        return container.render()

    def value_preprocessor(self, value):
        try:
            return float(value)
        except Exception:
            return self._value

class Slider(Topping):
    def __init__(self, label:str, range_min:float, range_max:float, value:Optional[float]=None, step: float=1.0, **kwargs):
        super().__init__(label, range_min, range_max, value=value, step=step, **kwargs)

    def prepare(self, label, range_min, range_max, value=None, step=1.0):
        self.label_str = label
        self.value_display_func = None
        self.ranges = (range_min, range_max, step)
        if value is None:
            value = self.ranges[0]

        # Use Web Awesome's default slider appearance.
        self.user_input = Tag("wa-slider", style={"width": "100%"}, value_ref=self)

        self.set_value(value, skip_update=True)
        
    def html(self):
        div = Tag("div")
        current_value = self.value
        display_value = self.value_display_func(current_value) if self.value_display_func is not None else current_value
        label = div.add("div", style={"font-size": "var(--wa-font-size-s)", "color": "var(--wa-color-text-quiet)", "margin-bottom": "4px"})
        label.add_html(f"{self.label_str}: {display_value}")
        self.user_input.properties["min"] = self.ranges[0]
        self.user_input.properties["max"] = self.ranges[1]
        self.user_input.properties["step"] = self.ranges[2]
        div.add(self.user_input)
        return div.render()
    
    def value_preprocessor(self, value):
        return value
    
    def value_getter(self):
        return get_number(self._value)
            
    @property
    def display(self):
        return self.value_display_func
    
    @display.setter
    def display(self, func):
        self.value_display_func = func
        if self.value is not None:
            self.set_value(self.value, force_update=True)

class DictInput(Topping):
    def __init__(self, default:dict, horizontal:bool=False, **kwargs):
        super().__init__(default, horizontal=horizontal, **kwargs)

    def prepare(self, default:dict, horizontal:bool=False):
        self.horizontal = horizontal
        self.input_dict = {}
        self._set(default)

    def _set(self, d):
        if not isinstance(d, dict):
            return
        if not self.horizontal:
            grid = self.add(Column(centering=False, padding=False))
        else:
            grid = self.add(Row())
        for key, value in d.items():
            label = key.replace("_", " ").capitalize() if len(key) > 1 else key
            self.input_dict[key] = grid.add(Input(label, value, _dict_input_key=key))

    def html(self):
        if len(self.input_dict) == 0:
            return ""
        card = Tag("wa-card", style={"width": "fit-content", "margin": "5px"})
        inner = card.add("div", style={"padding": "8px"})
        inner.add_html(self.children_html)
        return card.render()

    def items(self):
        return self.value.items()

    def converted_dict(self):
        return {k: self[k] for k in self.input_dict.keys()}
    
    def value_preprocessor(self, d:dict):
        for key, value in d.items():
            if key in self.input_dict:
                self.input_dict[key].value = value
        return None # to prevent value substitution

    def value_getter(self):
        def setitem_callback(key, value):
            self.__setitem__(key, value)
        return pk_wrapped_dict(setitem_callback, {key:self[key] for key in self.input_dict.keys()})
    
    def event_preprocessor(self, event):
        if event.event_type == "value_changed" and event.origin is not None:
            return (event.origin.arguments["_dict_input_key"], event.value)

    def __getitem__(self, key):
        if key not in self.input_dict:
            return
        try:
            return ast.literal_eval(self.input_dict[key].value)
        except:
            return self.input_dict[key].value

    def __setitem__(self, key, value):
        if key not in self.input_dict:
            return
        self.input_dict[key].value = value
    
    def __str__(self):
        return_str = ""
        for key, item in self.input_dict.items():
            return_str += f"{key}:{item.value}" + os.linesep
        return return_str


class GridPanel(Topping):
    def __init__(self, size: tuple[int, int], status_dict: dict | None = None, style: dict | None = None, **kwargs):
        super().__init__(size=size, status_dict=status_dict, style=style, **kwargs)
        self._value = {} if status_dict is None else dict(status_dict)
        self._status_input: DictInput | None = None
        self._sync_status_input(self._ensure_status_dict())

    def prepare(self, size: tuple[int, int], status_dict: dict | None = None, style: dict | None = None):
        self.rows, self.cols = size
        style = {} if style is None else style.copy()
        button_size = style.pop("button_size", 64)
        square_size = f"{button_size}px"
        self.button_size = button_size
        # Account for the default 2px margin on each side of the button.
        self.cell_size = f"{button_size + 4}px"
        self.default_button_style = {
            "width": square_size,
            "height": square_size,
            "display": "inline-flex",
            "align-items": "center",
            "justify-content": "center",
            "padding": "0.5rem",
            "margin": "2px",
            "box-sizing": "border-box",
            "appearance": "auto",
            "font": "inherit",
        }
        if style is not None:
            self.default_button_style.update(style)

        self.button_positions: dict[tuple[int, int], Button] = {}
        self.button_names: dict[tuple[int, int], str] = {}
        self._button_clicked_handler = None
        self._button_pressed_handler = None
        if status_dict is not None and (self._value is None or not isinstance(self._value, dict) or len(self._value) == 0):
            self._value = dict(status_dict)
        elif self._value is None or not isinstance(self._value, dict):
            self._value = {}
        self._sync_status_input(self._ensure_status_dict())

    def _ensure_status_dict(self) -> dict:
        if self._value is None or not isinstance(self._value, dict):
            self._value = {}
        return self._value

    def _sync_status_input(self, status_dict: dict) -> None:
        if self._status_input is None:
            self._status_input = self.add(DictInput(status_dict), name="status")
            self._status_input.value_changed = self._on_status_input_changed
            return

        existing_keys = set(getattr(self._status_input, "input_dict", {}).keys())
        target_keys = set(status_dict.keys())
        if existing_keys != target_keys:
            self.remove(self._status_input.name)
            self._status_input = self.add(DictInput(status_dict), name="status")
            self._status_input.value_changed = self._on_status_input_changed
            return

        self._status_input.value = status_dict

    def _on_status_input_changed(self, item, event=None):
        try:
            key, value = item
        except Exception:
            return
        updated = self._ensure_status_dict().copy()
        updated[key] = value
        self.value = updated

    def value_preprocessor(self, status_dict: dict | None):
        status_dict = {} if status_dict is None else dict(status_dict)
        if hasattr(self, "_status_input") and self._status_input is not None:
            self._sync_status_input(status_dict)
        return status_dict

    def value_getter(self):
        def setitem_callback(key, value):
            self.__setitem__(key, value)
        return pk_wrapped_dict(setitem_callback, self._ensure_status_dict().copy())

    def __getitem__(self, key):
        if isinstance(key, tuple) and len(key) == 2:
            return self.button_positions.get(tuple(key))
        return self._ensure_status_dict().get(key)

    def __setitem__(self, key, value):
        if isinstance(key, tuple) and len(key) == 2:
            row, col = key
            self._set_button(row, col, value)
            return
        updated = self._ensure_status_dict().copy()
        updated[key] = value
        self.value = updated

    def html(self):
        container = Tag(
            "div",
            style={"display": "flex", "align-items": "flex-start", "gap": "8px", "flex-wrap": "wrap"},
        )
        grid = container.add(
            "div",
            style={
                "display": "grid",
                "grid-template-columns": f"repeat({self.cols}, {self.cell_size})",
                "grid-auto-rows": self.cell_size,
                "gap": "4px",
            },
        )
        for r in range(self.rows):
            for c in range(self.cols):
                cell = grid.add(
                    "div",
                    style={
                        "width": self.cell_size,
                        "height": self.cell_size,
                        "display": "flex",
                        "align-items": "center",
                        "justify-content": "center",
                        "box-sizing": "border-box",
                    },
                )
                button = self.button_positions.get((r, c))
                if button is not None:
                    cell.add_html(button.render())

        if self._status_input is not None:
            status_container = container.add("div", style={"flex": "0 0 auto", "display": "flow-root"})
            status_container.add_html(self._status_input.render())
        return container.render()

    def _set_button(self, row: int, col: int, value):
        self._validate_position(row, col)
        coord = (row, col)
        if value is None:
            if coord in self.button_names:
                self.remove(self.button_names.pop(coord))
                self.button_positions.pop(coord, None)
                self.updated()
            return

        button = value if isinstance(value, Button) else Button(str(value))
        target_button: Button
        if coord not in self.button_positions:
            added = self.add(button, name=self._cell_name(row, col))
            self.button_positions[coord] = added
            self.button_names[coord] = added.name
            target_button = added
        else:
            current = self.button_positions[coord]
            if isinstance(value, Button) and current is not value:
                self.remove(self.button_names[coord])
                added = self.add(button, name=self._cell_name(row, col))
                self.button_positions[coord] = added
                self.button_names[coord] = added.name
                target_button = added
            else:
                if not isinstance(value, Button):
                    current.title = str(value)
                target_button = current

        self._apply_button_style(target_button)
        if self._button_clicked_handler is not None:
            target_button.clicked = self._button_clicked_handler
        if self._button_pressed_handler is not None:
            target_button.pressed = self._button_pressed_handler

        self.updated()

    def _apply_button_style(self, button: Button):
        style = self.default_button_style.copy()

        # Merge any per-button overrides.
        if hasattr(button, "_style") and isinstance(button._style, dict):
            style.update(button._style)
        if hasattr(button, "button") and hasattr(button.button, "_style") and isinstance(button.button._style, dict):
            style.update(button.button._style)

        # Apply styles to the actual <button> element (not the wrapper <div> produced by Topping.render()).
        if hasattr(button, "button"):
            button.button.style = style

    def _cell_name(self, row: int, col: int):
        return f"cell_{row}_{col}"

    def _validate_position(self, row: int, col: int):
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise IndexError(f"Cell ({row}, {col}) is outside of the grid size ({self.rows}, {self.cols}).")

    @property
    def clicked(self):
        return self._button_clicked_handler

    @clicked.setter
    def clicked(self, func):
        self._button_clicked_handler = func
        for button in self.button_positions.values():
            button.clicked = func

    @property
    def pressed(self):
        return self._button_pressed_handler

    @pressed.setter
    def pressed(self, func):
        self._button_pressed_handler = func
        for button in self.button_positions.values():
            button.pressed = func


class Group(GroupContainer):
    def __init__(self, toppings:list[Topping]=None, *, title: str=None, padding: bool | None = None, styles: dict | None = None, classes: dict | str | None = None, **kwargs):
        toppings = [] if toppings is None else toppings
        super().__init__(toppings, title=title, padding=padding, styles=styles, classes=classes, draggable=False, **kwargs)

class Row(Arrangement):
    def __init__(self, toppings:list[Topping]=[], padding:bool=True, **kwargs):
        super().__init__(toppings, padding, **kwargs)

    def prepare(self, toppings, padding):
        self.padding = padding
        from .automatic import topping_from_object
        for topping in toppings:
            self.add(topping)
        
    def html(self):
        gap = "var(--wa-space-m)" if self.padding else "0"
        row = Tag("div", style={"display": "flex", "flex-wrap": "wrap", "align-items": "flex-start", "gap": gap})
        for child in self.child_htmls:
            column = row.add("div", style={"flex": "1 1 0", "min-width": "12rem"})
            column.add_html(child)
        return row.render()

class Column(Arrangement):
    def __init__(self, toppings:list[Topping]=[], centering:bool=True, padding:bool=True, **kwargs):
        super().__init__(toppings, centering, padding, **kwargs)
        
    def prepare(self, toppings, centering, padding):
        self.centering = centering
        self.padding = padding
        for topping in toppings:
            self.add(topping)
        
    def html(self):
        gap = "var(--wa-space-m)" if self.padding else "0"
        styles = {"display": "flex", "flex-direction": "column", "gap": gap}
        if self.centering:
            styles["align-items"] = "center"
        column = Tag("div", style=styles)
        for child in self.child_htmls:
            row = column.add("div")
            row.add_html(child)
        return column.render()
