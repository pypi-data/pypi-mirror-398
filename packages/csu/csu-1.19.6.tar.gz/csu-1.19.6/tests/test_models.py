import pytest
from django.db.models import OuterRef

from csu.query import count_subquery

pytest.importorskip("django")

from django.db import connection
from django.test.utils import CaptureQueriesContext

from testproject.models import MyBaseModel
from testproject.models import MyBaseModel2


@pytest.mark.django_db
def test_basemodel_bad():
    t = MyBaseModel()
    t.update_fields(foo="bar")
    with pytest.raises(ValueError, match=r"Field 'foo' expected a number but got 'bar'."):
        t.update_fields_and_save(foo="bar")


@pytest.mark.django_db
def test_basemodel_insert():
    with CaptureQueriesContext(connection) as ctx:
        t = MyBaseModel()
        t.update_fields(foo="bar")
        t.update_fields_and_save(foo="123")
    assert len(ctx.captured_queries) == 1
    sql = ctx.captured_queries[0]["sql"]
    assert sql.startswith('INSERT INTO "testproject_mybasemodel" ("created_at", "modified_at", "foo") ')


@pytest.mark.django_db
def test_basemodel_update():
    t = MyBaseModel(foo="1")
    t.save()

    with CaptureQueriesContext(connection) as ctx:
        t.update_fields(foo="bar")
        t.update_fields_and_save(foo="123")
    assert len(ctx.captured_queries) == 1
    sql = ctx.captured_queries[0]["sql"]
    assert sql.startswith('UPDATE "testproject_mybasemodel" SET ')
    assert ' "modified_at" = \'' in sql
    assert ' "foo" = 123 ' in sql


@pytest.mark.django_db
def test_count_subquery():
    t = MyBaseModel.objects.create(foo="1")
    for i in range(10):
        MyBaseModel2.objects.create(bar=i, mbm=t)
    with CaptureQueriesContext(connection) as ctx:
        r = list(MyBaseModel.objects.annotate(counts=count_subquery(MyBaseModel2.objects.filter(mbm=OuterRef("pk"), bar__gt=5))))
    assert len(ctx.captured_queries) == 1
    assert len(r) == 1
    assert r[0].counts == 4
    sql = ctx.captured_queries[0]["sql"]
    assert (
        sql == 'SELECT "testproject_mybasemodel"."id", "testproject_mybasemodel"."created_at", "testproject_mybasemodel"."modified_at", '
        '"testproject_mybasemodel"."foo", COALESCE((SELECT COUNT(U0."id") AS "count" FROM "testproject_mybasemodel2" U0 WHERE '
        '(U0."bar" > 5 AND U0."mbm_id" = ("testproject_mybasemodel"."id"))), 0) AS "counts" FROM "testproject_mybasemodel"'
    )
