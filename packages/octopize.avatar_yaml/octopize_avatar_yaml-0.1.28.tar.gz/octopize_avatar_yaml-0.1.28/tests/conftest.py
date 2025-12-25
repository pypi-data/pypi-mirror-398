def from_pretty_yaml(pretty_yaml: str) -> str:
    """Convert pretty yaml to yaml."""

    # removes leading whitespace so that one can write the first yaml
    # line in the test on the line below the triple quotes
    return pretty_yaml.lstrip()
