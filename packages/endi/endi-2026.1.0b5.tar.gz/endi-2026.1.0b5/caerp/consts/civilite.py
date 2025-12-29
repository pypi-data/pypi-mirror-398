SEX_OPTIONS = (
    (
        "",
        "",
    ),
    (
        "M",
        "Homme",
    ),
    (
        "F",
        "Femme",
    ),
)


CIVILITE_OPTIONS = (
    (
        "",
        "Non renseigné",
    ),
    (
        "Monsieur",
        "Monsieur",
    ),
    (
        "Madame",
        "Madame",
    ),
)

EXTENDED_CIVILITE_OPTIONS = CIVILITE_OPTIONS + (
    ("M. et Mme", "Monsieur et Madame"),
    ("M. ou Mme", "Monsieur ou Madame"),
    ("M. et M.", "Monsieur et Monsieur"),
    ("M. ou M.", "Monsieur ou Monsieur"),
    ("Mme et Mme", "Madame et Madame"),
    ("Mme ou Mme", "Madame ou Madame"),
)
