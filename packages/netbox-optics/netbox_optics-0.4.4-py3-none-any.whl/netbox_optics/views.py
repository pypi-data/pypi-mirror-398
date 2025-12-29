import logging

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.db.models import Count
from django.urls import reverse
from netbox.views import generic
from utilities.forms import restrict_form_fields
from utilities.exceptions import AbortRequest, PermissionsViolation
from utilities.utils import prepare_cloned_fields, normalize_querydict
from utilities.htmx import is_htmx
from extras.signals import clear_events
from netbox.views.generic.utils import get_prerequisite_model

from dcim.models import Device

from .models import (
    OpticalGridType,
    OpticalGrid,
    OpticalGridWavelength,
    OpticalGridTypeWavelength,
    OpticalSpan,
    OpticalConnection,
    MuxWavelengthMap,
)

from .tables import (
    OpticalGridTypeTable,
    OpticalGridTable,
    OpticalGridWavelengthTable,
    OpticalGridTypeWavelengthTable,
    OpticalSpanTable,
    OpticalConnectionTable,
    MuxWavelengthMapTable,
)
from .forms import (
    OpticalGridTypeForm,
    OpticalGridForm,
    BulkWavelengthForm,
    OpticalGridWavelengthForm,
    OpticalSpanForm,
    OpticalConnectionForm,
    MuxWavelengthMapForm,
    OpticalGridTypeFilterForm,
    OpticalGridFilterForm,
    OpticalGridWavelengthFilterForm,
    OpticalGridTypeWavelengthFilterForm,
    OpticalSpanFilterForm,
    OpticalConnectionFilterForm,
    MuxWavelengthMapFilterForm,
    OpticalGridTypeImportForm,
    OpticalGridImportForm,
    OpticalGridWavelengthImportForm,
    OpticalSpanImportForm,
    OpticalConnectionImportForm,
    MuxWavelengthMapImportForm,
    OpticalGridTypeWavelengthForm,
)
from .filters import (
    OpticalGridTypeFilter,
    OpticalGridFilter,
    OpticalGridWavelengthFilter,
    OpticalGridTypeWavelengthFilter,
    OpticalSpanFilter,
    OpticalConnectionFilter,
    MuxWavelengthMapFilter,
)


logger = logging.getLogger(__name__)


# OpticalGridType views
class OpticalGridTypeView(generic.ObjectView):
    queryset = OpticalGridType.objects.all()
    template_name = "netbox_optics/opticalgridtype.html"


class OpticalGridTypeListView(generic.ObjectListView):
    queryset = OpticalGridType.objects.all().annotate(grids_count=Count("grids"))
    table = OpticalGridTypeTable
    filterset = OpticalGridTypeFilter
    filterset_form = OpticalGridTypeFilterForm


class OpticalGridTypeEditView(generic.ObjectEditView):
    queryset = OpticalGridType.objects.all()
    model_form = OpticalGridTypeForm
    form = OpticalGridTypeForm
    template_name = "netbox_optics/opticalgridtype_edit.html"

    def get(self, request, *args, **kwargs):
        # adds bulk wavelengths form handing, uses original super().get() code
        obj = self.get_object(**kwargs)
        obj = self.alter_object(obj, request, args, kwargs)
        model = self.queryset.model

        initial_data = normalize_querydict(request.GET)
        form = self.model_form(instance=obj, initial=initial_data)
        restrict_form_fields(form, request.user)

        # HTMX request - return only form HTML
        if is_htmx(request):
            return render(request, self.htmx_template_name, {
                'form': form,
            })

        # Create bulk form only for new objects
        bulk_form = BulkWavelengthForm() if not obj.pk else None

        return render(
            request,
            self.template_name,
            {
                "model": model,
                "object": obj,
                "form": form,
                "bulk_form": bulk_form,
                "return_url": self.get_return_url(request, obj),
                "prerequisite_model": get_prerequisite_model(self.queryset),
                **self.get_extra_context(request, obj),
            },
        )

    def post(self, request, *args, **kwargs):
        # adds bulk wavelengths form handing, uses original super().post() code
        logger = logging.getLogger('netbox.views.ObjectEditView')
        obj = self.get_object(**kwargs)
        is_new = not obj.pk

        # Take a snapshot for change logging (if editing an existing object)
        if obj.pk and hasattr(obj, 'snapshot'):
            obj.snapshot()

        obj = self.alter_object(obj, request, args, kwargs)

        form = self.model_form(data=request.POST, files=request.FILES, instance=obj)
        restrict_form_fields(form, request.user)

        if form.is_valid():
            logger.debug("Form validation was successful")

            try:
                with transaction.atomic():
                    object_created = form.instance.pk is None
                    obj = form.save()

                    # Handle bulk wavelengths for new objects
                    if object_created:
                        bulk_form = BulkWavelengthForm(request.POST)
                        if bulk_form.is_valid():
                            for wavelength_value in bulk_form.cleaned_data.get("bulk_wavelengths", []):
                                if not obj.allowed_wavelengths.filter(value=wavelength_value).exists():
                                    OpticalGridTypeWavelength.objects.create(
                                        grid_type=obj, value=wavelength_value
                                    )

                    # Check that the new object conforms with any assigned object-level permissions
                    if not self.queryset.filter(pk=obj.pk).exists():
                        raise PermissionsViolation()

                msg = '{} {}'.format(
                    'Created' if object_created else 'Modified',
                    self.queryset.model._meta.verbose_name
                )
                logger.info(f"{msg} {obj} (PK: {obj.pk})")
                if hasattr(obj, 'get_absolute_url'):
                    msg = mark_safe(f'{msg} <a href="{obj.get_absolute_url()}">{escape(obj)}</a>')
                else:
                    msg = f'{msg} {obj}'
                messages.success(request, msg)

                if '_addanother' in request.POST:
                    redirect_url = request.path
                    params = prepare_cloned_fields(obj)
                    params.update(self.get_extra_addanother_params(request))
                    if params:
                        if 'return_url' in request.GET:
                            params['return_url'] = request.GET.get('return_url')
                        redirect_url += f"?{params.urlencode()}"
                    return redirect(redirect_url)

                return redirect(self.get_return_url(request, obj))

            except (AbortRequest, PermissionsViolation) as e:
                logger.debug(e.message)
                form.add_error(None, e.message)
                clear_events.send(sender=self)

        else:
            logger.debug("Form validation failed")

        bulk_form = BulkWavelengthForm(request.POST) if is_new else None
        return render(
            request,
            self.template_name,
            {
                "model": self.queryset.model,
                "object": obj,
                "form": form,
                "bulk_form": bulk_form,
                "return_url": self.get_return_url(request, obj),
                "prerequisite_model": get_prerequisite_model(self.queryset),
                **self.get_extra_context(request, obj),
            },
        )


class OpticalGridTypeDeleteView(generic.ObjectDeleteView):
    queryset = OpticalGridType.objects.all()


class OpticalGridTypeBulkDeleteView(generic.BulkDeleteView):
    queryset = OpticalGridType.objects.all()
    filterset = OpticalGridTypeFilter
    table = OpticalGridTypeTable


class OpticalGridTypeBulkEditView(generic.BulkEditView):
    queryset = OpticalGridType.objects.all()
    filterset = OpticalGridTypeFilter
    table = OpticalGridTypeTable
    form = OpticalGridTypeForm


class OpticalGridTypeBulkImportView(generic.BulkImportView):
    queryset = OpticalGridType.objects.all()
    model_form = OpticalGridTypeImportForm
    table = OpticalGridTypeTable
    default_return_url = "plugins:netbox_optics:opticalgridtype_list"


# OpticalGrid views
class OpticalGridView(generic.ObjectView):
    queryset = OpticalGrid.objects.all()
    template_name = "netbox_optics/opticalgrid.html"


class OpticalGridListView(generic.ObjectListView):
    queryset = OpticalGrid.objects.all()
    table = OpticalGridTable
    action_buttons = ["add", "import", "export", "delete"]
    filterset = OpticalGridFilter
    filterset_form = OpticalGridFilterForm


class OpticalGridEditView(generic.ObjectEditView):
    queryset = OpticalGrid.objects.all()
    model_form = OpticalGridForm
    form = OpticalGridForm
    template_name = "netbox_optics/opticalgrid_edit.html"


class OpticalGridDeleteView(generic.ObjectDeleteView):
    queryset = OpticalGrid.objects.all()


class OpticalGridBulkDeleteView(generic.BulkDeleteView):
    queryset = OpticalGrid.objects.all()
    filterset = OpticalGridFilter
    table = OpticalGridTable


class OpticalGridBulkEditView(generic.BulkEditView):
    queryset = OpticalGrid.objects.select_related("grid_type")
    filterset = OpticalGridFilter
    table = OpticalGridTable
    form = OpticalGridForm


class OpticalGridBulkImportView(generic.BulkImportView):
    queryset = OpticalGrid.objects.all()
    model_form = OpticalGridImportForm
    table = OpticalGridTable


# OpticalGridWavelength views
class OpticalGridWavelengthView(generic.ObjectView):
    queryset = OpticalGridWavelength.objects.all()
    template_name = "netbox_optics/opticalgridwavelength.html"


class OpticalGridWavelengthListView(generic.ObjectListView):
    queryset = OpticalGridWavelength.objects.select_related("grid")
    table = OpticalGridWavelengthTable
    action_buttons = ["add", "import", "export", "delete"]
    filterset = OpticalGridWavelengthFilter
    filterset_form = OpticalGridWavelengthFilterForm


class OpticalGridWavelengthAddView(generic.ObjectEditView):
    queryset = OpticalGridWavelength.objects.all()
    model_form = OpticalGridWavelengthForm
    form = OpticalGridWavelengthForm
    template_name = "netbox_optics/opticalgridwavelength_edit.html"

    def alter_object(self, obj, request, url_args, url_kwargs):
        # Pre-populate grid from URL param when adding wavelength from grid detail page
        grid_id = request.GET.get("grid_id")
        if grid_id:
            try:
                obj.grid = OpticalGrid.objects.get(pk=int(grid_id))
            except (ValueError, OpticalGrid.DoesNotExist):
                pass
        return obj

    def get_return_url(self, request, obj):
        if obj and hasattr(obj, "grid") and obj.grid:
            return reverse("plugins:netbox_optics:opticalgrid", args=[obj.grid.pk])

        # For new objects, use grid_id from URL params
        grid_id = self.request.GET.get("grid_id")
        if grid_id:
            try:
                return reverse("plugins:netbox_optics:opticalgrid", args=[int(grid_id)])
            except ValueError:
                pass

        return reverse("plugins:netbox_optics:opticalgridwavelength_list")


class OpticalGridWavelengthEditView(generic.ObjectEditView):
    queryset = OpticalGridWavelength.objects.all()
    model_form = OpticalGridWavelengthForm
    form = OpticalGridWavelengthForm
    template_name = "netbox_optics/opticalgridwavelength_edit.html"

    def get_return_url(self, request, obj):
        if obj and hasattr(obj, "grid") and obj.grid:
            return reverse("plugins:netbox_optics:opticalgrid", args=[obj.grid.pk])
        return reverse("plugins:netbox_optics:opticalgrid_list")


class OpticalGridWavelengthDeleteView(generic.ObjectDeleteView):
    queryset = OpticalGridWavelength.objects.all()


class OpticalGridWavelengthBulkDeleteView(generic.BulkDeleteView):
    queryset = OpticalGridWavelength.objects.all()
    filterset = OpticalGridWavelengthFilter
    table = OpticalGridWavelengthTable


class OpticalGridWavelengthBulkEditView(generic.BulkEditView):
    queryset = OpticalGridWavelength.objects.select_related("grid")
    filterset = OpticalGridWavelengthFilter
    table = OpticalGridWavelengthTable
    form = OpticalGridWavelengthForm


class OpticalGridWavelengthBulkImportView(generic.BulkImportView):
    queryset = OpticalGridWavelength.objects.all()
    model_form = OpticalGridWavelengthImportForm
    table = OpticalGridWavelengthTable


# OpticalGridTypeWavelength views
class OpticalGridTypeWavelengthListView(generic.ObjectListView):
    queryset = OpticalGridTypeWavelength.objects.all()
    table = OpticalGridTypeWavelengthTable
    action_buttons = ["add", "import", "export"]
    filterset = OpticalGridTypeWavelengthFilter
    filterset_form = OpticalGridTypeWavelengthFilterForm


class OpticalGridTypeWavelengthView(generic.ObjectView):
    queryset = OpticalGridTypeWavelength.objects.all()
    template_name = "netbox_optics/opticalgridtypewavelength.html"


class OpticalGridTypeWavelengthAddView(generic.ObjectEditView):
    queryset = OpticalGridTypeWavelength.objects.all()
    model_form = OpticalGridTypeWavelengthForm
    form = OpticalGridTypeWavelengthForm
    template_name = "netbox_optics/opticalgridtypewavelength_edit.html"

    def alter_object(self, obj, request, url_args, url_kwargs):
        # Pre-populate grid_type from URL param when adding wavelength from grid type detail page
        grid_type_id = request.GET.get("grid_type_id")
        if grid_type_id:
            try:
                obj.grid_type = OpticalGridType.objects.get(pk=int(grid_type_id))
            except (ValueError, OpticalGridType.DoesNotExist):
                pass
        return obj

    def get_return_url(self, request, obj):
        if obj and hasattr(obj, "grid_type") and obj.grid_type:
            return reverse(
                "plugins:netbox_optics:opticalgridtype", args=[obj.grid_type.pk]
            )

        # For new objects, use grid_type_id from URL params
        grid_type_id = self.request.GET.get("grid_type_id")
        if grid_type_id:
            try:
                return reverse(
                    "plugins:netbox_optics:opticalgridtype", args=[int(grid_type_id)]
                )
            except ValueError:
                pass

        return reverse("plugins:netbox_optics:opticalgridtype_list")


class OpticalGridTypeWavelengthEditView(generic.ObjectEditView):
    queryset = OpticalGridTypeWavelength.objects.all()
    model_form = OpticalGridTypeWavelengthForm
    form = OpticalGridTypeWavelengthForm
    template_name = "netbox_optics/opticalgridtypewavelength_edit.html"

    def get_return_url(self, request, obj):
        if obj and hasattr(obj, "grid_type") and obj.grid_type:
            return reverse(
                "plugins:netbox_optics:opticalgridtype", args=[obj.grid_type.pk]
            )
        return reverse("plugins:netbox_optics:opticalgridtype_list")


# OpticalSpan views
class OpticalSpanView(generic.ObjectView):
    queryset = OpticalSpan.objects.select_related(
        "grid", "site_a", "site_b", "mux_a", "mux_z"
    ).prefetch_related(
        "grid__allowed_wavelengths",
        "connections",
        "connections__wavelength",
        "mux_a__mux_maps__port",
        "mux_a__mux_maps__wavelength",
        "mux_z__mux_maps__port",
        "mux_z__mux_maps__wavelength",
    )
    template_name = "netbox_optics/opticalspan.html"

    def get_extra_context(self, request, instance):
        # prepare extra data for rendering connections and mux maps of span
        connections_by_wavelength = {}
        for connection in instance.connections.all():
            if connection.wavelength:
                connections_by_wavelength[connection.wavelength.id] = connection

        # Get mux port maps for both muxes using prefetched data
        mux_a_maps = {}
        mux_z_maps = {}

        if instance.mux_a:
            for m in instance.mux_a.mux_maps.all():
                mux_a_maps[m.wavelength.id] = m.port

        if instance.mux_z:
            for m in instance.mux_z.mux_maps.all():
                mux_z_maps[m.wavelength.id] = m.port

        return {
            "connections_by_wavelength": connections_by_wavelength,
            "mux_a_maps": mux_a_maps,
            "mux_z_maps": mux_z_maps,
        }


class OpticalSpanListView(generic.ObjectListView):
    queryset = OpticalSpan.objects.all().annotate(
        connections_count=Count("connections")
    )
    table = OpticalSpanTable
    action_buttons = ["add", "import", "export", "delete"]
    filterset = OpticalSpanFilter
    filterset_form = OpticalSpanFilterForm


class OpticalSpanEditView(generic.ObjectEditView):
    queryset = OpticalSpan.objects.all()
    model_form = OpticalSpanForm
    form = OpticalSpanForm


class OpticalSpanDeleteView(generic.ObjectDeleteView):
    queryset = OpticalSpan.objects.all()


class OpticalSpanBulkDeleteView(generic.BulkDeleteView):
    queryset = OpticalSpan.objects.all()
    filterset = OpticalSpanFilter
    table = OpticalSpanTable


class OpticalSpanBulkEditView(generic.BulkEditView):
    queryset = OpticalSpan.objects.select_related("grid", "site_a", "site_b")
    filterset = OpticalSpanFilter
    table = OpticalSpanTable
    form = OpticalSpanForm


class OpticalSpanBulkImportView(generic.BulkImportView):
    queryset = OpticalSpan.objects.all()
    model_form = OpticalSpanImportForm
    table = OpticalSpanTable
    default_return_url = "plugins:netbox_optics:opticalspan_list"


# OpticalConnection views
class OpticalConnectionView(generic.ObjectView):
    queryset = OpticalConnection.objects.select_related(
        "span",
        "wavelength",
        "interface_a",
        "interface_a__device",
        "interface_z",
        "interface_z__device",
        "span__grid",
    )
    template_name = "netbox_optics/opticalconnection.html"


class OpticalConnectionListView(generic.ObjectListView):
    queryset = OpticalConnection.objects.select_related(
        "span",
        "span__mux_a",
        "span__mux_z",
        "span__site_a",
        "span__site_b",
        "wavelength",
        "interface_a",
        "interface_a__device",
        "interface_z",
        "interface_z__device",
    )
    table = OpticalConnectionTable
    action_buttons = ["add", "import", "export", "delete"]
    filterset = OpticalConnectionFilter
    filterset_form = OpticalConnectionFilterForm


class OpticalConnectionEditView(generic.ObjectEditView):
    queryset = OpticalConnection.objects.all()
    model_form = OpticalConnectionForm
    form = OpticalConnectionForm


class OpticalConnectionDeleteView(generic.ObjectDeleteView):
    queryset = OpticalConnection.objects.select_related("span")
    default_return_url = "plugins:netbox_optics:opticalconnection_list"


class OpticalConnectionBulkDeleteView(generic.BulkDeleteView):
    queryset = OpticalConnection.objects.all()
    filterset = OpticalConnectionFilter
    table = OpticalConnectionTable


class OpticalConnectionBulkEditView(generic.BulkEditView):
    queryset = OpticalConnection.objects.select_related(
        "interface_a", "interface_z", "span", "wavelength"
    )
    filterset = OpticalConnectionFilter
    table = OpticalConnectionTable
    form = OpticalConnectionForm


class OpticalConnectionBulkImportView(generic.BulkImportView):
    queryset = OpticalConnection.objects.all()
    model_form = OpticalConnectionImportForm
    table = OpticalConnectionTable
    default_return_url = "plugins:netbox_optics:opticalconnection_list"


# MuxWavelengthMap views
class MuxWavelengthMapView(generic.ObjectView):
    queryset = MuxWavelengthMap.objects.select_related(
        "mux", "port", "wavelength", "wavelength__grid"
    )
    template_name = "netbox_optics/muxwavelengthmap.html"


class MuxWavelengthMapListView(generic.ObjectListView):
    queryset = MuxWavelengthMap.objects.select_related(
        "mux", "port", "wavelength", "wavelength__grid"
    )
    table = MuxWavelengthMapTable
    action_buttons = ["add", "import", "export", "delete"]
    filterset = MuxWavelengthMapFilter
    filterset_form = MuxWavelengthMapFilterForm


class MuxWavelengthMapEditView(generic.ObjectEditView):
    queryset = MuxWavelengthMap.objects.select_related(
        "mux", "port", "wavelength", "wavelength__grid"
    )
    model_form = MuxWavelengthMapForm
    form = MuxWavelengthMapForm

    def alter_object(self, obj, request, url_args, url_kwargs):
        # todo add to ui
        if not obj.pk:
            mux_id = request.GET.get("mux_a") or request.GET.get("mux_z")
            if mux_id:
                try:
                    obj.mux = Device.objects.get(pk=int(mux_id))
                except (ValueError, Device.DoesNotExist):
                    pass
        return obj


class MuxWavelengthMapDeleteView(generic.ObjectDeleteView):
    queryset = MuxWavelengthMap.objects.select_related(
        "mux", "port", "wavelength", "wavelength__grid"
    )


class MuxWavelengthMapBulkDeleteView(generic.BulkDeleteView):
    queryset = MuxWavelengthMap.objects.select_related(
        "mux", "port", "wavelength", "wavelength__grid"
    )
    filterset = MuxWavelengthMapFilter
    table = MuxWavelengthMapTable


class MuxWavelengthMapBulkEditView(generic.BulkEditView):
    queryset = MuxWavelengthMap.objects.select_related(
        "mux", "port", "wavelength", "wavelength__grid"
    )
    filterset = MuxWavelengthMapFilter
    table = MuxWavelengthMapTable
    form = MuxWavelengthMapForm


class MuxWavelengthMapBulkImportView(generic.BulkImportView):
    queryset = MuxWavelengthMap.objects.all()
    model_form = MuxWavelengthMapImportForm
    table = MuxWavelengthMapTable
