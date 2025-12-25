import pytest
import awkward as ak
import numpy as np

from wp21_train.utils.slicing_utils import (
    replace_ak_fields,
    copy_fields,
    copy_all_fields_except,
    produce_mask_discrete_field,
    filter_fields_by_discrete_field,
    above,
    remove_fields,
    select_fields,
    rename_fields,
    add_zero_fields,
    drop_nans_in_field_group,
    merge_disjoint_fields,
    restrict_contiguous_eta_range,
)


@pytest.fixture
def sample_data1():
    return ak.Array({
        "a": [[1, 2, 3, 4]],
        "b": [[10, 20, 30, 40]],
        "eta1": [[0.1, 0.5, 1.5, 2.5]],
        "eta2": [[0.2, 0.4, 1.6, 2.6]],
    })

@pytest.fixture
def sample_data2():
    return ak.Array({
        "a": [[7,89,10, 11]],
        "d": [[10, 20, 30, 40]],
        "phi": [[0.1, 0.5, 1.5, 2.5]],
    })


def test_replace_ak_fields(sample_data1):
    mask = (sample_data1["a"]==1) | (sample_data1["a"]==3)
    result = replace_ak_fields(sample_data1, ["a"], mask)
    assert result["a"].to_list() == [[1, 3]]  # masked subset

def test_replace_ak_fields_other_data(sample_data1, sample_data2):
    mask = (sample_data1["a"]==1) | (sample_data1["a"]==3)
    result = replace_ak_fields(sample_data1, ["a"], mask, sample_data2)
    assert result["a"].to_list() == [[7, 10]]  # masked subset

def test_copy_fields(sample_data1):
    dst = ak.Array({"x": [[0, 0, 0, 0]]})
    result = copy_fields(dst, sample_data1, ["a", "b"])
    assert set(result.fields) == {"x", "a", "b"}
    assert result["a"].to_list() == [[1, 2, 3, 4]]


def test_copy_all_fields_except(sample_data1):
    dst = ak.Array({"c": [[0, 0, 0, 0]]})
    result = copy_all_fields_except(dst, sample_data1, ["b"])
    assert "b" not in result.fields
    assert "a" in result.fields
    assert "eta1" in result.fields


def test_produce_mask_discrete_field(sample_data1):
    mask = produce_mask_discrete_field(sample_data1, "a", [1, 3])
    assert mask.to_list() == [[True, False, True, False]]


def test_filter_fields_by_discrete_field(sample_data1):
    result = filter_fields_by_discrete_field(sample_data1, "a", [1, 2], ["b"])
    assert "a" in result.fields and "b" in result.fields
    assert result["a"].to_list() == [[1, 2]]
    assert result["b"].to_list() == [[10, 20]]
    assert "eta1" in result.fields


def test_above(sample_data1):
    result = above(sample_data1, "b", ["a", "b"], 25)
    assert result["b"].to_list() == [[30, 40]]


def test_remove_fields(sample_data1):
    result = remove_fields(sample_data1, ["b"])
    assert "b" not in result.fields
    assert "a" in result.fields


def test_select_fields(sample_data1):
    result = select_fields(sample_data1, ["a", "b"])
    assert set(result.fields) == {"a", "b"}


def test_rename_fields(sample_data1):
    mapping = {"a": "alpha", "b": "beta"}
    result = rename_fields(sample_data1, mapping)
    assert "alpha" in result.fields
    assert "beta" in result.fields
    assert "a" not in result.fields
    assert result["alpha"].to_list() == [[1, 2, 3, 4]]


def test_add_zero_fields(sample_data1):
    result = add_zero_fields(sample_data1, ["zero1", "zero2"])
    assert "zero1" in result.fields
    assert ak.all(result["zero1"] == 0)


def test_add_zero_fields_conflict(sample_data1):
    with pytest.raises(AssertionError):
        add_zero_fields(sample_data1, ["a"])  # field already exists


def test_drop_nans_in_field_group():
    data = ak.Array({
        "x": [[1.0, np.nan, 3.0, 4.0]],
        "y": [[10.0, 20.0, np.nan, 40.0]],
        "c": [[11.0, 2.0, np.nan]]
    })
    result = drop_nans_in_field_group(data, ["x", "y"])
    assert np.all(np.isfinite(result["x"]))
    assert len(result["x"][0]) == 2  # two entries should remain
    assert "c" not in result.fields


def test_merge_disjoint_fields():
    arr1 = ak.Array({"a": [[1, 2, 3]]})
    arr2 = ak.Array({"b": [[4, 5, 6,7]]})
    result = merge_disjoint_fields([arr1, arr2])
    assert set(result.fields) == {"a", "b"}
    assert result["a"].to_list() == [[1, 2, 3]]


def test_merge_disjoint_fields_conflict():
    arr1 = ak.Array({"a": [[1, 2, 3]]})
    arr2 = ak.Array({"a": [[4, 5, 6]]})
    with pytest.raises(AssertionError):
        merge_disjoint_fields([arr1, arr2])

def test_restrict_contiguous_eta_range(sample_data1):
    result = restrict_contiguous_eta_range(
        sample_data1,
        restricting_eta_field="eta1",
        restricted_eta_field="eta2",
        restricted_fields=["eta2"]
    )
    eta1_min, eta1_max = ak.min(sample_data1["eta1"]), ak.max(sample_data1["eta1"])
    assert ak.all((result["eta2"] > eta1_min) & (result["eta2"] < eta1_max))


def test_empty_merge_disjoint_fields():
    result = merge_disjoint_fields([])
    assert len(result) == 0

