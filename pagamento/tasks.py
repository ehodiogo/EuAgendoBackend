from celery import shared_task
import time

@shared_task
def verificar_pagamento(a, b):
    time.sleep(5)
    print("TA PAGO!")
    return a + b
