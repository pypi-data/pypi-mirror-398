import typing as t
from pydantic import Field, BaseModel
from starlette_templates.components.base import ComponentModel


class SelectOption(BaseModel):
    """Option for select dropdown."""

    label: str
    """Option label text."""
    value: str
    """Option value."""
    selected: bool = False
    """Whether option is selected."""
    disabled: bool = False
    """Whether option is disabled."""


class Input(ComponentModel):
    """Bootstrap form input component."""

    template: str = Field("components/forms/input.html", frozen=True)
    """Bootstrap input form control component."""
    name: str = Field(..., description="Input name attribute")
    """Input name attribute."""
    label: t.Optional[str] = Field(default=None, description="Input label")
    """Input label."""
    type: str = Field(default="text", description="Input type: text, email, password, number, tel, url, etc.")
    """Input type, e.g., text, email, password, number, tel, url, etc."""
    value: t.Optional[str] = Field(default=None, description="Input value")
    """Input value."""
    placeholder: t.Optional[str] = Field(default=None, description="Placeholder text")
    """Placeholder text."""
    help_text: t.Optional[str] = Field(default=None, description="Help text below input")
    """Help text below input."""
    required: bool = Field(default=False, description="Required field")
    """Whether the input is required."""
    disabled: bool = Field(default=False, description="Disabled input")
    """Whether the input is disabled."""
    readonly: bool = Field(default=False, description="Readonly input")
    """Whether the input is readonly."""
    validation_state: t.Optional[str] = Field(default=None, description="Validation state: valid, invalid")
    """Validation state: valid, invalid."""
    validation_message: t.Optional[str] = Field(default=None, description="Validation feedback message")
    """Validation feedback message."""
    prepend: t.Optional[str] = Field(default=None, description="Prepend text/icon to input")
    """Prepend text/icon to input."""
    append: t.Optional[str] = Field(default=None, description="Append text/icon to input")
    """Append text/icon to input."""
    size: t.Optional[str] = Field(default=None, description="Input size: sm, lg")
    """Input size: sm, lg."""

    @classmethod
    def prepare_field_params(
        cls,
        params: dict[str, t.Any],
        field_value: t.Any,
    ) -> dict[str, t.Any]:
        """Convert field value to string for input element."""
        if field_value is not None:
            params["value"] = str(field_value)
        else:
            params["value"] = None
        return params


class Textarea(ComponentModel):
    """Bootstrap textarea component."""

    template: str = Field("components/forms/textarea.html", frozen=True)
    """Bootstrap textarea component template."""
    name: str = Field(..., description="Textarea name attribute")
    """Textarea name attribute."""
    label: t.Optional[str] = Field(default=None, description="Textarea label")
    """Textarea label."""
    value: t.Optional[str] = Field(default=None, description="Textarea value")
    """Textarea value."""
    placeholder: t.Optional[str] = Field(default=None, description="Placeholder text")
    """Placeholder text."""
    help_text: t.Optional[str] = Field(default=None, description="Help text below textarea")
    """Help text below textarea."""
    rows: int = Field(default=3, description="Number of rows")
    """Number of rows."""
    required: bool = Field(default=False, description="Required field")
    """Whether the textarea is required."""
    disabled: bool = Field(default=False, description="Disabled textarea")
    """Whether the textarea is disabled."""
    readonly: bool = Field(default=False, description="Readonly textarea")
    """Whether the textarea is readonly."""
    validation_state: t.Optional[str] = Field(default=None, description="Validation state: valid, invalid")
    """Validation state: valid, invalid."""
    validation_message: t.Optional[str] = Field(default=None, description="Validation feedback message")
    """Validation feedback message."""

    @classmethod
    def prepare_field_params(
        cls,
        params: dict[str, t.Any],
        field_value: t.Any,
    ) -> dict[str, t.Any]:
        """Convert field value to string for textarea element."""
        if field_value is not None:
            params["value"] = str(field_value)
        else:
            params["value"] = None
        return params


class Select(ComponentModel):
    """Bootstrap select dropdown component."""

    template: str = Field("components/forms/select.html", frozen=True)
    """Bootstrap select dropdown component template."""
    name: str = Field(..., description="Select name attribute")
    """Select name attribute."""
    label: t.Optional[str] = Field(default=None, description="Select label")
    """Select label."""
    options: t.List[SelectOption] = Field(default_factory=list, description="Select options")
    """Select options."""
    help_text: t.Optional[str] = Field(default=None, description="Help text below select")
    """Help text below select."""
    required: bool = Field(default=False, description="Required field")
    """Whether the select is required."""
    disabled: bool = Field(default=False, description="Disabled select")
    """Whether the select is disabled."""
    multiple: bool = Field(default=False, description="Allow multiple selections")
    """Allow multiple selections."""
    size: t.Optional[str] = Field(default=None, description="Select size: sm, lg")
    """Select size: sm, lg."""
    validation_state: t.Optional[str] = Field(default=None, description="Validation state: valid, invalid")
    """Validation state: valid, invalid."""
    validation_message: t.Optional[str] = Field(default=None, description="Validation feedback message")
    """Validation feedback message."""

    @classmethod
    def prepare_field_params(
        cls,
        params: dict[str, t.Any],
        field_value: t.Any,
    ) -> dict[str, t.Any]:
        """Convert choices to SelectOption objects with proper selected state."""
        choices = params.pop("choices", [])

        if isinstance(field_value, list):
            selected_values = set(field_value)
        else:
            selected_values = {field_value} if field_value is not None else set()

        params["options"] = [
            SelectOption(
                value=str(choice["value"]),
                label=choice["label"],
                selected=choice["value"] in selected_values or choice["value"] == field_value,
                disabled=choice.get("disabled", False),
            )
            for choice in choices
        ]
        return params


class Checkbox(ComponentModel):
    """Bootstrap checkbox component."""

    template: str = Field("components/forms/checkbox.html", frozen=True)
    """Bootstrap checkbox component template."""
    name: str = Field(..., description="Checkbox name attribute")
    """Checkbox name attribute."""
    label: str = Field(..., description="Checkbox label")
    """Checkbox label."""
    value: str = Field(default="1", description="Checkbox value")
    """Checkbox value."""
    checked: bool = Field(default=False, description="Checked state")
    """Checked state."""
    disabled: bool = Field(default=False, description="Disabled checkbox")
    """Whether the checkbox is disabled."""
    inline: bool = Field(default=False, description="Display inline")
    """Display inline."""
    validation_state: t.Optional[str] = Field(default=None, description="Validation state: valid, invalid")
    """Validation state: valid, invalid."""
    validation_message: t.Optional[str] = Field(default=None, description="Validation feedback message")
    """Validation feedback message."""

    @classmethod
    def prepare_field_params(
        cls,
        params: dict[str, t.Any],
        field_value: t.Any,
    ) -> dict[str, t.Any]:
        """Set checked state from field value instead of using value."""
        params["checked"] = bool(field_value)
        # Don't pass field_value as value - checkbox has its own value attribute
        return params


class Radio(ComponentModel):
    """Bootstrap radio button component."""

    template: str = Field("components/forms/radio.html", frozen=True)
    """Bootstrap radio button component template."""
    name: str = Field(..., description="Radio name attribute (same for group)")
    """Radio name attribute (same for group)."""
    label: str = Field(..., description="Radio label")
    """Radio label."""
    value: str = Field(..., description="Radio value")
    """Radio value."""
    checked: bool = Field(default=False, description="Checked state")
    """Checked state."""
    disabled: bool = Field(default=False, description="Disabled radio")
    """Whether the radio is disabled."""
    inline: bool = Field(default=False, description="Display inline")
    """Display inline."""
    validation_state: t.Optional[str] = Field(default=None, description="Validation state: valid, invalid")
    """Validation state: valid, invalid."""
    validation_message: t.Optional[str] = Field(default=None, description="Validation feedback message")
    """Validation feedback message."""


class Switch(ComponentModel):
    """Bootstrap switch component (styled checkbox)."""

    template: str = Field("components/forms/switch.html", frozen=True)
    """Bootstrap switch component template."""
    name: str = Field(..., description="Switch name attribute")
    """Switch name attribute."""
    label: str = Field(..., description="Switch label")
    """Switch label."""
    value: str = Field(default="1", description="Switch value")
    """Switch value."""
    checked: bool = Field(default=False, description="Checked state")
    """Checked state."""
    disabled: bool = Field(default=False, description="Disabled switch")
    """Whether the switch is disabled."""
    validation_state: t.Optional[str] = Field(default=None, description="Validation state: valid, invalid")
    """Validation state: valid, invalid."""
    validation_message: t.Optional[str] = Field(default=None, description="Validation feedback message")
    """Validation feedback message."""


class FileInput(ComponentModel):
    """Bootstrap file input component."""

    template: str = Field("components/forms/file_input.html", frozen=True)
    """Bootstrap file input component template."""
    name: str = Field(..., description="File input name attribute")
    """File input name attribute."""
    label: t.Optional[str] = Field(default=None, description="File input label")
    """File input label."""
    help_text: t.Optional[str] = Field(default=None, description="Help text below input")
    """Help text below input."""
    required: bool = Field(default=False, description="Required field")
    """Whether the file input is required."""
    disabled: bool = Field(default=False, description="Disabled input")
    """Whether the file input is disabled."""
    multiple: bool = Field(default=False, description="Allow multiple files")
    """Allow multiple files."""
    accept: t.Optional[str] = Field(default=None, description="Accepted file types (e.g., 'image/*')")
    """Accepted file types (e.g., 'image/*')."""
    validation_state: t.Optional[str] = Field(default=None, description="Validation state: valid, invalid")
    """Validation state: valid, invalid."""
    validation_message: t.Optional[str] = Field(default=None, description="Validation feedback message")
    """Validation feedback message."""


class Range(ComponentModel):
    """Bootstrap range slider component."""

    template: str = Field("components/forms/range.html", frozen=True)
    """Bootstrap range slider component template."""
    name: str = Field(..., description="Range name attribute")
    """Range name attribute."""
    label: t.Optional[str] = Field(default=None, description="Range label")
    """Range label."""
    min: float = Field(default=0, description="Minimum value")
    """Minimum value."""
    max: float = Field(default=100, description="Maximum value")
    """Maximum value."""
    step: float = Field(default=1, description="Step increment")
    """Step increment."""
    value: float = Field(default=50, description="Current value")
    """Current value."""
    disabled: bool = Field(default=False, description="Disabled range")
    """Whether the range is disabled."""
    help_text: t.Optional[str] = Field(default=None, description="Help text below range")
    """Help text below range."""
    validation_state: t.Optional[str] = Field(default=None, description="Validation state: valid, invalid")
    """Validation state: valid, invalid."""
    validation_message: t.Optional[str] = Field(default=None, description="Validation feedback message")
    """Validation feedback message."""


class ChoiceOption(BaseModel):
    """Option for Choices.js select."""

    label: str
    """Option label text."""
    value: str
    """Option value."""
    selected: bool = False
    """Whether option is selected."""
    disabled: bool = False
    """Whether option is disabled."""
    customProperties: t.Optional[dict] = None
    """Custom properties for the option."""


class ChoiceGroup(BaseModel):
    """Option group for Choices.js."""

    label: str
    """Group label text."""
    options: t.List[ChoiceOption]
    """Options in this group."""


class ChoicesSelect(ComponentModel):
    """Choices.js enhanced select component."""

    id: str
    """Element ID for the select."""
    template: str = Field("components/forms/choices_select.html", frozen=True)
    """Choices.js select component template."""
    name: str = Field(..., description="Select name attribute")
    """Select name attribute."""
    label: t.Optional[str] = Field(default=None, description="Select label")
    """Select label."""
    options: t.List[t.Union[ChoiceOption, ChoiceGroup]] = Field(default_factory=list)
    """Select options or option groups."""
    placeholder: str = Field(default="Select an option", description="Placeholder text")
    """Placeholder text."""
    search_enabled: bool = Field(default=True, description="Enable search functionality")
    """Enable search functionality."""
    search_placeholder: str = Field(default="Type to search", description="Search placeholder")
    """Search placeholder."""
    multiple: bool = Field(default=False, description="Allow multiple selections")
    """Allow multiple selections."""
    remove_button: bool = Field(default=True, description="Show remove button for selected items")
    """Show remove button for selected items."""
    max_item_count: t.Optional[int] = Field(default=None, description="Max items that can be selected (for multiple)")
    """Max items that can be selected (for multiple)."""
    help_text: t.Optional[str] = Field(default=None, description="Help text below select")
    """Help text below select."""
    required: bool = Field(default=False, description="Required field")
    """Whether the select is required."""
    disabled: bool = Field(default=False, description="Disabled select")
    """Whether the select is disabled."""
    validation_state: t.Optional[str] = Field(default=None, description="Validation state: valid, invalid")
    """Validation state: valid, invalid."""
    validation_message: t.Optional[str] = Field(default=None, description="Validation feedback message")
    """Validation feedback message."""

    @classmethod
    def prepare_field_params(
        cls,
        params: dict[str, t.Any],
        field_value: t.Any,
    ) -> dict[str, t.Any]:
        """Convert choices to ChoiceOption objects with proper selected state."""
        choices = params.pop("choices", [])

        if isinstance(field_value, list):
            selected_values = set(field_value)
        else:
            selected_values = {field_value} if field_value is not None else set()

        params["options"] = [
            ChoiceOption(
                value=str(choice["value"]),
                label=choice["label"],
                selected=choice["value"] in selected_values,
                disabled=choice.get("disabled", False),
            )
            for choice in choices
        ]
        return params


class DatePicker(ComponentModel):
    """Flatpickr date picker component."""

    id: str
    """Element ID for the date picker."""
    template: str = Field("components/forms/datepicker.html", frozen=True)
    """Flatpickr date picker component template."""
    name: str = Field(..., description="Input name attribute")
    """Input name attribute."""
    label: t.Optional[str] = Field(default=None, description="Input label")
    """Input label."""
    value: t.Optional[str] = Field(default=None, description="Initial date value (YYYY-MM-DD)")
    """Initial date value (YYYY-MM-DD)."""
    placeholder: t.Optional[str] = Field(default="Select date", description="Placeholder text")
    """Placeholder text."""
    mode: str = Field(default="single", description="Selection mode: single, multiple, range")
    """Selection mode: single, multiple, range."""
    enable_time: bool = Field(default=False, description="Enable time picker")
    """Enable time picker."""
    time_24hr: bool = Field(default=True, description="Use 24-hour time format")
    """Use 24-hour time format."""
    date_format: str = Field(default="Y-m-d", description="Date format string")
    """Date format string."""
    min_date: t.Optional[str] = Field(default=None, description="Minimum selectable date")
    """Minimum selectable date."""
    max_date: t.Optional[str] = Field(default=None, description="Maximum selectable date")
    """Maximum selectable date."""
    disable_dates: t.List[str] = Field(default_factory=list, description="Dates to disable")
    """Dates to disable."""
    inline: bool = Field(default=False, description="Display calendar inline")
    """Display calendar inline."""
    help_text: t.Optional[str] = Field(default=None, description="Help text below input")
    """Help text below input."""
    required: bool = Field(default=False, description="Required field")
    """Whether the date picker is required."""
    disabled: bool = Field(default=False, description="Disabled input")
    """Whether the date picker is disabled."""
    validation_state: t.Optional[str] = Field(default=None, description="Validation state: valid, invalid")
    """Validation state: valid, invalid."""
    validation_message: t.Optional[str] = Field(default=None, description="Validation feedback message")
    """Validation feedback message."""

    @classmethod
    def prepare_field_params(
        cls,
        params: dict[str, t.Any],
        field_value: t.Any,
    ) -> dict[str, t.Any]:
        """Convert date/datetime values to ISO string format."""
        import datetime

        if field_value is None:
            params["value"] = None
        elif isinstance(field_value, datetime.datetime):
            params["value"] = field_value.date().isoformat()
        elif isinstance(field_value, datetime.date):
            params["value"] = field_value.isoformat()
        else:
            params["value"] = field_value
        return params


class TimePicker(ComponentModel):
    """Flatpickr time picker component."""

    id: str
    """Element ID for the time picker."""
    template: str = Field("components/forms/timepicker.html", frozen=True)
    """Flatpickr time picker component template."""
    name: str = Field(..., description="Input name attribute")
    """Input name attribute."""
    label: t.Optional[str] = Field(default=None, description="Input label")
    """Input label."""
    value: t.Optional[str] = Field(default=None, description="Initial time value (HH:MM)")
    """Initial time value (HH:MM)."""
    placeholder: t.Optional[str] = Field(default="Select time", description="Placeholder text")
    """Placeholder text."""
    time_24hr: bool = Field(default=True, description="Use 24-hour time format")
    """Use 24-hour time format."""
    min_time: t.Optional[str] = Field(default=None, description="Minimum selectable time")
    """Minimum selectable time."""
    max_time: t.Optional[str] = Field(default=None, description="Maximum selectable time")
    """Maximum selectable time."""
    minute_increment: int = Field(default=1, description="Increment of minutes in picker")
    """Increment of minutes in picker."""
    help_text: t.Optional[str] = Field(default=None, description="Help text below input")
    """Help text below input."""
    required: bool = Field(default=False, description="Required field")
    """Whether the time picker is required."""
    disabled: bool = Field(default=False, description="Disabled input")
    """Whether the time picker is disabled."""


class DateTimePicker(ComponentModel):
    """Flatpickr date and time picker component."""

    id: str
    """Element ID for the datetime picker."""
    template: str = Field("components/forms/datetimepicker.html", frozen=True)
    """Flatpickr datetime picker component template."""
    name: str = Field(..., description="Input name attribute")
    """Input name attribute."""
    label: t.Optional[str] = Field(default=None, description="Input label")
    """Input label."""
    value: t.Optional[str] = Field(default=None, description="Initial datetime value")
    """Initial datetime value."""
    placeholder: t.Optional[str] = Field(default="Select date and time", description="Placeholder text")
    """Placeholder text."""
    date_format: str = Field(default="Y-m-d H:i", description="Date format string")
    """Date format string."""
    time_24hr: bool = Field(default=True, description="Use 24-hour time format")
    """Use 24-hour time format."""
    min_date: t.Optional[str] = Field(default=None, description="Minimum selectable date")
    """Minimum selectable date."""
    max_date: t.Optional[str] = Field(default=None, description="Maximum selectable date")
    """Maximum selectable date."""
    help_text: t.Optional[str] = Field(default=None, description="Help text below input")
    """Help text below input."""
    required: bool = Field(default=False, description="Required field")
    """Whether the datetime picker is required."""
    disabled: bool = Field(default=False, description="Disabled input")
    """Whether the datetime picker is disabled."""


class SubmitButton(ComponentModel):
    """Bootstrap submit button component for forms."""

    template: str = Field("components/forms/submit_button.html", frozen=True)
    """Bootstrap submit button component template."""
    text: str = Field(default="Submit", description="Button text")
    """Button text."""
    button_type: str = Field(default="submit", description="Button type: submit, button, reset")
    """Button type: submit, button, reset."""
    name: t.Optional[str] = Field(default=None, description="Button name attribute")
    """Button name attribute."""
    classes: t.List[str] = Field(default_factory=lambda: ["btn", "btn-primary"], description="CSS classes")
    """CSS classes."""
    disabled: bool = Field(default=False, description="Disabled button")
    """Whether the button is disabled."""
    form: t.Optional[str] = Field(default=None, description="Form element the button is associated with")
    """Form element the button is associated with."""
    formaction: t.Optional[str] = Field(default=None, description="URL where form data is sent")
    """URL where form data is sent."""
    formenctype: t.Optional[str] = Field(default=None, description="How form data is encoded")
    """How form data is encoded."""
    formmethod: t.Optional[str] = Field(default=None, description="HTTP method when button is clicked")
    """HTTP method when button is clicked."""
    formnovalidate: bool = Field(default=False, description="Whether to bypass form validation")
    """Whether to bypass form validation."""
    formtarget: t.Optional[str] = Field(default=None, description="Where to display response")
    """Where to display response."""

    @classmethod
    def prepare_field_params(
        cls,
        params: dict[str, t.Any],
        field_value: t.Any,
    ) -> dict[str, t.Any]:
        """Submit buttons don't use field values."""
        return params