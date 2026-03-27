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
