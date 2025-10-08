import os
import subprocess
from celery import shared_task
from datetime import datetime
from django.conf import settings
import glob
import gzip
import shutil

MAX_BACKUPS = 7  # Quantos backups manter

@shared_task
def backup_postgres_local():
    db = settings.DATABASES['default']

    if db['ENGINE'] != 'django.db.backends.postgresql_psycopg2':
        print("Backup PostgreSQL ignorado: não é PostgreSQL")
        return

    DB_NAME = db['NAME']
    DB_USER = db['USER']
    DB_PASSWORD = db['PASSWORD']
    DB_HOST = db.get('HOST', 'localhost')
    DB_PORT = db.get('PORT', '5432')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Pasta de backup relativa ao BASE_DIR (fora do projeto)
    backup_dir = os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'BACKUPS'))
    os.makedirs(backup_dir, exist_ok=True)

    # Nome do arquivo temporário do pg_dump
    temp_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
    backup_file = temp_file + '.gz'  # Arquivo final compactado

    os.environ['PGPASSWORD'] = DB_PASSWORD
    subprocess.run([
        'pg_dump',
        '-h', DB_HOST,
        '-p', str(DB_PORT),
        '-U', DB_USER,
        '-F', 'c',  # formato custom
        '-b',       # incluir blobs
        '-v',
        '-f', temp_file,
        DB_NAME
    ], check=True)

    # Compactar para .gz
    with open(temp_file, 'rb') as f_in, gzip.open(backup_file, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    # Remover arquivo temporário
    os.remove(temp_file)

    print(f"Backup do banco {DB_NAME} salvo em {backup_file} com sucesso!")

    # Limitar quantidade de backups antigos
    backups = sorted(glob.glob(os.path.join(backup_dir, 'backup_*.sql.gz')))
    if len(backups) > MAX_BACKUPS:
        for old_backup in backups[:-MAX_BACKUPS]:
            os.remove(old_backup)
            print(f"Removido backup antigo: {old_backup}")
