from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Profile(models.TextChoices):
        PATIENT = "PATIENT", "Paciente"
        DOCTOR = "DOCTOR", "Medico"
        PROVIDER = "PROVIDER", "Parceiro/Fornecedor"
        ADMIN = "ADMIN", "Admin"

    profile = models.CharField(
        max_length=20,
        choices=Profile.choices,
        default=Profile.PATIENT,
        db_index=True,
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True, db_index=True)

    @property
    def is_patient(self) -> bool:
        return self.profile == self.Profile.PATIENT

    @property
    def is_doctor(self) -> bool:
        return self.profile == self.Profile.DOCTOR

    @property
    def is_provider(self) -> bool:
        return self.profile == self.Profile.PROVIDER

    @property
    def is_admin_profile(self) -> bool:
        return self.profile == self.Profile.ADMIN

    def save(self, *args, **kwargs):
        # Mantem o perfil alinhado para contas de superusuario criadas pelo Django admin.
        if self.is_superuser:
            self.profile = self.Profile.ADMIN
        super().save(*args, **kwargs)


class AuthAuditEvent(models.Model):
    class EventType(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"

    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Sucesso"
        FAILED = "FAILED", "Falha"

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auth_audit_events",
    )
    username_snapshot = models.CharField(max_length=150, blank=True)
    profile_snapshot = models.CharField(max_length=20, blank=True)
    event_type = models.CharField(max_length=20, choices=EventType.choices, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUCCESS)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Evento de Auditoria de Autenticacao"
        verbose_name_plural = "Eventos de Auditoria de Autenticacao"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        username = self.username_snapshot or (self.user.username if self.user else "anonimo")
        return f"{self.event_type} ({self.status}) - {username}"
