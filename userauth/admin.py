from django.contrib import admin
from .models import CustomUser


# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ('email','phone_number', 'is_staff','date_joined','is_active')
    actions = ['block', 'unblock']
    
    def unblock(self, request, queryset):
        queryset.update(is_active=True)
    unblock.short_description = "Mark selected users as UNBLOCKED"
    def block(self, request, queryset):
        queryset.update(is_active=False)
    block.short_description = "Mark selected users as BLOCKED"

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2',),  # Make sure 'username' isn't here
        }),
    )


admin.site.register(CustomUser, UserAdmin)



