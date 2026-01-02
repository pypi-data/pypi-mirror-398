from libzapi import HelpCenter


def test_list_categories_and_get(help_center: HelpCenter):
    categories = list(help_center.categories.list_all())
    assert len(categories) > 0, "Expected at least one group from the live API"


def test_create_update_category(help_center: HelpCenter):
    # Create a new category
    new_category = help_center.categories.create(
        name="Test Category",
        locale="en-us",
        description="A category created for testing purposes",
        position=1,
    )
    assert new_category.id is not None, "Expected the created category to have an ID"

    try:
        # Update the category
        updated_category = help_center.categories.update(
            category_id=new_category.id,
            name="Updated Test Category",
            description="An updated category for testing purposes",
            position=2,
        )
        assert updated_category.position == 2

        # Get the category by ID
        fetched_category = help_center.categories.get(category_id=new_category.id)
        assert fetched_category.id == new_category.id, "Expected to fetch the same category by ID"

    finally:
        # Clean up by deleting the category
        help_center.categories.delete(category_id=new_category.id)
