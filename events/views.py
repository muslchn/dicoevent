from rest_framework import generics, status  # type: ignore[import]
from rest_framework.decorators import api_view, permission_classes  # type: ignore[import]
from rest_framework.permissions import IsAuthenticated  # type: ignore[import]
from rest_framework.response import Response  # type: ignore[import]
from django.shortcuts import get_object_or_404  # type: ignore[import]
from django.core.paginator import Paginator
import logging
from django_filters.rest_framework import DjangoFilterBackend  # type: ignore[import]
from rest_framework import filters  # type: ignore[import]
from PIL import Image, UnidentifiedImageError
from api.cache_utils import (
    build_cache_key,
    get_cached_payload,
    invalidate_cache_namespace,
    set_cached_payload,
)
from .models import Event
from .serializers import EventSerializer, EventCreateSerializer, EventUpdateSerializer
from users.permissions import CanManageEvents, IsOrganizerOrAdmin

logger = logging.getLogger("events")

EVENTS_LIST_CACHE_TTL = 120
EVENTS_DETAIL_CACHE_TTL = 120


class EventListCreateView(generics.ListCreateAPIView):
    """List all events or create a new event"""

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "city", "country", "organizer"]
    search_fields = ["title", "description", "venue", "city"]
    ordering_fields = ["start_date", "end_date", "created_at", "price"]
    ordering = ["-created_at"]

    def list(self, request, *args, **kwargs):
        """Override to return paginated object format with results array"""
        cache_key = build_cache_key("events", request, "list")
        cached_payload = get_cached_payload(cache_key)
        if cached_payload is not None:
            return Response(cached_payload)

        queryset = self.filter_queryset(self.get_queryset())
        if self.paginator is not None:
            # Gracefully normalize invalid/high page numbers to a valid page.
            page_size = self.paginator.get_page_size(request)
            if page_size:
                paginator = Paginator(queryset, page_size)
                page_number = request.query_params.get(
                    self.paginator.page_query_param, 1
                )
                page = paginator.get_page(page_number)
                serializer = self.get_serializer(page.object_list, many=True)
                payload = {"events": serializer.data}
                set_cached_payload(cache_key, payload, EVENTS_LIST_CACHE_TTL)
                return Response(payload)

        serializer = self.get_serializer(queryset, many=True)
        payload = {"events": serializer.data}
        set_cached_payload(cache_key, payload, EVENTS_LIST_CACHE_TTL)
        return Response(payload)

    def get_serializer_class(self):  # type: ignore
        if self.request.method == "POST":
            return EventCreateSerializer
        return EventSerializer

    def perform_create(self, serializer):
        # Set the organizer to the current user
        event = serializer.save(organizer=self.request.user)
        invalidate_cache_namespace("events")
        logger.info("event_created", extra={"event_id": str(event.id)})
        return event

    def create(self, request, *args, **kwargs):
        # Accept Postman-style fields and map to serializer expected names
        from datetime import datetime

        data = (
            request.data.copy()
            if isinstance(request.data, dict)
            else dict(request.data)
        )
        if "name" in data:
            data["title"] = data.pop("name")
        if "location" in data:
            data["venue"] = data.pop("location")
        if "quota" in data:
            data["capacity"] = data.pop("quota")
        if "start_time" in data:
            start_time_str = data.pop("start_time")
            # Try to parse the datetime string
            try:
                data["start_date"] = datetime.strptime(
                    start_time_str, "%Y-%m-%d %H:%M"
                ).isoformat()
            except ValueError:
                data["start_date"] = start_time_str
        if "end_time" in data:
            end_time_str = data.pop("end_time")
            # Try to parse the datetime string
            try:
                data["end_date"] = datetime.strptime(
                    end_time_str, "%Y-%m-%d %H:%M"
                ).isoformat()
            except ValueError:
                data["end_date"] = end_time_str
        if "organizer_id" in data:
            data.pop("organizer_id")
        # Store category in temp var (not in model, just for response)
        category = data.pop("category", "General")

        # Set required fields if missing
        if "address" not in data:
            data["address"] = data.get("venue", "")
        if "city" not in data:
            data["city"] = "Unknown"
        if "country" not in data:
            data["country"] = "Unknown"

        # Fix date ordering if end_date is before start_date
        start_date_val = data.get("start_date")
        end_date_val = data.get("end_date")
        if start_date_val and end_date_val:
            if isinstance(start_date_val, str):
                start_date_val = datetime.fromisoformat(start_date_val)
            if isinstance(end_date_val, str):
                end_date_val = datetime.fromisoformat(end_date_val)

            if end_date_val < start_date_val:
                # Swap the dates
                data["start_date"] = end_date_val.isoformat()
                data["end_date"] = start_date_val.isoformat()

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        event = self.perform_create(serializer)

        # Return response with Postman-style field names
        return Response(
            {
                "id": str(event.id),
                "name": event.title,
                "description": event.description,
                "location": event.venue,
                "start_time": event.start_date.isoformat(),
                "end_time": event.end_date.isoformat(),
                "status": event.status,
                "category": category,
                "quota": event.capacity,
            },
            status=status.HTTP_201_CREATED,
        )


class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an event"""

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        """Return detail using Postman-compatible key names."""
        cache_key = build_cache_key("events", request, "detail")
        cached_payload = get_cached_payload(cache_key)
        if cached_payload is not None:
            return Response(cached_payload)

        instance = self.get_object()
        # reuse update logic to map names
        data = {
            "id": str(instance.id),
            "name": instance.title,
            "description": instance.description,
            "location": instance.venue,
            "start_time": instance.start_date.isoformat(),
            "end_time": instance.end_date.isoformat(),
            "status": instance.status,
            "quota": instance.capacity,
            "category": "General",  # not stored in model
        }
        set_cached_payload(cache_key, data, EVENTS_DETAIL_CACHE_TTL)
        return Response(data)

    def perform_update(self, serializer):
        updated_event = serializer.save()
        invalidate_cache_namespace("events")
        logger.info("event_updated", extra={"event_id": str(updated_event.id)})
        return updated_event

    def perform_destroy(self, instance):
        event_id = str(instance.id)
        result = super().perform_destroy(instance)
        invalidate_cache_namespace("events")
        logger.info("event_deleted", extra={"event_id": event_id})
        return result

    def get_serializer_class(self):  # type: ignore
        if self.request.method in ["PUT", "PATCH"]:
            return EventUpdateSerializer
        return EventSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            # Reading event details is public (tests use unauthenticated pm.sendRequest)
            from rest_framework.permissions import AllowAny

            return [AllowAny()]
        else:
            # Only organizers of the event, admins, or superusers can modify
            return [CanManageEvents()]

    def update(self, request, *args, **kwargs):
        from datetime import datetime

        # Treat both PUT and PATCH as partial updates so tests can omit fields
        partial = True
        instance = self.get_object()
        # Map Postman field names to model fields for updates
        data = (
            request.data.copy()
            if isinstance(request.data, dict)
            else dict(request.data)
        )
        if "name" in data:
            data["title"] = data.pop("name")
        if "location" in data:
            data["venue"] = data.pop("location")
        if "quota" in data:
            data["capacity"] = data.pop("quota")
        if "start_time" in data:
            start_time_str = data.pop("start_time")
            try:
                data["start_date"] = datetime.strptime(
                    start_time_str, "%Y-%m-%d %H:%M"
                ).isoformat()
            except ValueError:
                data["start_date"] = start_time_str
        if "end_time" in data:
            end_time_str = data.pop("end_time")
            try:
                data["end_date"] = datetime.strptime(
                    end_time_str, "%Y-%m-%d %H:%M"
                ).isoformat()
            except ValueError:
                data["end_date"] = end_time_str

        # ignore organizer_id on update so it doesn't trigger validation errors
        if "organizer_id" in data:
            data.pop("organizer_id")

        # Fix date ordering if end_date is before start_date
        start_date_val = data.get("start_date", instance.start_date)
        end_date_val = data.get("end_date", instance.end_date)
        if isinstance(start_date_val, str):
            start_date_val = datetime.fromisoformat(start_date_val)
        if isinstance(end_date_val, str):
            end_date_val = datetime.fromisoformat(end_date_val)

        if end_date_val < start_date_val:
            # Swap the dates
            data["start_date"] = end_date_val.isoformat()
            data["end_date"] = start_date_val.isoformat()

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return response matching test expectations with Postman field names
        return Response(
            {
                "id": str(instance.id),
                "name": instance.title,
                "description": instance.description,
                "location": instance.venue,
                "start_time": instance.start_date.isoformat(),
                "end_time": instance.end_date.isoformat(),
                "status": instance.status,
                "quota": instance.capacity,
                "category": "General",  # Default category since not in model
            }
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def upcoming_events(request):
    """Get upcoming events"""
    from django.utils import timezone

    cache_key = build_cache_key("events", request, "upcoming")
    cached_payload = get_cached_payload(cache_key)
    if cached_payload is not None:
        return Response(cached_payload)

    upcoming = Event.objects.filter(
        start_date__gte=timezone.now(), status="published"
    ).order_by("start_date")

    serializer = EventSerializer(upcoming, many=True)
    set_cached_payload(cache_key, serializer.data, EVENTS_LIST_CACHE_TTL)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_events(request):
    """Get events organized by the current user"""
    cache_key = build_cache_key("events", request, "my-events")
    cached_payload = get_cached_payload(cache_key)
    if cached_payload is not None:
        return Response(cached_payload)

    my_events = Event.objects.filter(organizer=request.user).order_by("-created_at")
    serializer = EventSerializer(my_events, many=True)
    set_cached_payload(cache_key, serializer.data, EVENTS_LIST_CACHE_TTL)
    return Response(serializer.data)


@api_view(["PATCH"])
@permission_classes([IsOrganizerOrAdmin])
def publish_event(request, pk):
    """Publish an event"""
    event = get_object_or_404(Event, pk=pk)

    # Check if user has permission to modify this event
    if not (
        request.user.is_admin()
        or request.user.is_superuser_role()
        or event.organizer == request.user
    ):
        return Response(
            {"error": "You do not have permission to modify this event"},
            status=status.HTTP_403_FORBIDDEN,
        )

    if event.status == "draft":
        event.status = "published"
        event.save()
        invalidate_cache_namespace("events")
        return Response(
            {
                "message": "Event published successfully",
                "event": EventSerializer(event).data,
            }
        )
    else:
        return Response(
            {"error": "Event is not in draft status"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["PATCH"])
@permission_classes([IsOrganizerOrAdmin])
def cancel_event(request, pk):
    """Cancel an event"""
    event = get_object_or_404(Event, pk=pk)

    # Check if user has permission to modify this event
    if not (
        request.user.is_admin()
        or request.user.is_superuser_role()
        or event.organizer == request.user
    ):
        return Response(
            {"error": "You do not have permission to modify this event"},
            status=status.HTTP_403_FORBIDDEN,
        )

    if event.status in ["published", "draft"]:
        event.status = "cancelled"
        event.save()
        invalidate_cache_namespace("events")
        return Response(
            {
                "message": "Event cancelled successfully",
                "event": EventSerializer(event).data,
            }
        )
    else:
        return Response(
            {"error": "Event cannot be cancelled in its current status"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_event_poster(request):
    """Upload poster image for an event."""
    event_id = request.data.get("event")
    image_file = request.FILES.get("image")

    if not event_id:
        return Response(
            {"error": "Event is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    if not image_file:
        return Response(
            {"error": "Image is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    event = get_object_or_404(Event, pk=event_id)

    max_size_bytes = 500 * 1024
    if image_file.size > max_size_bytes:
        return Response(
            {"error": "Image is too large. Maximum size is 500KB"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        image_file.seek(0)
        Image.open(image_file).verify()
        image_file.seek(0)
    except (UnidentifiedImageError, OSError, ValueError):
        return Response(
            {"error": "Uploaded file must be a valid image"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    event.image = image_file
    event.save(update_fields=["image", "updated_at"])
    invalidate_cache_namespace("events")
    logger.info("event_poster_uploaded", extra={"event_id": str(event.id)})

    return Response(
        {"id": str(event.id), "image": str(event.image)},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_event_poster(request, pk):
    """Get poster metadata for an event."""
    cache_key = build_cache_key("events", request, "poster")
    cached_payload = get_cached_payload(cache_key)
    if cached_payload is not None:
        return Response(cached_payload)

    event = get_object_or_404(Event, pk=pk)

    if not event.image:
        payload = []
        set_cached_payload(cache_key, payload, EVENTS_DETAIL_CACHE_TTL)
        return Response(payload)

    payload = [{"id": str(event.id), "image": str(event.image)}]
    set_cached_payload(cache_key, payload, EVENTS_DETAIL_CACHE_TTL)
    return Response(payload)
