# Customizing Admin

Adding your own models to the admin panel is straightforward, but there's one important quirk: FastroAI models use SQLAlchemy's `MappedAsDataclass`, which requires a special mixin to work with SQLAdmin.

For the full range of configuration options, see the [SQLAdmin documentation](https://aminalaee.github.io/sqladmin/).

## The DataclassModelMixin

SQLAdmin's default behavior creates an empty model instance, then sets attributes one by one. This breaks with dataclass models that have required fields without defaults.

FastroAI solves this with `DataclassModelMixin`, which creates the model with all form data at once:

```python
from ..mixins import DataclassModelMixin

class MyModelAdmin(DataclassModelMixin, ModelView, model=MyModel):
    ...
```

Every admin view in FastroAI uses this mixin. If you add a new view and forget it, you'll get `AttributeError` when trying to create records.

## Adding a New Model View

Create a new file in `backend/src/interfaces/admin/views/`:

```python
# backend/src/interfaces/admin/views/my_model.py

from sqladmin import ModelView
from ....modules.my_module.models import MyModel
from ....modules.my_module.schemas import MyModelCreate, MyModelUpdate
from ..mixins import DataclassModelMixin


class MyModelAdmin(DataclassModelMixin, ModelView, model=MyModel):
    name = "My Model"
    name_plural = "My Models"
    icon = "fa-solid fa-star"
    category = "My Category"

    # List view columns
    column_list = [MyModel.id, MyModel.name, MyModel.created_at]
    column_searchable_list = [MyModel.name]
    column_sortable_list = [MyModel.id, MyModel.name]
    column_default_sort = [(MyModel.id, True)]

    # Detail view shows all fields
    column_details_list = "__all__"

    # Form fields (use your Pydantic schemas)
    form_create_rules = list(MyModelCreate.model_fields.keys())
    form_edit_rules = list(MyModelUpdate.model_fields.keys())

    # Permissions
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    can_export = True
```

Then register it in `backend/src/interfaces/admin/views/__init__.py`:

```python
from .my_model import MyModelAdmin

__all__ = [
    # ... existing views ...
    "MyModelAdmin",
    "register_admin_views",
]

def register_admin_views(admin: Admin) -> None:
    # ... existing registrations ...
    admin.add_view(MyModelAdmin)
```

## Configuration Options

### Column Display

Control what shows up in the list view and how it's labeled:

```python
column_list = [MyModel.id, MyModel.name, MyModel.status]
column_labels = {
    MyModel.id: "ID",
    MyModel.name: "Display Name",
    MyModel.status: "Current Status",
}
```

### Search and Sort

Make columns searchable and sortable:

```python
column_searchable_list = [MyModel.name, MyModel.email]
column_sortable_list = [MyModel.id, MyModel.created_at]
column_default_sort = [(MyModel.created_at, True)]  # True = descending
```

### Form Rules

Use your Pydantic schemas to determine which fields appear in forms:

```python
form_create_rules = list(MyModelCreate.model_fields.keys())
form_edit_rules = list(MyModelUpdate.model_fields.keys())
```

This keeps your admin forms consistent with your API validation.

### Foreign Keys and Relationships

FastroAI models use a dual pattern: **foreign key columns** for database operations and **relationships** for SQLAdmin display. Understanding this pattern is essential when adding models to the admin.

**The Model Pattern**

Every model that has a foreign key also defines a corresponding relationship:

```python
# backend/src/modules/payment/models.py

class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    # Foreign key column - used by FastCRUD and database constraints
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)

    # Relationship - used by SQLAdmin for display and forms
    # Must use lazy="selectin" for async compatibility
    # Must use init=False to exclude from dataclass __init__
    user: Mapped["User"] = relationship("User", back_populates="payments", lazy="selectin", init=False)
```

**Why Both?**

- **FastCRUD** works with FK columns directly and returns dictionaries: `payment["user_id"]`
- **SQLAdmin** uses relationships to render user-friendly dropdowns and display the related object's name instead of a raw ID

**Using Relationships in column_list**

When you list columns in `column_list`, use the **relationship** to display the related object:

```python
class PaymentAdmin(DataclassModelMixin, ModelView, model=Payment):
    # Use Payment.user (relationship), not Payment.user_id (FK column)
    # This shows the user's name/representation instead of just an integer
    column_list = [Payment.id, Payment.user, Payment.status, Payment.amount]
```

**Using FK Columns in Forms**

For forms, include the **FK column names** in your rules. SQLAdmin then auto-generates searchable dropdowns:

```python
class PaymentAdmin(DataclassModelMixin, ModelView, model=Payment):
    # Include FK column names - SQLAdmin creates dropdowns for these
    form_create_rules = [*PaymentCreateAdmin.model_fields.keys(), "user_id", "price_id", "discount_code_id"]
```

**The lazy="selectin" Requirement**

SQLAdmin runs async, so relationships must use `lazy="selectin"` to avoid lazy loading errors. If you see errors like `greenlet_spawn has not been called`, check that your relationships specify this loading strategy.

**Important: Don't Use default=None on Relationships**

For nullable foreign keys, never set `default=None` on the relationship:

```python
# WRONG - causes SQLAlchemy to clear the FK value during commit
discount_code: Mapped["DiscountCode | None"] = relationship(..., default=None, init=False)

# CORRECT - relationship naturally returns None when FK is null
discount_code: Mapped["DiscountCode | None"] = relationship(..., init=False)
```

The `DataclassModelMixin` automatically filters out relationship objects before creating the model instance, passing only FK column values to the dataclass constructor.

## Data Transformation Hooks

Sometimes you need to transform data before it's saved. The `on_model_change` hook runs before creation and updates:

```python
async def on_model_change(
    self, data: dict[str, Any], model: Any, is_created: bool, request: Request
) -> None:
    if is_created and "password" in data and data["password"]:
        # Hash password before saving
        data["hashed_password"] = get_password_hash(data["password"])
        del data["password"]
```

The `is_created` flag tells you if this is a new record or an update. For new records, `model` is `None`.

There's also an `after_model_change` hook that runs after the record is committed to the database:

```python
async def after_model_change(
    self, data: dict[str, Any], model: Any, is_created: bool, request: Request
) -> None:
    if is_created:
        # Send welcome email, trigger webhook, etc.
        await notify_new_record(model)
```

## Adding Bulk Actions

Bulk actions let users select multiple records and perform an operation on all of them. Use the `@action` decorator:

```python
from sqladmin import action
from starlette.requests import Request
from starlette.responses import RedirectResponse


@action(
    name="deactivate",
    label="Deactivate Selected",
    confirmation_message="Are you sure you want to deactivate these records?",
    add_in_list=True,
)
async def action_deactivate(self, request: Request) -> RedirectResponse:
    pks = request.query_params.get("pks", "").split(",")
    if pks and pks[0]:
        ids = [int(pk) for pk in pks]
        async with local_session() as db:
            await crud_my_model.update(
                db=db,
                object={"is_active": False},
                allow_multiple=True,
                id__in=ids,
            )
            await db.commit()

    referer = request.headers.get("Referer")
    return RedirectResponse(referer or request.url_for("admin:list", identity=self.identity))
```

The action gets the selected record IDs from `request.query_params.get("pks")` as a comma-separated string. Parse them, do your update, and redirect back to the list.

## Icons

SQLAdmin uses Font Awesome icons. Set them with the `icon` attribute:

```python
icon = "fa-solid fa-star"        # Solid star
icon = "fa-solid fa-users"       # Users icon
icon = "fa-solid fa-credit-card" # Credit card
icon = "fa-solid fa-layer-group" # Layered squares
```

Browse the [Font Awesome gallery](https://fontawesome.com/icons) for options.

## Categories

Group related views together with the `category` attribute:

```python
category = "Users & Access"
category = "Products & Pricing"
category = "Billing"
```

Views with the same category appear together in the sidebar.

## Key Files

| Component | Location |
|-----------|----------|
| Dataclass mixin | `backend/src/interfaces/admin/mixins.py` |
| View registration | `backend/src/interfaces/admin/views/__init__.py` |
| Example views | `backend/src/interfaces/admin/views/*.py` |

---

[← Admin Overview](index.md){ .md-button } [Infrastructure →](../infrastructure/index.md){ .md-button .md-button--primary }
