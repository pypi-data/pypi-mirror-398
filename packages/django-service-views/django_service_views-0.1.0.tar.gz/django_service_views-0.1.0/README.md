# Django Service Views

Django class-based views that support the service layer pattern by preventing automatic `form.save()` calls.

## Why?

Django's generic class-based views automatically call `form.save()` in `form_valid()`, which bypasses your service layer. This package provides views that skip the automatic save, allowing you to handle all data operations through your service layer.

## Installation

```bash
# With pip
pip install django-service-views

# With uv
uv add django-service-views
```

## Quick Start

### Basic Usage

```python
from django_service_views import ServiceUpdateView
from myapp.services import product_service

class ProductUpdateView(ServiceUpdateView):
    model = Product
    fields = ['name', 'price', 'description']
    template_name = 'products/update.html'
    success_url = '/products/'
    
    def form_valid(self, form):
        # Call your service layer instead of form.save()
        product_service.update_product(
            self.object,
            **form.cleaned_data
        )
        return super().form_valid(form)
```

### Create View

```python
from django_service_views import ServiceCreateView

class ProductCreateView(ServiceCreateView):
    model = Product
    fields = ['name', 'price', 'description']
    template_name = 'products/create.html'
    
    def form_valid(self, form):
        # Service layer handles the creation
        self.object = product_service.create_product(
            user=self.request.user,
            **form.cleaned_data
        )
        return super().form_valid(form)
```

### Delete View

```python
from django_service_views import ServiceDeleteView
from django.urls import reverse_lazy

class ProductDeleteView(ServiceDeleteView):
    model = Product
    template_name = 'products/delete_confirm.html'
    success_url = reverse_lazy('product_list')
    
    def delete_with_service(self, obj):
        # Service layer handles the deletion
        product_service.delete_product(obj, user=self.request.user)
```

## Views Provided

### `ServiceModelFormMixin`

Base mixin that prevents automatic `form.save()`. Can be used with any generic view that uses `ModelFormMixin`.

**Important:** Must be placed immediately before the generic view in the inheritance order:

```python
class MyView(ServiceModelFormMixin, UpdateView):  # ✓ Correct
    pass

class MyView(LoginRequiredMixin, ServiceModelFormMixin, UpdateView):  # ✓ Correct
    pass

class MyView(UpdateView, ServiceModelFormMixin):  # ✗ Won't work
    pass
```

### `ServiceUpdateView`

Inherits from `ServiceModelFormMixin` and Django's `UpdateView`. Override `form_valid()` to call your service layer.

### `ServiceCreateView`

Inherits from `ServiceModelFormMixin` and Django's `CreateView`. Override `form_valid()` to call your service layer. Don't forget to set `self.object` to the created instance.

### `ServiceDeleteView`

Inherits from `ServiceModelFormMixin` and Django's `DeleteView`. Must implement `delete_with_service(obj)` method.

## Complete Example with Service Layer

```python
# services.py
from django.db import transaction

class ProductService:
    @transaction.atomic
    def create_product(self, user, **data):
        product = Product.objects.create(**data)
        self.log_creation(product, user)
        self.notify_admins(product)
        return product
    
    @transaction.atomic
    def update_product(self, product, **data):
        for field, value in data.items():
            setattr(product, field, value)
        product.save()
        self.log_update(product)
        return product
    
    def delete_product(self, product, user):
        self.log_deletion(product, user)
        product.delete()

product_service = ProductService()

# views.py
from django_service_views import (
    ServiceCreateView, 
    ServiceUpdateView, 
    ServiceDeleteView
)
from .services import product_service

class ProductCreateView(ServiceCreateView):
    model = Product
    fields = ['name', 'price', 'description']
    
    def form_valid(self, form):
        self.object = product_service.create_product(
            user=self.request.user,
            **form.cleaned_data
        )
        messages.success(self.request, f"Product {self.object.name} created!")
        return super().form_valid(form)

class ProductUpdateView(ServiceUpdateView):
    model = Product
    fields = ['name', 'price', 'description']
    
    def form_valid(self, form):
        product_service.update_product(
            self.object,
            **form.cleaned_data
        )
        messages.success(self.request, "Product updated!")
        return super().form_valid(form)

class ProductDeleteView(ServiceDeleteView):
    model = Product
    success_url = reverse_lazy('product_list')
    
    def delete_with_service(self, obj):
        product_service.delete_product(obj, user=self.request.user)
        messages.success(self.request, "Product deleted!")
```

## Benefits

- **Separation of Concerns**: Keep business logic in service layer, not in views
- **Testability**: Service layer can be tested independently of views
- **Reusability**: Same service methods can be used from views, management commands, API endpoints, etc.
- **Transaction Management**: Handle transactions in service layer where it belongs
- **Consistency**: All data operations go through the same service layer code

## Requirements

- Python >= 3.8
- Django >= 4.2

## License

MIT

## Contributing

Issues and pull requests are welcome at https://github.com/yourusername/django-service-views
