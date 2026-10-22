
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = "Create or promote an admin account"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = os.environ.get("ADMIN_USERNAME")
        password = os.environ.get("ADMIN_PASSWORD")

        if not username or not password:
            self.stdout.write(self.style.ERROR(
                "ADMIN_USERNAME and ADMIN_PASSWORD must be configured."
            ))
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": ""},
        )
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        self.stdout.write(self.style.SUCCESS(
            f"Admin account {'created' if created else 'updated'} successfully."
        ))
