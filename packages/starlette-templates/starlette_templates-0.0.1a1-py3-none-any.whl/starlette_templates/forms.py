from __future__ import annotations

import datetime
import typing as t
from markupsafe import Markup
from jinja2 import pass_context
from jinja2.runtime import Context
from starlette.requests import Request
from pydantic_core import PydanticUndefined as Undefined
from pydantic.fields import FieldInfo as PydanticFieldInfo
from pydantic._internal._model_construction import ModelMetaclass
from pydantic import BaseModel, ConfigDict, Field, ValidationError

T = t.TypeVar("T")


@t.overload
async def model_from_request(request: Request, model: t.Type[T]) -> T: ...


@t.overload
async def model_from_request(request: Request, model: None = None) -> dict: ...


async def model_from_request(request: Request, model: t.Optional[t.Type[T]] = None) -> t.Union[T, dict]:
    """Parse and validate request body against a Pydantic model.

    Loads data from path params, query params, and request body (JSON or form),
    in that order, overriding earlier values. Form fields that allow multiple values
    (like multi-select) are handled appropriately.

    This function can be used to populate a Pydantic model instance from request data,
    or return a dict of parameters if no model is provided.

    Args:
        request: Starlette Request object
        model: Pydantic model class to validate against (optional)

    Returns:
        An instance of the Pydantic model if provided, otherwise a dict of parameters.
    """
    params = {}
    # First load path params
    # /country/{country_code}/city/{city_name} -> {"country_code": "...", "city_name": "..."}
    if hasattr(request, "path_params"):
        params.update(request.path_params)
    # Next load query params, overriding path params if keys overlap
    # /search?q=hiking&sort=asc&country_code=us -> {"q": "hiking", "sort": "asc", "country_code": "us", "city_name": "..."}
    if hasattr(request, "query_params"):
        params.update(request.query_params)

    content_type = request.headers.get("content-type", "")

    # Load body params depending on content type (JSON or form data)
    try:
        if "application/json" in content_type:
            # JSON body overrides path and query params if keys overlap
            body = await request.json()
            if isinstance(body, dict):
                params.update(body)
        # There are two common form content types
        # application/x-www-form-urlencoded is standard form submission
        # multipart/form-data is used for file uploads and complex forms
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            # Parse form data and handle multiple values (like multi-select)
            form = await request.form()
            multiple_fields = set()
            if model is not None and hasattr(model, "model_fields"):
                for field_name, field_info in model.model_fields.items():
                    json_extra = getattr(field_info, "json_schema_extra", {}) or {}
                    if json_extra.get("multiple", False):
                        multiple_fields.add(field_name)
                    annotation = field_info.annotation
                    origin = t.get_origin(annotation)
                    if origin is list or origin is t.List:
                        multiple_fields.add(field_name)

            for key in form.keys():
                values = form.getlist(key)
                if key in multiple_fields:
                    params[key] = values
                elif len(values) == 1:
                    params[key] = values[0]
                else:
                    params[key] = values
    except Exception:
        pass

    # Validate and return model instance or raw params dict if no model provided
    if model is None:
        return params
    return model.model_validate(params)


def __dataclass_transform__(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_descriptors: t.Tuple[t.Union[type, t.Callable[..., t.Any]], ...] = (()),
) -> t.Callable[[T], T]:
    return lambda a: a


class FormConfig(ConfigDict, total=False):
    template: str = "components/form.html"
    method: str = "POST"
    enctype: str = "application/x-www-form-urlencoded"
    action: t.Optional[str] = None
    show_validation_styling: bool = False
    error_banner_text: str = "Please correct the errors below"
    layout: str = "vertical"  # "vertical" or "horizontal"


class ModelField:
    pass


@__dataclass_transform__(kw_only_default=True, field_descriptors=(Field, PydanticFieldInfo))
class FormModelMetaclass(ModelMetaclass):
    model_config: FormConfig
    model_fields: t.ClassVar[t.Dict[str, PydanticFieldInfo]]
    __config__: t.Type[FormConfig]
    __fields__: t.Dict[str, ModelField]  # type: ignore[assignment]


class FormModel(BaseModel, metaclass=FormModelMetaclass):
    """Base class for form models with rendering capabilities.

    Attributes:
        model_config: Configuration for form rendering and behavior

    Example:
        Define a form model by inheriting from `FormModel` and using form field helpers:

        ```python
        import datetime
        from starlette_templates.forms import FormModel, SelectField, DateField, SubmitButtonField

        class Filters(FormModel):
            storefront: str = SelectField(
                default="ww",
                choices={"ww": "Worldwide", "us": "United States"},
                label="Storefront",
            )
            start_date: datetime.date = DateField(
                default_factory=lambda: datetime.date.today(),
                label="Start Date",
            )
            submit: str = SubmitButtonField(text="Submit")
        ```

        Add forms to a specific template using `TemplateResponse`

        ```python
        async def overview(request: Request) -> TemplateResponse:
            form = await Filters.from_request(request)
            return TemplateResponse("overview.html", {"form": form})
        
        app = Starlette(routes=[
            Route("/overview", overview, methods=["GET", "POST"], name="overview")
        ])
        ```

        Add forms to all templates using `context_processors` parameter of `TemplateRouter`

        ```python hl_lines="7-9"
        async def form_context_processor(request: Request) -> dict:
            form = await Filters.from_request(request)
            return {"form": form}

        app = Starlette(
            routes=[
                Mount("/", TemplateRouter(
                    context_processors=[form_context_processor],
                )),
            ],
            middleware=[Middleware(Jinja2TemplatesMiddleware)],
        )
        ```

        Or assign forms to specific routes using `Route` in `context_processors`

        ```python hl_lines="8"
        app = Starlette(
            routes=[
                Route(
                    "/",
                    TemplateRouter(
                        context_processors=[
                            # Only add form to /search route templates
                            Route("/search", form_context_processor)
                        ],
                    ),
                ),
            ],
            middleware=[Middleware(Jinja2TemplatesMiddleware)],
        )
        ```
    """

    model_config = FormConfig(from_attributes=True, extra="allow")

    def __init__(self, **data):
        super().__init__(**data)
        self._validation_errors = {}
        self._is_validated = False
        self._field_errors = {}  # Field-level errors for display
        self._raw_data = {}  # Raw input data when validation fails

    def is_valid(self, request: t.Optional[Request] = None) -> bool:
        """Check if form has no validation errors. If request is provided,
        checks for both HTTP method and field errors to determine validity.

        If `request` is provided, the form is only considered valid if the request method is
        the same as the form's configured method (default: POST) and there are no field errors.
        This means `is_valid()` will return False for GET requests even if there are no field errors
        and will only return True for requests with the correct method and no field errors, which is
        the typical behavior for form submissions.
        
        Args:
            request: Starlette Request object (optional)
        
        Returns:
            True if form is valid, False otherwise
        
        Example:
            ```python hl_lines="3"
            async def search_page(request: Request):
                form = await SearchForm.from_request(request)
                if form.is_valid(request):
                    # Process valid form submission
                    ...
                return TemplateResponse("search.html", {"form": form})
            ```
        """
        if request is not None:
            method = self.model_config.get("method", "POST").upper()
            if request.method.upper() != method:
                return False
        return not self.has_errors()

    def has_errors(self, name: t.Optional[str] = None) -> bool:
        """Check if form has validation errors. If name is provided, checks for errors on that specific field.
        
        Args:
            name: Name of the field to check for errors (optional)
        
        Returns:
            True if there are validation errors, False otherwise
        
        Example:
            ```python
            if form.has_errors():
                print("Form has validation errors")

            if form.has_errors('email'):
                print("Email field has a validation error")
            ```

            You can also use this in Jinja2 templates:

            ```jinja
            {% if form.has_errors() %}
                <div class="error-banner">{{ form.get_error_banner_text() }}</div>
            {% endif %}

            {% if form.has_errors('email') %}
                <div class="field-error">{{ form.get_field_error('email') }}</div>
            {% endif %}
            ```
        """
        if name:
            return name in self._field_errors
        return bool(self._field_errors)

    def get_field_error(self, name: str, default: t.Optional[str] = None) -> t.Optional[str]:
        """Get validation error message for a specific field, if any.
        
        Args:
            name: Name of the field
            default: Default value to return if no error exists for the field
        
        Returns:
            The error message for the field, or the default value if no error exists
        
        Example:
            ```python
            error_message = form.get_field_error('email', default='No error')
            ```
        """
        return self._field_errors.get(name, default)

    def get_error_banner_text(self) -> str:
        """Get the error banner text from form config. This is text that can be displayed
        at the top of the form when there are validation errors."""
        return self.model_config.get("error_banner_text", "Please correct the errors below")

    def model_dump(self, **kwargs) -> t.Dict[str, t.Any]:
        """Override model_dump to exclude fields marked with exclude_from_dump."""
        data = super().model_dump(**kwargs)

        # Remove fields that should be excluded from dump (like submit buttons)
        # Fields can define json_schema_extra={"exclude_from_dump": True} to exclude them from the dumped data
        for field_name, field_info in self.__class__.model_fields.items():
            json_extra = getattr(field_info, "json_schema_extra", {}) or {}
            if json_extra.get("exclude_from_dump", False):
                data.pop(field_name, None)

        return data

    @pass_context
    async def render(self, ctx: Context, field_name: str, request: Request | None = None) -> Markup:
        """Render a specific field in HTML. This is a Jinja2 template method.

        This calls the component's render method with appropriate parameters defined in the form.

        If the request parameter is not provided, it will attempt to get it from the template context. If
        the request is still not found, an error will be raised.

        Args:
            ctx: Jinja2 context
            field_name: Name of the field to render
            request: Starlette request object

        Returns:
            Markup of the rendered component HTML

        Example:
            In a Jinja2 templates, use sync or async to render the field:

            ```jinja
            {{ form.render('start_date', request) }}
            {{ await form.render('start_date', request) }}
            ```

            You can also omit the request parameter if the template context has a `request` variable:

            ```jinja
            {{ form.render('start_date') }}
            ```

        Raises:
            ValueError: If the request object is not provided or found in context
            ValueError: If the field name is not found in the form
            ValueError: If the field does not have a component_cls defined
        """
        # Get request from context if not provided
        if request is None:
            request = ctx.get("request")
            if request is None:
                raise ValueError("Request object must be provided either as parameter or in template context")

        # Get field info
        if field_name not in self.__class__.model_fields:
            raise ValueError(f"Field '{field_name}' not found in form")

        field_info = self.__class__.model_fields[field_name]
        json_extra = getattr(field_info, "json_schema_extra", {}) or {}

        # Extract component class
        component_cls = json_extra.get("component_cls")
        if not component_cls:
            raise ValueError(f"Field '{field_name}' does not have a component_cls defined")

        # Determine which value to use: raw data (if validation failed) or field value
        if self._raw_data and field_name in self._raw_data:
            field_value = self._raw_data[field_name]
        else:
            field_value = getattr(self, field_name)

        # Copy all params from json_extra (excluding component_cls and None values)
        params = {k: v for k, v in json_extra.items() if k != "component_cls" and v is not None}

        # Add defaults for id and name
        params.setdefault("id", field_name)
        params.setdefault("name", field_name)

        # Add help_text from field description
        if field_info.description and "help_text" not in params:
            params["help_text"] = field_info.description

        # Let the component handle value conversion and any special param transformations
        # e.g., converting datetime.date to string for date input, converting choices to options
        # Components can implement prepare_field_params() classmethod for this purpose
        # NOTE: Only call this ONCE with the correct value to avoid issues with params
        # that get consumed (like choices being converted to options)
        params = component_cls.prepare_field_params(params, field_value)

        # Inject validation errors if present and validation styling is enabled
        config = self.model_config
        if self._field_errors and field_name in self._field_errors:
            # Only add validation feedback if enabled in config
            if config.get("show_validation_styling", False):
                params["validation_state"] = "invalid"
                params["validation_message"] = self._field_errors[field_name]

        # Instantiate and render component
        component = component_cls(**params)
        return await component.render(request)

    async def render_form(
        self,
        request: Request,
        *,
        id: str | None = None,
        action: str | None = None,
        method: str | None = None,
        enctype: str | None = None,
        classes: list[str] | None = None,
        novalidate: bool = False,
    ) -> Markup:
        """Internal implementation for rendering the form."""
        # Get config values with overrides
        config = self.model_config
        form_template = config.get("template", "components/form.html")
        form_method = method or config.get("method", "POST")
        form_enctype = enctype or config.get("enctype", "application/x-www-form-urlencoded")
        form_action = action or config.get("action")
        form_layout = config.get("layout", "vertical")

        # Render all fields and separate submit buttons
        regular_fields = []
        submit_fields = []

        for field_name, field_info in self.__class__.model_fields.items():
            json_extra = getattr(field_info, "json_schema_extra", {}) or {}
            component_cls = json_extra.get("component_cls")

            if not component_cls:
                # Skip fields without a component_cls (shouldn't happen normally)
                continue

            # Determine which value to use: raw data (if validation failed) or field value
            if self._raw_data and field_name in self._raw_data:
                field_value = self._raw_data[field_name]
            else:
                field_value = getattr(self, field_name)

            # Copy all params from json_extra (excluding component_cls and None values)
            params = {k: v for k, v in json_extra.items() if k != "component_cls" and v is not None}

            # Add defaults for id and name
            params.setdefault("id", field_name)
            params.setdefault("name", field_name)

            # Add help_text from field description
            if field_info.description and "help_text" not in params:
                params["help_text"] = field_info.description

            # Let the component handle value conversion and any special param transformations
            # NOTE: Only call this ONCE with the correct value to avoid issues with params
            # that get consumed (like choices being converted to options)
            params = component_cls.prepare_field_params(params, field_value)

            # Inject validation errors if present and validation styling is enabled
            if self._field_errors and field_name in self._field_errors:
                # Only add validation feedback if enabled in config
                if config.get("show_validation_styling", False):
                    params["validation_state"] = "invalid"
                    params["validation_message"] = self._field_errors[field_name]

            # Instantiate and render component
            component = component_cls(**params)
            field_html = await component.render(request)

            # Check if this is a submit button
            from starlette_templates.components.forms import SubmitButton
            if isinstance(component, SubmitButton):
                submit_fields.append({
                    "html": field_html,
                    "col_class": json_extra.get("col_class", "col-12"),
                })
            else:
                regular_fields.append({
                    "html": field_html,
                    "col_class": json_extra.get("col_class", "col-md-6" if form_layout == "horizontal" else "col-12"),
                })

        # Render the form template
        jinja_env = request.state.jinja_env
        template = jinja_env.get_template(form_template)
        rendered = await template.render_async(
            {
                "request": request,
                "id": id,
                "method": form_method,
                "action": form_action,
                "enctype": form_enctype,
                "classes": classes or [],
                "novalidate": novalidate,
                "layout": form_layout,
                "regular_fields": regular_fields,
                "submit_fields": submit_fields,
            }
        )
        return Markup(rendered)

    @pass_context
    async def __call__(
        self,
        ctx: Context,
        request: Request | None = None,
        *,
        id: str | None = None,
        action: str | None = None,
        method: str | None = None,
        enctype: str | None = None,
        classes: list[str] | None = None,
        novalidate: bool = False,
    ) -> Markup:
        """Render the entire form. Alias for render_form().

        Example:
            ```jinja
            {{ form() }}
            {{ form(action='/submit', classes=['my-form'], enctype='multipart/form-data') }}
            ```
        """
        if request is None:
            request = ctx.get("request")
            if request is None:
                raise ValueError("Request object must be provided either as parameter or in template context")

        return await self.render_form(
            request, id=id, action=action, method=method, enctype=enctype, classes=classes, novalidate=novalidate
        )

    @classmethod
    def _parse_validation_errors(cls, exc: ValidationError) -> t.Dict[str, str]:
        """Parse Pydantic ValidationError into field-level errors.

        Returns dict mapping field names to error messages.
        """
        field_errors = {}

        for error in exc.errors():
            loc = error.get("loc", ())
            msg = error.get("msg", "Invalid value")

            # Extract field name from location tuple
            if loc:
                field_name = str(loc[0])

                # Only track if field exists in model
                if field_name in cls.model_fields:
                    # Use first error per field (don't overwrite)
                    if field_name not in field_errors:
                        field_errors[field_name] = msg

        return field_errors

    @classmethod
    def _get_field_defaults(cls) -> t.Dict[str, t.Any]:
        """Get default values for all form fields."""
        defaults = {}
        for field_name, field_info in cls.model_fields.items():
            if field_info.default is not Undefined:
                defaults[field_name] = field_info.default
            elif field_info.default_factory is not None:
                defaults[field_name] = field_info.default_factory()
        return defaults

    @classmethod
    async def from_request(cls, request: Request, raise_on_error: bool = True) -> FormModel:
        """Create form instance from request data.

        This class method parses data from the request (path params, query params, form data, and JSON body) and 
        validates it against the form model and returns an instance of the form model. If validation errors occur, 
        they are either raised as ValidationError or captured in the instance based on the `raise_on_error` flag.

        If a field with the same name appears in multiple sources, the precedence is as follows: path params < 
        query params < form data < JSON body. For example, if a field is present in both query params and form data,
        the value from form data will be used.

        Use the `.is_valid()` method on the returned instance to check if the form data is valid when `raise_on_error` is False.

        Args:
            request: Starlette Request object
            raise_on_error: If True, raises ValidationError. If False, captures errors in instance.

        Returns:
            FormModel instance (with errors if raise_on_error=False)
        """
        try:
            return await model_from_request(request=request, model=cls)
        except ValidationError as e:
            if raise_on_error:
                raise

            # Capture raw data before validation
            raw_data = await model_from_request(request=request, model=None)

            # Parse errors into field-level dict
            field_errors = cls._parse_validation_errors(e)

            # Create instance with defaults, bypassing validation
            # IMPORTANT: We use model_construct() instead of the regular constructor
            # because the defaults themselves may not pass validation (e.g., empty strings
            # for fields with min_length, None for required fields). Since we already have
            # the validation errors from the original attempt, we don't want to trigger
            # validation again - we just need a form instance to attach the errors to.
            instance = cls.model_construct(**cls._get_field_defaults())
            instance._field_errors = field_errors
            instance._raw_data = raw_data
            instance._is_validated = True

            return instance


def TextField(
    default: t.Any = Undefined,
    *,
    min_length: t.Optional[int] = None,
    max_length: t.Optional[int] = None,
    regex: t.Optional[str] = None,
    name: t.Any = Undefined,
    id: t.Any = Undefined,
    label: t.Any = Undefined,
    title: str = Undefined,
    placeholder: str = Undefined,
    description: str = Undefined,
    required: bool = False,
    hidden: bool = False,
    disabled: bool = False,
    readonly: bool = False,
    col_class: t.Optional[str] = None,
    **kwargs: t.Any,
) -> t.Any:
    """Create a string form field with validation and formatting options.

    Args:
        default: Default value for the field
        min_length: Minimum length validation
        max_length: Maximum length validation
        regex: Regular expression pattern for validation
        name: Field name attribute
        id: Field id attribute
        label: Field label for display
        title: Field title
        placeholder: Placeholder text for input
        description: Field description
        required: Whether field is required
        hidden: Whether field is hidden
        disabled: Whether field is disabled
        readonly: Whether field is readonly
        col_class: Bootstrap column class for horizontal layout (e.g., "col-md-4")
        **kwargs: Additional field attributes

    Returns:
        A Pydantic Field configured for string validation
    """
    from starlette_templates.components.forms import Input

    return Field(
        default=default,
        min_length=min_length,
        max_length=max_length,
        pattern=regex,
        title=title if title is not Undefined else None,
        description=description if description is not Undefined else None,
        json_schema_extra={
            "component_cls": Input,
            "name": name if name is not Undefined else None,
            "id": id if id is not Undefined else None,
            "label": label if label is not Undefined else None,
            "placeholder": placeholder if placeholder is not Undefined else None,
            "required": required,
            "type": "hidden" if hidden else "text",
            "disabled": disabled,
            "readonly": readonly,
            "col_class": col_class,
            **kwargs,
        },
    )


def IntegerField(
    default: t.Any = Undefined,
    *,
    gt: t.Optional[int] = None,
    ge: t.Optional[int] = None,
    lt: t.Optional[int] = None,
    le: t.Optional[int] = None,
    multiple_of: t.Optional[int] = None,
    name: t.Any = Undefined,
    id: t.Any = Undefined,
    label: t.Any = Undefined,
    title: str = Undefined,
    placeholder: str = Undefined,
    description: str = Undefined,
    required: bool = False,
    hidden: bool = False,
    disabled: bool = False,
    readonly: bool = False,
    **kwargs: t.Any,
) -> t.Any:
    """Create an integer form field with numeric validation options.

    Args:
        default: Default value for the field
        gt: Greater than validation
        ge: Greater than or equal validation
        lt: Less than validation
        le: Less than or equal validation
        multiple_of: Multiple of validation
        name: Field name attribute
        id: Field id attribute
        label: Field label for display
        title: Field title
        placeholder: Placeholder text for input
        description: Field description
        required: Whether field is required
        hidden: Whether field is hidden
        disabled: Whether field is disabled
        readonly: Whether field is readonly
        **kwargs: Additional field attributes

    Returns:
        A Pydantic Field configured for integer validation
    """
    from starlette_templates.components.forms import Input

    return Field(
        default=default,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        title=title if title is not Undefined else None,
        description=description if description is not Undefined else None,
        json_schema_extra={
            "component_cls": Input,
            "name": name if name is not Undefined else None,
            "id": id if id is not Undefined else None,
            "label": label if label is not Undefined else None,
            "placeholder": placeholder if placeholder is not Undefined else None,
            "required": required,
            "type": "hidden" if hidden else "number",
            "disabled": disabled,
            "readonly": readonly,
            **kwargs,
        },
    )


def FloatField(
    default: t.Any = Undefined,
    *,
    gt: t.Optional[float] = None,
    ge: t.Optional[float] = None,
    lt: t.Optional[float] = None,
    le: t.Optional[float] = None,
    multiple_of: t.Optional[float] = None,
    name: t.Any = Undefined,
    id: t.Any = Undefined,
    label: t.Any = Undefined,
    title: str = Undefined,
    placeholder: str = Undefined,
    description: str = Undefined,
    required: bool = False,
    hidden: bool = False,
    disabled: bool = False,
    readonly: bool = False,
    **kwargs: t.Any,
) -> t.Any:
    """Create a float form field with numeric validation options.

    Args:
        default: Default value for the field
        gt: Greater than validation
        ge: Greater than or equal validation
        lt: Less than validation
        le: Less than or equal validation
        multiple_of: Multiple of validation
        name: Field name attribute
        id: Field id attribute
        label: Field label for display
        title: Field title
        placeholder: Placeholder text for input
        description: Field description
        required: Whether field is required
        hidden: Whether field is hidden
        disabled: Whether field is disabled
        readonly: Whether field is readonly
        **kwargs: Additional field attributes

    Returns:
        A Pydantic Field configured for float validation
    """
    from starlette_templates.components.forms import Input

    return Field(
        default=default,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        title=title if title is not Undefined else None,
        description=description if description is not Undefined else None,
        json_schema_extra={
            "component_cls": Input,
            "name": name if name is not Undefined else None,
            "id": id if id is not Undefined else None,
            "label": label if label is not Undefined else None,
            "placeholder": placeholder if placeholder is not Undefined else None,
            "required": required,
            "type": "hidden" if hidden else "number",
            "disabled": disabled,
            "readonly": readonly,
            **kwargs,
        },
    )


def EmailField(
    default: t.Any = Undefined,
    *,
    max_length: t.Optional[int] = None,
    name: t.Any = Undefined,
    id: t.Any = Undefined,
    label: t.Any = Undefined,
    title: str = Undefined,
    placeholder: str = Undefined,
    description: str = Undefined,
    required: bool = False,
    hidden: bool = False,
    disabled: bool = False,
    readonly: bool = False,
    **kwargs: t.Any,
) -> t.Any:
    """Create an email form field with email validation.

    Args:
        default: Default value for the field
        max_length: Maximum length validation
        name: Field name attribute
        id: Field id attribute
        label: Field label for display
        title: Field title
        placeholder: Placeholder text for input
        description: Field description
        required: Whether field is required
        hidden: Whether field is hidden
        disabled: Whether field is disabled
        readonly: Whether field is readonly
        **kwargs: Additional field attributes

    Returns:
        A Pydantic Field configured for email validation
    """
    from starlette_templates.components.forms import Input

    return Field(
        default=default,
        max_length=max_length,
        title=title if title is not Undefined else None,
        description=description if description is not Undefined else None,
        json_schema_extra={
            "component_cls": Input,
            "name": name if name is not Undefined else None,
            "id": id if id is not Undefined else None,
            "label": label if label is not Undefined else None,
            "placeholder": placeholder if placeholder is not Undefined else None,
            "required": required,
            "type": "hidden" if hidden else "email",
            "disabled": disabled,
            "readonly": readonly,
            **kwargs,
        },
    )


def TextAreaField(
    default: t.Any = Undefined,
    *,
    min_length: t.Optional[int] = None,
    max_length: t.Optional[int] = None,
    rows: int = 3,
    name: t.Any = Undefined,
    id: t.Any = Undefined,
    label: t.Any = Undefined,
    title: str = Undefined,
    placeholder: str = Undefined,
    description: str = Undefined,
    required: bool = False,
    disabled: bool = False,
    readonly: bool = False,
    **kwargs: t.Any,
) -> t.Any:
    """Create a textarea form field for multi-line text input.

    Args:
        default: Default value for the field
        min_length: Minimum length validation
        max_length: Maximum length validation
        rows: Number of rows for textarea
        name: Field name attribute
        id: Field id attribute
        label: Field label for display
        title: Field title
        placeholder: Placeholder text for textarea
        description: Field description
        required: Whether field is required
        disabled: Whether field is disabled
        readonly: Whether field is readonly
        **kwargs: Additional field attributes

    Returns:
        A Pydantic Field configured for textarea input
    """
    from starlette_templates.components.forms import Textarea

    return Field(
        default=default,
        min_length=min_length,
        max_length=max_length,
        title=title if title is not Undefined else None,
        description=description if description is not Undefined else None,
        json_schema_extra={
            "component_cls": Textarea,
            "name": name if name is not Undefined else None,
            "id": id if id is not Undefined else None,
            "label": label if label is not Undefined else None,
            "placeholder": placeholder if placeholder is not Undefined else None,
            "required": required,
            "rows": rows,
            "disabled": disabled,
            "readonly": readonly,
            **kwargs,
        },
    )


def CheckboxField(
    default: t.Any = Undefined,
    *,
    name: t.Any = Undefined,
    id: t.Any = Undefined,
    label: t.Any = Undefined,
    title: str = Undefined,
    description: str = Undefined,
    value: str = "1",
    required: bool = False,
    disabled: bool = False,
    inline: bool = False,
    **kwargs: t.Any,
) -> t.Any:
    """Create a checkbox form field for boolean input.

    Args:
        default: Default value for the field (True/False)
        name: Field name attribute
        id: Field id attribute
        label: Field label for display
        title: Field title
        description: Field description
        value: Value submitted when checkbox is checked
        required: Whether field is required
        disabled: Whether field is disabled
        inline: Whether to display inline
        **kwargs: Additional field attributes

    Returns:
        A Pydantic Field configured for checkbox input
    """
    from starlette_templates.components.forms import Checkbox

    return Field(
        default=default,
        title=title if title is not Undefined else None,
        description=description if description is not Undefined else None,
        json_schema_extra={
            "component_cls": Checkbox,
            "name": name if name is not Undefined else None,
            "id": id if id is not Undefined else None,
            "label": label if label is not Undefined else None,
            "value": value,
            "required": required,
            "disabled": disabled,
            "inline": inline,
            **kwargs,
        },
    )


class Choice(BaseModel):
    """Represents a single choice option with a value and label.

    Used in select fields to define available options. The value is what gets
    submitted with the form, while the label is what's displayed to the user.

    Attributes:
        value: The actual value to be submitted (can be any type)
        label: The display text shown to the user (must be a string)
        disabled: Whether the choice is disabled (default: False)

    Example:
        Choice(value="active", label="Active User")
        Choice(value=1, label="Option 1", disabled=True)
    """

    value: t.Any
    label: str
    disabled: bool = False


def SelectField(
    default: t.Any = Undefined,
    default_factory: t.Optional[t.Callable[[], t.Any]] = Undefined,
    *,
    choices: t.Optional[t.Dict[t.Any, str] | t.List[t.Any] | t.List[Choice]] = None,
    choices_factory: t.Optional[t.Callable[[], t.Dict[t.Any, str] | t.List[t.Any] | t.List[Choice]]] = None,
    multiple: bool = False,
    size: t.Optional[int] = None,
    name: t.Any = Undefined,
    id: t.Any = Undefined,
    label: t.Any = Undefined,
    title: str = Undefined,
    placeholder: str = Undefined,
    required: bool = False,
    description: str = Undefined,
    disabled: bool = False,
    search_enabled: bool = True,
    search_placeholder: str = "Type to search",
    remove_button: bool = True,
    max_item_count: t.Optional[int] = None,
    col_class: t.Optional[str] = None,
    **kwargs: t.Any,
) -> t.Any:
    """Create a select form field with options.

    Args:
        default: Default value for the field
        choices: Dict of {value: label}, list of values where value=label,
            or list of Choice objects. Order is preserved in all formats.
        choices_factory: Callable that returns a dict, list, or list of Choice objects
        multiple: Whether multiple selections are allowed (uses ChoicesSelect when True)
        size: Number of visible options (for Select component)
        name: Field name attribute
        id: Field id attribute
        label: Field label for display
        title: Field title
        placeholder: Placeholder text (for ChoicesSelect)
        required: Whether field is required
        description: Field description
        hidden: Whether field is hidden
        disabled: Whether field is disabled
        search_enabled: Enable search functionality (for ChoicesSelect)
        search_placeholder: Search placeholder text (for ChoicesSelect)
        remove_button: Show remove button for selected items (for ChoicesSelect)
        max_item_count: Max items that can be selected (for ChoicesSelect with multiple)
        col_class: Bootstrap column class for horizontal layout (e.g., "col-md-4")
        **kwargs: Additional field attributes

    Returns:
        A Pydantic Field configured for select input

    Example:
        Single select with dict choices (different value and label)
        ```python
        status = SelectField(
            choices={"active": "Active", "inactive": "Inactive", "pending": "Pending"},
            label="Status"
        )
        ```

        Single select with list choices (same value and label)

        ```python
        fruits = SelectField(
            choices=["Apple", "Orange", "Banana"],
            label="Fruit"
        )
        ```

        Single select with Choice objects

        ```python
        country = SelectField(
            choices=[
                Choice(value="us", label="United States"),
                Choice(value="ca", label="Canada"),
                Choice(value="uk", label="United Kingdom"),
            ],
            label="Country"
        )
        ```

        Multiple select (uses ChoicesSelect component)

        ```python
        interests = SelectField(
            choices={"sports": "Sports", "music": "Music", "reading": "Reading"},
            multiple=True,
            label="Interests"
        )
        ```

        Dynamic choices using a factory function

        ```python
        def get_country_choices():
            return {"us": "United States", "uk": "United Kingdom", "ca": "Canada"}

        country = SelectField(
            choices_factory=get_country_choices,
            label="Country"
        )
        ```
    """
    from starlette_templates.components.forms import Select, ChoicesSelect

    choices = choices or {}
    if choices_factory is not None:
        choices = choices_factory()
    if default_factory is not Undefined:
        default = default_factory()

    # Convert choices to list of objects to preserve order
    # (Pydantic sorts dict keys alphabetically in json_schema_extra)
    if isinstance(choices, dict):
        # Dict format: {"value": "label"}
        choices_list = [{"value": k, "label": v} for k, v in choices.items()]
    elif isinstance(choices, list):
        # Check if list contains Choice objects
        if choices and isinstance(choices[0], Choice):
            # List of Choice objects
            choices_list = [{"value": choice.value, "label": choice.label} for choice in choices]
        else:
            # List format: ["item1", "item2"] - use same value for both value and label
            choices_list = [{"value": item, "label": item} for item in choices]
    else:
        choices_list = []

    # Use ChoicesSelect for multiple selection, Select for single selection
    component_cls = ChoicesSelect if multiple else Select

    return Field(
        default=default,
        title=title if title is not Undefined else None,
        description=description if description is not Undefined else None,
        json_schema_extra={
            "component_cls": component_cls,
            "name": name if name is not Undefined else None,
            "id": id if id is not Undefined else None,
            "label": label if label is not Undefined else None,
            "placeholder": placeholder if placeholder is not Undefined else "Select an option",
            "required": required,
            "choices": choices_list,  # Will be converted to SelectOption/ChoiceOption at render time
            "multiple": multiple,
            "size": size,
            "disabled": disabled,
            "search_enabled": search_enabled,
            "search_placeholder": search_placeholder,
            "remove_button": remove_button,
            "max_item_count": max_item_count,
            "col_class": col_class,
            **kwargs,
        },
    )


def SubmitButtonField(
    text: str = "Submit",
    *,
    button_type: str = "submit",
    name: t.Any = Undefined,
    id: t.Any = Undefined,
    classes: t.Optional[t.List[str]] = None,
    disabled: bool = False,
    form: t.Any = Undefined,
    formaction: t.Any = Undefined,
    formenctype: t.Any = Undefined,
    formmethod: t.Any = Undefined,
    formnovalidate: bool = False,
    formtarget: t.Any = Undefined,
    col_class: t.Optional[str] = None,
    **kwargs: t.Any,
) -> t.Any:
    """Create a submit button form field with customization options.

    Args:
        text: Button text/label
        button_type: Button type (submit, button, reset)
        name: Button name attribute
        id: Button id attribute
        classes: CSS classes for the button
        disabled: Whether button is disabled
        form: Form element the button is associated with
        formaction: URL where form data is sent when button is clicked
        formenctype: How form data is encoded when button is clicked
        formmethod: HTTP method when button is clicked
        formnovalidate: Whether form validation is bypassed when button is clicked
        formtarget: Where to display response when button is clicked
        col_class: Bootstrap column class for horizontal layout (e.g., "col-md-4")
        template: Jinja2 template for rendering the field
        **kwargs: Additional button attributes

    Returns:
        A Pydantic Field configured for submit button

    Example:
        Basic submit button

        ```python
        submit = SubmitButtonField("Save Changes")
        ```

        Customized submit button

        ```python
        submit = SubmitButtonField(
            text="Create Account",
            classes=["btn", "btn-primary", "btn-lg"],
            id="create-account-btn"
        )
        ```

        Button with form attributes

        ```python
        delete_btn = SubmitButtonField(
            text="Delete",
            button_type="submit",
            formmethod="DELETE",
            formnovalidate=True,
            classes=["btn", "btn-danger"]
        )
        ```
    """
    from starlette_templates.components.forms import SubmitButton

    return Field(
        default="",  # Submit buttons don't have meaningful values
        json_schema_extra={
            "component_cls": SubmitButton,
            "name": name if name is not Undefined else None,
            "id": id if id is not Undefined else None,
            "input_type": "submit",
            "text": text,
            "button_type": button_type,
            "classes": classes or ["btn", "btn-primary"],
            "disabled": disabled,
            "form": form if form is not Undefined else None,
            "formaction": formaction if formaction is not Undefined else None,
            "formenctype": formenctype if formenctype is not Undefined else None,
            "formmethod": formmethod if formmethod is not Undefined else None,
            "formnovalidate": formnovalidate,
            "formtarget": formtarget if formtarget is not Undefined else None,
            "col_class": col_class,
            "exclude_from_validation": True,  # Don't validate submit buttons
            "exclude_from_dump": True,  # Don't include in model_dump
            **kwargs,
        },
    )


def HiddenField(
    default: t.Any = Undefined,
    *,
    name: t.Any = Undefined,
    id: t.Any = Undefined,
    title: str = Undefined,
    description: str = Undefined,
    **kwargs: t.Any,
) -> t.Any:
    """Create a hidden form field for passing data without user interaction.

    Args:
        default: Default value for the field
        name: Field name attribute
        id: Field id attribute
        title: Field title
        description: Field description
        **kwargs: Additional field attributes

    Returns:
        A Pydantic Field configured for hidden input

    Example:
        Basic hidden field

        ```python
        csrf_token = HiddenField(default="abc123")
        ```

        Hidden field with custom name

        ```python
        user_id = HiddenField(default=42, name="user_id")
        ```

        Hidden field that excludes from validation

        ```python
        session_key = HiddenField(
            default="session_xyz",
            exclude_from_validation=True
        )
        ```
    """
    from starlette_templates.components.forms import Input

    return Field(
        default=default,
        title=title if title is not Undefined else None,
        description=description if description is not Undefined else None,
        json_schema_extra={
            "component_cls": Input,
            "name": name if name is not Undefined else None,
            "id": id if id is not Undefined else None,
            "type": "hidden",
            "exclude_from_validation": kwargs.get("exclude_from_validation", False),
            "exclude_from_dump": kwargs.get("exclude_from_dump", False),
            **{k: v for k, v in kwargs.items() if k not in ["exclude_from_validation", "exclude_from_dump"]},
        },
    )


def TagField(
    default: t.Any = Undefined,
    *,
    separator: str = ",",
    placeholder: str = "Enter tags separated by commas",
    max_tags: t.Optional[int] = None,
    tag_pattern: t.Optional[str] = None,
    badge_class: str = "badge bg-primary text-white",
    show_validation: bool = True,
    name: t.Any = Undefined,
    id: t.Any = Undefined,
    label: t.Any = Undefined,
    title: str = Undefined,
    description: str = Undefined,
    required: bool = False,
    hidden: bool = False,
    disabled: bool = False,
    **kwargs: t.Any,
) -> t.Any:
    """Create a tag input form field for comma-separated values.

    This field renders as a text input with live tag visualization using Bootstrap badges.
    It supports tag validation, max tag limits, and custom styling.

    Args:
        default: Default value for the field (can be list or comma-separated string)
        separator: Character used to separate tags (default: comma)
        placeholder: Placeholder text for the input field
        max_tags: Maximum number of tags allowed (None for unlimited)
        tag_pattern: Regex pattern for individual tag validation
        badge_class: Bootstrap badge CSS classes for tag display
        show_validation: Whether to show validation styling (is-valid/is-invalid)
        name: Field name attribute
        id: Field id attribute
        label: Field label for display
        title: Field title
        description: Field description
        required: Whether field is required
        template: Jinja2 template for rendering the field
        **kwargs: Additional field attributes

    Returns:
        A Pydantic Field configured for tag input

    Example:
        Basic tag field

        ```python
        tags = TagField(label="Tags", default=["python", "javascript"])
        ```

        Tag field with custom separator

        ```python
        keywords = TagField(
            label="Keywords",
            separator=";",
            placeholder="Enter keywords separated by semicolons"
        )
        ```

        Limited tag field with custom styling

        ```python
        categories = TagField(
            label="Categories",
            max_tags=5,
            badge_class="badge bg-secondary text-white",
            required=True
        )
        ```

        Tag field without validation styling

        ```python
        draft_tags = TagField(
            label="Draft Tags",
            show_validation=False,
            badge_class="badge border border-primary text-primary"
        )
        ```
    """
    from starlette_templates.components.forms import Input

    return Field(
        default=default,
        title=title if title is not Undefined else None,
        description=description if description is not Undefined else None,
        json_schema_extra={
            "component_cls": Input,
            "name": name if name is not Undefined else None,
            "id": id if id is not Undefined else None,
            "label": label if label is not Undefined else None,
            "required": required,
            "type": "hidden" if hidden else "text",
            "separator": separator,
            "placeholder": placeholder,
            "max_tags": max_tags,
            "tag_pattern": tag_pattern,
            "badge_class": badge_class,
            "show_validation": show_validation,
            "disabled": disabled,
            **kwargs,
        },
    )


def DateField(
    default: t.Any = Undefined,
    default_factory: t.Optional[t.Callable[[], t.Any]] = Undefined,
    *,
    min: t.Any = Undefined,
    max: t.Any = Undefined,
    name: t.Any = Undefined,
    id: t.Any = Undefined,
    label: t.Any = Undefined,
    title: str = Undefined,
    placeholder: str = "Select date",
    description: str = Undefined,
    required: bool = False,
    disabled: bool = False,
    mode: str = "single",
    enable_time: bool = False,
    time_24hr: bool = True,
    date_format: str = "Y-m-d",
    inline: bool = False,
    col_class: t.Optional[str] = None,
    **kwargs: t.Any,
) -> t.Any:
    """Create a date form field with Flatpickr date picker.

    This field renders using the Flatpickr date picker component with advanced
    date selection features.

    Args:
        default: Default value for the field (can be date, datetime, or string)
        default_factory: Factory function to generate default value
        min: Minimum allowed date (date, datetime, or ISO string)
        max: Maximum allowed date (date, datetime, or ISO string)
        name: Field name attribute
        id: Field id attribute
        label: Field label for display
        title: Field title
        placeholder: Placeholder text for input
        description: Field description
        required: Whether field is required
        hidden: Whether field is hidden
        disabled: Whether field is disabled
        mode: Selection mode: "single", "multiple", or "range"
        enable_time: Enable time picker
        time_24hr: Use 24-hour time format
        date_format: Date format string (Flatpickr format)
        inline: Display calendar inline
        col_class: Bootstrap column class for horizontal layout (e.g., "col-md-4")
        **kwargs: Additional field attributes

    Returns:
        A Pydantic Field configured for date input

    Example:
        Basic date field

        ```python
        birth_date = DateField(label="Birth Date", required=True)
        ```

        Date field with range constraints

        ```python
        event_date = DateField(
            label="Event Date",
            min="2024-01-01",
            max="2024-12-31"
        )
        ```

        Date field with default value

        ```python
        from datetime import date
        appointment_date = DateField(
            label="Appointment Date",
            default=date.today(),
            required=True
        )
        ```

        Date range picker

        ```
        date_range = DateField(
            label="Date Range",
            mode="range"
        )
        ```

        Date and time picker

        ```python
        appointment = DateField(
            label="Appointment",
            enable_time=True,
            date_format="Y-m-d H:i"
        )
        ```
    """
    from starlette_templates.components.forms import DatePicker

    # Convert min to ISO string if it's a date or datetime
    min_value = None
    if min is not Undefined:
        if isinstance(min, datetime.datetime):
            min_value = min.date().isoformat()
        elif isinstance(min, datetime.date):
            min_value = min.isoformat()
        else:
            min_value = min

    # Convert max to ISO string if it's a date or datetime
    max_value = None
    if max is not Undefined:
        if isinstance(max, datetime.datetime):
            max_value = max.date().isoformat()
        elif isinstance(max, datetime.date):
            max_value = max.isoformat()
        else:
            max_value = max

    if default_factory is not Undefined:
        default = default_factory()

    return Field(
        default=default,
        title=title if title is not Undefined else None,
        description=description if description is not Undefined else None,
        json_schema_extra={
            "component_cls": DatePicker,
            "name": name if name is not Undefined else None,
            "id": id if id is not Undefined else None,
            "label": label if label is not Undefined else None,
            "placeholder": placeholder,
            "required": required,
            "min_date": min_value,
            "max_date": max_value,
            "disabled": disabled,
            "mode": mode,
            "enable_time": enable_time,
            "time_24hr": time_24hr,
            "date_format": date_format,
            "inline": inline,
            "col_class": col_class,
            **kwargs,
        },
    )
