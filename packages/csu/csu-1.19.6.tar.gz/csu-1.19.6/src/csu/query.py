from django.db.models import Count
from django.db.models import Func
from django.db.models import IntegerField
from django.db.models import QuerySet
from django.db.models import Subquery
from django.db.models.functions import Coalesce


def count_subquery(qs: QuerySet) -> Func:
    qs = qs.annotate(count=Count("id")).order_by().values("count")
    qs.query.group_by = []
    return Coalesce(Subquery(qs), 0, output_field=IntegerField())
