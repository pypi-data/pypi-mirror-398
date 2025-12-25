from netbox.api.routers import NetBoxRouter

router = NetBoxRouter()
app_name = 'netpicker'
urlpatterns = router.urls
