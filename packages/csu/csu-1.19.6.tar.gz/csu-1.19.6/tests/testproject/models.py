import pytest

pytest.importorskip("django")
from django.db import models

from csu.models import BaseModel


class MyBaseModel(BaseModel):
    foo = models.PositiveIntegerField()


class MyBaseModel2(BaseModel):
    mbm = models.ForeignKey(MyBaseModel, on_delete=models.CASCADE)
    bar = models.PositiveIntegerField()
