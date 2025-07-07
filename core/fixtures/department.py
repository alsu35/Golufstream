from core.models import Department, Organization
from django.core.exceptions import ObjectDoesNotExist

# Список подразделений из JSON
departments_data = [
    {"pk": 1, "organization": 8, "name": "Отдел промышленной безопасности, охраны труда и охраны окружающей среды"},
    {"pk": 2, "organization": 8, "name": "Служба подготовительных работ"},
    {"pk": 3, "organization": 8, "name": "База производственного обеспечения"},
    {"pk": 4, "organization": 8, "name": "Автотранспортный цех"},
    {"pk": 5, "organization": 8, "name": "Ремонтно-механическая мастерская"},
    {"pk": 6, "organization": 8, "name": "Цех бурения"},
    {"pk": 7, "organization": 8, "name": "Цех текущего и капитального ремонта"},
    {"pk": 8, "organization": 8, "name": "Служба наклонно-капитального бурения и телеметрии"},
    {"pk": 9, "organization": 8, "name": "Управление геофизики"},
    {"pk": 10, "organization": 8, "name": "Служба главного энергетика"},
    {"pk": 11, "organization": 8, "name": "Служба главного механика"},
    {"pk": 12, "organization": 8, "name": "Производственный отдел"},
    {"pk": 13, "organization": 8, "name": "Отдел АСУ ТП"},
    {"pk": 14, "organization": 8, "name": "Отдел долотно-двигательного сервиса"},
    {"pk": 15, "organization": 2, "name": "Отдел управления персоналом"},
    {"pk": 16, "organization": 3, "name": "Финансово-экономический отдел"},
    {"pk": 17, "organization": 4, "name": "Юридический отдел"},
    {"pk": 18, "organization": 2, "name": "Инженерно-технический отдел"},
    {"pk": 19, "organization": 3, "name": "Отдел логистики и закупок"},
]

# Получаем организации по ID (предполагается, что они уже существуют)
try:
    org_8 = Organization.objects.get(pk=8)  # Гольфстрим
    org_2 = Organization.objects.get(pk=2)  # Гамма Аддитив
    org_3 = Organization.objects.get(pk=3)  # Контур
    org_4 = Organization.objects.get(pk=4)  # СМУ №7
except Organization.DoesNotExist as e:
    print(f"Организация {e} не найдена. Убедитесь, что фикстуры организаций загружены.")
    exit(1)

# Создаем подразделения
for data in departments_data:
    try:
        # Определяем организацию
        if data["organization"] == 8:
            org = org_8
        elif data["organization"] == 2:
            org = org_2
        elif data["organization"] == 3:
            org = org_3
        elif data["organization"] == 4:
            org = org_4
        else:
            print(f"Неизвестная организация в данных: {data}")
            continue

        # Создаем или обновляем подразделение
        dept, created = Department.objects.update_or_create(
            pk=data["pk"],
            defaults={
                "organization": org,
                "name": data["name"]
            }
        )
        if created:
            print(f"Создано подразделение: {dept.name} (ID: {dept.pk})")
        else:
            print(f"Обновлено подразделение: {dept.name} (ID: {dept.pk})")

    except Exception as e:
        print(f"Ошибка при обработке {data}: {e}")