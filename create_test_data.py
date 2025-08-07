"""
from create_test_data import create_test_data
create_test_data()
"""
import os
import django
from datetime import date, timedelta
import random
from django.utils import timezone

# Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

print("=== Начало создания тестовых данных ===")
print("1. Импорт моделей...")

# Импорт моделей с правильными путями
from users.models import User, Profile, Organization, Department
from core.models import OrganizationLocation, Role, Status, Category
from myrequests.models import Request

# === 1. Создаем справочники (core) ===
print("2. Создаем справочники...")

# Статусы
statuses = [
    ('new', 'Новая'),
    ('assigned', 'Назначена'),
    ('work', 'В работе'),
    ('done', 'Выполнена'),
    ('cancel', 'Отменена')
]
for code, name in statuses:
    Status.objects.get_or_create(code=code, defaults={'name': name})

# Категории
categories = [
    ('lifting', 'Подъемные сооружения'),
    ('cargo', 'Перевозка грузов'),
    ('people', 'Перевозка людей'),
    ('special', 'Специализированная техника'),
    ('other', 'Прочее')
]
for code, name in categories:
    Category.objects.get_or_create(code=code, defaults={'name': name})

# Локации
locations = [
    ('alm', 'Альметьевск'),
    ('nch', 'Нижнекамск'),
    ('ext', 'Внешний')
]
for code, name in locations:
    OrganizationLocation.objects.get_or_create(code=code, defaults={'name': name})

# Роли
roles = [
    ('admin', 'Администратор'),
    ('operator', 'Оператор'),
    ('customer', 'Заказчик'),
    ('employee', 'Сотрудник')
]
for code, name in roles:
    Role.objects.get_or_create(code=code, defaults={'name': name})

print(f"  - Создано: {Status.objects.count()} статусов, {Category.objects.count()} категорий, "
    f"{OrganizationLocation.objects.count()} локаций, {Role.objects.count()} ролей")

# === 2. Создаем организационную структуру ===
print("3. Создаем организационную структуру...")

# Организации
organizations = [
    ("Татнефть", "ПАО «Татнефть» им. В.И. Шашина", "1648014054"),
    ("Гамма Аддитив", "ООО «Гамма Аддитив»", "1650349746"),
    ("Контур", "АО «Контур»", "9704117428"),
    ("СМУ №7", "ООО «СМУ №7»", "1639034037"),
    ("Техбурсервис", "ООО «Техбурсервис»", "1643012519"),
    ("Крафтпайп", "АО «Крафтпайп»", "1674005550"),
    ("Гольфстрим", "ООО «Гольфстрим»", "1650289328"),
    ("Инжиниринг", "ООО «Бона Фиде Инжиниринг»", "1650339240"),
    ("СМУ-7", "ООО «СМУ-7»", "1644094722"),

]

created_orgs = []
for name, full_name, inn in organizations:
    org, created = Organization.objects.get_or_create(
        name=name,
        defaults={
            'full_name': full_name,
            'inn': inn
        }
    )
    created_orgs.append(org)
    action = "Создана" if created else "Найдена"
    print(f"  - {action} организация: {org.name}")

# Подразделения
departments_data = [
    {"pk": 1, "organization": 1, "name": "Отдел логистики"},
    {"pk": 2, "organization": 7, "name": "Производственный отдел"},
    {"pk": 3, "organization": 7, "name": "Отдел безопасности"},
    {"pk": 4, "organization": 7, "name": "Административный отдел"},
    {"pk": 5, "organization": 7, "name": "Технический отдел"},
    {"pk": 6, "organization": 2, "name": "Инженерный отдел"},
    {"pk": 7, "organization": 3, "name": "Отдел продаж"},
    {"pk": 8, "organization": 4, "name": "Строительный отдел"},
    {"pk": 9, "organization": 5, "name": "Сервисный центр"},
    {"pk": 10, "organization": 6, "name": "Конструкторский отдел"},
    {"pk": 11, "organization": 7, "name": "Отдел транспорта"},
    {"pk": 12, "organization": 8, "name": "Инженерно-технический отдел"}
]

created_depts = []
for data in departments_data:
    try:
        # Найдем организацию по индексу в created_orgs (индекс = pk - 1)
        org = created_orgs[data["organization"] - 1]
        
        dept, created = Department.objects.get_or_create(
            pk=data["pk"],
            defaults={
                'organization': org,
                'name': data["name"]
            }
        )
        created_depts.append(dept)
        action = "Создано" if created else "Найдено"
        print(f"  - {action} подразделение: {dept.name} ({dept.organization.name})")
    except Exception as e:
        print(f"  - Ошибка при создании подразделения {data}: {e}")

# === 3. Создаем пользователей и профили ===
print("4. Создаем пользователей и профили...")

def create_user_with_profile(email, role_code, department, is_superuser=False, is_staff=False, 
                            last_name=None, first_name=None, middle_name=None, position=None):
    """Создает пользователя и связанный профиль"""
    
    # Генерируем имена, если не указаны
    if not last_name:
        last_name = f"{role_code.capitalize()}"
    if not first_name:
        first_name = "Тестовый"
    if not position:
        position = f"{role_code.capitalize()}"
    
    # Создаем пользователя
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'is_superuser': is_superuser,
            'is_staff': is_staff,
            # 'is_active': True
        }
    )
    
    if created:
        user.set_password('password123')
        user.save()
        print(f"  - Создан пользователь: {email}")
    else:
        print(f"  - Найден пользователь: {email}")
    
    # Создаем профиль, если его нет
    if not hasattr(user, 'profile'):
        try:
            # Выбираем случайную локацию
            location = random.choice(OrganizationLocation.objects.all())
            
            Profile.objects.create(
                user=user,
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name or "Пользователь",
                position=position,
                birth_date=date(1985 + random.randint(0, 20), 1, 1),
                role=Role.objects.get(code=role_code),
                department=department,
                phone=f"8-999-{random.randint(100, 999):03d}-{random.randint(10, 99):02d}-{random.randint(10, 99):02d}",
                location=location
            )
            print(f"    Создан профиль для {email}")
        except Exception as e:
            print(f"    Ошибка при создании профиля для {email}: {e}")
    
    return user

# Администраторы
admin2 = create_user_with_profile(
    'admin2@example.com', 
    'admin', 
    created_depts[0], 
    is_superuser=False, 
    is_staff=True,
    last_name="Системов",
    first_name="Сергей",
    position="Системный администратор"
)

# Операторы
operator1 = create_user_with_profile(
    'operator1@example.com', 
    'operator', 
    created_depts[1],
    last_name="Операторов",
    first_name="Олег",
    position="Оператор"
)
operator2 = create_user_with_profile(
    'operator2@example.com', 
    'operator', 
    created_depts[1],
    last_name="Диспетчеров",
    first_name="Дмитрий",
    position="Диспетчер"
)

# Заказчики
customer1 = create_user_with_profile(
    'customer1@example.com', 
    'customer', 
    created_depts[2],
    last_name="Заказчиков",
    first_name="Иван",
    position="Представитель заказчика"
)
customer2 = create_user_with_profile(
    'customer2@example.com', 
    'customer', 
    created_depts[2],
    last_name="Клиентов",
    first_name="Константин",
    position="Клиент"
)

# Сотрудники
employee1 = create_user_with_profile(
    'employee1@example.com', 
    'employee', 
    created_depts[3],
    last_name="Сотрудников",
    first_name="Сергей",
    position="Сотрудник"
)
employee2 = create_user_with_profile(
    'employee2@example.com', 
    'employee', 
    created_depts[3],
    last_name="Работников",
    first_name="Роман",
    position="Рабочий"
)

# === 4. Создаем тестовые заявки ===
print("5. Создаем тестовые заявки...")

# Список возможных работ
work_objects = ["Складской комплекс", "Производственный цех", "Административное здание", "Территория предприятия"]
work_types = ["Погрузка", "Монтаж оборудования", "Демонтаж", "Транспортировка"]
transport_types = ["Грузовой автомобиль", "Экскаватор", "Автовышка", "Кран-манипулятор", "Спецтехника"]

# Создаем заявки
for i in range(15):
    # Случайные даты (сегодня + несколько дней)
    start_date = date.today() + timedelta(days=random.randint(0, 5))
    end_date = start_date + timedelta(days=random.randint(1, 3))
    
    # Случайное время
    start_hour = random.randint(8, 10)
    end_hour = random.randint(16, 18)
    
    # Случайные перерывы
    break_periods = []
    if random.choice([True, False]):
        break_count = random.randint(1, 2)
        for _ in range(break_count):
            start_break = f"{random.randint(start_hour+1, end_hour-2):02d}:{random.choice(['00', '15', '30', '45'])}"
            end_break = f"{int(start_break[:2]) + random.randint(1, 2):02d}:{start_break[3:]}"
            break_periods.append(f"{start_break}-{end_break}")
    
    # Случайный статус (новые заявки чаще)
    status_choices = ['new', 'assigned', 'work', 'done', 'cancel']
    status_weights = [0.4, 0.3, 0.2, 0.05, 0.05]  # Больше новых заявок
    status_code = random.choices(status_choices, weights=status_weights, k=1)[0]
    
    # Случайный пользователь-заказчик
    customers = [customer1, customer2]
    customer = random.choice(customers)
    
    # Случайный ответственный (оператор или сотрудник)
    responsibles = [operator1, operator2, employee1, employee2]
    responsible = random.choice(responsibles)
    
    # Случайная локация
    location = random.choice(OrganizationLocation.objects.all())
    
    # Случайная категория
    category = random.choice(Category.objects.all())
    
    # Данные для категории "Подъемные сооружения"
    responsible_certificate = ""
    rigger_name = ""
    rigger_certificates = ""
    
    if category.code == 'lifting':
        responsible_certificate = f"Сертификат №{random.randint(1000, 9999)}"
        rigger_count = random.randint(1, 3)
        rigger_names = [f"{name} {random.choice('АБВГДЕЖЗИКЛМН')}.{random.choice('АБВГДЕЖЗИКЛМН')}." 
                        for name in ['Иванов', 'Петров', 'Сидоров', 'Кузнецов', 'Смирнов']]
        rigger_name = ", ".join(rigger_names[:rigger_count])
        rigger_certificates = ", ".join([f"№{random.randint(100, 999)}" for _ in range(rigger_count)])
    
    # Создаем заявку
    Request.objects.create(
        customer=customer.profile,
        responsible=responsible.profile,
        location=location,
        date_start=start_date,
        date_end=end_date,
        time_start=f"{start_hour}:00",
        time_end=f"{end_hour}:00",
        work_object=random.choice(work_objects),
        work_type=random.choice(work_types),
        transport_type=random.choice(transport_types),
        status=Status.objects.get(code=status_code),
        equipment_category=category,
        break_periods=break_periods,
        is_completed_fact=random.choice([True, False]),
        comment=f"Тестовая заявка #{i+1}. Дополнительные комментарии..." if random.choice([True, False]) else "",
        responsible_certificate=responsible_certificate,
        rigger_name=rigger_name,
        rigger_certificates=rigger_certificates
    )
    print(f"  - Создана заявка #{i+1} ({status_code})")

# === 5. Сводка ===
print("\n=== Сводка по созданным данным ===")
print(f"Организации: {Organization.objects.count()}")
print(f"Подразделения: {Department.objects.count()}")
print(f"Пользователи: {User.objects.count()}")
print(f"  - Администраторы: {User.objects.filter(is_staff=True).count()}")
print(f"  - Операторы: {Profile.objects.filter(role__code='operator').count()}")
print(f"  - Заказчики: {Profile.objects.filter(role__code='customer').count()}")
print(f"  - Сотрудники: {Profile.objects.filter(role__code='employee').count()}")
print(f"Заявки: {Request.objects.count()}")
print(f"  - По статусам:")
for status in Status.objects.all():
    count = Request.objects.filter(status=status).count()
    print(f"    * {status.name}: {count}")

print("\n=== Готово! ===")
print("Данные успешно созданы.")
print("Логин для администратора: admin@gmail.com / password123")
print("Логин для заказчика: customer1@example.com / password123")