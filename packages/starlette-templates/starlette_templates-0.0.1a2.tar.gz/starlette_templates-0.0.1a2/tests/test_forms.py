"""Tests for starlette_templates.forms module.

This test module demonstrates form handling features including:
- model_from_request: Parse and validate request data against Pydantic models
- FormModel: Base class for form models with rendering capabilities
- Form field helpers: TextField, EmailField, SelectField, DateField, etc.
- Form validation and error handling
- Multi-source data merging (path params, query params, form data, JSON)
"""
import pytest
import datetime
from starlette.requests import Request
from starlette.datastructures import FormData, Headers
from pydantic import ValidationError
from starlette_templates.forms import (
    model_from_request,
    FormModel,
    TextField,
    IntegerField,
    FloatField,
    EmailField,
    TextAreaField,
    CheckboxField,
    SelectField,
    SubmitButtonField,
    HiddenField,
    DateField,
    Choice,
)


async def test_model_from_request_json():
    """Test model_from_request with JSON data."""
    from pydantic import BaseModel

    class User(BaseModel):
        name: str
        age: int

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [(b"content-type", b"application/json")],
        "query_string": b"",
    }

    async def receive():
        return {"body": b'{"name": "John", "age": 30}', "type": "http.request"}

    request = Request(scope, receive)
    user = await model_from_request(request, User)

    assert user.name == "John"
    assert user.age == 30


async def test_model_from_request_form():
    """Test model_from_request with form data."""
    from pydantic import BaseModel

    class User(BaseModel):
        name: str
        age: int

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [(b"content-type", b"application/x-www-form-urlencoded")],
        "query_string": b"",
    }

    async def receive():
        return {"body": b"name=John&age=30", "type": "http.request"}

    request = Request(scope, receive)
    user = await model_from_request(request, User)

    assert user.name == "John"
    assert user.age == 30


async def test_model_from_request_with_path_params():
    """Test model_from_request includes path parameters."""
    from pydantic import BaseModel

    class Article(BaseModel):
        category: str
        slug: str

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/tech/hello-world",
        "headers": [],
        "query_string": b"",
        "path_params": {"category": "tech", "slug": "hello-world"},
    }

    request = Request(scope)
    article = await model_from_request(request, Article)

    assert article.category == "tech"
    assert article.slug == "hello-world"


async def test_model_from_request_with_query_params():
    """Test model_from_request includes query parameters."""
    from pydantic import BaseModel

    class SearchParams(BaseModel):
        q: str
        page: int = 1

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/search",
        "headers": [],
        "query_string": b"q=python&page=2",
    }

    request = Request(scope)
    params = await model_from_request(request, SearchParams)

    assert params.q == "python"
    assert params.page == 2


async def test_model_from_request_without_model():
    """Test model_from_request returns dict when no model provided."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [(b"content-type", b"application/json")],
        "query_string": b"",
    }

    async def receive():
        return {"body": b'{"name": "John", "age": 30}', "type": "http.request"}

    request = Request(scope, receive)
    data = await model_from_request(request)

    assert isinstance(data, dict)
    assert data["name"] == "John"
    assert data["age"] == 30


def test_textfield():
    """Test TextField helper."""
    field = TextField(default="Hello", label="Name", required=True)

    assert field.default == "Hello"
    json_extra = field.json_schema_extra
    assert json_extra["label"] == "Name"
    assert json_extra["required"] is True
    assert json_extra["type"] == "text"


def test_integerfield():
    """Test IntegerField helper."""
    field = IntegerField(default=10, label="Age", ge=0, le=120)

    assert field.default == 10
    # Check constraints were set (they're in metadata)
    json_extra = field.json_schema_extra
    assert json_extra["type"] == "number"


def test_floatfield():
    """Test FloatField helper."""
    field = FloatField(default=19.99, label="Price", ge=0.0)

    assert field.default == 19.99
    # Check that field was created successfully
    json_extra = field.json_schema_extra
    assert json_extra["type"] == "number"


def test_emailfield():
    """Test EmailField helper."""
    field = EmailField(default="test@example.com", label="Email", required=True)

    assert field.default == "test@example.com"
    json_extra = field.json_schema_extra
    assert json_extra["type"] == "email"


def test_textareafield():
    """Test TextAreaField helper."""
    field = TextAreaField(default="", label="Description", rows=5)

    json_extra = field.json_schema_extra
    assert json_extra["rows"] == 5


def test_checkboxfield():
    """Test CheckboxField helper."""
    field = CheckboxField(default=False, label="Accept Terms")

    assert field.default is False
    json_extra = field.json_schema_extra
    assert "label" in json_extra


def test_selectfield_with_dict():
    """Test SelectField with dict choices."""
    field = SelectField(
        default="us",
        choices={"us": "United States", "uk": "United Kingdom"},
        label="Country",
    )

    assert field.default == "us"
    json_extra = field.json_schema_extra
    assert "choices" in json_extra
    # Should be converted to list of dicts
    assert isinstance(json_extra["choices"], list)


def test_selectfield_with_list():
    """Test SelectField with list choices."""
    field = SelectField(
        default="apple",
        choices=["apple", "orange", "banana"],
        label="Fruit",
    )

    assert field.default == "apple"
    json_extra = field.json_schema_extra
    assert "choices" in json_extra


def test_selectfield_with_choice_objects():
    """Test SelectField with Choice objects."""
    field = SelectField(
        default="us",
        choices=[
            Choice(value="us", label="United States"),
            Choice(value="uk", label="United Kingdom"),
        ],
        label="Country",
    )

    assert field.default == "us"


def test_selectfield_multiple():
    """Test SelectField with multiple selection."""
    field = SelectField(
        default=[],
        choices={"sports": "Sports", "music": "Music"},
        multiple=True,
        label="Interests",
    )

    json_extra = field.json_schema_extra
    assert json_extra["multiple"] is True


def test_submitbuttonfield():
    """Test SubmitButtonField helper."""
    field = SubmitButtonField(text="Save Changes", classes=["btn", "btn-primary"])

    json_extra = field.json_schema_extra
    assert json_extra["text"] == "Save Changes"
    assert "btn-primary" in json_extra["classes"]
    assert json_extra["exclude_from_dump"] is True


def test_hiddenfield():
    """Test HiddenField helper."""
    field = HiddenField(default="token123", name="csrf_token")

    assert field.default == "token123"
    json_extra = field.json_schema_extra
    assert json_extra["type"] == "hidden"


def test_datefield():
    """Test DateField helper."""
    field = DateField(
        default=datetime.date(2024, 1, 1),
        label="Birth Date",
        required=True,
    )

    assert field.default == datetime.date(2024, 1, 1)
    json_extra = field.json_schema_extra
    assert json_extra["required"] is True


def test_datefield_with_factory():
    """Test DateField with default_factory."""
    field = DateField(
        default_factory=datetime.date.today,
        label="Today",
    )

    # Default should be set from factory
    assert isinstance(field.default, datetime.date)


def test_formmodel_basic():
    """Test basic FormModel creation."""
    class ContactForm(FormModel):
        name: str = TextField(default="", label="Name")
        email: str = EmailField(default="", label="Email")

    form = ContactForm()
    assert hasattr(form, "name")
    assert hasattr(form, "email")


def test_formmodel_is_valid():
    """Test FormModel.is_valid method."""
    class ContactForm(FormModel):
        name: str = TextField(default="John", label="Name")
        email: str = EmailField(default="john@example.com", label="Email")

    form = ContactForm()
    assert form.is_valid() is True


def test_formmodel_has_errors():
    """Test FormModel.has_errors method."""
    class ContactForm(FormModel):
        name: str = TextField(default="", label="Name")

    form = ContactForm()
    assert form.has_errors() is False

    # Simulate adding an error
    form._field_errors["name"] = "Name is required"
    assert form.has_errors() is True


def test_formmodel_model_dump_excludes_submit():
    """Test FormModel.model_dump excludes submit buttons."""
    class ContactForm(FormModel):
        name: str = TextField(default="John", label="Name")
        submit: str = SubmitButtonField(text="Submit")

    form = ContactForm()
    data = form.model_dump()

    assert "name" in data
    assert "submit" not in data  # Excluded by exclude_from_dump


async def test_formmodel_from_request():
    """Test FormModel.from_request method."""
    class ContactForm(FormModel):
        name: str = TextField(default="", label="Name")
        email: str = EmailField(default="", label="Email")

        model_config = {"method": "POST"}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/contact",
        "headers": [(b"content-type", b"application/x-www-form-urlencoded")],
        "query_string": b"",
    }

    async def receive():
        return {"body": b"name=John&email=john@example.com", "type": "http.request"}

    request = Request(scope, receive)
    form = await ContactForm.from_request(request)

    assert form.name == "John"
    assert form.email == "john@example.com"


async def test_formmodel_from_request_with_validation_error():
    """Test FormModel.from_request captures validation errors."""
    from pydantic import Field

    class ContactForm(FormModel):
        name: str = TextField(default="", label="Name", min_length=3)
        email: str = EmailField(default="", label="Email")

        model_config = {"method": "POST"}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/contact",
        "headers": [(b"content-type", b"application/x-www-form-urlencoded")],
        "query_string": b"",
    }

    async def receive():
        return {"body": b"name=Jo&email=invalid", "type": "http.request"}

    request = Request(scope, receive)
    form = await ContactForm.from_request(request, raise_on_error=False)

    assert form.has_errors() is True
    assert len(form._field_errors) > 0


def test_formmodel_get_error_banner_text():
    """Test FormModel.get_error_banner_text method."""
    class ContactForm(FormModel):
        name: str = TextField(default="", label="Name")

        model_config = {"error_banner_text": "Custom error message"}

    form = ContactForm()
    assert form.get_error_banner_text() == "Custom error message"


def test_choice_model():
    """Test Choice model."""
    choice = Choice(value="us", label="United States")
    assert choice.value == "us"
    assert choice.label == "United States"
    assert choice.disabled is False

    choice_disabled = Choice(value="ca", label="Canada", disabled=True)
    assert choice_disabled.disabled is True


async def test_formmodel_is_valid_checks_method():
    """Test FormModel.is_valid checks HTTP method when request provided."""
    class ContactForm(FormModel):
        name: str = TextField(default="John", label="Name")

        model_config = {"method": "POST"}

    scope = {
        "type": "http",
        "method": "GET",  # Wrong method
        "path": "/",
        "headers": [],
    }
    request = Request(scope)

    form = ContactForm()
    assert form.is_valid(request) is False  # Wrong method

    # Correct method
    scope2 = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [],
    }
    request2 = Request(scope2)
    assert form.is_valid(request2) is True


def test_formmodel_get_field_defaults():
    """Test FormModel._get_field_defaults class method."""
    class ContactForm(FormModel):
        name: str = TextField(default="John", label="Name")
        age: int = IntegerField(default=30, label="Age")

    defaults = ContactForm._get_field_defaults()

    assert defaults["name"] == "John"
    assert defaults["age"] == 30


def test_formmodel_parse_validation_errors():
    """Test FormModel._parse_validation_errors class method."""
    from pydantic import BaseModel, Field

    class User(BaseModel):
        name: str = Field(min_length=3)
        age: int

    try:
        User(name="Jo", age="invalid")
    except ValidationError as e:
        from starlette_templates.forms import FormModel

        # Create a simple FormModel to test the method
        class UserForm(FormModel):
            name: str = TextField(default="", min_length=3)
            age: int = IntegerField(default=0)

        errors = UserForm._parse_validation_errors(e)

        assert "name" in errors or "age" in errors
        assert isinstance(errors, dict)


def test_selectfield_choices_factory():
    """Test SelectField with choices_factory."""
    def get_countries():
        return {"us": "United States", "uk": "United Kingdom"}

    field = SelectField(
        default="us",
        choices_factory=get_countries,
        label="Country",
    )

    json_extra = field.json_schema_extra
    assert "choices" in json_extra
    assert len(json_extra["choices"]) == 2


def test_datefield_with_min_max():
    """Test DateField with min and max constraints."""
    field = DateField(
        default=datetime.date(2024, 6, 1),
        min=datetime.date(2024, 1, 1),
        max=datetime.date(2024, 12, 31),
        label="Event Date",
    )

    json_extra = field.json_schema_extra
    assert json_extra["min_date"] == "2024-01-01"
    assert json_extra["max_date"] == "2024-12-31"


def test_textfield_hidden():
    """Test TextField with hidden=True."""
    field = TextField(default="secret", label="Secret", hidden=True)

    json_extra = field.json_schema_extra
    assert json_extra["type"] == "hidden"
