from core.models import User

# Администраторы (superuser и staff)
admin1 = User.objects.create_superuser(username='admin', email='admin@gmail.com', password='password123')
admin2 = User.objects.create_user(username='admin2', email='admin2@example.com', password='adminpass2', is_staff=True, is_superuser=False)

# Заказчики
customer1 = User.objects.create_user(username='customer1', email='customer1@example.com', password='custpass1')
customer2 = User.objects.create_user(username='customer2', email='customer2@example.com', password='custpass2')

# Операторы
operator1 = User.objects.create_user(username='operator1', email='operator1@example.com', password='operpass1')
operator2 = User.objects.create_user(username='operator2', email='operator2@example.com', password='operpass2')

# Сотрудники
employee1 = User.objects.create_user(username='employee1', email='employee1@example.com', password='emppass1')
employee2 = User.objects.create_user(username='employee2', email='employee2@example.com', password='emppass2')

# Гость (без профиля)
guest = User.objects.create_user(username='guest', email='guest@example.com', password='guestpass')

print("Пользователи успешно созданы.")
