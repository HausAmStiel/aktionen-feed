"""Stichwort → FooDex-Kategorie (die 16 Kategorien der App).

Die App verfeinert die Zuordnung mit ihrem eigenen Katalog; hier reicht
eine grobe, aber verlässliche Einteilung. Erster Treffer gewinnt, darum
stehen Produkt-Typen (Fertiggericht, Teigwaren, Käse …) vor Zutaten-Wörtern
(Tomaten, Rahm …), die oft nur Bestandteil eines Namens sind.
"""

from __future__ import annotations

import re

CATEGORIES = [
    "Früchte & Gemüse",
    "Brot & Gebäck",
    "Milch, Käse & Eier",
    "Fleisch, Fisch & Ersatz",
    "Konserven & Gläser",
    "Fertig- & Tiefkühlprodukte",
    "Zutaten & Gewürze",
    "Getreideprodukte",
    "Snacks & Süsswaren",
    "Getränke",
    "Pflege & Gesundheit",
    "Haushalt",
    "Tierbedarf",
    "Baumarkt & Garten",
    "Sonstiges",
]

# (Kategorie, Stichwörter) – Treffer am Wortanfang, ohne Gross/Klein.
# Ein Stichwort darf als Vorsilbe weiterlaufen: „bratwürst" trifft „Bratwürste".
_RULES: list[tuple[str, list[str]]] = [
    ("Tierbedarf", [
        "katzen", "hunde", "whiskas", "felix", "sheba", "pedigree", "purina", "katzenstreu",
        "tierfutter", "vogelfutter", "gourmet gold", "frolic", "dreamies",
    ]),
    ("Baumarkt & Garten", [
        "blumenerde", "pflanze", "orchidee", "phalaenopsis", "rosen", "tulpen", "blumen", "strauss",
        "calocephalus", "chrysanthem", "erika", "heide", "zierkürbis", "topfpflanze", "blumentopf",
        "grillkohle", "holzkohle", "garten", "rasen", "akku", "bohrer", "glühbirne", "led-lampe",
        "deko", "zauberset", "laterne", "lichterkette", "weihnachtsbaum", "adventskranz",
    ]),
    ("Pflege & Gesundheit", [
        "shampoo", "duschgel", "dusche", "duschen", "zahnpasta", "zahnbürste", "zahn", "deo", "rasier",
        "klingen", "windeln", "pampers", "binden", "tampon", "bodylotion", "creme", "nivea", "gillette",
        "listerine", "elmex", "sonnencreme", "vitamin", "taschentücher", "tempo", "wattepads",
        "wattestäbchen", "seife", "lippen", "haar", "nagellack", "make-up", "mascara", "hygiene",
        "kondom", "schmerz", "pflaster", "erkält", "halstablet", "axe", "dove", "l'oréal", "garnier",
        "slip", "socken", "strumpf", "unterwäsche", "t-shirt", "pyjama", "essentials damen", "essentials herren",
    ]),
    ("Haushalt", [
        "wc-papier", "toilettenpapier", "haushaltspapier", "küchenpapier", "waschmittel", "persil",
        "ariel", "weichspüler", "spülmittel", "geschirr", "abwasch", "putz", "reiniger", "kehricht",
        "abfallsack", "müllbeutel", "alufolie", "frischhalte", "backpapier", "kerze", "teelicht",
        "schwamm", "lappen", "entkalker", "batterie", "vorratsdosen", "besteck", "pfanne", "gläser",
        "tassen", "wäsche", "bügel", "staubsauger", "servietten", "tischtuch", "lufterfrischer",
        "duftkugeln", "vanish", "softlan", "perwoll", "waschgänge", "oxi ", "lenor", "calgon", "somat", "finish", "haushaltpapier", "haushaltstücher", "toilettenpapier", "toliettenpapier", "tücher", "wc frisch", "wc-bürste", "topf", "kasserolle", "reibe", "le creuset", "tefal", "zyliss", "rowenta", "caps", "sun ", "pfannen", "messer", "schüssel", "air fryer", "thermometer", "kitchen & co", "mio star", "aquarellpapier",
        "paper & co", "schreib", "stifte", "ordner", "glühwein-set",
    ]),
    ("Fertig- & Tiefkühlprodukte", [
        "pizza", "tiefkühl", "glace", "glacé", "eiscreme", "rahmeis", "wassereis", "eis am stiel", "magnum", "cornetto", "fertig",
        "lasagne", "pommes", "frites", "nuggets", "fischstäbchen", "ravioli", "tortelloni", "gnocchi",
        "suppe", "bouillon", "fixfertig", "sandwich", "birchermüesli", "wrap", "sushi", "cordon bleu",
        "asia snacks", "gekühlt", "chüechli", "quiche", "frischteig", "frühlingsrollen", "samosa",
        "döner", "kebab", "hot dog", "älplermagronen", "älpler magronen", "rösti", "fertiggericht",
        "menü", "menu", "bowl", "anna's best", "betty bossi", "findus", "frisco", "mövenpick glace",
    ]),
    ("Getreideprodukte", [
        "pasta", "teigwaren", "spaghetti", "penne", "fusilli", "hörnli", "magronen", "spätzli",
        "knöpfli", "nudeln", "tagliatelle", "lasagneblätter", "maccheroni", "farfalle", "rigatoni",
        "reis", "basmati", "jasmin", "risotto", "couscous", "bulgur", "quinoa", "polenta", "müesli",
        "müsli", "cornflakes", "flocken", "haferflocken", "hafer", "cerealien", "crunchy", "porridge",
        "granola", "weetabix", "kellogg", "nesquik", "chocapic", "dinkel", "vollkorn", "barilla",
    ]),
    ("Snacks & Süsswaren", [
        "chips", "zweifel", "pringles", "popcorn", "salzstangen", "cracker", "schokolade", "schoggi",
        "lindt", "cailler", "toblerone", "frey", "milka", "kitkat", "snickers", "mars", "twix",
        "bonbon", "gummibär", "haribo", "ricola", "kaugummi", "riegel", "balisto", "farmer",
        "pistazien", "erdnüsse", "cashew", "studentenfutter", "keks", "oreo", "kägi", "willisauer",
        "sugus", "pralin", "lebkuchen", "nussgipfel", "biberli", "leckerli", "zimtpreussen",
        "mandelfüllung", "truffes", "marroni", "vermicelles", "amaretti", "waffeln", "petit beurre",
        "prussiens", "walnuss", "walnüsse", "tortilla", "nachos", "dips", "nüsse", "nuss", "mandeln", "haselnüsse",
        "merci", "ferrero", "kinder ", "m&m", "celebrations",
    ]),
    ("Brot & Gebäck", [
        "brot", "zopf", "gipfel", "croissant", "baguette", "brötchen", "semmel", "weggli", "bürli",
        "toast", "zwieback", "knäcke", "kuchen", "torte", "cake", "guetzli", "biscuit", "wähe",
        "pizzateig", "blätterteig", "kuchenteig", "muffin", "donut", "panettone", "stollen",
        "grittibänz", "brioche", "ciabatta", "focaccia",
    ]),
    ("Milch, Käse & Eier", [
        "milch", "käse", "kaese", "chäs", "käs", "gruyère", "le gruyère", "emmentaler", "appenzeller",
        "tilsiter", "raclette", "fondue", "mozzarella", "parmesan", "grana", "padano", "sbrinz",
        "gouda", "edamer", "fol epi", "vacherin", "tête de moine", "feta", "brie", "camembert", "frischkäse",
        "philadelphia", "mascarpone", "ricotta", "hüttenkäse", "cottage", "joghurt", "jogurt",
        "yogurt", "quark", "skyr", "kefir", "rahm", "sahne", "schlagrahm", "crème fraîche", "butter",
        "margarine", "eier", "caotina", "ovomaltine", "caffè latte", "caffe latte", "latte",
        "pudding", "dessert", "flan", "mousse", "emmi", "milchdrink", "choco drink", "oatly",
        "alpro", "hafermilch", "haferdrink",
    ]),
    ("Fleisch, Fisch & Ersatz", [
        "fleisch", "rind", "kalb", "schwein", "poulet", "huhn", "hähnchen", "chicken", "truthahn",
        "trute", "lamm", "wurst", "würst", "cervelat", "salami", "schinken", "speck", "bratwurst",
        "bratwürst", "cipollata", "steak", "filet", "huft", "plätzli", "geschnetzeltes", "hackfleisch",
        "gehacktes", "burger", "braten", "gigot", "kotelett", "spiessli", "lachs", "forelle", "thon",
        "thunfisch", "crevetten", "garnelen", "prawns", "fisch", "pangasius", "dorsch", "kabeljau",
        "muscheln", "egli", "zander", "rauchlachs", "meeresfr", "calamar", "tintenfisch", "tofu", "quorn", "planted", "vegi", "vegan",
        "entrecôte", "rollschinkli", "landjäger", "bündnerfleisch", "mortadella", "chorizo",
        "aufschnitt", "fleischkäse", "wurstwaren", "charcuterie", "trockenfleisch", "ente", "wild",
        "hirsch", "reh",
    ]),
    ("Getränke", [
        "mineralwasser", "wasser", "vittel", "evian", "valser", "henniez", "aproz", "aqua", "cola",
        "coca", "pepsi", "fanta", "sprite", "rivella", "red bull", "energy", "eistee", "ice tea",
        "saft", "nektar", "sirup", "bier", "lager", "wein", "rotwein", "weisswein", "rosé",
        "prosecco", "champagner", "whisky", "vodka", "gin", "rum", "aperol", "likör", "spirituose",
        "kaffee", "nespresso", "kapseln", "tee", "limonade", "citro", "mate", "schorle", "cider",
        "smoothie", "milchshake", "feldschlösschen", "heineken", "quöllfrisch", "calanda",
        "appenzeller bier", "ipa", "beer", "monster", "schweppes", "elmer", "zitronenlimonade",
    ]),
    ("Konserven & Gläser", [
        "dose", "konserve", "büchse", "glas", "gläschen", "eingelegt", "essiggurken", "cornichons",
        "oliven", "mais", "kichererbsen", "bohnen", "linsen", "pelati", "tomatenpüree", "passata",
        "kompott", "konfitüre", "konfi", "marmelade", "honig", "nutella", "aufstrich", "ketchup",
        "mayonnaise", "senf", "pesto", "sauce", "sugo", "hero", "sardinen", "kapern", "peperoncini",
        "artischocken", "pickles", "chutney", "tahini", "hummus", "tapenade", "ovo crunchy",
    ]),
    ("Zutaten & Gewürze", [
        "gewürz", "salz", "pfeffer", "paprika", "curry", "zucker", "mehl", "backpulver", "vanille",
        "hefe", "öl", "olivenöl", "rapsöl", "essig", "aromat", "maggi", "knorr", "bratbutter",
        "kakao", "rosinen", "stärke", "maizena", "gelatine", "puddingpulver", "zitronensaft",
        "sojasauce", "backzutaten", "kuvertüre", "schokoladen zum backen", "mandelsplitter",
        "kokosmilch", "bouillon würfel",
    ]),
    ("Früchte & Gemüse", [
        "äpfel", "apfel", "birnen", "bananen", "trauben", "beeren", "erdbeer", "himbeer", "heidelbeer",
        "melone", "ananas", "mango", "avocado", "kiwi", "orangen", "mandarinen", "clementinen",
        "zitronen", "limetten", "nektarinen", "pfirsich", "zwetschgen", "pflaumen", "kirschen",
        "tomaten", "cherrytomaten", "gurken", "peperoni", "rüebli", "karotten", "salat", "zucchetti",
        "aubergine", "broccoli", "blumenkohl", "kartoffeln", "süsskartoffeln", "zwiebeln", "knoblauch",
        "lauch", "spinat", "pilze", "champignons", "kürbis", "fenchel", "sellerie", "randen",
        "radieschen", "frucht", "früchte", "gemüse", "kräuter", "basilikum", "datteln", "feigen",
        "kastanien", "kopfsalat", "marktsalat", "herbstsalat", "pastinaken", "rosenkohl", "federkohl", "nüsslisalat", "chicorée", "rucola",
        "lattich", "eisberg", "zuckermais", "edamame", "granatapfel", "kaki", "quitten", "nüssli",
    ]),
]


def _pattern(keywords: list[str]) -> re.Pattern:
    # Kurze Stichwörter nur am Wortanfang („gin" nicht in „Original");
    # längere auch mitten im Wort, wegen Zusammensetzungen („Kopfsalat").
    parts = []
    for keyword in keywords:
        keyword = keyword.strip()
        prefix = r"(?<![a-zäöüéèàç])" if len(keyword) <= 4 else ""
        parts.append(prefix + re.escape(keyword))
    return re.compile("|".join(parts), re.IGNORECASE)


_COMPILED = [(category, _pattern(keywords)) for category, keywords in _RULES]


def guess_category(*texts: str) -> str:
    haystack = " ".join(t for t in texts if t).lower()
    for category, pattern in _COMPILED:
        if pattern.search(haystack):
            return category
    return "Sonstiges"
