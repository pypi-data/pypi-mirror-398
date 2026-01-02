from django.contrib import admin

from django_keycloak_oidc.models import KeyCloakPermissionMapping
from django_keycloak_oidc.forms import KeyCloakPermissionMappingForm


@admin.register(KeyCloakPermissionMapping)
class KeyCloakPermissionMappingAdmin(admin.ModelAdmin):
    list_display = ('id', 'keycloak_role_name', 'keycloak_group_name', 'django_groups')
    search_fields = ('keycloak_role_name', 'keycloak_group_name', 'groups__name')
    list_filter = ('groups',)

    form = KeyCloakPermissionMappingForm

    def django_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])
