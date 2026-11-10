# Milan Hydrotech — Website

Website ya **Milan Hydrotech**, kampuni ya uchimbaji wa visima vya maji kwa mashine kubwa (Mafinga, Iringa).

- **Backend:** Django 5.2
- **Database:** PostgreSQL (Supabase)
- **Picha:** Supabase Storage bucket (kupitia S3 API)
- **Frontend:** HTML, CSS, JavaScript (bila framework)
- **Lugha:** Kiswahili (default) na Kiingereza, kitufe kwenye menyu

## Kurasa
| URL | Ukurasa |
|---|---|
| `/` | Mwanzo: hero, huduma, jinsi tunavyofanya kazi, kazi zetu, mikoa |
| `/kuhusu-sisi/` | Historia, taarifa za kampuni, timu |
| `/huduma/` na `/huduma/<slug>/` | Huduma 9, kila moja na ukurasa wake |
| `/miradi/` | Gallery yenye filter na lightbox |
| `/wasiliana-nasi/` | Fomu ya kuomba huduma, simu, WhatsApp, ramani |
| `/admin/` | Usimamizi (badilisha kwa `ADMIN_URL`) |

Kila kitu kinabadilishwa kwenye admin bila kugusa code: taarifa za kampuni, huduma, timu, mikoa,
miradi/picha, na maombi ya wateja kutoka kwenye fomu.

## Kuendesha kwenye kompyuta yako
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env          # kisha weka DJANGO_DEBUG=True
python manage.py migrate
python manage.py seed_site   # inaweka data za mteja na picha za kwanza
python manage.py createsuperuser
python manage.py runserver
```
Bila `DATABASE_URL` inatumia SQLite; bila funguo za Supabase picha zinakaa kwenye folder `media/`.

## Supabase
1. **Database:** Connect → *Session pooler* → nakili connection string kwenye `DATABASE_URL`.
2. **Bucket:** Storage → New bucket → jina `milan-hydrotech`, chagua **Public**.
3. **S3 keys:** Storage → Settings → *S3 access keys* → New key. Weka `SUPABASE_S3_ACCESS_KEY_ID`,
   `SUPABASE_S3_SECRET_ACCESS_KEY`, na region kwenye `SUPABASE_S3_REGION`.
4. `SUPABASE_PROJECT_REF` ni sehemu ya `https://<ref>.supabase.co`.

Funguo hizi ziwe kwenye environment ya host tu. Usiziweke kwenye git.

## Deploy kwenye Render
Repo ina `render.yaml`, kwa hiyo Render inasoma mipangilio yenyewe:

1. Render → **New → Blueprint** → chagua repo `hydrotech`.
2. Jaza thamani zinazoulizwa: `ADMIN_URL`, `DATABASE_URL`, `SUPABASE_PROJECT_REF`, `SUPABASE_S3_REGION`,
   `SUPABASE_S3_ACCESS_KEY_ID`, `SUPABASE_S3_SECRET_ACCESS_KEY`. `DJANGO_SECRET_KEY` inatengenezwa na Render.
3. **Apply.** Build (`build.sh`) inafanya install, collectstatic, migrate na `seed_site`.
4. Admin wa kwanza: Render ya bure haina Shell. Kwenye kompyuta yako, weka `DATABASE_URL` ya Supabase kwenye
   `.env` kisha endesha `python manage.py createsuperuser`. Database ni moja, kwa hiyo inafanya kazi Render pia.
5. Domain yako (ukiwa nayo): Render → Settings → Custom Domains, kisha ongeza `ALLOWED_HOSTS=domain.co.tz,www.domain.co.tz`
   na `SITE_URL=https://domain.co.tz` kwenye Environment.

## Picha
Picha zinazopakiwa kwenye admin hupunguzwa ukubwa zenyewe (upande mrefu ≤ 1600px, JPEG), ili
simu za wateja zifungue site haraka. Picha za mwanzo ziko `website/seed_images/`.

## Tests
```bash
DJANGO_DEBUG=True python manage.py test
```
