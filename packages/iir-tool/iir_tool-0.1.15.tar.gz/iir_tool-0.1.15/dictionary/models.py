from django.db import models


class Entry(models.Model):
    category = models.CharField(max_length=32)
    value = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "value"], name="entry_unique_category_value"
            )
        ]
        ordering = ["-updated_at", "-id"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.category}:{self.value}"
