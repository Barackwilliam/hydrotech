"""
Two languages, Swahili (default) and English. The visitor's choice lives in the "lang" cookie.
Fixed words of the pages are here; the content itself is in the models (_sw / _en fields).
"""
LANGS = ("sw", "en")
DEFAULT = "sw"
COOKIE = "lang"


def get_lang(request):
    lang = request.COOKIES.get(COOKIE, DEFAULT)
    return lang if lang in LANGS else DEFAULT


def pick(obj, field, lang):
    """obj.<field>_<lang>, falling back to the Swahili text when the English is empty."""
    value = getattr(obj, f"{field}_{lang}", "") or ""
    if not value and lang != DEFAULT:
        value = getattr(obj, f"{field}_{DEFAULT}", "") or ""
    return value


UI = {
    # videos
    "videos_title": ("Tazama Tukifanya Kazi", "Watch Us at Work"),
    "videos_lead": (
        "Video za mashine zetu zikichimba, maji yakitoka, na miradi ikikamilika.",
        "Videos of our rigs drilling, water flowing and projects being finished.",
    ),
    "eyebrow_videos": ("Video", "Videos"),
    "see_all_videos": ("Ona video zote", "See all videos"),
    "play": ("Cheza video", "Play video"),
    "no_videos": ("Video zitawekwa hivi karibuni.", "Videos are coming soon."),
    "watch_on": ("Tazama kwenye", "Watch on"),
    "close": ("Funga", "Close"),
    # modern home extras
    "hero_title_a": ("Maji safi,", "Clean water,"),
    "hero_title_b": ("karibu na wewe.", "close to you."),
    "trust": (
        ["Mtaalamu wa maji ardhini", "Mashine kubwa za kisasa", "Pampu na solar"],
        ["Our own hydrogeologist", "Heavy modern rigs", "Pumps and solar"],
    ),
    "badge_survey": ("Utafiti kabla ya kuchimba", "Survey before drilling"),
    "badge_regions": ("Mikoa tunayohudumia", "Regions we serve"),
    "eyebrow_services": ("Tunachofanya", "What we do"),
    "eyebrow_process": ("Hatua kwa hatua", "Step by step"),
    "eyebrow_projects": ("Kazi halisi", "Real work"),
    "eyebrow_why": ("Kwa nini sisi", "Why us"),
    "eyebrow_team": ("Watu wetu", "Our people"),
    "eyebrow_contact": ("Tuko tayari", "We are ready"),
    "call_now": ("Piga sasa", "Call now"),
    "quick_title": ("Unahitaji maji?", "Need water?"),
    "quick_text": ("Tupigie au tuandikie WhatsApp. Tunajibu haraka.", "Call or WhatsApp us. We answer quickly."),
    # navigation
    "nav_home": ("Mwanzo", "Home"),
    "nav_about": ("Kuhusu Sisi", "About Us"),
    "nav_services": ("Huduma", "Services"),
    "nav_projects": ("Miradi", "Projects"),
    "nav_contact": ("Wasiliana Nasi", "Contact Us"),
    "nav_videos": ("Video", "Videos"),
    "lang_switch": ("English", "Kiswahili"),
    "menu": ("Menyu", "Menu"),
    # buttons
    "cta_quote": ("Omba Huduma", "Request a Quote"),
    "cta_call": ("Piga Simu", "Call Us"),
    "cta_whatsapp": ("WhatsApp", "WhatsApp"),
    "cta_services": ("Angalia Huduma", "Our Services"),
    "read_more": ("Soma zaidi", "Read more"),
    "see_all_projects": ("Ona miradi yote", "See all projects"),
    "see_all_services": ("Ona huduma zote", "See all services"),
    # home
    "hero_kicker": ("Uchimbaji wa visima kwa mashine kubwa", "Borehole drilling with heavy rigs"),
    "hero_title": ("Maji safi, karibu na wewe.", "Clean water, close to you."),
    "hero_text": (
        "Kuanzia utafiti wa maji ardhini hadi kisima kinachotoa maji, pampu na tenki: tunafanya kazi yote, "
        "kwa wataalamu wetu wenyewe.",
        "From groundwater survey to a flowing borehole, pump and tank: we do the whole job, "
        "with our own specialists.",
    ),
    "stat_services": ("Huduma", "Services"),
    "stat_regions": ("Mikoa", "Regions"),
    "stat_founded": ("Tangu", "Since"),
    "stat_team": ("Wataalamu", "Specialists"),
    "services_title": ("Huduma Zetu", "Our Services"),
    "services_lead": (
        "Kila hatua ya kupata maji, chini ya kampuni moja.",
        "Every step of getting water, under one company.",
    ),
    "process_title": ("Jinsi Tunavyofanya Kazi", "How We Work"),
    "process": (
        [
            ("Utafiti", "Mtaalamu wa jiolojia ya maji (hydrogeologist) anachunguza eneo lako na kuchagua sehemu bora ya kuchimba."),
            ("Uchimbaji", "Mashine kubwa inachimba hadi kina kinachofikia maji ya kutosha, kisha kisima kinawekewa casing."),
            ("Upimaji", "Tunapima wingi wa maji (pump test) na ubora wake ili kujua pampu sahihi na usalama wa maji."),
            ("Ufungaji", "Tunafunga pampu ya umeme, solar au ya mkono, pamoja na tenki na mabomba. Unapata maji."),
        ],
        [
            ("Survey", "Our hydrogeologist studies your site and chooses the best point to drill."),
            ("Drilling", "A heavy rig drills down to a good water level, then the borehole is cased."),
            ("Testing", "We test the yield (pump test) and the water quality to size the pump and keep the water safe."),
            ("Installation", "We install an electric, solar or hand pump, with tanks and piping. You have water."),
        ],
    ),
    "why_title": ("Kwa Nini Utuchague", "Why Choose Us"),
    "why": (
        [
            ("Mashine kubwa za kisasa", "Rig zenye nguvu zinazochimba visima virefu hata kwenye miamba migumu."),
            ("Mtaalamu wa maji ardhini", "Hydrogeologist wetu anapunguza hatari ya kuchimba kisima kisicho na maji."),
            ("Kazi kamili, mwanzo hadi mwisho", "Utafiti, uchimbaji, pump test, pampu, solar na tenki: mtu mmoja wa kuwasiliana naye."),
            ("Tunakufikia ulipo", "Tunafanya kazi Mbeya, Njombe, Iringa, Dodoma na Singida."),
        ],
        [
            ("Heavy modern rigs", "Powerful rigs that drill deep boreholes, even through hard rock."),
            ("Groundwater specialist", "Our hydrogeologist lowers the risk of drilling a dry borehole."),
            ("The complete job", "Survey, drilling, pump test, pump, solar and tanks: one contact for everything."),
            ("We come to you", "We work in Mbeya, Njombe, Iringa, Dodoma and Singida."),
        ],
    ),
    "projects_title": ("Kazi Zetu", "Our Work"),
    "projects_lead": ("Baadhi ya visima na miradi tuliyokamilisha.", "Some of the boreholes and projects we have completed."),
    "regions_title": ("Mikoa Tunayohudumia", "Regions We Serve"),
    "regions_lead": (
        "Uko nje ya mikoa hii? Tupigie, tutaangalia namna ya kukufikia.",
        "Outside these regions? Call us and we will see how to reach you.",
    ),
    "cta_band_title": ("Unahitaji kisima cha maji?", "Need a water borehole?"),
    "cta_band_text": (
        "Tuambie ulipo na unachohitaji. Tutakupigia na kukupa makadirio ya gharama.",
        "Tell us where you are and what you need. We will call you back with a cost estimate.",
    ),
    "water_is_life": ("Maji ni Uhai", "Water is Life"),
    # about
    "about_title": ("Kuhusu Milan Hydrotech", "About Milan Hydrotech"),
    "team_title": ("Timu Yetu", "Our Team"),
    "team_lead": ("Watu wanaofanya kazi yako.", "The people who do your job."),
    # services
    "service_steps": ("Hatua za kazi", "How it is done"),
    "service_projects": ("Kazi za huduma hii", "Work in this service"),
    "other_services": ("Huduma nyingine", "Other services"),
    # projects
    "filter_all": ("Zote", "All"),
    "no_projects": ("Picha za miradi zitawekwa hivi karibuni.", "Project photos are coming soon."),
    # contact
    "contact_title": ("Wasiliana Nasi", "Contact Us"),
    "contact_lead": (
        "Jaza fomu hii, au tupigie moja kwa moja. Tunajibu haraka.",
        "Fill in this form, or call us directly. We answer quickly.",
    ),
    "form_name": ("Jina lako", "Your name"),
    "form_phone": ("Namba ya simu", "Phone number"),
    "form_email": ("Barua pepe (si lazima)", "Email (optional)"),
    "form_region": ("Mkoa / mahali kazi ilipo", "Region / site location"),
    "form_service": ("Huduma unayohitaji", "Service you need"),
    "form_service_any": ("Sijui bado / ushauri", "Not sure yet / advice"),
    "form_message": ("Maelezo", "Details"),
    "form_message_ph": (
        "Mfano: Nahitaji kisima cha maji nyumbani, Mafinga. Shamba lina ekari 2.",
        "Example: I need a borehole at home in Mafinga. The farm is 2 acres.",
    ),
    "form_send": ("Tuma Ombi", "Send Request"),
    "form_sent": (
        "Asante! Ombi lako limepokelewa. Tutakupigia hivi karibuni.",
        "Thank you! Your request has been received. We will call you soon.",
    ),
    "form_error": ("Tafadhali rekebisha sehemu zilizo na alama nyekundu.", "Please correct the fields marked in red."),
    "form_phone_bad": ("Andika namba ya simu sahihi.", "Enter a valid phone number."),
    "label_phone": ("Simu", "Phone"),
    "label_email": ("Barua pepe", "Email"),
    "label_office": ("Ofisi kuu", "Head office"),
    "label_pobox": ("S.L.P", "P.O. Box"),
    "label_ceo": ("Mkurugenzi", "CEO"),
    # first-visit language popup (shown in both languages at once)
    "lang_close": ("Funga", "Close"),
    # footer
    "footer_rights": ("Haki zote zimehifadhiwa.", "All rights reserved."),
    "footer_quick": ("Viungo", "Links"),
    "footer_contact": ("Mawasiliano", "Contact"),
    "not_found_title": ("Ukurasa haupatikani", "Page not found"),
    "not_found_text": ("Samahani, ukurasa unaoutafuta haupo.", "Sorry, the page you are looking for does not exist."),
    "back_home": ("Rudi Mwanzo", "Back to Home"),
}


def strings(lang):
    i = LANGS.index(lang)
    return {key: pair[i] for key, pair in UI.items()}
