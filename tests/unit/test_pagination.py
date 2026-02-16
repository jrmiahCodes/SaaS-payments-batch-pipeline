from mock_api.data_generator import filter_and_paginate, generate_dataset


def test_filter_and_paginate_by_created_window() -> None:
    rows = generate_dataset()["charges"]
    first = rows[10]
    last = rows[25]

    page, has_more = filter_and_paginate(
        rows,
        created_gte=first["created"],
        created_lte=last["created"],
        starting_after=None,
        limit=5,
    )

    assert len(page) == 5
    assert has_more is True
    assert all(first["created"] <= row["created"] <= last["created"] for row in page)


def test_pagination_with_starting_after() -> None:
    rows = generate_dataset()["customers"]
    first_page, _ = filter_and_paginate(rows, created_gte=None, created_lte=None, starting_after=None, limit=3)
    second_page, _ = filter_and_paginate(
        rows,
        created_gte=None,
        created_lte=None,
        starting_after=first_page[-1]["id"],
        limit=3,
    )
    assert second_page[0]["id"] != first_page[0]["id"]
