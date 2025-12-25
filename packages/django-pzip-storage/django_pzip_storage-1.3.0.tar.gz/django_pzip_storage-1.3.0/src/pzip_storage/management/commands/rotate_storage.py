import os

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models, transaction

from pzip_storage import PZipStorage


def rotate_model(model, fields, storage_changes, save=True, verbosity=0):
    for instance in model.objects.all():
        changed = []
        for field in fields:
            old = getattr(instance, field.name)
            if not old:
                continue
            path_changes = storage_changes.setdefault(field.storage, {})
            if old.name in path_changes:
                raise ValueError(f"Duplicate path in {instance!r}: {old.name}")
            try:
                new_name = field.generate_filename(instance, os.path.basename(old.name))
                new_path = field.storage.save(new_name, old)
                setattr(instance, field.attname, new_path)
                changed.append(field.attname)
                path_changes[old.name] = new_path
                if not save and verbosity > 1:
                    print(old.name, "->", new_path)
            except OSError as e:
                if verbosity > 0:
                    print("error rotating", old, "-", str(e))
        if changed and save:
            instance.save(update_fields=changed)


class Command(BaseCommand):
    help = "Rotates FileFields stored in PZipStorage"

    def add_arguments(self, parser):
        parser.add_argument("-n", "--dry-run", action="store_true", default=False)
        parser.add_argument("--delete", action="store_true", default=False)
        parser.add_argument("models", nargs="*")

    def handle(self, *args, **options):
        verbosity = options["verbosity"]
        save = not options["dry_run"]
        rotate_models = [apps.get_model(m) for m in options["models"]]
        if not rotate_models:
            rotate_models = apps.get_models()
        # Track {storage: {old_path: new_path}}
        storage_changes = {}
        with transaction.atomic():
            for model in rotate_models:
                file_fields = [
                    f
                    for f in model._meta.fields
                    if isinstance(f, models.FileField)
                    and isinstance(f.storage, PZipStorage)
                ]
                if file_fields:
                    rotate_model(
                        model,
                        file_fields,
                        storage_changes,
                        save=save,
                        verbosity=verbosity,
                    )
        if options["delete"]:
            for storage, path_changes in storage_changes.items():
                if save:
                    # Real run, delete the old files.
                    delete_paths = set(path_changes.keys())
                else:
                    # For a dry run, delete the newly-created files.
                    delete_paths = set(path_changes.values())
                for path in delete_paths:
                    try:
                        storage.delete(path)
                        if verbosity > 1:
                            print(f"removed {path}")
                    except Exception as e:
                        if verbosity > 0:
                            print("error removing", path, "-", str(e))
