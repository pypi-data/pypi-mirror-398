from funcy_bear.tools.list_merger import ListMerge


def list_merger_int(*lists, unique: bool = False) -> list[int]:
    """Merge two lists of integers."""
    return ListMerge[int](unique=unique).merge(*lists)


def list_merger_str(*lists, unique: bool = False) -> list[str]:
    """Merge two lists of strings."""
    return ListMerge[str](unique=unique).merge(*lists)


def test_list_merge() -> None:
    list1: list[int] = [1, 2, 3]
    list2: list[int] = [4, 5, 6]
    merged1: list[int] = list_merger_int(list1, list2)
    assert merged1 == [1, 2, 3, 4, 5, 6]

    list3: list[str] = ["a", "b", "c"]
    list4: list[str] = ["d", "e", "f"]
    merged2: list[str] = list_merger_str(list3, list4)
    assert merged2 == ["a", "b", "c", "d", "e", "f"]

    list5: list[int] = []
    list6: list[int] = [1, 2, 3]
    merged3: list[int] = list_merger_int(list5, list6)
    assert merged3 == [1, 2, 3]

    list7: list[int] = [1, 2, 3]
    list8: list[int] = []
    merged: list[int] = list_merger_int(list7, list8)
    assert merged == [1, 2, 3]

    merged = ListMerge([], [], []).as_list()
    assert merged == []


def test_unique_list_merge() -> None:
    list1: list[int] = [1, 2, 3, 2]
    list2: list[int] = [3, 4, 5, 4]
    merger: ListMerge[int] = ListMerge(unique=True)
    merged1: list[int] = merger.merge(list1, list2)
    assert merged1 == [1, 2, 3, 4, 5]

    list3: list[str] = ["a", "b", "a"]
    list4: list[str] = ["b", "c", "d"]
    merger2: ListMerge[str] = ListMerge(unique=True)
    merged2: list[str] = merger2.merge(list3, list4)
    assert merged2 == ["a", "b", "c", "d"]


def test_delayed_adds() -> None:
    merger1: ListMerge[int] = ListMerge[int](unique=True).add([1, 2, 3])
    merger1.add([4, 5, 6])
    merger1.merge([7, 8, 9], [10])
    merged1: list[int] = merger1.as_list()
    assert merged1 == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    merger2 = ListMerge[int](unique=False)
    merger2.add([1, 2, 2])
    merger2.add([2, 3, 3])
    merged2: list[int] = merger2.as_list()
    assert merged2 == [1, 2, 2, 2, 3, 3]
