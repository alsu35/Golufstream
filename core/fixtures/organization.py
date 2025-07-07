from core.models import Organization

# Создание головной организации
tatneft = Organization.objects.create(
    name="Татнефть",
    full_name="ПАО «Татнефть» им. В.И. Шашина",
    inn="1648014054"
)

# Дочерние организации
Organization.objects.create(name="Гамма Аддитив", full_name="ООО «Гамма Аддитив»", inn="1650349746")
Organization.objects.create(name="Контур", full_name="АО «Контур»", inn="9704117428")
Organization.objects.create(name="СМУ №7", full_name="ООО «СМУ №7»", inn="1639034037")
Organization.objects.create(name="Техбурсервис", full_name="ООО «Техбурсервис»", inn="1643012519")
Organization.objects.create(name="СМУ-7", full_name="ООО «СМУ-7»", inn="1644094722")
Organization.objects.create(name="Крафтпайп", full_name="АО «Крафтпайп»", inn="1674005550")
Organization.objects.create(name="Гольфстрим", full_name="ООО «Гольфстрим»", inn="1650289328")
Organization.objects.create(name="Инжиниринг", full_name="ООО «Бона Фиде Инжиниринг»", inn="1650339240")
