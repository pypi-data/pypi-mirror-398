from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework.permissions import IsAuthenticated

from .admin_user import IsAdminUser
from .ges import IsGesUser
from .het import IsHetUser
from .hududgaz_liqufiedgas import IsHududGazLiqufiedGasUser
from .hududgaz_naturalgaz import IsHududGazNaturalgazUser
from .ies import IsIesUser
from .ies_file import IsIesFileUser
from .liquidhydrocarbons import IsLiquidHydrocarbonsUser
from .met import IsMetUser
from .min_energo_report import IsMinEnergoReportUser
from .national_dispatch_center import IsNationalDispatchUser
from .neftegaz import IsNeftegazUser
from .neftegaz_file import IsNeftegazFileUser
from .neftegaz_naturalgaz import IsNeftegazNaturalgazUser
from .neftegaz_oil_well import IsOilWellUser
from .superuser import IsSuperUser
from .uz_energo_sell import IsUzEnergoSaleUser
from .uzbekkomir import IsUzbekkomirUser
from .uzgastrade import IsUzGasTradeUser
from .uztransgaz import IsUzTransGazUser
from .uztransgaz_file import IsUzTransGazFileUser
from .smart_integrity import IsSmartIntegrityUser
from .gas import IsGasUser
from .electricity import IsElectricityUser

roles = settings.REST_FRAMEWORK.get('ROLE_PERMISSION_CLASSES', [])

role_classes = []

for role in roles:
    role_classes.append(import_string(role))

roles = settings.REST_FRAMEWORK.get('ROLE_APP_PERMISSION_CLASSES', [])

for role in roles:
    role_class = import_string(role[0])
    role_class.add_role_app(role[1])
    role_classes.append(role_class)

if role_classes:
    DEFAULT_ROLE_PERMISSIONS = role_classes[0]
else:
    DEFAULT_ROLE_PERMISSIONS = IsAuthenticated

for role_class in role_classes[1:]:
    DEFAULT_ROLE_PERMISSIONS = DEFAULT_ROLE_PERMISSIONS | role_class

__all__ = [
    'IsSuperUser', 'IsAdminUser', 'IsGesUser', 'IsHetUser', 'IsHududGazLiqufiedGasUser', 'IsUzEnergoSaleUser',
    'IsIesUser', 'IsLiquidHydrocarbonsUser', 'IsHududGazNaturalgazUser', 'IsMetUser', 'IsOilWellUser',
    'IsNeftegazNaturalgazUser', 'IsUzGasTradeUser', 'IsUzTransGazUser', 'IsUzbekkomirUser', 'IsIesFileUser',
    'IsUzTransGazFileUser', 'IsNeftegazFileUser', 'IsNationalDispatchUser', 'IsNeftegazUser', 'IsSmartIntegrityUser',
    'IsGasUser', 'IsElectricityUser', 'IsMinEnergoReportUser', 'DEFAULT_ROLE_PERMISSIONS'
]
