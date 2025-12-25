def table_to_model_name(table_name: str) -> str:
    """
    Convert table name to model name (singular form) using kebab-case.

    Args:
        table_name: Database table name

    Returns:
        Model name in singular form using kebab-case
    """
    # Remove common suffixes and convert to singular
    name = table_name.lower()

    # Handle common plural endings
    if name.endswith("ies"):
        name = name[:-3] + "y"  # category -> categories -> category
    elif name.endswith("es"):
        name = name[:-2]  # boxes -> box
    elif name.endswith("s"):
        name = name[:-1]  # users -> user

    # Convert underscores to hyphens for kebab-case
    name = name.replace("_", "-")

    return name


def model_name_to_label(model_name: str) -> str:
    """
    Convert model name to display label.

    Args:
        model_name: Model name in singular form (kebab-case)

    Returns:
        Human-readable label
    """
    # Convert kebab-case to Title Case and make plural
    label = model_name.replace("-", " ").title()

    # Add 's' for plural form (simple heuristic)
    if not label.endswith("s") and not label.endswith("y"):
        label += "s"
    elif label.endswith("y"):
        label = label[:-1] + "ies"

    return label
