"""
Service layer views for Django.

These views provide a pattern for separating business logic into service layers
while using Django's class-based views.
"""

from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DeleteView, UpdateView


class ServiceModelFormMixin:
    """
        Mixin that disables automatic form.save() in form_valid().
        Use this when you want to handle saving through a service layer instead.

        MUST BE USED IMMEDIATELY BEFORE UpdateView/CreateView IN THE INHERITANCE ORDER.
    s
        This prevents ModelFormMixin.form_valid() from calling form.save() by providing
        an alternative implementation that skips the save step.

        Example:
            class MyUpdateView(ServiceModelFormMixin, UpdateView):
                model = MyModel
                fields = ['field1', 'field2']

                def form_valid(self, form):
                    # Use your service layer here
                    my_service.update(self.object, form.cleaned_data)
                    return super().form_valid(form)
    """

    def form_valid(self, form):
        """
        Handle valid form without automatic save.
        Subclasses should use service layer to save data.

        Instead of calling form.save(), we set self.object (if needed for ModelFormMixin)
        then continue to the next form_valid() in the chain, eventually reaching
        FormMixin which just does the redirect.
        """
        return HttpResponseRedirect(self.get_success_url())


class ServiceUpdateView(ServiceModelFormMixin, UpdateView):
    """
    View to update a model using a service class.
    The form.save() method from UpdateView is overridden to prevent automatic saving.

    Subclasses should override form_valid() to call their service layer:

    Example:
        class ProductUpdateView(ServiceUpdateView):
            model = Product
            fields = ['name', 'price']

            def form_valid(self, form):
                product_service.update_product(
                    self.object,
                    **form.cleaned_data
                )
                return super().form_valid(form)
    """


class ServiceCreateView(ServiceModelFormMixin, CreateView):
    """
    View to create a model instance using a service class.
    The form.save() method from CreateView is overridden to prevent automatic saving.

    Subclasses should override form_valid() to call their service layer:

    Example:
        class ProductCreateView(ServiceCreateView):
            model = Product
            fields = ['name', 'price']

            def form_valid(self, form):
                self.object = product_service.create_product(
                    **form.cleaned_data
                )
                return super().form_valid(form)
    """


class ServiceDeleteView(ServiceModelFormMixin, DeleteView):
    """
    View to delete a model instance using a service class.
    The delete() method from DeleteView is overridden to call the service layer.

    Must define a delete_with_service() method in subclasses to call the service
    layer's delete method.

    Example:
        class ProductDeleteView(ServiceDeleteView):
            model = Product
            success_url = reverse_lazy('product_list')

            def delete_with_service(self, obj):
                product_service.delete_product(obj)
    """

    def form_valid(self, form):
        """
        Handle valid form without automatic delete.
        Subclasses should use service layer to delete data.
        """
        success_url = self.get_success_url()
        self.delete_with_service(self.object)
        return HttpResponseRedirect(success_url)

    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.delete_with_service(self.object)
        return HttpResponseRedirect(success_url)

    def delete_with_service(self, obj):
        """
        Subclasses should implement this method to call the service layer's delete method.

        Args:
            obj: The model instance to delete

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement delete_with_service() method.")
