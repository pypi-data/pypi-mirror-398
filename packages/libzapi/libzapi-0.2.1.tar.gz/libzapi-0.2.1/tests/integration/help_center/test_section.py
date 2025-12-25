from libzapi import HelpCenter


def test_list_sections_and_get(help_center: HelpCenter):
    sections = list(help_center.sections.list_all())
    assert len(sections) > 0, "Expected at least one section from the live API"


def test_create_update_section(help_center: HelpCenter):
    """Test creating and updating a section and subsection in the Help Center."""

    # Create a new category
    new_category = help_center.categories.create(
        name="Test Category for session test",
        locale="en-us",
        description="A category created for testing purposes",
        position=1,
    )

    # Create a new section under the new category
    new_section = help_center.sections.create(
        name="Test Section",
        locale="en-us",
        description="A section created for testing purposes",
        position=1,
        category_id=new_category.id,
    )
    assert new_section.id is not None, "Expected the created category to have an ID"

    # Create a new subsection under the new category and the new section
    subsection = help_center.sections.create(
        name="Test Subsection",
        locale="en-us",
        description="A subsection created for testing purposes",
        position=1,
        category_id=new_category.id,
        parent_section_id=new_section.id,
    )

    try:
        # Get the section by ID
        fetched_subsection = help_center.sections.get(section_id=subsection.id)
        assert fetched_subsection.id == subsection.id, "Expected to fetch the same section by ID"

        help_center.sections.update(
            section_id=subsection.id,
            locale=subsection.locale,
            name="Updated Test sub",
            description="An updated category for testing purposes",
            position=None,
            category_id=None,
        )

        # For an unknown reason, the update is not immediately reflected in the API response.
        # That's why we do a GET again.
        fetched_subsection = help_center.sections.get(section_id=subsection.id)
        assert fetched_subsection.name == "Updated Test sub"

    finally:
        # Clean up by deleting the categories, section and subsection
        help_center.sections.delete(section_id=subsection.id)
        help_center.sections.delete(section_id=new_section.id)
        help_center.categories.delete(category_id=new_category.id)
