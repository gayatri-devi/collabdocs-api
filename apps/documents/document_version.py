import uuid
from django.conf import settings
from django.db import models

class DocumentVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='document_versions')
    created_at = models.DateTimeField(auto_now_add=True)
