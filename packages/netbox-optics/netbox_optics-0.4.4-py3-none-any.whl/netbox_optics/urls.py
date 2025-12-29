from django.urls import path

from netbox.views.generic import ObjectChangeLogView

from . import views
from . import models

urlpatterns = [
    # OpticalGridType URLs
    path(
        "opticalgridtype/",
        views.OpticalGridTypeListView.as_view(),
        name="opticalgridtype_list",
    ),
    path(
        "opticalgridtype/<int:pk>/",
        views.OpticalGridTypeView.as_view(),
        name="opticalgridtype",
    ),
    path(
        "opticalgridtype/add/",
        views.OpticalGridTypeEditView.as_view(),
        name="opticalgridtype_add",
    ),
    path(
        "opticalgridtype/<int:pk>/edit/",
        views.OpticalGridTypeEditView.as_view(),
        name="opticalgridtype_edit",
    ),
    path(
        "opticalgridtype/<int:pk>/delete/",
        views.OpticalGridTypeDeleteView.as_view(),
        name="opticalgridtype_delete",
    ),
    path(
        "opticalgridtype/delete/",
        views.OpticalGridTypeBulkDeleteView.as_view(),
        name="opticalgridtype_bulk_delete",
    ),
    path(
        "opticalgridtype/import/",
        views.OpticalGridTypeBulkImportView.as_view(),
        name="opticalgridtype_import",
    ),
    # OpticalGrid URLs
    path(
        "opticalgrid/",
        views.OpticalGridListView.as_view(),
        name="opticalgrid_list",
    ),
    path(
        "opticalgrid/<int:pk>/",
        views.OpticalGridView.as_view(),
        name="opticalgrid",
    ),
    path(
        "opticalgrid/add/",
        views.OpticalGridEditView.as_view(),
        name="opticalgrid_add",
    ),
    path(
        "opticalgrid/<int:pk>/edit/",
        views.OpticalGridEditView.as_view(),
        name="opticalgrid_edit",
    ),
    path(
        "opticalgrid/<int:pk>/delete/",
        views.OpticalGridDeleteView.as_view(),
        name="opticalgrid_delete",
    ),
    path(
        "opticalgrid/delete/",
        views.OpticalGridBulkDeleteView.as_view(),
        name="opticalgrid_bulk_delete",
    ),
    path(
        "opticalgrid/import/",
        views.OpticalGridBulkImportView.as_view(),
        name="opticalgrid_import",
    ),
    # OpticalGridWavelength URLs
    path(
        "opticalgridwavelength/",
        views.OpticalGridWavelengthListView.as_view(),
        name="opticalgridwavelength_list",
    ),
    path(
        "opticalgridwavelength/<int:pk>/",
        views.OpticalGridWavelengthView.as_view(),
        name="opticalgridwavelength",
    ),
    path(
        "opticalgridwavelength/add/",
        views.OpticalGridWavelengthAddView.as_view(),
        name="opticalgridwavelength_add",
    ),
    path(
        "opticalgridwavelength/<int:pk>/edit/",
        views.OpticalGridWavelengthEditView.as_view(),
        name="opticalgridwavelength_edit",
    ),
    path(
        "opticalgridwavelength/<int:pk>/delete/",
        views.OpticalGridWavelengthDeleteView.as_view(),
        name="opticalgridwavelength_delete",
    ),
    path(
        "opticalgridwavelength/delete/",
        views.OpticalGridWavelengthBulkDeleteView.as_view(),
        name="opticalgridwavelength_bulk_delete",
    ),
    path(
        "opticalgridwavelength/import/",
        views.OpticalGridWavelengthBulkImportView.as_view(),
        name="opticalgridwavelength_import",
    ),
    # OpticalGridTypeWavelength URLs
    path(
        "opticalgridtypewavelength/",
        views.OpticalGridTypeWavelengthListView.as_view(),
        name="opticalgridtypewavelength_list",
    ),
    path(
        "opticalgridtypewavelength/<int:pk>/",
        views.OpticalGridTypeWavelengthView.as_view(),
        name="opticalgridtypewavelength",
    ),
    path(
        "opticalgridtypewavelength/add/",
        views.OpticalGridTypeWavelengthAddView.as_view(),
        name="opticalgridtypewavelength_add",
    ),
    path(
        "opticalgridtypewavelength/<int:pk>/edit/",
        views.OpticalGridTypeWavelengthEditView.as_view(),
        name="opticalgridtypewavelength_edit",
    ),
    # OpticalSpan URLs
    path("opticalspan/", views.OpticalSpanListView.as_view(), name="opticalspan_list"),
    path("opticalspan/<int:pk>/", views.OpticalSpanView.as_view(), name="opticalspan"),
    path(
        "opticalspan/add/", views.OpticalSpanEditView.as_view(), name="opticalspan_add"
    ),
    path(
        "opticalspan/<int:pk>/edit/",
        views.OpticalSpanEditView.as_view(),
        name="opticalspan_edit",
    ),
    path(
        "opticalspan/<int:pk>/delete/",
        views.OpticalSpanDeleteView.as_view(),
        name="opticalspan_delete",
    ),
    path(
        "opticalspan/delete/",
        views.OpticalSpanBulkDeleteView.as_view(),
        name="opticalspan_bulk_delete",
    ),
    path(
        "opticalspan/import/",
        views.OpticalSpanBulkImportView.as_view(),
        name="opticalspan_import",
    ),
    # OpticalConnection URLs
    path(
        "opticalconnection/",
        views.OpticalConnectionListView.as_view(),
        name="opticalconnection_list",
    ),
    path(
        "opticalconnection/<int:pk>/",
        views.OpticalConnectionView.as_view(),
        name="opticalconnection",
    ),
    path(
        "opticalconnection/add/",
        views.OpticalConnectionEditView.as_view(),
        name="opticalconnection_add",
    ),
    path(
        "opticalconnection/<int:pk>/edit/",
        views.OpticalConnectionEditView.as_view(),
        name="opticalconnection_edit",
    ),
    path(
        "opticalconnection/<int:pk>/delete/",
        views.OpticalConnectionDeleteView.as_view(),
        name="opticalconnection_delete",
    ),
    path(
        "opticalconnection/delete/",
        views.OpticalConnectionBulkDeleteView.as_view(),
        name="opticalconnection_bulk_delete",
    ),
    path(
        "opticalconnection/import/",
        views.OpticalConnectionBulkImportView.as_view(),
        name="opticalconnection_import",
    ),
    # MuxWavelengthMap URLs
    path(
        "muxwavelengthmap/",
        views.MuxWavelengthMapListView.as_view(),
        name="muxwavelengthmap_list",
    ),
    path(
        "muxwavelengthmap/<int:pk>/",
        views.MuxWavelengthMapView.as_view(),
        name="muxwavelengthmap",
    ),
    path(
        "muxwavelengthmap/add/",
        views.MuxWavelengthMapEditView.as_view(),
        name="muxwavelengthmap_add",
    ),
    path(
        "muxwavelengthmap/<int:pk>/edit/",
        views.MuxWavelengthMapEditView.as_view(),
        name="muxwavelengthmap_edit",
    ),
    path(
        "muxwavelengthmap/<int:pk>/delete/",
        views.MuxWavelengthMapDeleteView.as_view(),
        name="muxwavelengthmap_delete",
    ),
    path(
        "muxwavelengthmap/delete/",
        views.MuxWavelengthMapBulkDeleteView.as_view(),
        name="muxwavelengthmap_bulk_delete",
    ),
    path(
        "muxwavelengthmap/import/",
        views.MuxWavelengthMapBulkImportView.as_view(),
        name="muxwavelengthmap_import",
    ),
    path(
        "muxwavelengthmap/export/",
        views.MuxWavelengthMapListView.as_view(),
        name="muxwavelengthmap_export",
    ),
]

changelog_urls = [
    path(
        "opticalgridtype/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="opticalgridtype_changelog",
        kwargs={"model": models.OpticalGridType},
    ),
    path(
        "opticalgrid/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="opticalgrid_changelog",
        kwargs={"model": models.OpticalGrid},
    ),
    path(
        "opticalgridwavelength/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="opticalgridwavelength_changelog",
        kwargs={"model": models.OpticalGridWavelength},
    ),
    path(
        "opticalspan/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="opticalspan_changelog",
        kwargs={"model": models.OpticalSpan},
    ),
    path(
        "opticalconnection/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="opticalconnection_changelog",
        kwargs={"model": models.OpticalConnection},
    ),
    path(
        "muxwavelengthmap/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="muxwavelengthmap_changelog",
        kwargs={"model": models.MuxWavelengthMap},
    ),

]

urlpatterns.extend(changelog_urls)
