# django-delete-guard (DeleteGuard)

**Blocks dangerous Django ORM deletes in production — before they happen.**

Backups and alerts are too late.  
This stops risky `QuerySet.delete()` calls **at execution time**, unless the developer explicitly opts in.

---

## Why this exists

If you’ve ever:
- wiped production with a bad `.delete()`
- underestimated cascade deletes
- run a “quick cleanup” script in prod
- trusted migrations too much

…this is for you.

**Most catastrophic data loss is valid code with invalid intent.**  
Django makes bulk deletes deceptively easy. This guard makes them explicit.

---

## What it does (V1)

In **production only** (`APP_ENV=production|prod`), it blocks:

- ❌ **Unfiltered deletes**  
  `Model.objects.all().delete()`

- ❌ **Bulk deletes over 100 rows**

Unless you explicitly override with intent.

Everything else works normally.

---

## Install (60 seconds)

```bash
pip install django-delete-guard
