from kiarina.lib.falkordb import get_falkordb


def test_get_falkordb() -> None:
    # Check if it is cached
    db1 = get_falkordb(use_retry=True)
    db2 = get_falkordb()
    assert db1 is db2

    # Verify that changing the cache key allows retrieval of a different instance
    db3 = get_falkordb(cache_key="other")
    assert db1 is not db3

    # Test basic query execution
    g = db1.select_graph("test")
    nodes = g.query("CREATE (n:TestNode {name: 'Test'}) RETURN n").result_set
    assert len(nodes) == 1
