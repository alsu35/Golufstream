# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Request, send_telegram_message

# @receiver(post_save, sender=Request)
# def notify_responsible_on_create(sender, instance, created, **kwargs):
#     if created and instance.responsible:
#         chat_id = instance.responsible.profile.telegram_chat_id
#         if chat_id:
#             send_telegram_message(chat_id, f"📝 Вы назначены ответственным за заявку #{instance.id}")
