def compute_visible_area(
    prev: tuple[int, int],
    cursor: int,
    dim: tuple[int, int],
    list_sizes: tuple[int, int],
) -> tuple[int, int]:
    """Return first (inclusive) and last (exclusive) visible index of a list.

    Args:
        prev: The previous first and last visible item.
        cursor: The selected item index.
        dim: The dimension in which the list should be displayed.
        list_sizes: Previous size of the list and current size of the list.

    Returns:
        The new first and last visible indicies.

    Raises:
        ValueError on an unhandled case
    """

    target_cursor = cursor
    first, last = prev
    n_rows, n_cols = dim
    capacity = n_rows * n_cols

    if list_sizes[0] > list_sizes[1]:
        # List became smaller
        cursor = min(cursor, list_sizes[1] - 1)
        last = list_sizes[1]
        first = last - capacity + last % n_cols

    if first <= cursor < first + capacity:
        # Cursor already within visible area
        last = first + capacity
    elif cursor >= last:
        # Cursor below current visible area
        last = cursor + (n_cols - cursor % n_cols)
        first = last - capacity
    elif cursor < first:
        # Cursor above current visible area
        first = cursor - cursor % n_cols
        last = first + capacity
    else:
        msg = (
            f"Unhandled case: prev=({prev}), cursor={target_cursor}, dim={dim}, "
            f"old_list_size={list_sizes[0]}, new_list_size={list_sizes[1]}"
        )
        raise ValueError(msg)

    first = max(0, first)
    last = min(list_sizes[1], last)

    return first, last
