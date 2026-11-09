"""Synthetic demo data for video 05 (Fabric Warehouse AI functions).

Fictional company: **Toastly**, an online shop for small kitchen appliances
(North America + Germany, France, Spain, Italy). Everything here is made up.
Fake people use reserved domains (example.com / example.org / example.net) and 555-01xx phones.

    python -I make_data.py <out_dir>

Writes products.csv, product_reviews.csv, support_emails.csv (UTF-8) and 02_load_data.sql
(plain INSERT ... VALUES, runnable in the Fabric SQL query editor). Fixed seed: same output every run.
"""
import csv
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 505
rng = random.Random(SEED)

# ---------------------------------------------------------------- products
# id, name, category, price, profile (share of happy reviews), pros, cons
PRODUCTS = [
    (1, "SmartToast 2-Slice Toaster", "Toasters", 49.99, 0.45,
     ["toasts really fast", "looks great on the counter", "the bagel setting is handy"],
     ["one side always comes out darker", "the crumb tray is a pain to slide out", "it burned my bread on setting 3"]),
    (2, "SmartToast 4-Slice Toaster", "Toasters", 79.99, 0.7,
     ["even toast on both sides", "fits the whole family's breakfast at once", "the defrost button actually works"],
     ["it's bigger than it looks in the photos", "the outside gets very hot", "the lever feels a bit cheap"]),
    (3, "AirCrisp 5L Air Fryer", "Air Fryers", 119.00, 0.6,
     ["the fries come out super crispy", "it heats up in like two minutes", "so easy to clean"],
     ["the basket coating started peeling after a month", "it smells like plastic the first few uses", "the timer beeps way too loud"]),
    (4, "AirCrisp XL Dual Air Fryer", "Air Fryers", 189.00, 0.65,
     ["two baskets means dinner is done at the same time", "big enough for a whole chicken", "the sync finish feature is genius"],
     ["the app never pairs with my phone", "it takes up half the counter", "the right basket runs colder than the left"]),
    (5, "BrewMate Espresso Machine", "Coffee", 329.00, 0.4,
     ["the espresso is cafe quality", "the steam wand makes great foam", "it looks premium"],
     ["it leaks water under the machine", "it's really loud in the morning", "the drip tray fills up after two coffees"]),
    (6, "BrewMate Milk Frother", "Coffee", 59.99, 0.85,
     ["perfect foam every time", "it's quiet", "hot chocolate in it is amazing"],
     ["the whisk falls off sometimes", "it's small for two big mugs"]),
    (7, "KettlePro Glass Kettle", "Kettles", 44.99, 0.45,
     ["boils fast", "the blue light is pretty", "easy to see the water level"],
     ["the lid hinge broke", "the lid pops open while boiling", "limescale shows a lot on the glass"]),
    (8, "KettlePro Temp Control Kettle", "Kettles", 89.99, 0.85,
     ["the temperature presets are perfect for green tea", "keeps water warm for an hour", "the display is clear"],
     ["the beep can't be turned off", "the handle gets warm"]),
    (9, "BlendMax 1200 Blender", "Blenders", 99.00, 0.55,
     ["crushes ice like nothing", "smoothies are silky", "powerful motor"],
     ["the jar cracked after a few weeks", "it's very loud", "the lid leaks when it's full"]),
    (10, "BlendMax Go Portable Blender", "Blenders", 39.99, 0.4,
     ["great for the gym", "charges with USB-C", "fits in my bag"],
     ["the battery dies after two smoothies", "it can't handle frozen fruit", "the charging port stopped working"]),
    (11, "RiceRight Rice Cooker", "Cookers", 69.99, 0.9,
     ["perfect rice every single time", "the keep-warm mode is great", "even sushi rice works"],
     ["the inner pot scratches easily"]),
    (12, "SlowJoe 6Qt Slow Cooker", "Cookers", 64.99, 0.7,
     ["set it and forget it", "my chili has never been better", "big enough for meal prep"],
     ["the lid rattles", "the low setting still boils", "the cord is way too short"]),
    (13, "ChopChop Food Processor", "Prep", 129.00, 0.7,
     ["chops onions in seconds", "lots of blades included", "the dough setting is great"],
     ["it's loud", "too many parts to wash", "the lid lock is hard to close"]),
    (14, "WaffleWiz Waffle Maker", "Breakfast", 54.99, 0.5,
     ["fluffy waffles", "the kids love it", "heats up quick"],
     ["the waffles stick to the plates", "the plates don't come out for cleaning", "batter spills over the sides"]),
    (15, "ScaleSmart Kitchen Scale", "Prep", 24.99, 0.85,
     ["very accurate", "great value", "the tare button is handy"],
     ["it turns itself off too fast", "the battery cover is fiddly"]),
    (16, "IceDream Ice Cream Maker", "Desserts", 149.00, 0.75,
     ["the ice cream is so creamy", "sorbet in 30 minutes", "the kids are obsessed"],
     ["the bowl needs 24 hours in the freezer", "it's noisy", "the paddle is hard to clean"]),
]

# foreign pros/cons per product (short, natural), by language
FOREIGN = {
    "de": {
        3: (["die Pommes werden richtig knusprig", "schnell aufgeheizt"], ["die Beschichtung vom Korb löst sich schon", "riecht am Anfang nach Plastik"]),
        5: (["der Espresso schmeckt wie im Café", "der Milchschaum ist top"], ["die Maschine tropft unten Wasser", "sie ist morgens extrem laut"]),
        7: (["kocht sehr schnell", "das blaue Licht ist schön"], ["das Scharnier vom Deckel ist gebrochen", "der Deckel springt beim Kochen auf"]),
        9: (["zerkleinert Eis ohne Probleme", "Smoothies werden super cremig"], ["der Becher hat einen Riss bekommen", "viel zu laut"]),
        11: (["der Reis ist jedes Mal perfekt", "die Warmhaltefunktion ist praktisch"], ["der Innentopf zerkratzt schnell"]),
        14: (["die Waffeln sind fluffig", "die Kinder lieben ihn"], ["die Waffeln kleben an den Platten", "der Teig läuft über"]),
        16: (["das Eis ist sehr cremig", "Sorbet in 30 Minuten"], ["die Schüssel muss 24 Stunden ins Gefrierfach"]),
    },
    "fr": {
        3: (["les frites sont croustillantes", "chauffe très vite"], ["le revêtement du panier s'écaille déjà", "une odeur de plastique au début"]),
        4: (["deux paniers, tout est prêt en même temps", "assez grande pour un poulet entier"], ["l'appli ne se connecte jamais", "prend la moitié du plan de travail"]),
        5: (["l'espresso est digne d'un café", "la buse vapeur est géniale"], ["elle fuit sous la machine", "très bruyante le matin"]),
        6: (["mousse parfaite à chaque fois", "silencieux"], ["le fouet se détache parfois"]),
        10: (["pratique pour la salle de sport", "se recharge en USB-C"], ["la batterie meurt après deux smoothies", "ne mixe pas les fruits congelés"]),
        13: (["hache les oignons en quelques secondes", "plein d'accessoires"], ["bruyant", "trop de pièces à laver"]),
        16: (["la glace est très onctueuse", "les enfants adorent"], ["le bol doit rester 24 heures au congélateur", "bruyante"]),
    },
    "es": {
        1: (["tuesta muy rápido", "queda bonita en la cocina"], ["un lado siempre sale más tostado", "me quemó el pan en el nivel 3"]),
        5: (["el espresso está buenísimo", "la espuma de leche es perfecta"], ["gotea agua por abajo", "hace muchísimo ruido"]),
        8: (["los programas de temperatura son perfectos para el té", "mantiene el agua caliente una hora"], ["el pitido no se puede quitar"]),
        9: (["tritura hielo sin problema", "batidos súper suaves"], ["la jarra se rajó a las pocas semanas", "la tapa gotea"]),
        12: (["lo dejas y te olvidas", "el chili me queda increíble"], ["la tapa vibra", "el cable es muy corto"]),
        15: (["muy precisa", "buena relación calidad-precio"], ["se apaga sola demasiado rápido"]),
    },
    "it": {
        3: (["le patatine vengono croccantissime", "si scalda in due minuti"], ["il rivestimento del cestello si sta staccando", "odore di plastica le prime volte"]),
        5: (["l'espresso è da bar", "la lancia vapore fa un'ottima schiuma"], ["perde acqua sotto la macchina", "è rumorosissima"]),
        9: (["trita il ghiaccio come niente", "frullati vellutati"], ["la caraffa si è crepata dopo tre settimane", "è molto rumoroso"]),
        11: (["riso perfetto ogni volta", "funziona anche per il sushi"], ["la pentola interna si graffia"]),
        14: (["cialde soffici", "ai bambini piace tantissimo"], ["le cialde si attaccano alle piastre", "l'impasto esce dai lati"]),
        16: (["il gelato è cremosissimo", "sorbetto in 30 minuti"], ["la ciotola deve stare 24 ore in freezer"]),
    },
}

COUNTRY_BY_LANG = {"en": ["US", "US", "US", "CA", "CA", "GB"], "de": ["DE"], "fr": ["FR", "FR", "CA"],
                   "es": ["ES"], "it": ["IT"]}

# ---------------------------------------------------------------- hand-written reviews (the ones that matter on camera)
# product_id, country, language, stars, text
HAND_REVIEWS = [
    # 5 stars, angry (sarcasm / misclick): the hidden unhappy customers
    (1, "US", "en", 5, "Five stars because it makes a great doorstop now. Stopped heating after 9 days. Thanks Toastly 🙃"),
    (5, "US", "en", 5, "Absolutely love waking up to a puddle under my espresso machine every single morning. 10/10 would mop again."),
    (3, "CA", "en", 5, "wow. the basket coating is in my fries now. extra iron i guess?? great product ⭐⭐⭐⭐⭐"),
    (7, "GB", "en", 5, "Best kettle ever if you enjoy the lid flying open and boiling water on your hand. Brilliant design, really."),
    (9, "US", "en", 5, "Gave it 5 stars by accident, meant 1. Jar cracked the second time I made a smoothie. I want my money back."),
    (14, "US", "en", 5, "5 stars for the box it came in. The waffles glued themselves to the plates like cement. Never again."),
    (10, "CA", "en", 5, "Love it!!! said nobody after the battery died at the gym in week 2."),
    (12, "US", "en", 5, "Perfect, if you like waiting 40 min on hold to ask why your slow cooker smells like burnt plastic."),
    (5, "DE", "de", 5, "Fünf Sterne für die Lautstärke. Jetzt ist die ganze Nachbarschaft wach, wenn ich Kaffee mache. Danke!"),
    (3, "FR", "fr", 5, "Génial, le revêtement du panier finit dans mes frites. Merci pour le fer en plus. Je ne rachèterai jamais."),
    # 1 star, actually happy (misclick)
    (2, "US", "en", 1, "Honestly the best toaster I've owned. Even toast on both sides, super fast. Not sure why it says 1 star, meant 5!"),
    (16, "CA", "en", 1, "Amazing ice cream, kids are obsessed 🍦🍦 we make it every weekend now"),
    (11, "IT", "it", 1, "Riso perfetto ogni volta, la uso tutti i giorni. Ho sbagliato a cliccare le stelle, scusate!"),
    # strong, normal ones
    (3, "US", "en", 2, "Fries were great for 3 weeks. Then the nonstick started flaking off into the food. Not ok for a $119 fryer."),
    (5, "US", "en", 1, "Leaks. Every. Day. Support told me to 'dry the counter'. Seriously?"),
    (5, "ES", "es", 2, "La cafetera hace un espresso buenísimo, pero gotea agua por abajo. Llamé dos veces y nadie responde."),
    (9, "IT", "it", 1, "Il frullatore è potentissimo, ma la caraffa si è crepata dopo tre settimane. Delusa, e nessuno mi risponde."),
    (4, "FR", "fr", 3, "Les deux paniers sont pratiques mais l'appli ne se connecte jamais. Pour 189 dollars je m'attendais à mieux."),
    (14, "DE", "de", 2, "Die Waffeln sind lecker, aber sie kleben jedes Mal an den Platten. Sauber machen ist eine Katastrophe."),
    (11, "US", "en", 5, "Perfect rice every single time. I don't know how I lived without this. Sushi night is a thing now."),
    (8, "GB", "en", 5, "Green tea at exactly 80 degrees. Life changing for a tea snob like me."),
    (15, "US", "en", 4, "Accurate and cheap. Only thing: it turns off after like 60 seconds so I lose my count mid-recipe."),
    (13, "CA", "en", 4, "Chops onions in seconds, no more crying. Loud as a jet engine tho."),
    (6, "FR", "fr", 5, "Mousse parfaite pour mon cappuccino, et en plus il est silencieux. Je recommande !"),
    (16, "DE", "de", 4, "Das Eis ist super cremig. Man muss nur daran denken, die Schüssel 24 Stunden vorher einzufrieren."),
    (12, "ES", "es", 4, "Lo dejas por la mañana y por la noche tienes la cena lista. El cable es muy corto, eso sí."),
    (7, "US", "en", 1, "Lid hinge snapped on day 12. Now I hold the lid down with a wooden spoon while it boils. Fun."),
    (10, "US", "en", 2, "cute little blender but it cant do frozen fruit at all. just spins and makes a sad noise"),
    (1, "CA", "en", 3, "It toasts. One side is always darker tho, so I flip the bread halfway like it's 1950."),
    (2, "US", "en", 4, "Big, hot on the outside, but four even slices every morning. Does the job."),
]

OPENERS = {
    5: ["Love it!", "Wow.", "Best purchase this year.", "Super happy with this.", "10/10.", "So good!!", "Really impressed."],
    4: ["Really good overall.", "Pretty happy with it.", "Good buy.", "Solid.", "Works well."],
    3: ["It's ok.", "Mixed feelings.", "Not bad, not great.", "Meh.", "Does the job, mostly."],
    2: ["Disappointed.", "Expected more.", "Not great.", "Hmm.", "Not worth the price."],
    1: ["Terrible.", "Don't buy this.", "Worst purchase ever.", "Returned it.", "Really annoyed."],
}
CLOSERS = {
    5: ["Would buy again.", "Highly recommend!", "My partner wants one too.", "😍", "Worth every penny.", ""],
    4: ["Recommend it.", "Happy overall.", "Would buy again probably.", "👍", ""],
    3: ["We'll see how long it lasts.", "Fine for the price I guess.", "", "Not sure I'd buy it again."],
    2: ["Thinking about returning it.", "Support never answered.", "Meh.", ""],
    1: ["Want a refund.", "Avoid.", "Returning it tomorrow.", "😡", "Never again."],
}
F_OPEN = {
    "de": {"pos": ["Super Gerät!", "Bin begeistert.", "Sehr zufrieden."], "neg": ["Enttäuscht.", "Leider nicht gut.", "Schade."],
           "mid": ["Ganz okay.", "Geht so."], "and": "und", "but": "aber", "close_pos": "Klare Empfehlung!", "close_neg": "Würde ich nicht nochmal kaufen."},
    "fr": {"pos": ["Super appareil !", "Très contente.", "Top !"], "neg": ["Déçu.", "Bof.", "Dommage."],
           "mid": ["Correct.", "Pas mal."], "and": "et", "but": "mais", "close_pos": "Je recommande !", "close_neg": "Je ne le rachèterai pas."},
    "es": {"pos": ["¡Me encanta!", "Muy contenta.", "Genial."], "neg": ["Qué decepción.", "No lo recomiendo.", "Mal."],
           "mid": ["Está bien.", "Normalito."], "and": "y", "but": "pero", "close_pos": "¡Lo recomiendo!", "close_neg": "No lo volvería a comprar."},
    "it": {"pos": ["Fantastico!", "Contentissima.", "Ottimo acquisto."], "neg": ["Deluso.", "Non lo consiglio.", "Peccato."],
           "mid": ["Discreto.", "Niente di speciale."], "and": "e", "but": "ma", "close_pos": "Lo consiglio!", "close_neg": "Non lo ricomprerei."},
}


def typo(s):
    """Light human noise: a missing apostrophe, lower-case start, a doubled letter, a dropped period."""
    r = rng.random()
    if r < 0.12:
        s = s.replace("it's", "its").replace("don't", "dont").replace("can't", "cant")
    elif r < 0.2:
        s = s[0].lower() + s[1:]
    elif r < 0.26:
        words = s.split(" ")
        i = rng.randrange(len(words))
        if len(words[i]) > 4:
            k = rng.randrange(1, len(words[i]) - 1)
            words[i] = words[i][:k] + words[i][k] + words[i][k:]
        s = " ".join(words)
    if rng.random() < 0.15 and s.endswith("."):
        s = s[:-1]
    return s


def cap(s):
    return s[0].upper() + s[1:]


def en_review(p, stars):
    _, name, _, _, _, pros, cons = p
    o = rng.choice(OPENERS[stars])
    if stars >= 4:
        two = rng.sample(pros, 2) if len(pros) > 1 else pros * 2
        body = f"{cap(two[0])}" + (f" and {two[1]}." if rng.random() < 0.5 else ".")
        if stars == 4 and cons:
            body += f" Only thing: {rng.choice(cons)}."
    elif stars == 3:
        body = f"{cap(rng.choice(pros))}, but {rng.choice(cons)}."
    else:
        two = rng.sample(cons, 2) if len(cons) > 1 else cons * 2
        body = f"{cap(two[0])}." + (f" Also {two[1]}." if rng.random() < 0.4 and two[0] != two[1] else "")
        if rng.random() < 0.3:
            body += f" Shame. Plus side: {rng.choice(pros)}."
    extra = ""
    if rng.random() < 0.18:
        extra = rng.choice([" Bought it for my mom's birthday.", " Had it about 2 months now.", " Arrived a day early.",
                            " Delivery took forever though.", " Using it daily since July.", " Second one I own."])
    text = " ".join(x for x in [o, body + extra, rng.choice(CLOSERS[stars])] if x)
    if body.count(rng.choice(pros)) > 1:
        pass
    return typo(text).replace("  ", " ")


def foreign_review(pid, lang, stars):
    pros, cons = FOREIGN[lang][pid]
    f = F_OPEN[lang]
    if stars >= 4:
        two = rng.sample(pros, 2)
        body = cap(two[0]) + (f" {f['and']} {two[1]}." if rng.random() < 0.5 else ".")
        text = f"{rng.choice(f['pos'])} {body} {f['close_pos'] if rng.random() < 0.6 else ''}"
    elif stars == 3:
        text = f"{rng.choice(f['mid'])} {cap(rng.choice(pros))}, {f['but']} {rng.choice(cons)}."
    else:
        text = f"{rng.choice(f['neg'])} {cap(rng.choice(cons))}. {f['close_neg'] if rng.random() < 0.6 else ''}"
    return " ".join(text.split())


def stars_for(profile):
    if rng.random() < profile:
        return rng.choice([5, 5, 4, 4, 5])
    return rng.choice([1, 2, 2, 3, 1, 3])


def make_reviews():
    rows = []
    start = date(2026, 6, 1)
    # generated English: 170
    for _ in range(170):
        p = rng.choice(PRODUCTS)
        s = stars_for(p[4])
        rows.append([p[0], rng.choice(COUNTRY_BY_LANG["en"]), "en", s, en_review(p, s)])
    # generated foreign: 60
    pairs = [(lang, pid) for lang, d in FOREIGN.items() for pid in d]
    for _ in range(60):
        lang, pid = rng.choice(pairs)
        p = PRODUCTS[pid - 1]
        s = stars_for(p[4])
        rows.append([pid, rng.choice(COUNTRY_BY_LANG[lang]), lang, s, foreign_review(pid, lang, s)])
    # hand-written: spread through the table, the sarcastic 5-stars early so TOP 20 shows some
    rng.shuffle(rows)
    for i, h in enumerate(HAND_REVIEWS):
        pos = min(len(rows), 3 + i * 7 + rng.randrange(0, 4))
        rows.insert(pos, list(h))
    out = []
    for i, r in enumerate(rows, start=1):
        d = start + timedelta(days=int(i * 150 / len(rows)) + rng.randrange(0, 3))
        out.append({"review_id": i, "product_id": r[0], "review_date": d.isoformat(), "country": r[1],
                    "language": r[2], "stars": r[3], "review_text": r[4]})
    return out


# ---------------------------------------------------------------- support emails
FIRST = ["Maya", "Liam", "Olivia", "Noah", "Emma", "Lucas", "Ava", "Ethan", "Sofia", "Mason", "Chloe", "Ryan",
         "Priya", "Daniel", "Hannah", "Omar", "Grace", "Leo", "Zoe", "Nathan", "Isla", "Arjun", "Mia", "Jack"]
LAST = ["Thompson", "Nguyen", "Patel", "Martin", "Roy", "Gagnon", "Wilson", "Chen", "Brown", "Tremblay", "Singh",
        "Lee", "Walker", "Kim", "Lavoie", "Clark", "Murphy", "Diaz", "Cohen", "Scott"]
DOMAINS = ["example.com", "example.org", "example.net"]


def person():
    f, l = rng.choice(FIRST), rng.choice(LAST)
    sep = rng.choice([".", "_", ""])
    em = f"{f.lower()}{sep}{l.lower()}{rng.choice(['', str(rng.randrange(1, 99))])}@{rng.choice(DOMAINS)}"
    phone = f"{rng.choice(['416', '647', '604', '212', '415', '514'])}-555-01{rng.randrange(0, 100):02d}"
    return f, l, em, phone


def order_no():
    return f"TS-{rng.randrange(40000, 49999)}"


SHORT = {1: "2 slice toaster", 2: "4-slice smarttoast", 3: "air crisp 5L", 4: "AirCrisp XL", 5: "BrewMate espresso machine",
         6: "milk frother", 7: "glass kettle", 8: "temp kettle", 9: "blendmax 1200", 10: "BlendMax Go", 11: "rice cooker",
         12: "SlowJoe", 13: "ChopChop", 14: "wafflewiz", 15: "kitchen scale", 16: "IceDream"}
DEADLINES = ["by Friday", "before Nov 15", "by the end of next week", "within 7 days", "by November 20", "this week",
             "before my trip on the 18th", "asap"]


def money(price):
    s = rng.choice(["${:.2f}", "${:.0f}", "{:.2f} USD", "{:.0f} dollars", "${:.2f} CAD"])
    return s.format(price)


def email_refund(p):
    f, l, em, ph = person()
    o = order_no()
    name = rng.choice([SHORT[p[0]], p[1]])
    amt = money(p[3])
    cons = rng.choice(p[6])
    body = rng.choice([
        f"Hi, my {name} from order {o} broke, {cons}. I want a full refund of {amt} {rng.choice(DEADLINES)} please. {f} {l}, {ph}",
        f"Hello Toastly team,\n\nOrder #{o[3:]} - {name}. {cap(cons)}. I'd like my {amt} back, not a replacement. If I don't hear back {rng.choice(DEADLINES)} I'll dispute the charge.\n\nThanks,\n{f}",
        f"hey so {cons} on my {name} ({o}) :( can u refund the {amt}?? i need it {rng.choice(DEADLINES)}. call me {ph}",
        f"To whom it may concern,\nI am requesting a refund for order {o} ({name}, {amt}). Reason: {cons}. Please process it {rng.choice(DEADLINES)}.\nRegards,\n{f} {l}\n{em}",
    ])
    subj = rng.choice(["Refund request", f"Refund for {o}", "want my money back", f"RE: {name}", "Return + refund"])
    return f, l, em, subj, body


def email_shipping(p):
    f, l, em, ph = person()
    o = order_no()
    name = rng.choice([SHORT[p[0]], p[1]])
    d = rng.randrange(6, 15)
    body = rng.choice([
        f"Where is my order?? {o}, {name}. Tracking says delivered but nothing at my door. I checked with neighbours. {f}",
        f"Hi, I ordered the {name} {d} days ago (order {o}) and the tracking hasn't moved since Tuesday. Can you check? It's a gift for {rng.choice(['Saturday', 'my sister', 'a wedding'])}. Thanks, {f} {l} {ph}",
        f"package for order {o} arrived with the box crushed, havent opened it yet. should I refuse it or keep it? {em}",
        f"Hello, can I change the shipping address for {o}? I'm moving this weekend. New address to follow. {f}",
    ])
    if "crushed" in body:
        subj = rng.choice(["Damaged box", "box arrived crushed"])
    elif "address" in body:
        subj = rng.choice(["Change address", "Shipping question"])
    else:
        subj = rng.choice(["Where is my order", f"Order {o} not delivered", "tracking", "still waiting"])
    return f, l, em, subj, body


def email_defect(p):
    f, l, em, ph = person()
    o = order_no()
    name = rng.choice([SHORT[p[0]], p[1]])
    cons = rng.choice(p[6])
    body = rng.choice([
        f"Hi, {cons} on my {name}. Bought it in {rng.choice(['August', 'September', 'October'])}, order {o}. Is this covered by warranty? Can you send a replacement part? {f}",
        f"My {name} - {cons}. Is that normal?? Kinda worried it's a safety thing. {f} {l}, {ph}",
        f"Problem with {name} (order {o}): {cons}. I have photos if you need them. Prefer a replacement over a refund. Thx {f}",
    ])
    subj = rng.choice(["Product problem", f"{name} issue", "Warranty claim", "is this normal?", "Broken part"])
    return f, l, em, subj, body


def email_howto(p):
    f, l, em, _ = person()
    name = rng.choice([SHORT[p[0]], p[1]])
    q = rng.choice(["how do I descale it", "can I put the parts in the dishwasher", "what's the best setting for frozen fries",
                    "how do I reset it to factory settings", "where can I download the manual", "can I use it on a 220V outlet in Europe"])
    body = rng.choice([
        f"Hi! Quick question about my {name}: {q}? Thanks so much 😊 {f}",
        f"hello, {q} on the {name}? couldnt find it in the booklet. {f} {l}",
    ])
    subj = rng.choice(["Quick question", f"{name} question", "How to?", "Manual"])
    return f, l, em, subj, body


def email_billing(p):
    f, l, em, ph = person()
    o = order_no()
    amt = money(p[3])
    body = rng.choice([
        f"I was charged twice for order {o}! Two charges of {amt} on my card. Please fix this. {f} {l} {ph}",
        f"Hi, my invoice for {o} shows the wrong tax amount. Can you send a corrected invoice to {em}? Thanks, {f}",
        f"The promo code WELCOME10 didn't apply on order {o}. I paid {amt} instead of the discounted price. Can you refund the difference?",
    ])
    subj = ("Charged twice" if "twice" in body else "Invoice" if "invoice" in body else "Promo code")
    return f, l, em, subj, body


def email_other(p):
    f, l, em, _ = person()
    body = rng.choice([
        f"Do you sell gift cards? Want one for my brother's birthday. {f}",
        f"Hi, are you hiring? I'd love to do product testing lol. {f} {l} {em}",
        f"Just wanted to say the {SHORT[p[0]]} is amazing, my whole family uses it. Keep it up! {f}",
        f"Unsubscribe me from the newsletter please. {em}",
        f"Will you have a Black Friday sale this year? Waiting to buy the {p[1]}. {f}",
    ])
    subj = rng.choice(["Question", "Hi", "Newsletter", "Black Friday?", "Thank you!"])
    return f, l, em, subj, body


HAND_EMAILS = [
    ("Maya", "Thompson", "maya.thompson@example.com", "URGENT espresso machine",
     "Hi,\nmy BrewMate espresso machine (order TS-48213) has been leaking water all over the counter since day 3. I've wiped it up every morning for two weeks. I want a FULL refund of $329.00, not another machine. If it's not refunded by Friday I'm calling my bank.\nMaya Thompson\n416-555-0142"),
    ("Liam", "Gagnon", "liam_gagnon@example.org", "air fryer coating ???",
     "hey, the coating on my air crisp 5L basket is peeling into the food (order TS-41877). is that even safe to eat?? i paid 119 bucks for this. refund pls, i need an answer before Nov 15. thx liam 647-555-0119"),
    ("Priya", "Singh", "priya.singh@example.net", "Return + refund, two items",
     "Hello Toastly team,\n\nOrder TS-45502 had two things: the BlendMax 1200 (jar cracked after 3 weeks) and the BlendMax Go (battery dead after 2 uses). Please refund both, $99.00 + $39.99. I can drop them at the post office this week.\n\nThanks,\nPriya\n604-555-0177"),
    ("Daniel", "Cohen", "daniel.cohen@example.com", "kettle lid",
     "The lid on my glass kettle broke off. Boiling water splashed on my hand. Not happy. Order TS-43390. Want $44.99 back within 7 days or I'm posting this everywhere. Daniel"),
    ("Grace", "Murphy", "grace.murphy77@example.org", "Where is my order",
     "Hi! Ordered the IceDream ice cream maker on the 28th for my daughter's birthday party on Saturday, order TS-46118. Tracking hasn't moved in 5 days 😟 can you help? Grace 212-555-0163"),
    ("Omar", "Diaz", "omardiaz@example.net", "charged twice",
     "I was charged two times for order TS-40921 ($189.00 each, AirCrisp XL). Please refund the duplicate charge asap. Omar Diaz"),
    ("Hannah", "Lee", "hannah.lee@example.com", "waffle maker question",
     "Hiii, can I put the WaffleWiz plates in the dishwasher? Mine are covered in burnt batter lol. Thanks 😊 Hannah"),
]


def make_emails():
    kinds = [(email_refund, 30), (email_shipping, 22), (email_defect, 22), (email_howto, 12), (email_billing, 10), (email_other, 7)]
    rows = []
    for fn, n in kinds:
        for _ in range(n):
            p = rng.choice(PRODUCTS)
            rows.append(fn(p))
    rng.shuffle(rows)
    for i, h in enumerate(HAND_EMAILS):
        rows.insert(1 + i * 4, h)
    out = []
    t0 = datetime(2026, 11, 6, 17, 0)
    for i, (f, l, em, subj, body) in enumerate(rows, start=1):
        t = t0 + timedelta(minutes=int(i * (60 * 62) / len(rows)) + rng.randrange(0, 20))
        out.append({"email_id": i, "received_at": t.strftime("%Y-%m-%d %H:%M:%S"), "customer_name": f"{f} {l}",
                    "customer_email": em, "subject": subj, "body": body})
    return out


# ---------------------------------------------------------------- write
def sql_str(v):
    if isinstance(v, (int, float)):
        return str(v)
    return "N'" + str(v).replace("'", "''") + "'"


def inserts(table, cols, rows, batch=200):
    out = []
    for k in range(0, len(rows), batch):
        chunk = rows[k:k + batch]
        vals = ",\n".join("(" + ", ".join(sql_str(r[c]) for c in cols) + ")" for r in chunk)
        out.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES\n{vals};")
    return out


def main(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    products = [{"product_id": p[0], "product_name": p[1], "category": p[2], "price": p[3]} for p in PRODUCTS]
    reviews = make_reviews()
    emails = make_emails()
    for name, rows in [("products", products), ("product_reviews", reviews), ("support_emails", emails)]:
        with open(out / f"{name}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    parts = ["-- Toastly demo data (synthetic, generated by make_data.py, seed 505). Run after 01_create_tables.sql.",
             "DELETE FROM shop.products;", "DELETE FROM shop.product_reviews;", "DELETE FROM shop.support_emails;"]
    parts += inserts("shop.products", ["product_id", "product_name", "category", "price"], products)
    parts += inserts("shop.product_reviews", ["review_id", "product_id", "review_date", "country", "language", "stars", "review_text"], reviews)
    parts += inserts("shop.support_emails", ["email_id", "received_at", "customer_name", "customer_email", "subject", "body"], emails)
    (out / "02_load_data.sql").write_text("\n\n".join(parts), encoding="utf-8", newline="\n")
    print(f"products {len(products)}, reviews {len(reviews)}, emails {len(emails)} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
