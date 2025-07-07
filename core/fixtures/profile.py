

from core.models import User, Profile, Role, Department, OrganizationLocation
from django.core.exceptions import ObjectDoesNotExist

# Получаем пользователей по email или username
try:
    customer_user = User.objects.get(email='customer@example.com')
    employee_user = User.objects.get(email='employee@example.com')
    operator_user = User.objects.get(email='operator@example.com')
    admin_user = User.objects.get(email='adminRole@example.com')
except User.DoesNotExist as e:
    print(f"Пользователь {e} не найден. Убедитесь, что пользователи созданы.")
    exit(1)

# Получаем роли по коду
try:
    admin_role = Role.objects.get(code='admin')
    operator_role = Role.objects.get(code='operator')
    customer_role = Role.objects.get(code='customer')
    employee_role = Role.objects.get(code='employee')
except Role.DoesNotExist as e:
    print(f"Роль {e} не найдена. Убедитесь, что роли загружены.")
    exit(1)

# Получаем подразделения и локации (замените PK на реальные значения)
try:
    dept_1 = Department.objects.get(pk=1)  # Пример: "Отдел промышленной безопасности"
    dept_5 = Department.objects.get(pk=5)  # Пример: "Ремонтно-механическая мастерская"
    dept_6 = Department.objects.get(pk=6)  # Пример: "Цех бурения"
    
    location_1 = OrganizationLocation.objects.get(pk=1)  # Альметьевск
    location_2 = OrganizationLocation.objects.get(pk=2)  # Нижнекамск
except ObjectDoesNotExist as e:
    print(f"Не найден объект: {e}. Убедитесь, что фикстуры загружены.")
    exit(1)

# Создаем профили
def create_profile(user, role, department, location, last_name, first_name, position, birth_date, phone):
    try:
        Profile.objects.create(
            user=user,
            role=role,
            department=department,
            location=location,
            last_name=last_name,
            first_name=first_name,
            position=position,
            birth_date=birth_date,
            phone=phone
        )
        print(f"Профиль для {user.username} создан")
    except Exception as e:
        print(f"Ошибка при создании профиля для {user.username}: {e}")

# --- Профиль заказчика ---
create_profile(
    user=customer_user,
    role=customer_role,
    department=dept_5,  # Замените на реальное подразделение
    location=location_1,
    last_name='Заказчиков',
    first_name='Заказчик',
    position='Заказчик',
    birth_date='1995-01-01',
    phone='+7 900 123-45-69'
)

# --- Профиль сотрудника ---
create_profile(
    user=employee_user,
    role=employee_role,
    department=dept_1,  # Замените на реальное подразделение
    location=location_1,
    last_name='Сотрудников',
    first_name='Сотрудник',
    position='Сотрудник',
    birth_date='2000-01-01',
    phone='+7 900 123-45-70'
)

# --- Профиль оператора ---
create_profile(
    user=operator_user,
    role=operator_role,
    department=dept_6,  # Замените на реальное подразделение
    location=location_1,
    last_name='Операторов',
    first_name='Оператор',
    position='Оператор',
    birth_date='1990-01-01',
    phone='+7 900 123-45-68'
)

# --- Профиль администратора ---
create_profile(
    user=admin_user,
    role=admin_role,
    department=dept_1,  # Замените на реальное подразделение
    location=location_1,
    last_name='Админов',
    first_name='Администратор',
    position='Администратор',
    birth_date='1985-01-01',
    phone='+7 900 123-45-67'
)