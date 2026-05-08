from django.db import models


class MessagesHistory(models.Model):
    primary_key = models.BigAutoField(primary_key=True, editable=False)
    messages_json = models.TextField()
    conversation_id = models.CharField(max_length=255)

    class Meta:
        db_table = "messages_history"
        ordering = ["-primary_key"]
        verbose_name_plural = "MESSAGES HISTORY"
