# tests/test_utils.py
import pytest
import importlib
from opticedge_cloud_utils.merge import _deep_get, _compute_new_value_from_delta_or_data, detect_field_changes, safe_any_changed, prune_conflicting_set_unset

MODULE_PATH = "opticedge_cloud_utils.merge"  # adjust if deep_merge is in another file/module


@pytest.fixture
def module():
    """Dynamically import and reload the target module before each test."""
    mod = importlib.import_module(MODULE_PATH)
    importlib.reload(mod)
    return mod


def test_merges_non_overlapping_keys(module):
    base = {"a": 1}
    updates = {"b": 2}
    result = module.deep_merge(base, updates)
    assert result == {"a": 1, "b": 2}


def test_overwrites_existing_value(module):
    base = {"a": 1, "b": 2}
    updates = {"b": 99}
    result = module.deep_merge(base, updates)
    assert result == {"a": 1, "b": 99}


def test_deep_merges_nested_dicts(module):
    base = {"a": {"x": 1, "y": 2}}
    updates = {"a": {"y": 99, "z": 3}}
    result = module.deep_merge(base, updates)
    assert result == {"a": {"x": 1, "y": 99, "z": 3}}


def test_removes_key_when_value_none_and_delete_nulls_true(module):
    base = {"a": 1, "b": 2}
    updates = {"b": None}
    result = module.deep_merge(base, updates, delete_nulls=True)
    assert result == {"a": 1}


def test_preserves_none_when_delete_nulls_false(module):
    base = {"a": 1, "b": 2}
    updates = {"b": None}
    result = module.deep_merge(base, updates, delete_nulls=False)
    assert result == {"a": 1, "b": None}


def test_handles_empty_updates(module):
    base = {"a": 1}
    updates = {}
    result = module.deep_merge(base, updates)
    assert result == {"a": 1}


def test_handles_empty_base(module):
    base = {}
    updates = {"x": 10}
    result = module.deep_merge(base, updates)
    assert result == {"x": 10}


def test_original_base_not_modified(module):
    base = {"a": {"b": 1}}
    updates = {"a": {"c": 2}}
    result = module.deep_merge(base, updates)
    assert result == {"a": {"b": 1, "c": 2}}
    assert base == {"a": {"b": 1}}
    assert id(result) != id(base)


def test_deep_get_found_and_not_found():
    obj = {"a": {"b": None}, "x": 1}
    # nested key exists and is None -> found True
    val, found = _deep_get(obj, "a.b")
    assert found is True
    assert val is None

    # top-level key
    val, found = _deep_get(obj, "x")
    assert found is True
    assert val == 1

    # missing key
    val, found = _deep_get(obj, "a.c")
    assert found is False
    assert val is None

    # empty path returns the object itself
    val, found = _deep_get(obj, "")
    assert found is True
    assert val == obj


def test_deep_get_obj_none_branches():
    # obj is None and non-empty path -> should be not found
    val, found = _deep_get(None, "a.b")
    assert found is False
    assert val is None

    # obj is None and empty path -> earlier code returns (None, False) because obj is None
    val, found = _deep_get(None, "")
    assert found is False
    assert val is None


@pytest.mark.parametrize(
    "data, delta, path, delete_nulls, expected_val, expected_found",
    [
        # delta contains non-None value -> use delta
        ({"k": "old"}, {"k": "new"}, "k", True, "new", True),
        # delta contains None and delete_nulls=True -> removed
        ({"k": "old"}, {"k": None}, "k", True, None, False),
        # delta contains None and delete_nulls=False -> explicit None
        ({"k": "old"}, {"k": None}, "k", False, None, True),
        # delta doesn't contain it -> fallback to data
        ({"a": {"b": 2}}, {"x": 1}, "a.b", True, 2, True),
        # neither contains it
        ({"a": {}}, {"x": {}}, "a.missing", True, None, False),
        # nested delta overrides nested data
        ({"profile": {"type": "student"}}, {"profile": {"type": "alumni"}}, "profile.type", True, "alumni", True),
        
        # ancestor in delta is a dict -> allow nested resolution (read from delta)
        ({"a": {"b": 1}}, {"a": {"b": 2}}, "a.b", True, 2, True),

        # ancestor in delta is None -> nested path should be considered removed
        ({"a": {"b": 1}}, {"a": None}, "a.b", True, None, False),

        # ancestor in delta replaced by scalar -> nested path removed
        ({"a": {"b": 1}}, {"a": 5}, "a.b", True, None, False),
    ]
)
def test_compute_new_value_from_delta_or_data(data, delta, path, delete_nulls, expected_val, expected_found):
    val, found = _compute_new_value_from_delta_or_data(data, delta, path, delete_nulls=delete_nulls)
    assert found is expected_found
    assert val == expected_val


def test_deep_merge_preserves_unmentioned_nested_keys():
    data = {"test": {"a": 123, "b": {"c": 123, "d": "abc"}}}
    delta = {"test": {"a": 1234}}

    new_val, found = _compute_new_value_from_delta_or_data(data, delta, "test", delete_nulls=True)
    assert found is True
    # new_val should have both 'a' updated and 'b' preserved
    assert new_val == {"a": 1234, "b": {"c": 123, "d": "abc"}}


def test_detect_field_changes_basic_scenario():
    data = {
        "email": "old@example.com",
        "profile": {"type": "student", "name": "Alice"},
        "extras": {"x": 1}
    }
    delta = {
        "email": None,               # deletion
        "profile": {"type": "alumni"}  # update nested field
    }
    fields = ["email", "profile.type", "profile.name", "extras.x", "missing.field"]

    changes = detect_field_changes(data, delta, fields, delete_nulls=True)

    # email -> deleted
    assert changes["email"]["old"] == "old@example.com"
    assert changes["email"]["new"] is None
    assert changes["email"]["old_found"] is True
    assert changes["email"]["new_found"] is False
    assert changes["email"]["changed"] is True
    assert changes["email"]["reason"] == "deleted"

    # profile.type -> updated
    assert changes["profile.type"]["old"] == "student"
    assert changes["profile.type"]["new"] == "alumni"
    assert changes["profile.type"]["old_found"] is True
    assert changes["profile.type"]["new_found"] is True
    assert changes["profile.type"]["changed"] is True
    assert changes["profile.type"]["reason"] == "updated"

    # profile.name -> unchanged (not present in delta)
    assert changes["profile.name"]["old"] == "Alice"
    assert changes["profile.name"]["new"] == "Alice"
    assert changes["profile.name"]["changed"] is False
    assert changes["profile.name"]["reason"] == "unchanged"

    # extras.x -> unchanged
    assert changes["extras.x"]["old"] == 1
    assert changes["extras.x"]["new"] == 1
    assert changes["extras.x"]["changed"] is False

    # missing.field -> remains missing
    assert changes["missing.field"]["old_found"] is False
    assert changes["missing.field"]["new_found"] is False
    assert changes["missing.field"]["changed"] is False


def test_detect_field_changes_delete_nulls_false_treats_null_as_value():
    data = {"k": "old"}
    delta = {"k": None}
    fields = ["k"]

    changes = detect_field_changes(data, delta, fields, delete_nulls=False)
    assert changes["k"]["old"] == "old"
    assert changes["k"]["old_found"] is True
    # new_found should be True because we treat None as explicit value
    assert changes["k"]["new_found"] is True
    assert changes["k"]["new"] is None
    assert changes["k"]["changed"] is True
    assert changes["k"]["reason"] == "updated"


def test_detect_field_changes_added_branch():
    # field does not exist in data but exists in delta -> 'added' branch should be hit
    data = {}
    delta = {"new_field": "value123"}
    fields = ["new_field"]

    changes = detect_field_changes(data, delta, fields, delete_nulls=True)

    assert changes["new_field"]["old_found"] is False
    assert changes["new_field"]["new_found"] is True
    assert changes["new_field"]["new"] == "value123"
    assert changes["new_field"]["changed"] is True
    assert changes["new_field"]["reason"] == "added"


def test_fields_none_auto_discover_union_of_paths_and_deletions():
    data = {"a": {"b": 1}, "c": 2}
    delta = {"a": None, "d": 3}
    # when fields=None should auto-discover: "a", "a.b", "c", "d"
    changes = detect_field_changes(data, delta, fields=None, delete_nulls=True)

    # a is deleted by delta
    assert "a" in changes
    assert changes["a"]["old_found"] is True
    assert changes["a"]["new_found"] is False
    assert changes["a"]["reason"] == "deleted"

    # nested a.b should also be considered absent after deletion
    assert "a.b" in changes
    assert changes["a.b"]["old"] == 1
    assert changes["a.b"]["old_found"] is True
    assert changes["a.b"]["new_found"] is False
    assert changes["a.b"]["changed"] is True
    assert changes["a.b"]["reason"] == "deleted"

    # c unchanged
    assert changes["c"]["old"] == 2
    assert changes["c"]["new"] == 2
    assert changes["c"]["changed"] is False

    # d added
    assert changes["d"]["old_found"] is False
    assert changes["d"]["new_found"] is True
    assert changes["d"]["new"] == 3
    assert changes["d"]["reason"] == "added"


def test_list_values_treated_as_leaves_and_delete_nulls_behavior():
    data = {"arr": [{"x": 1}], "k": "old"}
    # delta sets arr -> None (delete) and k -> None (explicit null)
    delta = {"arr": None, "k": None}

    # delete_nulls=True: arr removed, k removed
    changes = detect_field_changes(data, delta, fields=None, delete_nulls=True)
    assert "arr" in changes
    assert changes["arr"]["old_found"] is True
    assert changes["arr"]["new_found"] is False
    assert changes["arr"]["reason"] == "deleted"

    # delete_nulls=False: None is treated as explicit value for same-key
    changes2 = detect_field_changes(data, delta, fields=["k"], delete_nulls=False)
    assert changes2["k"]["old"] == "old"
    assert changes2["k"]["new_found"] is True
    assert changes2["k"]["new"] is None
    assert changes2["k"]["reason"] == "updated"


def test_parent_deleted_in_delta_marks_nested_as_deleted():
    data = {"a": {"b": 1}}
    delta = {"a": None}
    changes = detect_field_changes(data, delta, fields=["a", "a.b"], delete_nulls=True)

    assert changes["a"]["old_found"] is True
    assert changes["a"]["new_found"] is False
    assert changes["a"]["reason"] == "deleted"

    assert changes["a.b"]["old"] == 1
    assert changes["a.b"]["old_found"] is True
    # Important: nested path is considered deleted when parent is None
    assert changes["a.b"]["new_found"] is False
    assert changes["a.b"]["changed"] is True
    assert changes["a.b"]["reason"] == "deleted"


def test_parent_replaced_by_scalar_removes_nested_paths():
    data = {"a": {"b": 1}}
    delta = {"a": 5}  # ancestor replaced by scalar -> nested removed
    changes = detect_field_changes(data, delta, fields=["a", "a.b"], delete_nulls=True)

    assert changes["a"]["old_found"] is True
    assert changes["a"]["new_found"] is True
    assert changes["a"]["new"] == 5
    assert changes["a.b"]["old_found"] is True
    assert changes["a.b"]["new_found"] is False
    assert changes["a.b"]["reason"] == "deleted"


def test_empty_dict_intermediate_keys_and_no_data_no_delta():
    # intermediate empty dict: "a" should be discovered but no deeper keys
    data = {"a": {}}
    delta = {}
    changes = detect_field_changes(data, delta, fields=None, delete_nulls=True)
    assert "a" in changes
    assert changes["a"]["old_found"] is True
    # there should be no "a.*" entries because a is empty
    assert not any(key.startswith("a.") for key in changes.keys())

    # no data and no delta -> fields=None => empty result
    changes_empty = detect_field_changes(None, None, fields=None, delete_nulls=True)
    assert changes_empty == {}


def test_ancestor_in_delta_is_dict_allows_nested_resolution():
    """
    Covers the ancestor-check path where the ancestor exists in delta and is a dict.
    The loop should continue (not early-return) and exact nested keys should be resolved
    from delta when present.
    """
    data = {"a": {"b": 1}}
    delta = {"a": {"b": 2}}  # ancestor 'a' is a dict in delta -> allow nested resolution
    changes = detect_field_changes(data, delta, fields=["a", "a.b"], delete_nulls=True)

    # ancestor 'a' is present in delta and replaced with dict -> top-level value should be the dict
    assert changes["a"]["old_found"] is True
    assert changes["a"]["new_found"] is True
    # new should be the dict from delta
    assert isinstance(changes["a"]["new"], dict)
    assert changes["a"]["new"]["b"] == 2

    # nested 'a.b' should be updated to 2 (read from delta)
    assert changes["a.b"]["old"] == 1
    assert changes["a.b"]["new"] == 2
    assert changes["a.b"]["old_found"] is True
    assert changes["a.b"]["new_found"] is True
    assert changes["a.b"]["changed"] is True
    assert changes["a.b"]["reason"] == "updated"


def test_collect_paths_handles_non_dict_input_and_none_data():
    """
    Covers the _collect_paths early-return branch when obj is None or not a dict.
    Passing a non-dict (list) as 'data' should not blow up: collector returns empty set
    and detect_field_changes should still work using delta-only paths if any.
    """
    # Case A: data is a non-dict (list) -> should be treated as no-discoverable paths
    data = []  # intentionally non-dict
    delta = {"x": 1}
    changes = detect_field_changes(data, delta, fields=None, delete_nulls=True)

    # since data contributed no paths and delta only had "x", we should still see "x"
    assert "x" in changes
    assert changes["x"]["old_found"] is False
    assert changes["x"]["new_found"] is True
    assert changes["x"]["new"] == 1

    # Case B: both data and delta are None -> collector returns empty and result is empty dict
    changes_empty = detect_field_changes(None, None, fields=None, delete_nulls=True)
    assert changes_empty == {}


def test_safe_any_changed_empty_and_non_dict_entries():
    # empty -> False
    assert safe_any_changed({}) is False

    # values that are not dict should be ignored
    changes = {
        "a": "not-a-dict",
        "b": 123,
    }
    assert safe_any_changed(changes) is False


def test_safe_any_changed_detects_true_changed_flag():
    changes = {
        "unchanged": {"old": 1, "new": 1, "changed": False},
        "changed": {"old": 1, "new": 2, "changed": True},
    }
    assert safe_any_changed(changes) is True

    # when all dict entries have changed==False -> False
    all_unchanged = {
        "x": {"old": None, "new": None, "changed": False},
        "y": {"old": 1, "new": 1, "changed": False},
    }
    assert safe_any_changed(all_unchanged) is False

    # mixed: non-dict + dict with changed True -> True
    mixed = {"a": "str", "b": {"changed": True}}
    assert safe_any_changed(mixed) is True


def test_set_parent_removes_set_children():
    set_map = {
        "record.a": {"x": 1},
        "record.a.b": 2,
        "record.a.b.c": 3,
        "record.z": 10,
    }
    unset_map = {}
    pruned_set, pruned_unset = prune_conflicting_set_unset(set_map, unset_map)

    # parent 'record.a' should remain, children removed
    assert "record.a" in pruned_set
    assert "record.a.b" not in pruned_set
    assert "record.a.b.c" not in pruned_set
    # unrelated key preserved
    assert "record.z" in pruned_set
    # unset_map unchanged
    assert pruned_unset == {}


def test_unset_parent_removes_set_children_and_unset_children():
    set_map = {
        "record.a.b": 2,
        "record.a.b.c": 3,
        "record.other": 5,
    }
    unset_map = {
        "record.a": "",
        "record.some": ""
    }

    pruned_set, pruned_unset = prune_conflicting_set_unset(set_map, unset_map)

    # 'record.a' is a parent in unset_map -> children under it must be removed from set_map & unset_map
    assert "record.a" in pruned_unset
    assert "record.a.b" not in pruned_set
    assert "record.a.b.c" not in pruned_set
    # unrelated keys preserved
    assert "record.other" in pruned_set
    assert "record.some" in pruned_unset


def test_same_key_in_set_and_unset_prefers_set():
    set_map = {"record.a": 1}
    unset_map = {"record.a": ""}

    pruned_set, pruned_unset = prune_conflicting_set_unset(set_map, unset_map)

    # set should win; unset should be removed
    assert "record.a" in pruned_set
    assert "record.a" not in pruned_unset


def test_no_conflicts_keeps_all_keys():
    set_map = {"record.a.b": 2, "x": 1}
    unset_map = {"record.c": "", "y.z": ""}

    pruned_set, pruned_unset = prune_conflicting_set_unset(set_map, unset_map)

    # nothing conflicts here, all keys preserved
    assert pruned_set == set_map
    assert pruned_unset == unset_map


def test_dot_boundary_does_not_prune_similarly_prefixed_keys():
    # ensure 'record.a' does not prune 'record.aa' (dot boundary requirement)
    set_map = {"record.a": {"foo": "bar"}, "record.aa": {"baz": "qux"}}
    unset_map = {"record.a.b": ""}

    pruned_set, pruned_unset = prune_conflicting_set_unset(set_map, unset_map)

    # record.a exists in set -> children under record.a removed from unset/set, but record.aa stays
    assert "record.a" in pruned_set
    assert "record.aa" in pruned_set
    # 'record.a.b' must be removed because ancestor 'record.a' exists
    assert "record.a.b" not in pruned_unset


def test_multiple_level_parents_and_children():
    set_map = {
        "record.a.b.c.d": 1,
        "record.a.b": {"updated": True},
        "record.a.b.c": 2,
    }
    unset_map = {
        "record.a": "",
        "other": ""
    }

    pruned_set, pruned_unset = prune_conflicting_set_unset(set_map, unset_map)

    # Because unset_map contains 'record.a', all deeper keys under 'record.a' must be removed
    assert "record.a" in pruned_unset
    assert not any(k.startswith("record.a.") for k in pruned_set.keys())
    # unrelated keys preserved
    assert "other" in pruned_unset
