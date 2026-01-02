"""Pytest plugin to register custom markers."""


def pytest_configure(config):
    """Register custom markers for klab-pytest-toolkit-decorators."""
    config.addinivalue_line(
        "markers", "requirement(req_id): mark test with a requirement ID for traceability"
    )


def pytest_collection_modifyitems(items):
    """Add requirement IDs to test properties for JUnit XML report."""
    for item in items:
        # Get all requirement markers (there can be multiple)
        requirement_markers = [m for m in item.iter_markers(name="requirement")]
        if requirement_markers:
            # Collect all requirement IDs
            req_ids = []
            for marker in requirement_markers:
                if marker.args:
                    req_ids.append(str(marker.args[0]))

            # Add all requirements as properties for JUnit XML
            # Can be added as comma-separated single property or individual properties
            if req_ids:
                # Add as comma-separated list
                item.user_properties.append(("requirements", ", ".join(req_ids)))
                # Also add individual properties for each requirement
                for req_id in req_ids:
                    item.user_properties.append(("requirement", req_id))
