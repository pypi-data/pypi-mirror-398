from django.urls import include, path
from utilities.urls import get_model_urls
from . import views  # noqa


urlpatterns = (
    path('automation/jobs/', include(get_model_urls('netpicker', 'job', detail=False))),
    path('automation/jobs/<str:pk>/', include(get_model_urls('netpicker', 'job'))),

    path('automation/logs/', include(get_model_urls('netpicker', 'log', detail=False))),
    path('automation/logs/<int:pk>/', include(get_model_urls('netpicker', 'log'))),

    path('automation/backups/<str:pk>/', include(get_model_urls('netpicker', 'backup'))),
    path('automation/backup-search/', include(get_model_urls('netpicker', 'backupsearchhit', detail=False))),
    path('map-devices/', include(get_model_urls('netpicker', 'mappeddevice', detail=False))),

    path("settings/", include(get_model_urls('netpicker', 'netpickersetting', detail=False))),
    path("settings/<int:pk>/", include(get_model_urls('netpicker', 'netpickersetting'))),
)
