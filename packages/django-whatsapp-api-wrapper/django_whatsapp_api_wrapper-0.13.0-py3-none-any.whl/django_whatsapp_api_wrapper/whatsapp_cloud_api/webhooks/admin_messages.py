from django.contrib import admin

from .models import (
    MessageText,
    MessageReaction,
    MessageMedia,
    MessageLocation,
    MessageContacts,
    MessageSystem,
    MessageOrder,
    MessageUnknown,
)


admin.site.register(MessageText)
admin.site.register(MessageReaction)
admin.site.register(MessageMedia)
admin.site.register(MessageLocation)
admin.site.register(MessageContacts)
admin.site.register(MessageSystem)
admin.site.register(MessageOrder)
admin.site.register(MessageUnknown)


