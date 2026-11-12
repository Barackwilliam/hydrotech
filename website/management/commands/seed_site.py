"""
Fill the site with the client's details, services and first photos.

    python manage.py seed_site

Safe to run again: existing rows are updated, pictures are uploaded only where none is set yet
(so a picture changed in the admin is kept). With Supabase keys set, the pictures go to the bucket.
"""
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from website.models import CompanyInfo, Project, Region, Service, TeamMember

IMAGES = Path(__file__).resolve().parents[2] / "seed_images"

COMPANY = {
    "name": "Milan Hydrotech",
    "founded_year": 2024,
    "ceo_name": "Godfrey S. Mwambage",
    "tagline_sw": "Wataalamu wa uchimbaji wa visima vya maji kwa mashine kubwa, utafiti wa maji ardhini, upimaji wa wingi wa maji (pump test), pampu na solar",
    "tagline_en": "Specialists in borehole drilling with heavy rigs, groundwater survey, water yield testing (pump test), pumps and solar",
    "about_sw": (
        "Milan Hydrotech ni kampuni ya Kitanzania yenye makao makuu Mafinga, mkoani Iringa. Tunachimba visima "
        "vya maji kwa mashine kubwa za kisasa na kutoa huduma zote zinazohusiana na maji ya ardhini.\n"
        "Kazi yetu huanza na utafiti wa maji ardhini unaofanywa na mtaalamu wetu wa jiolojia ya maji "
        "(hydrogeologist), ili kuchimba mahali penye maji ya kutosha. Baada ya uchimbaji, tunapima wingi na "
        "ubora wa maji, tunafunga pampu za umeme au za solar, tunajenga minara ya tenki, na tunakarabati visima "
        "vilivyoharibika.\n"
        "Tunahudumia nyumba binafsi, mashamba, shule, taasisi, makanisa na misikiti, viwanda na jamii katika "
        "mikoa ya Mbeya, Njombe, Iringa, Dodoma na Singida."
    ),
    "about_en": (
        "Milan Hydrotech is a Tanzanian company headquartered in Mafinga, Iringa region. We drill water "
        "boreholes with heavy modern rigs and offer every service connected to groundwater.\n"
        "Our work starts with a groundwater survey by our own hydrogeologist, so that we drill where there is "
        "enough water. After drilling, we test the yield and quality of the water, install electric or solar "
        "pumps, build tank towers and rehabilitate broken boreholes.\n"
        "We serve private homes, farms, schools, institutions, places of worship, industries and communities "
        "in Mbeya, Njombe, Iringa, Dodoma and Singida regions."
    ),
    "phone_1": "+255 714 425 262",
    "phone_2": "+255 784 822 566",
    "whatsapp": "+255 714 425 262",
    "email": "msgodfrey559@gmail.com",
    "website_domain": "milanhydrotech.co.tz",
    "po_box": "655, Iringa",
    "address_sw": "Mafinga, Iringa, Tanzania",
    "address_en": "Mafinga, Iringa, Tanzania",
    "map_query": "Mafinga, Iringa, Tanzania",
}
HERO_IMAGE = "rig-ya-kuchimba.jpg"
ABOUT_IMAGE = "compressor-na-rig.jpg"

REGIONS = ["Iringa", "Njombe", "Mbeya", "Dodoma", "Singida"]

TEAM = [
    ("Godfrey S. Mwambage", "Mkurugenzi Mtendaji (CEO)", "Chief Executive Officer"),
    ("Beatrice Godfrey", "", ""),  # role not given yet
    ("Imani Mwamlenga", "Mtaalamu wa Jiolojia ya Maji", "Hydrogeologist"),
    ("Abdalah Msimbe", "Fundi (Technician)", "Technician"),
    ("Denis Urasa", "Fundi (Technician)", "Technician"),
]

SERVICES = [
    {
        "slug": "uchimbaji-visima", "icon": "drill", "image": "kisima-bomba-la-bluu.jpg",
        "title_sw": "Uchimbaji wa Visima vya Maji", "title_en": "Borehole Drilling & Construction",
        "summary_sw": "Tunachimba visima virefu vya maji kwa mashine kubwa za kisasa, kwa nyumba, mashamba, shule, taasisi na jamii.",
        "summary_en": "We drill deep water boreholes with heavy modern rigs for homes, farms, schools, institutions and communities.",
        "body_sw": "Kisima kizuri ni zaidi ya shimo refu. Tunachimba kwa mashine kubwa zinazoweza kupenya hata miamba migumu, kisha tunajenga kisima kwa casing na screen bora ili maji yabaki safi na kisima kidumu miaka mingi.\nKina cha kisima huamuliwa na utafiti wa maji ardhini uliofanyika kabla, na hali halisi tunayoikuta wakati wa kuchimba.",
        "body_en": "A good borehole is more than a deep hole. We drill with heavy rigs that cut through even hard rock, then build the borehole with quality casing and screens so the water stays clean and the borehole lasts for years.\nThe depth is set by the groundwater survey done beforehand and by what we find while drilling.",
        "steps_sw": "Utafiti wa maji ardhini na kuchagua sehemu ya kuchimba\nKuchimba kwa rig hadi kufikia tabaka la maji\nKuweka casing, screen na gravel pack\nKusafisha kisima (development / flushing)\nKupima wingi wa maji (pump test)\nKukabidhi kisima pamoja na ripoti",
        "steps_en": "Groundwater survey and choosing the drilling point\nRig drilling down to the water-bearing layer\nInstalling casing, screens and gravel pack\nCleaning the borehole (development / flushing)\nYield test (pump test)\nHandover with a report",
    },
    {
        "slug": "utafiti-wa-maji-ardhini", "icon": "search", "image": "",
        "title_sw": "Utafiti wa Maji Ardhini", "title_en": "Groundwater Survey",
        "summary_sw": "Mtaalamu wetu wa jiolojia ya maji anachunguza eneo lako na kuonyesha sehemu bora na kina kinachotarajiwa.",
        "summary_en": "Our hydrogeologist studies your site and shows the best drilling point and the expected depth.",
        "body_sw": "Kuchimba bila utafiti ni kubahatisha. Kabla ya kuchimba, mtaalamu wetu wa jiolojia ya maji (hydrogeologist) anachunguza miamba na tabaka za ardhi kwa vifaa vya kisasa vya utafiti, ili kujua kama kuna maji, yako kina gani, na sehemu ipi ina nafasi kubwa zaidi.\nUnapata ripoti inayoeleza sehemu iliyochaguliwa na kina kinachotarajiwa. Ripoti hii pia inasaidia kwenye maombi ya vibali vinavyohitajika.",
        "body_en": "Drilling without a survey is guessing. Before drilling, our hydrogeologist studies the rocks and soil layers with modern survey equipment to find out whether there is water, how deep it is, and which point has the best chance.\nYou receive a report with the chosen point and the expected depth. It also helps with the permit applications that are required.",
        "steps_sw": "Kutembelea eneo na kusikiliza mahitaji yako\nUchunguzi wa jiolojia na vipimo vya utafiti (geophysical survey)\nKuchambua matokeo\nKuweka alama ya sehemu ya kuchimba\nRipoti ya utafiti",
        "steps_en": "Site visit and understanding your needs\nGeological study and geophysical measurements\nAnalysing the results\nMarking the drilling point\nSurvey report",
    },
    {
        "slug": "ufungaji-wa-pump", "icon": "pump", "image": "submersible-pump.jpg",
        "title_sw": "Ufungaji wa Pump na Solar Pump", "title_en": "Pump & Solar Pump Installation",
        "summary_sw": "Tunafunga submersible pump za umeme, solar pump na pampu za mkono, kulingana na wingi wa maji ya kisima chako.",
        "summary_en": "We install electric submersible pumps, solar pumps and hand pumps, sized to the yield of your borehole.",
        "body_sw": "Pampu sahihi inategemea kina cha kisima, wingi wa maji na kiasi unachohitaji kwa siku. Kwa kutumia matokeo ya pump test, tunachagua na kufunga pampu inayofaa: ya umeme (submersible), ya nishati ya jua (solar), au ya mkono kwa jamii.\nSolar pump inakuondolea gharama ya umeme na inafanya kazi hata maeneo yasiyo na umeme wa gridi.",
        "body_en": "The right pump depends on the borehole depth, its yield and how much water you need per day. Using the pump test results, we choose and install the right pump: electric (submersible), solar powered, or a hand pump for communities.\nA solar pump removes electricity bills and works even where there is no grid power.",
        "steps_sw": "Kupima mahitaji ya maji kwa siku\nKuchagua pampu na paneli za solar zinazofaa\nKufunga pampu, mabomba na control box\nKujaribu mfumo mzima\nKukuelekeza jinsi ya kuutunza",
        "steps_en": "Estimating your daily water need\nChoosing the right pump and solar panels\nInstalling the pump, piping and control box\nTesting the whole system\nShowing you how to look after it",
    },
    {
        "slug": "tenki-za-maji", "icon": "tank", "image": "mnara-wa-tenki.jpg",
        "title_sw": "Tenki na Minara ya Maji", "title_en": "Water Tanks & Tank Towers",
        "summary_sw": "Tunajenga minara ya tenki na kufunga matenki ya kuhifadhi maji, ili maji yafike kwa nguvu kila bomba.",
        "summary_en": "We build tank towers and install storage tanks so water reaches every tap with good pressure.",
        "body_sw": "Tenki lililoinuliwa juu linahifadhi maji ya kisima na kuyasambaza kwa nguvu ya mvutano, bila kuhitaji pampu kufanya kazi muda wote. Tunajenga minara imara ya zege au chuma, na kufunga matenki ya ukubwa unaofaa mahitaji yako.",
        "body_en": "An elevated tank stores water from the borehole and supplies it by gravity, without the pump running all the time. We build strong concrete or steel towers and install tanks sized to your needs.",
        "steps_sw": "Kupima ukubwa wa tenki unaohitajika\nKujenga msingi na mnara\nKufunga matenki\nKuunganisha mabomba kutoka kisimani hadi kwa watumiaji",
        "steps_en": "Sizing the storage you need\nBuilding the foundation and tower\nInstalling the tanks\nConnecting piping from the borehole to the users",
    },
    {
        "slug": "ukarabati-wa-visima", "icon": "wrench", "image": "kisima-pampu-ya-mkono.jpg",
        "title_sw": "Ukarabati wa Visima", "title_en": "Borehole Rehabilitation",
        "summary_sw": "Kisima chako kimepungua maji au kimeharibika? Tunakisafisha, kukitengeneza na kukirudisha kazini.",
        "summary_en": "Has your borehole lost water or broken down? We clean it, repair it and bring it back to work.",
        "body_sw": "Visima vingi huacha kutoa maji kwa sababu ya tope, mchanga, pampu iliyoharibika au casing iliyoziba, si kwa sababu maji yamekwisha. Tunachunguza chanzo cha tatizo, tunasafisha kisima, tunabadilisha vifaa vilivyoharibika, na kujenga upya slab ya juu inapohitajika.",
        "body_en": "Many boreholes stop giving water because of mud, sand, a broken pump or blocked casing, not because the water is gone. We find the cause, clean the borehole, replace broken parts and rebuild the top slab where needed.",
        "steps_sw": "Kuchunguza tatizo\nKutoa pampu na kusafisha kisima\nKurekebisha au kubadilisha vifaa\nKupima wingi wa maji upya\nKurudisha kisima kazini",
        "steps_en": "Diagnosing the problem\nRemoving the pump and cleaning the borehole\nRepairing or replacing parts\nRe-testing the yield\nPutting the borehole back to work",
    },
    {
        "slug": "ubora-wa-maji", "icon": "flask", "image": "maji-safi-bombani.jpg",
        "title_sw": "Upimaji wa Ubora wa Maji", "title_en": "Water Quality Testing (Laboratory Analysis)",
        "summary_sw": "Tunachukua sampuli za maji na kuzipima maabara, ili ujue kama maji yako ni salama kwa kunywa na matumizi mengine.",
        "summary_en": "We take water samples for laboratory analysis, so you know whether your water is safe to drink and use.",
        "body_sw": "Maji yanayoonekana safi yanaweza kuwa na chumvi nyingi, madini au vijidudu visivyoonekana kwa macho. Tunachukua sampuli kwa njia sahihi na kuzipeleka maabara kupima viwango vya kemikali na vijidudu, kisha tunakueleza matokeo na hatua za kuchukua inapohitajika.",
        "body_en": "Water that looks clean can still carry salts, minerals or germs you cannot see. We take samples correctly, send them for laboratory analysis of chemical and microbiological levels, and explain the results and any treatment needed.",
        "steps_sw": "Kuchukua sampuli kwa njia sahihi\nVipimo vya maabara (kemikali na vijidudu)\nKueleza matokeo\nUshauri wa kusafisha maji inapohitajika",
        "steps_en": "Proper sampling\nLaboratory tests (chemical and microbiological)\nExplaining the results\nTreatment advice where needed",
    },
    {
        "slug": "pump-test", "icon": "gauge", "image": "pump-test.jpg",
        "title_sw": "Upimaji wa Wingi wa Maji (Pump Test)", "title_en": "Pump Test (Yield Test)",
        "summary_sw": "Tunapima kisima kinatoa maji kiasi gani kwa saa, ili kuchagua pampu sahihi bila kukausha kisima.",
        "summary_en": "We measure how much water the borehole gives per hour, to choose the right pump without drying it out.",
        "body_sw": "Pump test inaonyesha uwezo halisi wa kisima: lita ngapi kwa saa, na jinsi kina cha maji kinavyoshuka na kurudi. Bila kipimo hiki, ni rahisi kufunga pampu kubwa kupita kiasi inayokausha kisima, au ndogo isiyotosheleza mahitaji yako.",
        "body_en": "A pump test shows the real capacity of a borehole: how many litres per hour, and how the water level drops and recovers. Without it, it is easy to fit a pump that is too big and dries the borehole, or too small for your needs.",
        "steps_sw": "Kufunga pampu ya majaribio\nKusukuma maji kwa muda maalum na kupima kiasi\nKupima kushuka na kurudi kwa kina cha maji\nRipoti na pendekezo la pampu",
        "steps_en": "Installing a test pump\nPumping for a set time and measuring the flow\nMeasuring drawdown and recovery\nReport and pump recommendation",
    },
    {
        "slug": "ujenzi-wa-mabwawa", "icon": "dam", "image": "bwawa-la-maji.jpg",
        "title_sw": "Ujenzi wa Mabwawa ya Maji", "title_en": "Dam & Water Reservoir Construction",
        "summary_sw": "Tunajenga mabwawa na mabirika ya kuhifadhi maji kwa ajili ya mifugo, umwagiliaji na matumizi ya jamii.",
        "summary_en": "We build dams and reservoirs that store water for livestock, irrigation and community use.",
        "body_sw": "Bwawa linahifadhi maji ya kisima au ya mvua kwa ajili ya kipindi cha kiangazi. Tunajenga mabwawa na mabirika ya zege yenye ukubwa unaolingana na matumizi yako, kwa mifugo, kilimo cha umwagiliaji au ufugaji wa samaki.",
        "body_en": "A dam stores borehole or rain water for the dry season. We build concrete dams and reservoirs sized to your use: livestock, irrigated farming or fish farming.",
        "steps_sw": "Kupima eneo na kubuni bwawa\nKuchimba na kuandaa msingi\nKujenga kuta na sakafu\nKuunganisha chanzo cha maji",
        "steps_en": "Site measurement and design\nExcavation and foundation\nBuilding walls and floor\nConnecting the water source",
    },
    {
        "slug": "umwagiliaji", "icon": "sprout", "image": "solar-pump-shambani.jpg",
        "title_sw": "Huduma za Umwagiliaji", "title_en": "Irrigation Services",
        "summary_sw": "Tunaunganisha kisima, pampu ya solar na mfumo wa umwagiliaji, ili ulime mwaka mzima bila kutegemea mvua.",
        "summary_en": "We connect your borehole, a solar pump and an irrigation system so you can farm all year without waiting for rain.",
        "body_sw": "Umwagiliaji unakuwezesha kuvuna zaidi ya mara moja kwa mwaka. Tunabuni mfumo unaolingana na shamba lako na zao lako, kuanzia chanzo cha maji (kisima au bwawa), pampu ya solar au ya umeme, hadi mabomba ya kusambaza maji shambani.",
        "body_en": "Irrigation lets you harvest more than once a year. We design a system that fits your farm and crop, from the water source (borehole or dam) and the solar or electric pump to the pipes that spread water over the field.",
        "steps_sw": "Kutembelea shamba na kujua zao\nKubuni mfumo wa umwagiliaji\nKufunga pampu na mabomba\nKujaribu na kukufundisha matumizi",
        "steps_en": "Farm visit and crop needs\nDesigning the irrigation system\nInstalling pump and piping\nTesting and training",
    },
]

PROJECTS = [
    # (image, title_sw, title_en, service slug, featured)
    ("kisima-bomba-la-bluu.jpg", "Kisima kipya kikitoa maji kwa nguvu", "New borehole flowing strongly", "uchimbaji-visima", True),
    ("pump-test.jpg", "Upimaji wa wingi wa maji (pump test)", "Yield measurement (pump test)", "pump-test", True),
    ("mnara-wa-tenki.jpg", "Mnara wa matenki mawili", "Tower with two storage tanks", "tenki-za-maji", True),
    ("kisima-kikitoa-maji.jpg", "Kichwa cha kisima baada ya kukamilika", "Finished borehole head", "uchimbaji-visima", True),
    ("bwawa-la-maji.jpg", "Bwawa la zege la kuhifadhi maji", "Concrete water reservoir", "ujenzi-wa-mabwawa", True),
    ("kisima-pampu-ya-mkono.jpg", "Kisima chenye pampu ya mkono na slab", "Borehole with hand pump and slab", "ukarabati-wa-visima", True),
    ("kisima-water-drilling.jpg", "Kisima kikitoa maji baada ya kuchimbwa", "Borehole flowing after drilling", "uchimbaji-visima", False),
    ("submersible-pump.jpg", "Submersible pump tayari kufungwa", "Submersible pump ready for installation", "ufungaji-wa-pump", False),
    ("rig-ya-kuchimba.jpg", "Mashine ya kuchimba visima ikiwa eneo la kazi", "Drilling rig on site", "uchimbaji-visima", False),
    ("compressor-na-rig.jpg", "Compressor ya mashine ya kuchimba", "Drilling rig compressor", "uchimbaji-visima", False),
    ("mnara-wa-tenki-nyumbani.jpg", "Mnara wa matenki ya maji nyumbani", "Water tank tower at a home", "tenki-za-maji", False),
    ("mabomba-ya-casing.jpg", "Mabomba ya casing tayari kwa kisima", "Casing pipes ready for a borehole", "uchimbaji-visima", False),
    ("eneo-la-kazi-shambani.jpg", "Eneo la kazi la uchimbaji", "On a drilling site", "uchimbaji-visima", False),
]


def attach(obj, field, filename):
    """Upload a seed picture into an empty image field."""
    if not filename or getattr(obj, field):
        return False
    path = IMAGES / filename
    if not path.exists():
        return False
    # handed over unsaved, so the model shrinks it and puts the watermark on it when it is saved
    setattr(obj, field, ContentFile(path.read_bytes(), name=filename))
    return True


class Command(BaseCommand):
    help = "Load Milan Hydrotech's details, services, team and first photos."

    @transaction.atomic
    def handle(self, *args, **options):
        company = CompanyInfo.load()
        for key, value in COMPANY.items():
            if not getattr(company, key):
                setattr(company, key, value)
        attach(company, "hero_image", HERO_IMAGE)
        attach(company, "about_image", ABOUT_IMAGE)
        company.save()

        for i, name in enumerate(REGIONS):
            Region.objects.update_or_create(name=name, defaults={"order": i})

        for i, (name, role_sw, role_en) in enumerate(TEAM):
            member, created = TeamMember.objects.get_or_create(
                name=name, defaults={"role_sw": role_sw, "role_en": role_en, "order": i})

        services = {}
        for i, data in enumerate(SERVICES):
            data = dict(data)
            image = data.pop("image")
            service, created = Service.objects.get_or_create(slug=data["slug"], defaults={**data, "order": i})
            if attach(service, "image", image) or created:
                service.save()
            services[service.slug] = service

        for i, (image, title_sw, title_en, slug, featured) in enumerate(PROJECTS):
            if Project.objects.filter(title_sw=title_sw).exists():
                continue
            project = Project(title_sw=title_sw, title_en=title_en, service=services.get(slug),
                              featured=featured, order=i)
            attach(project, "image", image)
            project.save()

        self.stdout.write(self.style.SUCCESS(
            f"Done: {Service.objects.count()} services, {TeamMember.objects.count()} team members, "
            f"{Project.objects.count()} projects, {Region.objects.count()} regions."))
