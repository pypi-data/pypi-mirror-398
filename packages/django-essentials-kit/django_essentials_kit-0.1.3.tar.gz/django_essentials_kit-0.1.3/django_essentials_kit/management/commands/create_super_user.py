from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as BaseUser
from django.core.management.base import BaseCommand, CommandError
from django.utils.crypto import get_random_string

User: BaseUser = get_user_model()


class Command(BaseCommand):
    help = "Create super user"

    def add_arguments(self, parser):
        parser.add_argument("-u", "--username", default="admin", type=str, help="New user username")
        parser.add_argument("-e", "--email", default="admin@example.com", type=str, help="New user email")
        parser.add_argument("-p", "--password", default="admin", type=str, help="New user password")
        parser.add_argument("-r", "--random-password", action="store_true", help="Use random password")

    def handle(self, *args, **options):
        try:
            user, created = User.objects.get_or_create(
                username=options["username"], email=options["email"], defaults={"is_superuser": True, "is_staff": True}
            )

            if created:
                self.stdout.write("Username is been created", self.style.SUCCESS)
            else:
                self.stdout.write("Username is already exists", self.style.WARNING)

            if options["random_password"]:
                password = get_random_string(length=16)
                self.stdout.write(f"Random password is '{password}'", self.style.SUCCESS)
            else:
                if options["password"]:
                    password = options["password"]
                else:
                    return self.stdout.write("Need password", self.style.WARNING)

            user.set_password(password)
            user.save()

        except Exception as e:
            raise CommandError(str(e))
