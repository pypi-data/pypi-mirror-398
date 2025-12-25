from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.core.management.base import BaseCommand

from umap.models import Map

vector = SearchVector("name", config=settings.UMAP_SEARCH_CONFIGURATION)


def confirm(prompt):
    return input(f"{prompt} [Y/n]").upper() in ["", "Y"]


class Command(BaseCommand):
    help = "Search maps and delete, block or restore them."

    def add_arguments(self, parser):
        parser.add_argument("search", help="Actual search.")
        parser.add_argument(
            "--dry-run",
            help="Do not replace for real, just display actions",
            action="store_true",
        )
        parser.add_argument(
            "--delete",
            help="Mark maps as deleted",
            action="store_true",
        )
        parser.add_argument(
            "--restore",
            help="Restore delete maps in the search results",
            action="store_true",
        )
        parser.add_argument(
            "--block",
            help="Block maps in the search results",
            action="store_true",
        )
        parser.add_argument(
            "--public",
            help="Search only public maps",
            action="store_true",
        )

    def handle(self, *args, **options):
        query = SearchQuery(
            options["search"],
            config=settings.UMAP_SEARCH_CONFIGURATION,
            search_type="websearch",
        )
        qs = Map.public.all() if options["public"] else Map.objects.all()
        qs = qs.annotate(search=vector).filter(search=query)
        for mm in qs:
            row = [
                mm.pk,
                mm.name[:50],
                str(mm.owner or "")[:10],
                mm.get_share_status_display(),
                settings.SITE_URL + mm.get_absolute_url(),
            ]
            print("{:1} | {:<50} | {:<10} | {:<20} | {}".format(*row))
        if options["delete"] and confirm(f"Delete {qs.count()} maps?"):
            for mm in qs:
                mm.move_to_rash()
            print("Done!")
        elif options["restore"]:
            to_restore = [mm for mm in qs if mm.share_status == Map.DELETED]
            if confirm(f"Restore {len(to_restore)} maps?"):
                for mm in to_restore:
                    mm.share_status = Map.DRAFT
                    mm.save()
                print("Done!")
        elif options["block"] and confirm(f"Block {qs.count()} maps?"):
            for mm in qs:
                mm.share_status = Map.BLOCKED
                mm.save()
            print("Done!")
