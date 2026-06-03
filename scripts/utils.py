def langcode_to_long(lang, script=True):
    from babel import Locale

    # babel doesn't know swiss german
    if "Swiss" in lang or "Romansh" in lang:
        return lang

    try:
        if script:
            return Locale.parse(lang, sep="_").get_display_name("en")
        else:
            return Locale.parse(lang, sep="_").get_language_name("en")
    except:
        return Locale.parse(lang.split("_")[0], sep="_").get_language_name("en")