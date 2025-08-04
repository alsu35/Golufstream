from django.db import models
from django.utils.translation import gettext_lazy as _

class NamedModel(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, unique=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name

class Status(NamedModel):
    """ Статусы заявок"""
    class Meta(NamedModel.Meta):
        verbose_name = _('Статус')
        verbose_name_plural = _('Статусы')

class Category(NamedModel):
    """ Категория транспорта при подаче заявки"""
    class Meta(NamedModel.Meta):
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')

class Role(NamedModel):
    """ Роль  заявки"""
    class Meta(NamedModel.Meta):
        verbose_name = _('Роль')
        verbose_name_plural = _('Роли')

class OrganizationLocation(NamedModel):
    class Meta(NamedModel.Meta):
        verbose_name = _('Локация организации')
        verbose_name_plural = _('Локации организаций')

