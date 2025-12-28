from django.db import models
from django.db.models.fields.related import ForeignKey, OneToOneField
from django.core.exceptions import FieldDoesNotExist


class OptimizationQuerySet(models.QuerySet):
    def _classify_and_apply(self, field_names):
        selects = []
        prefetches = []
        model = self.model

        for field_name in field_names:
            if "__" in field_name:
                prefetches.append(field_name)
                continue

            try:
                field = model._meta.get_field(field_name)
                if isinstance(field, (ForeignKey, OneToOneField)):
                    selects.append(field_name)
                else:
                    prefetches.append(field_name)
            except Exception:
                prefetches.append(field_name)

        qs = self
        if selects:
            qs = qs.select_related(*selects)
        if prefetches:
            qs = qs.prefetch_related(*prefetches)

        return qs

    def with_details(self, relations=None, add_relations=None, exclude_relations=None):
        if relations is not None:
            target_relations = set(relations)
        else:
            target_relations = set(getattr(self.model, '_optimize_relations', []))

        if add_relations:
            target_relations.update(add_relations)

        if exclude_relations:
            target_relations.difference_update(exclude_relations)

        if not target_relations:
            return self

        return self._classify_and_apply(target_relations)

    def live(self):
        try:
            self.model._meta.get_field('deleted_at')
            return self.filter(deleted_at__isnull=True)
        except FieldDoesNotExist:
            return self

class ModelOptimizationMixin(models.Model):
    _optimize_relations = []

    objects = models.Manager().from_queryset(OptimizationQuerySet)()

    class Meta:
        abstract = True
