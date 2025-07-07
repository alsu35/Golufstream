from core.models import Profile, OrganizationLocation, Status, Category, Request
from datetime import date, time

# Подгружаем справочники
loc_alm = OrganizationLocation.objects.get(pk=1)
loc_nch = OrganizationLocation.objects.get(pk=2)

status1 = Status.objects.get(pk=1)
status2 = Status.objects.get(pk=2)
status3 = Status.objects.get(pk=3)
status4 = Status.objects.get(pk=4)
status5 = Status.objects.get(pk=5)

cat1 = Category.objects.get(pk=1)
cat2 = Category.objects.get(pk=2)
cat3 = Category.objects.get(pk=3)  # lifting

# Профили (заказчики и ответственные)
cust2 = Profile.objects.get(pk=2)
cust4 = Profile.objects.get(pk=4)
cust5 = Profile.objects.get(pk=5)
resp2 = Profile.objects.get(pk=2)
resp3 = Profile.objects.get(pk=3)
resp4 = Profile.objects.get(pk=4)
resp5 = Profile.objects.get(pk=5)

# Удаляем старые заявки
Request.objects.all().delete()

# Helper
def mkreq(pk, customer, location, ds, de, ts, te, completed, breaks,
          obj, wtype, ttype, status, resp, comment,
          cat, rc=None, rig_names=None, rig_certs=None):
    r = Request(
        id=pk,
        customer=customer,
        location=location,
        date_start=ds,
        date_end=de,
        time_start=ts,
        time_end=te,
        is_completed_fact=completed,
        break_periods=breaks,
        work_object=obj,
        work_type=wtype,
        transport_type=ttype,
        status=status,
        responsible=resp,
        comment=comment,
        equipment_category=cat,
        responsible_certificate=rc,
        rigger_name=rig_names,
        rigger_certificates=rig_certs,
    )
    r.save()
    print(f"Created Request #{pk}")

# 5 заявок в ALM (loc_alm)
mkreq(1, cust2, loc_alm, date(2023,11,1), date(2023,11,3), time(8,0), time(17,0),
      True, ["12:00-13:00","15:30-15:45"], "Скважина №123","Ремонт насоса","Автокран",
      status1, resp3, "Работы срочные", cat3, rc="RC-001",
      rig_names="Иванов И.И., Петров П.П.", rig_certs="CERT-100,CERT-200")

mkreq(3, cust5, loc_alm, date(2023,11,10), date(2023,11,12), time(7,30), time(19,30),
      True, ["11:00-11:15"], "Цех №2","Монтаж каркаса","Кран-манипулятор",
      status3, resp3, "Работа в две смены", cat3, rc="RC-003",
      rig_names="Сидоров С.С.", rig_certs="CERT-201")

mkreq(5, cust5, loc_alm, date(2023,11,20), date(2023,11,25), time(6,0), time(18,0),
      True, ["10:00-10:15","13:00-14:00"], "Буровая установка","Замена бурового долота","Буровая машина",
      status5, resp2, "Требуется спецтехника", cat3, rc="RC-005",
      rig_names="Федоров Ф.Ф.", rig_certs="CERT-301")

mkreq(7, cust2, loc_alm, date(2023,11,8), date(2023,11,10), time(9,0), time(17,0),
      True, [], "Площадка строительства","Установка конструкций","Кран-манипулятор",
      status2, resp4, "Монтаж металлоконструкций", cat3, rc="RC-007",
      rig_names="Кузнецов К.К., Волков В.В.", rig_certs="CERT-303,CERT-404")

mkreq(9, Profile.objects.get(pk=1), loc_alm, date(2023,11,18), date(2023,11,20), time(8,0), time(18,0),
      True, ["12:00-13:00"], "Склад","Переезд","Газель",
      status4, resp2, "Требуется упаковка", cat1)

# 5 заявок в NCH (loc_nch)
mkreq(2, cust4, loc_nch, date(2023,11,5), date(2023,11,5), time(9,0), time(12,0),
      False, [], "Площадка №7","Транспортировка","Грузовик",
      status2, resp5, "Ожидается задержка", cat1)

mkreq(4, cust2, loc_nch, date(2023,11,15), date(2023,11,16), time(8,30), time(16,30),
      False, [], "Складское помещение","Перемещение","Электропогрузчик",
      status4, resp4, "", cat2)

mkreq(6, cust5, loc_nch, date(2023,11,22), date(2023,11,22), time(10,0), time(14,0),
      False, ["12:00-12:30"], "Насосная станция","Диагностика","Технический фургон",
      status1, resp3, "Обычный режим", cat1)

mkreq(8, Profile.objects.get(pk=1), loc_nch, date(2023,11,14), date(2023,11,14), time(7,0), time(15,0),
      False, ["11:30-12:00"], "Цех металлообработки","Погрузка металла","Погрузчик",
      status3, resp5, "Работа в стеснённых условиях", cat2)

mkreq(10, cust3 := Profile.objects.get(pk=3), loc_nch, date(2023,11,28), date(2023,11,30), time(7,30), time(17,30),
      True, ["10:30-10:45","13:00-13:30"], "Жилой корпус","Подъём стройматериалов","Автовышка",
      status5, resp3, "Сложная разгрузка", cat3, rc="RC-010",
      rig_names="Миронов М.М.", rig_certs="CERT-505")