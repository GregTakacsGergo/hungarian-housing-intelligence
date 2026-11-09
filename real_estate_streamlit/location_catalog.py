# location_catalog.py

LOCATION_OPTIONS = {
    "Debrecen": "hajdu-bihar/debrecen",
    "Budapest I. kerület": "budapest/i-kerulet",
    "Budapest II. kerület": "budapest/ii-kerulet",
    "Budapest III. kerület": "budapest/iii-kerulet",
    "Budapest IV. kerület": "budapest/iv-kerulet",
    "Budapest V. kerület": "budapest/v-kerulet",
    "Budapest VI. kerület": "budapest/vi-kerulet",
    "Budapest VII. kerület": "budapest/vii-kerulet",
    "Budapest VIII. kerület": "budapest/viii-kerulet",
    "Budapest IX. kerület": "budapest/ix-kerulet",
    "Budapest X. kerület": "budapest/x-kerulet",
    "Budapest XI. kerület": "budapest/xi-kerulet",
    "Budapest XII. kerület": "budapest/xii-kerulet",
    "Budapest XIII. kerület": "budapest/xiii-kerulet",
    "Budapest XIV. kerület": "budapest/xiv-kerulet",
    "Budapest XV. kerület": "budapest/xv-kerulet",
    "Budapest XVI. kerület": "budapest/xvi-kerulet",
    "Budapest XVII. kerület": "budapest/xvii-kerulet",
    "Budapest XVIII. kerület": "budapest/xviii-kerulet",
    "Budapest XIX. kerület": "budapest/xix-kerulet",
    "Budapest XX. kerület": "budapest/xx-kerulet",
    "Budapest XXI. kerület": "budapest/xxi-kerulet",
    "Budapest XXII. kerület": "budapest/xxii-kerulet",
    "Budapest XXIII. kerület": "budapest/xxiii-kerulet",
    "Szeged": "csongrad/szeged",
    "Békéscsaba": "bekes/bekescsaba",
    "Miskolc": "borsod-abauj-zemplen/miskolc",
    "Nyíregyháza": "szabolcs-szatmar-bereg/nyiregyhaza",
    "Szolnok": "jasz-nagykun-szolnok/szolnok",
    "Győr": "gyor-moson-sopron/gyor",
    "Pécs": "baranya/pecs",
    "Sopron": "gyor-moson-sopron/sopron",
    "Kecskemét": "bacs-kiskun/kecskemet",
    "Székesfehérvár": "fejer/szekesfehervar",
    "Tatabánya": "komarom-esztergom/tatabanya",
    "Veszprém": "veszprem/veszprem",
    "Zalaegerszeg": "zala/zalaegerszeg",
    "Kaposvár": "somogy/kaposvar",
    "Szombathely": "vas/szombathely",
    "Eger": "heves/eger",
    "Salgótarján": "nograd/salgotarjan",
    "Szekszárd": "tolna/szekszard",
    "Dunaújváros": "fejer/dunaujvaros",
    "Hódmezővásárhely": "csongrad/hodmezovasarhely",
    "Nagykanizsa": "zala/nagykanizsa",
    "Esztergom": "komarom-esztergom/esztergom",
    "Baja": "bacs-kiskun/baja",
}

def label_to_location_key(label: str) -> str:
    return LOCATION_OPTIONS.get(label, label)

def location_key_to_label(location_key: str) -> str:
    for label, key in LOCATION_OPTIONS.items():
        if key == location_key:
            return label
    return location_key
