from django.urls import path  # type: ignore[import]
from . import views

urlpatterns = [
    path(
        "ticket-types/",
        views.TicketTypeListCreateView.as_view(),
        name="ticket-type-list-create",
    ),
    path(
        "ticket-types/<uuid:pk>/",
        views.TicketTypeDetailView.as_view(),
        name="ticket-type-detail",
    ),
    path(
        "events/<uuid:event_pk>/ticket-types/",
        views.event_ticket_types,
        name="event-ticket-types",
    ),
    path(
        "ticket-types/<uuid:ticket_type_pk>/generate/",
        views.generate_tickets,
        name="generate-tickets",
    ),
    # allow accessing ticket types by the same /tickets/<id>/ path used in tests
    path("<uuid:pk>/", views.TicketTypeDetailView.as_view(), name="ticket-detail"),
    path("", views.TicketListView.as_view(), name="ticket-list"),
    path("validate/<str:ticket_code>/", views.validate_ticket, name="validate-ticket"),
    path("use/<str:ticket_code>/", views.use_ticket, name="use-ticket"),
]
