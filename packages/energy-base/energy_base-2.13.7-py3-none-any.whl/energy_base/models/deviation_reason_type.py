from django.db import models


class DeviationReasonType(models.TextChoices):
    NO_CONNECTION = 'no_connection', 'Нет связи с оборудованием'
    IN_RESERVE = 'in_reserve', 'В резерве'
    MALFUNCTION = 'malfunction', 'Неисправность устройства'
    OTHER = 'other', 'Другое'
