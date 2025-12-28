"""Bootstrap component models for starlette-templates."""

import typing as t
from markupsafe import Markup
from starlette.datastructures import URL
from pydantic import Field, BaseModel, ConfigDict
from starlette_templates.components.base import ComponentModel

# Type alias for flexible content
# Markup is included to support rendered components
Content = t.Union[str, Markup, ComponentModel, t.List[t.Union[str, ComponentModel, Markup]], None]


class Container(ComponentModel):
    """Bootstrap container component.

    Example:
        ```python
        container = Container(content="<h1>Trail Map</h1>")
        ```
    """

    template: str = Field("components/bootstrap/container.html", frozen=True)
    fluid: bool = Field(default=False, description="Use container-fluid instead of container")
    content: Content = Field(default="", description="HTML string, component, or list of components")
    classes: str = Field(default="", description="Additional CSS classes")


class Row(ComponentModel):
    """Bootstrap row component for grid layout.

    Example:
        ```python
        row = Row(content=[
            Col(md=6, content="Tent"),
            Col(md=6, content="Sleeping Bag")
        ])
        ```
    """

    template: str = Field("components/bootstrap/row.html", frozen=True)
    content: Content = Field(default="", description="HTML string, component, or list of components")
    gap: t.Optional[int] = Field(default=None, ge=0, le=5, description="Gap between children (Bootstrap spacing 0-5)")
    classes: str = Field(default="", description="Additional CSS classes")


class Col(ComponentModel):
    """Bootstrap column component for grid layout.

    Example:
        ```python
        col = Col(md=6, content="Backpack")
        ```
    """

    template: str = Field("components/bootstrap/col.html", frozen=True)
    content: Content = Field(default="", description="HTML string, component, or list of components")
    xs: t.Optional[int] = Field(default=None, description="Column width on extra small screens")
    sm: t.Optional[int] = Field(default=None, description="Column width on small screens")
    md: t.Optional[int] = Field(default=None, description="Column width on medium screens")
    lg: t.Optional[int] = Field(default=None, description="Column width on large screens")
    xl: t.Optional[int] = Field(default=None, description="Column width on extra large screens")
    xxl: t.Optional[int] = Field(default=None, description="Column width on extra extra large screens")
    classes: str = Field(default="", description="Additional CSS classes")


class Grid(ComponentModel):
    """CSS Grid component for simplified grid layouts.

    Example:
        ```python
        grid = Grid(cols=3, content="<div>Tent</div><div>Stove</div><div>Lamp</div>")
        ```
    """

    template: str = Field("components/bootstrap/grid.html", frozen=True)
    cols: int = Field(default=12, ge=1, le=12, description="Number of columns in the grid (1-12)")
    gap: int = Field(default=3, ge=0, le=5, description="Gap between grid items (0-5)")
    content: Content = Field(default="", description="HTML content or component inside grid")
    classes: str = Field(default="", description="Additional CSS classes")


class Card(ComponentModel):
    """Bootstrap card component.

    Example:
        ```python
        card = Card(title="Mountain Trail", content="5.2 miles, moderate")
        ```
    """

    template: str = Field("components/bootstrap/card.html", frozen=True)
    title: t.Optional[str] = Field(default=None, description="Card header title")
    content: Content = Field(default="", description="Card body content (HTML or component)")
    footer: t.Optional[Content] = Field(default=None, description="Card footer content (HTML or component)")
    header_classes: str = Field(default="", description="Additional classes for card header")
    body_classes: str = Field(default="", description="Additional classes for card body")
    footer_classes: str = Field(default="", description="Additional classes for card footer")
    classes: str = Field(default="", description="Additional classes for card wrapper")


class NavLink(BaseModel):
    """Navigation link item."""

    label: str
    href: str
    active: bool = False
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class (e.g., 'bi-home')")


class NavDropdown(BaseModel):
    """Navigation dropdown item."""

    label: str
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class")
    items: t.List[NavLink]


class Navbar(ComponentModel):
    """Bootstrap navbar component.

    Example:
        ```python
        navbar = Navbar(
            brand="Trail Guide",
            links=[
                NavLink(label="Trails", href="/", active=True),
                NavDropdown(label="Gear", items=[
                    NavLink(label="Tents", href="/tents"),
                    NavLink(label="Backpacks", href="/packs")
                ]),
                NavLink(label="Camps", href="/camps")
            ]
        )
        ```
    """

    template: str = Field("components/bootstrap/navbar.html", frozen=True)
    brand: t.Optional[str] = Field(default=None, description="Brand text")
    brand_href: str = Field(default="/", description="Brand link URL")
    brand_icon: t.Optional[str] = Field(default=None, description="Brand icon class")
    links: t.List[t.Union[NavLink, NavDropdown]] = Field(default_factory=list)
    theme: str = Field(default="light", description="Navbar theme: light, dark")
    bg_color: str = Field(default="light", description="Background color class: primary, secondary, light, dark, etc.")
    expand: str = Field(default="lg", description="Breakpoint to expand navbar: sm, md, lg, xl, xxl")
    fixed: t.Optional[str] = Field(default=None, description="Fixed position: top, bottom")
    sticky: bool = Field(default=False, description="Sticky top navbar")


class SidebarButton(ComponentModel):
    """Button component to toggle a Sidebar.

    Example:
        ```python
        sidebar_button = SidebarButton(target_id="nav", text="Menu")
        ```
    """

    template: str = Field("components/bootstrap/sidebar_button.html", frozen=True)
    target_id: str = Field(..., description="ID of the sidebar to toggle")
    text: str = Field(default="Menu", description="Button text")
    variant: str = Field(default="primary", description="Button variant")
    icon: t.Optional[str] = Field(default="bi-list", description="Button icon")


class Sidebar(ComponentModel):
    """Bootstrap offcanvas sidebar component.

    Example:
        ```python
        sidebar = Sidebar(
            title="Trails",
            links=[
                NavLink(label="Hiking", href="/hike"),
                NavLink(label="Camping", href="/camp")
            ]
        )
        ```
    """

    template: str = Field("components/bootstrap/sidebar.html", frozen=True)
    title: t.Optional[str] = Field(default=None, description="Sidebar title")
    links: t.List[t.Union[NavLink, NavDropdown]] = Field(default_factory=list)
    placement: str = Field(default="start", description="Sidebar placement: start, end, top, bottom")
    backdrop: bool = Field(default=True, description="Show backdrop overlay")
    scroll: bool = Field(default=False, description="Allow body scrolling while offcanvas is open")


class BreadcrumbItem(BaseModel):
    """Breadcrumb item."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    label: str
    href: t.Optional[str | URL] = None
    active: bool = False


class Breadcrumb(ComponentModel):
    """Bootstrap breadcrumb component.

    Example:
        ```python
        breadcrumb = Breadcrumb(items=[
            BreadcrumbItem(label="Trails", href="/"),
            BreadcrumbItem(label="Mountain", active=True)
        ])
        ```
    """

    template: str = Field("components/bootstrap/breadcrumb.html", frozen=True)
    items: t.List[BreadcrumbItem] = Field(default_factory=list)


class SubNavLink(BaseModel):
    """Sub-navigation link item."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    label: str
    href: str | URL
    active: bool = False
    icon: t.Optional[str] = Field(default=None, description="Icon class (e.g., 'ti ti-home')")


class SubNav(ComponentModel):
    """Dashboard sub-navigation component with links.

    Example:
        ```python
        subnav = SubNav(links=[
            SubNavLink(label="Trails", href="/trails", active=True),
            SubNavLink(label="Gear", href="/gear")
        ])
        ```
    """

    template: str = Field("components/bootstrap/subnav.html", frozen=True)
    links: t.List[SubNavLink] = Field(default_factory=list, description="Navigation links")
    classes: str = Field(default="", description="Additional CSS classes")
    dropdown_label: t.Optional[str] = Field(default=None, description="Custom label for mobile dropdown menu")


class Badge(ComponentModel):
    """Bootstrap badge component.

    Example:
        ```python
        badge = Badge(content="Easy", variant="success")
        ```
    """

    template: str = Field("components/bootstrap/badge.html", frozen=True)
    content: str = Field(..., description="Badge text")
    variant: str = Field(
        default="primary", description="Badge variant: primary, secondary, success, danger, warning, info, light, dark"
    )
    pill: bool = Field(default=False, description="Pill-shaped badge")
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class")


class ListGroupItem(BaseModel):
    """List group item."""

    text: str
    active: bool = False
    disabled: bool = False
    href: t.Optional[str] = None
    variant: t.Optional[str] = Field(
        default=None, description="Item variant: primary, secondary, success, danger, warning, info, light, dark"
    )
    badge_text: t.Optional[str] = None
    badge_variant: str = "primary"
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class")


class ListGroup(ComponentModel):
    """Bootstrap list group component.

    Example:
        ```python
        list_group = ListGroup(items=[
            ListGroupItem(text="Tent", active=True),
            ListGroupItem(text="Sleeping Bag"),
            ListGroupItem(text="Backpack")
        ])
        ```
    """

    template: str = Field("components/bootstrap/list_group.html", frozen=True)
    items: t.List[ListGroupItem] = Field(..., description="List items")
    flush: bool = Field(default=False, description="Remove borders and rounded corners")
    numbered: bool = Field(default=False, description="Numbered list")
    horizontal: t.Optional[str] = Field(default=None, description="Horizontal at breakpoint: sm, md, lg, xl, xxl")


class CarouselItem(BaseModel):
    """Carousel slide item."""

    image_url: str
    caption_title: t.Optional[str] = None
    caption_text: t.Optional[str] = None
    active: bool = False


class Carousel(ComponentModel):
    """Bootstrap carousel component.

    Example:
        ```python
        carousel = Carousel(
            id="trails",
            items=[
                CarouselItem(image_url="/mountain.jpg", active=True),
                CarouselItem(image_url="/forest.jpg")
            ]
        )
        ```
    """

    id: str
    template: str = Field("components/bootstrap/carousel.html", frozen=True)
    items: t.List[CarouselItem] = Field(..., description="Carousel slides")
    controls: bool = Field(default=True, description="Show prev/next controls")
    indicators: bool = Field(default=True, description="Show slide indicators")
    auto_play: bool = Field(default=True, description="Auto-advance slides")
    interval: int = Field(default=5000, description="Auto-play interval in milliseconds")
    fade: bool = Field(default=False, description="Fade transition instead of slide")


class Tag(ComponentModel):
    """Tag/chip component (badge variant).

    Example:
        ```python
        tag = Tag(content="Mountain", variant="info")
        ```
    """

    template: str = Field("components/bootstrap/tag.html", frozen=True)
    content: str = Field(..., description="Tag text")
    variant: str = Field(default="secondary", description="Tag variant")
    removable: bool = Field(default=False, description="Show remove button")
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class")


class Button(ComponentModel):
    """Bootstrap button component.

    Example:
        ```python
        button = Button(content="Start Hike", variant="primary")
        ```
    """

    template: str = Field("components/bootstrap/button.html", frozen=True)
    content: str = Field(..., description="Button text")
    variant: str = Field(default="primary", description="Button variant")
    size: t.Optional[str] = Field(default=None, description="Button size: sm, lg")
    outline: bool = Field(default=False, description="Outline button style")
    disabled: bool = Field(default=False, description="Disabled button")
    href: t.Optional[str] = Field(default=None, description="Link URL (renders as <a> tag)")
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class")
    icon_position: str = Field(default="left", description="Icon position: left, right")
    block: bool = Field(default=False, description="Block-level button")


class PageHeader(ComponentModel):
    """Page header with title and optional subtitle.

    Example:
        ```python
        page_header = PageHeader(title="Trail Guide", subtitle="Find your next adventure")
        ```
    """

    template: str = Field("components/bootstrap/page_header.html", frozen=True)
    title: str = Field(..., description="Page title (h1)")
    subtitle: t.Optional[str] = Field(default=None, description="Subtitle text (lead paragraph)")
    classes: str = Field(default="", description="Additional CSS classes")


class FilterItem(BaseModel):
    """A single filter item in the filter bar."""

    label: str = Field(..., description="Filter label")
    value: str = Field(..., description="Filter value to display")


class FilterBar(ComponentModel):
    """Sticky horizontal filter bar showing selected filter values.

    Example:
        ```python
        filter_bar = FilterBar(items=[
            FilterItem(label="Difficulty", value="Easy"),
            FilterItem(label="Distance", value="< 5 miles")
        ])
        ```
    """

    template: str = Field("components/bootstrap/filter_bar.html", frozen=True)
    items: t.List[FilterItem] = Field(default_factory=list, description="Filter items to display")
    sticky: bool = Field(default=True, description="Make the bar sticky on scroll")
    classes: str = Field(default="", description="Additional CSS classes")


class Alert(ComponentModel):
    """Bootstrap alert component.

    Example:
        ```python
        alert = Alert(content="Trail closed for maintenance", variant="warning")
        ```
    """

    template: str = Field("components/bootstrap/alert.html", frozen=True)
    content: str = Field(..., description="Alert message content")
    variant: str = Field(
        default="info", description="Alert variant: primary, secondary, success, danger, warning, info, light, dark"
    )
    dismissible: bool = Field(default=False, description="Show close button")
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class to display")
    heading: t.Optional[str] = Field(default=None, description="Alert heading")


class Toast(ComponentModel):
    """Bootstrap toast notification component.

    Example:
        ```python
        toast = Toast(title="Weather Alert", content="Rain expected at 3pm", variant="info")
        ```
    """

    template: str = Field("components/bootstrap/toast.html", frozen=True)
    title: str = Field(..., description="Toast title")
    content: str = Field(..., description="Toast message content")
    variant: str = Field(
        default="info", description="Toast variant: primary, secondary, success, danger, warning, info, light, dark"
    )
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class to display")
    autohide: bool = Field(default=True, description="Auto hide the toast")
    delay: int = Field(default=5000, description="Auto hide delay in milliseconds")
    position: str = Field(
        default="top-end",
        description="Toast position: top-start, top-center, top-end, middle-start, middle-center, middle-end, bottom-start, bottom-center, bottom-end",
    )
    show_time: bool = Field(default=True, description="Show timestamp")


class Modal(ComponentModel):
    """Bootstrap modal dialog component.

    Example:
        ```python
        modal = Modal(title="Trail Info", content="<p>Rocky terrain, bring boots</p>")
        ```
    """

    template: str = Field("components/bootstrap/modal.html", frozen=True)
    title: str = Field(..., description="Modal title")
    content: str = Field(..., description="Modal body content (HTML)")
    footer: t.Optional[str] = Field(default=None, description="Modal footer content (HTML)")
    size: t.Optional[str] = Field(default=None, description="Modal size: sm, lg, xl")
    centered: bool = Field(default=False, description="Vertically center modal")
    scrollable: bool = Field(default=False, description="Scrollable modal body")
    backdrop: t.Union[bool, str] = Field(default=True, description="Show backdrop: True, False, or 'static'")
    keyboard: bool = Field(default=True, description="Close modal on Escape key")
    show_close_button: bool = Field(default=True, description="Show close button in header")
    show_footer: bool = Field(default=True, description="Show modal footer")


class Tooltip(ComponentModel):
    """Bootstrap tooltip component.

    Example:
        ```python
        tooltip = Tooltip(content="Trail", tooltip_text="5.2 miles")
        ```
    """

    template: str = Field("components/bootstrap/tooltip.html", frozen=True)
    content: str = Field(..., description="Element content (text or HTML)")
    tooltip_text: str = Field(..., description="Tooltip text")
    placement: str = Field(default="top", description="Tooltip placement: top, bottom, left, right, auto")
    trigger: str = Field(default="hover focus", description="Trigger events: hover, focus, click")
    html: bool = Field(default=False, description="Allow HTML in tooltip")


class Popover(ComponentModel):
    """Bootstrap popover component.

    Example:
        ```python
        popover = Popover(content="Info", popover_title="Trail", popover_content="Moderate difficulty")
        ```
    """

    template: str = Field("components/bootstrap/popover.html", frozen=True)
    content: str = Field(..., description="Element content (text or HTML)")
    popover_title: t.Optional[str] = Field(default=None, description="Popover title")
    popover_content: str = Field(..., description="Popover content")
    placement: str = Field(default="top", description="Popover placement: top, bottom, left, right, auto")
    trigger: str = Field(default="click", description="Trigger events: hover, focus, click")
    html: bool = Field(default=False, description="Allow HTML in popover")


class ProgressBar(ComponentModel):
    """Bootstrap progress bar component.

    Example:
        ```python
        progress = ProgressBar(value=75, variant="success", show_label=True)
        ```
    """

    template: str = Field("components/bootstrap/progress.html", frozen=True)
    value: float = Field(..., description="Progress value (0-100)")
    variant: str = Field(
        default="primary", description="Progress bar variant: primary, secondary, success, danger, warning, info"
    )
    striped: bool = Field(default=False, description="Striped progress bar")
    animated: bool = Field(default=False, description="Animated stripes")
    show_label: bool = Field(default=False, description="Show percentage label")
    height: t.Optional[str] = Field(default=None, description="Custom height (e.g., '20px')")


class Spinner(ComponentModel):
    """Bootstrap spinner/loader component.

    Example:
        ```python
        spinner = Spinner(label="Loading trails...")
        ```
    """

    template: str = Field("components/bootstrap/spinner.html", frozen=True)
    type: str = Field(default="border", description="Spinner type: border, grow")
    variant: str = Field(
        default="primary",
        description="Spinner variant: primary, secondary, success, danger, warning, info, light, dark",
    )
    size: t.Optional[str] = Field(default=None, description="Spinner size: sm")
    label: str = Field(default="Loading...", description="Screen reader label")


class TabItem(BaseModel):
    """Tab item for Tabs component."""

    id: str
    title: str
    content: str
    active: bool = False
    disabled: bool = False
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class")


class Tabs(ComponentModel):
    """Bootstrap tabs component.

    Example:
        ```python
        tabs = Tabs(tabs=[
            TabItem(id="gear", title="Gear", content="<p>Equipment list</p>", active=True),
            TabItem(id="trails", title="Trails", content="<p>Trail maps</p>")
        ])
        ```
    """

    template: str = Field("components/bootstrap/tabs.html", frozen=True)
    tabs: t.List[TabItem] = Field(..., description="Tab items")
    variant: str = Field(default="tabs", description="Tab style: tabs, pills")
    justified: bool = Field(default=False, description="Equal width tabs")
    vertical: bool = Field(default=False, description="Vertical tabs")


class AccordionItem(BaseModel):
    """Accordion item."""

    title: str
    content: str
    expanded: bool = False
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class")


class Accordion(ComponentModel):
    """Bootstrap accordion component.

    Example:
        ```python
        accordion = Accordion(items=[
            AccordionItem(title="Gear", content="<p>Tent, sleeping bag</p>", expanded=True),
            AccordionItem(title="Food", content="<p>Trail mix, water</p>")
        ])
        ```
    """

    template: str = Field("components/bootstrap/accordion.html", frozen=True)
    items: t.List[AccordionItem] = Field(..., description="Accordion items")
    always_open: bool = Field(default=False, description="Allow multiple items to be open")
    flush: bool = Field(default=False, description="Remove borders and rounded corners")


class Pagination(ComponentModel):
    """Bootstrap pagination component.

    Example:
        ```python
        pagination = Pagination(current_page=2, total_pages=5, base_url="/trails")
        ```
    """

    template: str = Field("components/bootstrap/pagination.html", frozen=True)
    current_page: int = Field(..., description="Current page number (1-indexed)")
    total_pages: int = Field(..., description="Total number of pages")
    max_links: int = Field(default=5, description="Maximum page links to show")
    size: t.Optional[str] = Field(default=None, description="Pagination size: sm, lg")
    show_first_last: bool = Field(default=True, description="Show first/last page links")
    show_prev_next: bool = Field(default=True, description="Show previous/next links")
    base_url: str = Field(default="#", description="Base URL for page links")
    param_name: str = Field(default="page", description="Query parameter name for page")


class DropdownItem(BaseModel):
    """Dropdown menu item."""

    label: t.Optional[str] = None
    href: t.Optional[str] = None
    active: bool = False
    disabled: bool = False
    divider: bool = False
    header: bool = False
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class")


class Dropdown(ComponentModel):
    """Bootstrap dropdown component.

    Example:
        ```python
        dropdown = Dropdown(button_text="Trails", items=[
            DropdownItem(label="Mountain", href="/mountain"),
            DropdownItem(label="Forest", href="/forest")
        ])
        ```
    """

    template: str = Field("components/bootstrap/dropdown.html", frozen=True)
    button_text: str = Field(..., description="Dropdown button text")
    items: t.List[DropdownItem] = Field(..., description="Dropdown menu items")
    variant: str = Field(default="primary", description="Button variant")
    size: t.Optional[str] = Field(default=None, description="Button size: sm, lg")
    split: bool = Field(default=False, description="Split button dropdown")
    direction: str = Field(default="down", description="Dropdown direction: down, up, start, end")
    alignment: str = Field(default="start", description="Menu alignment: start, end")


class ButtonGroup(ComponentModel):
    """Bootstrap button group component.

    Example:
        ```python
        button_group = ButtonGroup(data=[
            {"label": "Easy", "href": "#", "active": True},
            {"label": "Hard", "href": "#"}
        ])
        ```
    """

    template: str = Field("components/bootstrap/button_group.html", frozen=True)
    data: t.List[t.Dict[str, t.Any]] = Field(
        ..., description="Buttons as list of dictionaries with label, href, variant, active, disabled"
    )
    size: t.Optional[str] = Field(default=None, description="Button group size: sm, lg")
    vertical: bool = Field(default=False, description="Vertical button group")
    toolbar: bool = Field(default=False, description="Button toolbar")


class Collapse(ComponentModel):
    """Bootstrap collapse component.

    Example:
        ```python
        collapse = Collapse(button_text="Trail Details", content="<p>Rocky terrain</p>")
        ```
    """

    template: str = Field("components/bootstrap/collapse.html", frozen=True)
    button_text: str = Field(..., description="Toggle button text")
    content: str = Field(..., description="Collapsible content (HTML)")
    expanded: bool = Field(default=False, description="Initially expanded")
    button_variant: str = Field(default="primary", description="Button variant")


class ActivityItem(ComponentModel):
    """Activity feed item.

    Example:
        ```python
        activity = ActivityItem(title="Trail completed", timestamp="2 hours ago")
        ```
    """

    template: str = Field("components/bootstrap/activity_item.html", frozen=True)
    title: str = Field(..., description="Activity title")
    description: t.Optional[str] = Field(default=None, description="Activity description")
    timestamp: str = Field(..., description="Activity timestamp")
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class")
    icon_variant: str = Field(default="primary", description="Icon background color variant")
    user_name: t.Optional[str] = Field(default=None, description="User name")
    user_avatar: t.Optional[str] = Field(default=None, description="User avatar URL")


class Timeline(ComponentModel):
    """Timeline component for events.

    Example:
        ```python
        timeline = Timeline(data=[
            {"title": "Started hike", "timestamp": "9am"},
            {"title": "Reached summit", "timestamp": "2pm"}
        ])
        ```
    """

    template: str = Field("components/bootstrap/timeline.html", frozen=True)
    title: t.Optional[str] = Field(default=None, description="Timeline title")
    data: t.List[t.Dict[str, t.Any]] = Field(
        ..., description="Timeline events as list of dictionaries with title, description, timestamp, icon, variant"
    )


class Table(ComponentModel):
    """Basic Bootstrap table component.

    Example:
        ```python
        table = Table(data=[
            {"trail": "Eagle Peak", "miles": 5.2},
            {"trail": "Pine Ridge", "miles": 3.8}
        ])
        ```
    """

    template: str = "components/bootstrap/table.html"
    columns: t.Optional[t.List[str]] = Field(
        default=None, description="Column names (inferred from data if not provided)"
    )
    data: t.List[t.Dict[str, t.Any]] = Field(..., description="Table data as list of dictionaries")
    column_labels: t.Optional[t.Dict[str, str]] = Field(
        default=None, description="Mapping of column keys to display labels"
    )
    striped: bool = Field(default=False, description="Striped rows")
    hover: bool = Field(default=False, description="Hoverable rows")
    bordered: bool = Field(default=False, description="Bordered table")
    borderless: bool = Field(default=False, description="Borderless table")
    small: bool = Field(default=False, description="Compact table")
    responsive: bool = Field(default=True, description="Responsive table wrapper")
    variant: t.Optional[str] = Field(default=None, description="Table color variant")

    def model_post_init(self, __context):
        """Infer columns from data if not provided."""
        super().model_post_init(__context)
        if self.columns is None and self.data:
            self.columns = list(self.data[0].keys())


class Icon(ComponentModel):
    """Bootstrap icon component.

    Example:
        ```python
        icon = Icon(name="bi-tree", color="green")
        ```
    """

    template: str = Field("components/bootstrap/icon.html", frozen=True)
    name: str = Field(..., description="Bootstrap icon class name (e.g., 'bi-heart-fill')")
    size: t.Optional[str] = Field(default=None, description="Icon size: 1rem, 2rem, etc.")
    color: t.Optional[str] = Field(default=None, description="Icon color (CSS color or Bootstrap text-* class)")


class Avatar(ComponentModel):
    """User avatar component.

    Example:
        ```python
        avatar = Avatar(initials="TG", variant="success")
        ```
    """

    template: str = Field("components/bootstrap/avatar.html", frozen=True)
    image_url: t.Optional[str] = Field(default=None, description="Avatar image URL")
    initials: t.Optional[str] = Field(default=None, description="User initials (if no image)")
    alt: str = Field(default="User avatar", description="Image alt text")
    size: str = Field(default="md", description="Avatar size: xs, sm, md, lg, xl")
    variant: str = Field(default="primary", description="Background color variant for initials")
    rounded: bool = Field(default=True, description="Rounded (circle) avatar")
    border: bool = Field(default=False, description="Show border")
    status: t.Optional[str] = Field(default=None, description="Status indicator: online, offline, away, busy")


class Skeleton(ComponentModel):
    """Loading skeleton placeholder component.

    Example:
        ```python
        skeleton = Skeleton(type="text", lines=3)
        ```
    """

    template: str = Field("components/bootstrap/skeleton.html", frozen=True)
    type: str = Field(default="text", description="Skeleton type: text, circle, rectangle")
    width: t.Optional[str] = Field(default=None, description="Custom width (e.g., '100%', '200px')")
    height: t.Optional[str] = Field(default=None, description="Custom height (e.g., '20px', '100px')")
    lines: int = Field(default=1, description="Number of text lines (for type='text')")
    animation: str = Field(default="wave", description="Animation style: wave, pulse, none")


class EmptyState(ComponentModel):
    """Empty state placeholder component.

    Example:
        ```python
        empty_state = EmptyState(title="No trails found", action_text="Browse All")
        ```
    """

    template: str = Field("components/bootstrap/empty_state.html", frozen=True)
    title: str = Field(..., description="Empty state title")
    description: t.Optional[str] = Field(default=None, description="Empty state description")
    icon: t.Optional[str] = Field(default=None, description="Bootstrap icon class")
    icon_size: str = Field(default="4rem", description="Icon size")
    icon_variant: str = Field(default="secondary", description="Icon color variant")
    action_text: t.Optional[str] = Field(default=None, description="Action button text")
    action_href: t.Optional[str] = Field(default=None, description="Action button URL")
    action_variant: str = Field(default="primary", description="Action button variant")


class Offcanvas(ComponentModel):
    """Bootstrap offcanvas component (generic version).

    Example:
        ```python
        offcanvas = Offcanvas(title="Trail Map", body="<p>Map content</p>")
        ```
    """

    template: str = Field("components/bootstrap/offcanvas.html", frozen=True)
    title: str = Field(..., description="Offcanvas title")
    body: str = Field(..., description="Offcanvas body content (HTML)")
    placement: str = Field(default="end", description="Placement: start, end, top, bottom")
    backdrop: bool = Field(default=True, description="Show backdrop overlay")
    scroll: bool = Field(default=False, description="Allow body scrolling")
    show_close_button: bool = Field(default=True, description="Show close button")


class Divider(ComponentModel):
    """Horizontal divider component.

    Example:
        ```python
        divider = Divider(text="OR")
        ```
    """

    template: str = Field("components/bootstrap/divider.html", frozen=True)
    text: t.Optional[str] = Field(default=None, description="Divider text label")
    margin: str = Field(default="my-3", description="Margin classes")


class CopyButton(ComponentModel):
    """Copy to clipboard button component.

    Example:
        ```python
        copy_button = CopyButton(text_to_copy="Trail coordinates: 47.6°N")
        ```
    """

    template: str = Field("components/bootstrap/copy_button.html", frozen=True)
    text_to_copy: str = Field(..., description="Text to copy to clipboard")
    button_text: str = Field(default="Copy", description="Button text")
    success_text: str = Field(default="Copied!", description="Success message")
    variant: str = Field(default="outline-secondary", description="Button variant")
    size: t.Optional[str] = Field(default="sm", description="Button size")
    icon: str = Field(default="bi-clipboard", description="Button icon")
    success_icon: str = Field(default="bi-check2", description="Success icon")
