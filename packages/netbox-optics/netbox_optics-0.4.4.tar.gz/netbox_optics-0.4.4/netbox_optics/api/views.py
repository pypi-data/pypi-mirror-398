from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404


from .serializers import (
    OpticalGridTypeSerializer,
    OpticalGridSerializer,
    OpticalGridWavelengthSerializer,
    OpticalGridTypeWavelengthSerializer,
    OpticalSpanSerializer,
    OpticalConnectionSerializer,
    MuxWavelengthMapSerializer,
    WavelengthSerializer,
)
from ..filters import (
    OpticalGridTypeFilter,
    OpticalGridFilter,
    OpticalGridWavelengthFilter,
    OpticalGridTypeWavelengthFilter,
    OpticalSpanFilter,
    OpticalConnectionFilter,
    MuxWavelengthMapFilter,
)
from ..models import (
    OpticalGridType,
    OpticalGrid,
    OpticalGridWavelength,
    OpticalGridTypeWavelength,
    OpticalSpan,
    OpticalConnection,
    MuxWavelengthMap,
)
from ..choices import WavelengthStatus

from netbox.api.viewsets import NetBoxModelViewSet


class OpticalGridTypeViewSet(NetBoxModelViewSet):
    queryset = OpticalGridType.objects.prefetch_related("tags").all()
    serializer_class = OpticalGridTypeSerializer
    filterset_class = OpticalGridTypeFilter


class OpticalGridTypeWavelengthViewSet(NetBoxModelViewSet):
    queryset = (
        OpticalGridTypeWavelength.objects.select_related("grid_type")
        .prefetch_related("tags")
        .all()
    )
    serializer_class = OpticalGridTypeWavelengthSerializer
    filterset_class = OpticalGridTypeWavelengthFilter


class OpticalGridViewSet(NetBoxModelViewSet):
    queryset = (
        OpticalGrid.objects.select_related("grid_type")
        .prefetch_related("tags", "allowed_wavelengths__connections")
        .all()
    )
    serializer_class = OpticalGridSerializer
    filterset_class = OpticalGridFilter


class OpticalGridWavelengthViewSet(NetBoxModelViewSet):
    queryset = OpticalGridWavelength.objects.select_related("grid")
    serializer_class = OpticalGridWavelengthSerializer
    filterset_class = OpticalGridWavelengthFilter


class OpticalSpanViewSet(NetBoxModelViewSet):
    queryset = (
        OpticalSpan.objects.select_related("grid", "site_a", "site_b")
        .prefetch_related("tags", "connections__wavelength")
        .all()
    )
    serializer_class = OpticalSpanSerializer
    filterset_class = OpticalSpanFilter

    @action(detail=True, methods=["get"])
    def wavelengths(self, request, pk=None):
        """Retrieve all wavelengths for an OpticalSpan with their status (free/reserved)"""
        span = get_object_or_404(OpticalSpan, pk=pk)

        status_filter = request.GET.get("status")

        if status_filter:
            if status_filter not in (WavelengthStatus.FREE, WavelengthStatus.RESERVED):
                return Response(
                    {
                        "error": (
                            f"Invalid status filter. Must be one of {(WavelengthStatus.FREE, WavelengthStatus.RESERVED)}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        wavelengths = span.get_wavelength_statuses(status_filter)

        serializer = WavelengthSerializer(wavelengths, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OpticalConnectionViewSet(NetBoxModelViewSet):
    queryset = (
        OpticalConnection.objects.select_related(
            "interface_a", "interface_z", "span", "wavelength"
        )
        .prefetch_related("tags")
        .all()
    )
    serializer_class = OpticalConnectionSerializer
    filterset_class = OpticalConnectionFilter


class MuxWavelengthMapViewSet(NetBoxModelViewSet):
    queryset = (
        MuxWavelengthMap.objects.select_related("mux", "port", "wavelength")
        .prefetch_related("tags")
        .all()
    )
    serializer_class = MuxWavelengthMapSerializer
    filterset_class = MuxWavelengthMapFilter
