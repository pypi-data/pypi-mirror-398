import smartpy as sp


@sp.module
def M():
    import smartpy.stdlib.list_utils as list_utils

    class C(sp.Contract):
        def __init__(self):
            pass

        @sp.private
        def test_replicate(self):
            assert sp.len(list_utils.replicate((0, 5))) == 5
            assert sp.pack(list_utils.replicate((0, 5))) == sp.pack([0, 0, 0, 0, 0])

        @sp.private
        def test_element_at(self):
            assert list_utils.element_at(([1, 2, 3], 0)) == 1
            assert list_utils.element_at(([1, 2, 3], 1)) == 2
            assert list_utils.element_at(([1, 2, 3], 2)) == 3

        @sp.private
        def test_insertion_sort(self):
            assert sp.len(list_utils.insertion_sort(([1, 3, 5, 7, 2, 4, 6, 8]))) == 8
            assert (
                list_utils.element_at(
                    (list_utils.insertion_sort([1, 3, 5, 7, 2, 4, 6, 8]), 0)
                )
                == 1
            )
            assert (
                list_utils.element_at(
                    (list_utils.insertion_sort([1, 3, 5, 7, 2, 4, 6, 8]), 1)
                )
                == 2
            )
            assert (
                list_utils.element_at(
                    (list_utils.insertion_sort([1, 3, 5, 7, 2, 4, 6, 8]), 2)
                )
                == 3
            )
            assert (
                list_utils.element_at(
                    (list_utils.insertion_sort([1, 3, 5, 7, 2, 4, 6, 8]), 3)
                )
                == 4
            )
            assert (
                list_utils.element_at(
                    (list_utils.insertion_sort([1, 3, 5, 7, 2, 4, 6, 8]), 4)
                )
                == 5
            )
            assert (
                list_utils.element_at(
                    (list_utils.insertion_sort([1, 3, 5, 7, 2, 4, 6, 8]), 5)
                )
                == 6
            )
            assert (
                list_utils.element_at(
                    (list_utils.insertion_sort([1, 3, 5, 7, 2, 4, 6, 8]), 6)
                )
                == 7
            )
            assert (
                list_utils.element_at(
                    (list_utils.insertion_sort([1, 3, 5, 7, 2, 4, 6, 8]), 7)
                )
                == 8
            )

        @sp.private
        def test_sort(self):
            assert sp.len(list_utils.sort(([1, 3, 5, 7, 2, 4, 6, 8]))) == 8
            assert (
                list_utils.element_at((list_utils.sort(([1, 3, 5, 7, 2, 4, 6, 8])), 0))
                == 1
            )
            assert (
                list_utils.element_at((list_utils.sort(([1, 3, 5, 7, 2, 4, 6, 8])), 1))
                == 2
            )
            assert (
                list_utils.element_at((list_utils.sort(([1, 3, 5, 7, 2, 4, 6, 8])), 2))
                == 3
            )
            assert (
                list_utils.element_at((list_utils.sort(([1, 3, 5, 7, 2, 4, 6, 8])), 3))
                == 4
            )
            assert (
                list_utils.element_at((list_utils.sort(([1, 3, 5, 7, 2, 4, 6, 8])), 4))
                == 5
            )
            assert (
                list_utils.element_at((list_utils.sort(([1, 3, 5, 7, 2, 4, 6, 8])), 5))
                == 6
            )
            assert (
                list_utils.element_at((list_utils.sort(([1, 3, 5, 7, 2, 4, 6, 8])), 6))
                == 7
            )
            assert (
                list_utils.element_at((list_utils.sort(([1, 3, 5, 7, 2, 4, 6, 8])), 7))
                == 8
            )

        @sp.private
        def test_sub_list(self):
            assert sp.pack(list_utils.sub_list(([1, 2, 3, 4, 5], 1, 2))) == sp.pack([2])
            assert sp.pack(list_utils.sub_list(([1, 2, 3, 4, 5], 1, 3))) == sp.pack(
                [2, 3]
            )
            assert sp.pack(list_utils.sub_list(([1, 2, 3, 4, 5], 1, 4))) == sp.pack(
                [2, 3, 4]
            )
            assert sp.pack(list_utils.sub_list(([1, 2, 3, 4, 5], 1, 5))) == sp.pack(
                [2, 3, 4, 5]
            )

        @sp.private
        def test_update_list(self):
            assert sp.pack(
                list_utils.update_list(([1, 2, 3, 4, 5], 0, 100))
            ) == sp.pack([100, 2, 3, 4, 5])
            assert sp.pack(
                list_utils.update_list(([1, 2, 3, 4, 5], 1, 100))
            ) == sp.pack([1, 100, 3, 4, 5])
            assert sp.pack(
                list_utils.update_list(([1, 2, 3, 4, 5], 2, 100))
            ) == sp.pack([1, 2, 100, 4, 5])
            assert sp.pack(
                list_utils.update_list(([1, 2, 3, 4, 5], 3, 100))
            ) == sp.pack([1, 2, 3, 100, 5])
            assert sp.pack(
                list_utils.update_list(([1, 2, 3, 4, 5], 4, 100))
            ) == sp.pack([1, 2, 3, 4, 100])

        @sp.private
        def test_merge_sort(self):
            assert sp.len(list_utils.merge_sort(([1, 3, 5, 7, 2, 4, 6, 8]))) == 8
            assert (
                list_utils.element_at(
                    (list_utils.merge_sort(([1, 3, 5, 7, 2, 4, 6, 8])), 0)
                )
                == 1
            )
            assert (
                list_utils.element_at(
                    (list_utils.merge_sort(([1, 3, 5, 7, 2, 4, 6, 8])), 1)
                )
                == 2
            )
            assert (
                list_utils.element_at(
                    (list_utils.merge_sort(([1, 3, 5, 7, 2, 4, 6, 8])), 2)
                )
                == 3
            )
            assert (
                list_utils.element_at(
                    (list_utils.merge_sort(([1, 3, 5, 7, 2, 4, 6, 8])), 3)
                )
                == 4
            )
            assert (
                list_utils.element_at(
                    (list_utils.merge_sort(([1, 3, 5, 7, 2, 4, 6, 8])), 4)
                )
                == 5
            )
            assert (
                list_utils.element_at(
                    (list_utils.merge_sort(([1, 3, 5, 7, 2, 4, 6, 8])), 5)
                )
                == 6
            )
            assert (
                list_utils.element_at(
                    (list_utils.merge_sort(([1, 3, 5, 7, 2, 4, 6, 8])), 6)
                )
                == 7
            )
            assert (
                list_utils.element_at(
                    (list_utils.merge_sort(([1, 3, 5, 7, 2, 4, 6, 8])), 7)
                )
                == 8
            )

        @sp.private
        def test_quick_select(self):
            assert list_utils.quick_select(([10, 4, 5, 8, 6, 11, 26], 0)) == 4
            assert list_utils.quick_select(([10, 4, 5, 8, 6, 11, 26], 1)) == 5
            assert list_utils.quick_select(([10, 4, 5, 8, 6, 11, 26], 2)) == 6
            assert list_utils.quick_select(([10, 4, 5, 8, 6, 11, 26], 3)) == 8
            assert list_utils.quick_select(([10, 4, 5, 8, 6, 11, 26], 4)) == 10
            assert list_utils.quick_select(([10, 4, 5, 8, 6, 11, 26], 5)) == 11
            assert list_utils.quick_select(([10, 4, 5, 8, 6, 11, 26], 6)) == 26

        @sp.entrypoint
        def ep(self):
            self.test_replicate()
            self.test_element_at()
            self.test_insertion_sort()
            self.test_sort()
            self.test_sub_list()
            self.test_update_list()
            self.test_merge_sort()
            self.test_quick_select()

        @sp.entrypoint
        def sub_list_error(self):
            _ = list_utils.sub_list(([1, 2, 3, 4, 5], 1, 1))


@sp.add_test()
def test():
    s = sp.test_scenario("Test")
    c = M.C()
    s += c
    c.ep()
    try:
        c.sub_list_error()
    except:
        pass
    else:
        assert (
            False
        ), "Sub list should face when start index is greater or equal than end index"
