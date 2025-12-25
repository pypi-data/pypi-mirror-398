from geneva.utils.sequence_queue import SequenceQueue


def test_basic_sequence() -> None:
    q = SequenceQueue[str]()
    q.put(0, 1, "first")
    q.put(1, 1, "second")
    q.put(2, 1, "third")

    assert q.pop() == "first"
    assert q.pop() == "second"
    assert q.pop() == "third"
    assert q.pop() is None


def test_out_of_order_insertion() -> None:
    q = SequenceQueue[str]()
    q.put(2, 1, "third")
    q.put(0, 1, "first")
    q.put(1, 1, "second")

    assert q.pop() == "first"
    assert q.pop() == "second"
    assert q.pop() == "third"
    assert q.pop() is None


def test_different_sizes() -> None:
    q = SequenceQueue[str]()
    q.put(1, 2, "second")  # size 2
    q.put(0, 1, "first")  # size 1
    q.put(3, 1, "third")  # size 1

    assert q.next_position() == 0
    assert q.pop() == "first"
    assert q.next_position() == 1
    assert q.pop() == "second"
    assert q.next_position() == 3
    assert q.pop() == "third"
    assert q.next_position() == 4
    assert q.pop() is None


def test_peek() -> None:
    q = SequenceQueue[str]()
    q.put(0, 1, "first")

    assert q.peek() == "first"
    assert q.pop() == "first"
    assert q.peek() is None


def test_empty_queue() -> None:
    q = SequenceQueue[str]()
    assert q.is_empty()
    assert q.pop() is None
    assert q.peek() is None
    assert q.next_position() == 0

    q.put(1, 1, "second")
    assert q.is_empty()
    assert q.pop() is None
    assert q.peek() is None
    assert q.next_position() == 0


def test_gap_in_sequence() -> None:
    q = SequenceQueue[str]()
    q.put(1, 1, "second")
    q.put(0, 1, "first")
    q.put(3, 1, "fourth")

    assert q.pop() == "first"
    assert q.pop() == "second"
    assert q.pop() is None  # Can't pop "fourth" because position 2 is missing
    assert q.next_position() == 2

    q.put(2, 1, "third")
    # Now we can pop "third" AND "fourth"
    assert q.pop() == "third"
    assert q.pop() == "fourth"
    assert q.pop() is None


def test_generic_type() -> None:
    q = SequenceQueue[int]()
    q.put(0, 1, 42)
    assert q.pop() == 42
    assert q.pop() is None
