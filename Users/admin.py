from django.contrib import admin
from django.urls import path, include
from .models import User,State,Address_table

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    def delete_model(self, request, obj):
        # Clear related M2M relationships to avoid IntegrityError
        obj.groups.clear()
        obj.user_permissions.clear()
        obj.delete()


admin.site.register(State)
admin.site.register(Address_table)


