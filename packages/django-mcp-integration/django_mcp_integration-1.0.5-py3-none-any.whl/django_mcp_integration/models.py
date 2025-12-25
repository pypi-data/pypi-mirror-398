from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import APIKeyManager


class AbstractAPIKey(models.Model):
    objects = APIKeyManager()

    id = models.CharField(max_length=150, unique=True, primary_key=True, editable=False)
    prefix = models.CharField(max_length=8, unique=True, editable=False)
    hashed_key = models.CharField(max_length=150, editable=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    name = models.CharField(
        max_length=50,
        blank=False,
        default=None,
        help_text=(
            _(
                "A free-form name for the API key. "
                "Need not be unique. "
                "50 characters max."
            )
        ),
    )
    revoked = models.BooleanField(
        blank=True,
        default=False,
        help_text=(
            _(
                "If the API key is revoked, clients cannot use it anymore. "
                "(This cannot be undone.)"
            )
        ),
    )
    expiry_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Expires"),
        help_text=_("Once API key expires, clients cannot use it anymore."),
    )

    class Meta:  # noqa
        abstract = True
        ordering = ("-created",)
        verbose_name = "API key"
        verbose_name_plural = "API keys"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # Store the initial value of `revoked` to detect changes.
        self._initial_revoked = self.revoked

    def _has_expired(self) -> bool:
        if self.expiry_date is None:
            return False
        return self.expiry_date < timezone.now()

    _has_expired.short_description = "Has expired"  # type: ignore
    _has_expired.boolean = True  # type: ignore
    has_expired = property(_has_expired)

    def is_valid(self, key: str) -> bool:
        key_generator = type(self).objects.key_generator
        valid = key_generator.verify(key, self.hashed_key)

        # Transparently update the key to use the preferred hasher
        # if it is using an outdated hasher.
        if valid and not key_generator.using_preferred_hasher(self.hashed_key):
            # Note that since the PK includes the hashed key,
            # they will be internally inconsistent following this upgrade.
            # See: https://github.com/florimondmanca/djangorestframework-api-key/issues/128
            self.hashed_key = key_generator.hash(key)
            self.save()

        return valid

    def clean(self) -> None:
        self._validate_revoked()

    def save(self, *args: Any, **kwargs: Any) -> None:
        self._validate_revoked()
        super().save(*args, **kwargs)

    def _validate_revoked(self) -> None:
        if self._initial_revoked and not self.revoked:
            raise ValidationError(
                _("The API key has been revoked, which cannot be undone.")
            )

    def __str__(self) -> str:
        return str(self.name)


class APIKey(AbstractAPIKey):
    pass