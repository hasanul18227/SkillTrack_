"""Part 3 - Daily deadline check: due-soon and overdue notifications (FR-09)."""
from django.core.management.base import BaseCommand

from enrollment import services


class Command(BaseCommand):
    help = "Create due-soon and overdue notifications and send reminder emails (run daily)."

    def handle(self, *args, **options):
        counts = services.check_deadlines()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. New notifications: {counts['due_soon']} due soon, {counts['overdue']} overdue."
            )
        )
