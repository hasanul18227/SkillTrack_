from django.contrib import admin
from django.urls import include, path

# Each app owns its own URL file. Names are global (no namespaces),
# so templates can use {% url 'name' %} from any app.
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),     # Part 1
    path("", include("modules.urls")),      # Part 2
    path("", include("enrollment.urls")),   # Part 3
]
