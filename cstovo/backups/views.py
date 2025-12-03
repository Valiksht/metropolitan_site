# cstovo/backups/views.py
import io
import os
import tarfile
import tempfile
import json
import datetime
from typing import Iterable, Dict, Any, List, Tuple, Optional

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.core import serializers
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import StreamingHttpResponse, HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.timezone import now
from django.core.management import call_command

from .models import BackupLog
from .groups import GROUPS, get_model

superuser_required = user_passes_test(
    lambda u: u.is_active and u.is_superuser,
    login_url="/admin/login/",
)


def _update_log(key: str, filename: str, count: Optional[int]):
    log, _ = BackupLog.objects.get_or_create(key=key)
    log.last_export_at = now()
    log.last_export_file = filename
    log.last_export_count = count
    log.save(update_fields=["last_export_at", "last_export_file", "last_export_count"])


@superuser_required
def center(request: HttpRequest):
    # Подготовим данные для шаблона: список групп + лог по каждой
    entries = []
    for key, group in GROUPS.items():
        log = BackupLog.objects.filter(key=key).first()
        entries.append({"key": key, "group": group, "log": log})
    full_log = BackupLog.objects.filter(key="full_export").first()
    ctx = {
        "entries": entries,
        "full_log": full_log,
    }
    return render(request, "backups/center.html", ctx)


def _stream_tar(files: List[Tuple[str, str]]) -> StreamingHttpResponse:
    """
    files: список (abs_path, arcname)
    Возвращает StreamingHttpResponse с tar.gz.
    """
    def generator():
        with tarfile.open(fileobj := io.BytesIO(), mode="w:gz") as tar:
            for abs_path, arcname in files:
                if os.path.exists(abs_path):
                    tar.add(abs_path, arcname=arcname)
        fileobj.seek(0)
        while True:
            chunk = fileobj.read(8192)
            if not chunk:
                break
            yield chunk

    resp = StreamingHttpResponse(generator(), content_type="application/gzip")
    resp["Content-Disposition"] = f'attachment; filename="full_backup_{now().strftime("%Y%m%d_%H%M%S")}.tar.gz"'
    return resp


@superuser_required
def full_export(request: HttpRequest):
    if request.method != "POST":
        return redirect(reverse("backups:center"))

    tmpdir = tempfile.mkdtemp(prefix="dbb_")
    ts = now().strftime("%Y%m%d_%H%M%S")
    db_file = os.path.join(tmpdir, f"db_{ts}.dump")
    media_file = os.path.join(tmpdir, f"media_{ts}.tar.gz")

    # Бэкап БД (django-dbbackup)
    call_command("dbbackup", output_filename=db_file, compress=getattr(settings, "DBBACKUP_COMPRESS", True))
    # Бэкап медиа
    call_command("mediabackup", output_filename=media_file, compress=True)

    response = _stream_tar([
        (db_file, os.path.basename(db_file)),
        (media_file, os.path.basename(media_file)),
    ])

    _update_log("full_export", filename=f"full_backup_{ts}.tar.gz", count=None)

    # Очистка временных файлов после отправки
    orig_close = response.close
    def cleanup_and_close(*a, **k):
        try:
            for p in (db_file, media_file):
                if os.path.exists(p):
                    os.remove(p)
            if os.path.exists(tmpdir):
                os.rmdir(tmpdir)
        except Exception:
            pass
        return orig_close(*a, **k)
    response.close = cleanup_and_close

    return response


@superuser_required
def full_import(request: HttpRequest):
    if request.method != "POST" or "file" not in request.FILES:
        return redirect(reverse("backups:center"))

    up = request.FILES["file"]
    tmpdir = tempfile.mkdtemp(prefix="dbb_imp_")
    archive_path = os.path.join(tmpdir, up.name)

    with open(archive_path, "wb") as f:
        for chunk in up.chunks():
            f.write(chunk)

    db_member = media_member = None
    with tarfile.open(archive_path, "r:gz") as tar:
        members = tar.getmembers()
        db_member = next((m for m in members if m.name.startswith("db_")), None)
        media_member = next((m for m in members if m.name.startswith("media_")), None)
        if db_member:
            tar.extract(db_member, path=tmpdir)
        if media_member:
            tar.extract(media_member, path=tmpdir)

    if db_member:
        db_path = os.path.join(tmpdir, db_member.name)
        call_command("dbrestore", input_filename=db_path)

    if media_member:
        media_path = os.path.join(tmpdir, media_member.name)
        with tarfile.open(media_path, "r:gz") as mtar:
            for member in mtar.getmembers():
                if not member.isfile():
                    continue
                rel = member.name
                f = mtar.extractfile(member)
                if not f:
                    continue
                # Не перезаписываем существующие файлы
                if not default_storage.exists(rel):
                    default_storage.save(rel, f)

    # Уборка
    try:
        for fn in os.listdir(tmpdir):
            p = os.path.join(tmpdir, fn)
            if os.path.isdir(p):
                # Удалим всё внутри
                for sub in os.listdir(p):
                    os.remove(os.path.join(p, sub))
                os.rmdir(p)
            else:
                os.remove(p)
        os.rmdir(tmpdir)
    except Exception:
        pass

    return redirect(reverse("backups:center"))


def _resolve_attr(obj, dotted: str):
    cur = obj
    for part in dotted.split("__"):
        cur = getattr(cur, part)
    return cur


def _collect_group_qs(group_cfg: Dict[str, Any], until_date: Optional[datetime.date]):
    payload = []  # [(Model, qs, mcfg)]
    total_count = 0
    for mcfg in group_cfg["models"]:
        Model = get_model(mcfg["model"])
        qs = Model.objects.all()
        date_field = mcfg.get("date_field")
        if date_field and until_date:
            qs = qs.filter(**{f"{date_field}__lte": until_date})
        payload.append((Model, qs, mcfg))
        total_count += qs.count()
    return payload, total_count


def _media_paths_for_qs(qs, media_fields: List[str]) -> Iterable[Tuple[str, str]]:
    """
    Для каждого объекта и каждого media-поля создаёт временный файл
    и возвращает (abs_path, arcname) для добавления в архив.
    arcname = относительный путь внутри media (например 'news/1.jpg').
    """
    for obj in qs.iterator():
        for field in media_fields:
            f = getattr(obj, field, None)
            if not f:
                continue
            try:
                if getattr(f, "name", "") and default_storage.exists(f.name):
                    with default_storage.open(f.name, "rb") as fh:
                        tmp = tempfile.NamedTemporaryFile(delete=False)
                        for chunk in iter(lambda: fh.read(8192), b""):
                            if not chunk:
                                break
                            tmp.write(chunk)
                        tmp.flush()
                        tmp.close()
                        yield (tmp.name, f.name)
            except Exception:
                continue


@superuser_required
def group_export(request: HttpRequest, key: str):
    group_cfg = GROUPS.get(key)
    if not group_cfg:
        return HttpResponse("Группа не найдена", status=404)
    # Дата нужна только для группы новостей
    until_str = request.GET.get("until")
    until_cutoff = None
    if key == "group_news" and until_str:
        try:
            # ожидаем формат YYYY-MM-DD
            d = datetime.date.fromisoformat(until_str)
            # конец дня, aware при USE_TZ
            end_dt = datetime.datetime.combine(d, datetime.time.max)
            if getattr(settings, "USE_TZ", False):
                end_dt = timezone.make_aware(end_dt, timezone.get_current_timezone())
            until_cutoff = end_dt
        except ValueError:
            # игнорируем неверный формат — делаем выгрузку без ограничения по дате
            until_cutoff = None
    # для остальных групп (не news) until_cutoff = None
    payload, total_count = _collect_group_qs(group_cfg, until_cutoff)
    tmp_files: List[Tuple[str, str]] = []        # ВРЕМЕННЫЕ JSON: (abs_path, arcname)
    media_entries: List[Tuple[str, str]] = []    # МЕДИА (НЕ удаляем!): (abs_path, arcname)
    ts = now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{key}_backup_{ts}"
    json_dir = tempfile.mkdtemp(prefix=f"{key}_json_")
    # Сериализуем каждую модель в отдельный JSON на диск (временные файлы)
    for Model, qs, mcfg in payload:
        label = f"{Model._meta.app_label}.{Model._meta.model_name}"
        json_path = os.path.join(json_dir, f"{label}.json")
        data = serializers.serialize(
            "json",
            qs,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=False,
            indent=2,
        )
        with open(json_path, "wb") as f:
            f.write(data.encode("utf-8"))
        tmp_files.append((json_path, f"data/{os.path.basename(json_path)}"))
        # Собираем медиа-пути (из реальных файлов; НЕ копируем и НЕ удаляем потом)
        media_fields = (mcfg.get("media_fields") or [])
        for abs_path, arcname in _media_paths_for_qs(qs, media_fields):
            # arcname должен быть относительным, без ведущего слеша
            media_entries.append((abs_path, f"media/{arcname}"))
    # Потоковая отдача архива: собираем .tar.gz в памяти и стримим
    def generator():
        buf = io.BytesIO()
        # ВАЖНО: именованный аргумент fileobj=...
        with tarfile.open(mode="w:gz", fileobj=buf) as tar:
            # 1) Добавляем JSON-файлы
            for abs_path, arcname in tmp_files:
                if os.path.exists(abs_path):
                    tar.add(abs_path, arcname=arcname)
            # 2) Добавляем медиа-файлы
            for abs_path, arcname in media_entries:
                if os.path.exists(abs_path):
                    tar.add(abs_path, arcname=arcname)
        buf.seek(0)
        try:
            chunk = buf.read(8192)
            while chunk:
                yield chunk
                chunk = buf.read(8192)
        finally:
            # ЧИСТИМ ТОЛЬКО временные JSON и каталог
            try:
                for abs_path, _ in tmp_files:
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                if os.path.isdir(json_dir):
                    os.rmdir(json_dir)
            except Exception:
                # намеренно глотаем — это не должно ронять отдачу архива
                pass
    response = StreamingHttpResponse(generator(), content_type="application/gzip")
    response["Content-Disposition"] = f'attachment; filename="{base_name}.tar.gz"'
    _update_log(key, filename=f"{base_name}.tar.gz", count=total_count)
    return response


@transaction.atomic
def _import_json_with_dedup(tar: tarfile.TarFile, group_cfg: Dict[str, Any]) -> int:
    """
    Импортирует JSON с дедупликацией на основе unique_fields.
    Возвращает число созданных новых записей.
    """
    created = 0

    # Все JSON-файлы
    json_members = [m for m in tar.getmembers() if m.isfile() and m.name.startswith("data/") and m.name.endswith(".json")]

    # Создаём по порядку, указанному в конфиге группы (чтобы зависимости шли корректно)
    for mcfg in group_cfg["models"]:
        Model = get_model(mcfg["model"])
        label = f"{Model._meta.app_label}.{Model._meta.model_name}.json"
        member = next((mm for mm in json_members if mm.name.endswith(label)), None)
        if not member:
            continue
        f = tar.extractfile(member)
        if not f:
            continue

        objects = list(serializers.deserialize("json", f.read().decode("utf-8")))
        uniq_fields = mcfg.get("unique_fields") or []

        for obj in objects:
            inst = obj.object
            if uniq_fields:
                flt = {}
                try:
                    for uf in uniq_fields:
                        flt[uf] = _resolve_attr(inst, uf)
                except Exception:
                    # Если не получилось прочитать поле — считаем, что запись новая
                    obj.save()
                    created += 1
                    continue

                if Model.objects.filter(**flt).exists():
                    # Уже есть — пропускаем
                    continue
                obj.save()
                created += 1
            else:
                # Без unique_fields ориентируемся на PK (не надёжно при миграциях между базами)
                if getattr(inst, "pk", None) and Model.objects.filter(pk=inst.pk).exists():
                    continue
                obj.save()
                created += 1

    # Медиа-файлы
    media_members = [m for m in tar.getmembers() if m.isfile() and m.name.startswith("media/")]
    for mm in media_members:
        relpath = mm.name[len("media/"):]  # относительный путь внутри storage
        f = tar.extractfile(mm)
        if not f:
            continue
        # Не перезаписываем существующие файлы
        if not default_storage.exists(relpath):
            default_storage.save(relpath, f)

    return created


@superuser_required
def group_import(request: HttpRequest, key: str):
    group_cfg = GROUPS.get(key)
    if not group_cfg:
        return HttpResponse("Группа не найдена", status=404)
    if request.method != "POST" or "file" not in request.FILES:
        return redirect(reverse("backups:center"))

    up = request.FILES["file"]
    # Читаем архив напрямую из upload-стрима
    with tarfile.open(fileobj=up, mode="r:gz") as tar:
        created = _import_json_with_dedup(tar, group_cfg)

    return HttpResponse(f"Загружено новых записей: {created}")