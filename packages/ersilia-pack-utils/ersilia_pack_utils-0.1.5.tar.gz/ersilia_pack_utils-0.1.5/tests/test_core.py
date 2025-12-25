import json
import numpy as np
import pytest

from src.ersilia_pack_utils.core import write_out_bin, _normalize_dtype, clip


def _read_bin_payload(path):
    with open(path, "rb") as f:
        meta_line = f.readline()
        meta = json.loads(meta_line.decode("utf-8"))
        dt = np.dtype(meta["dtype"])
        shape = tuple(meta["shape"])
        arr = np.frombuffer(f.read(), dtype=dt).reshape(shape)
    return meta, arr


def test_normalize_dtype_accepts_int32_float32():
    assert _normalize_dtype("int32") == np.dtype(np.int32)
    assert _normalize_dtype("float32") == np.dtype(np.float32)
    assert _normalize_dtype(np.int32) == np.dtype(np.int32)
    assert _normalize_dtype(np.float32) == np.dtype(np.float32)


def test_write_out_bin_rejects_other_dtypes(tmp_path):
    out = tmp_path / "x.bin"
    results = [[1.0, 2.0]]
    header = ["a", "b"]
    with pytest.raises(ValueError):
        write_out_bin(results, header, str(out), dtype="float64")
    with pytest.raises(ValueError):
        write_out_bin(results, header, str(out), dtype=np.int64)


def test_float32_clips_and_handles_infs_and_nans(tmp_path):
    out = tmp_path / "f.bin"
    header = ["x", "y"]
    f32 = np.finfo(np.float32)

    big = np.float64(f32.max) * 2.0
    neg_big = -np.float64(f32.max) * 2.0

    results = [
        [0.0, big],
        [neg_big, 1.0],
        [np.inf, -np.inf],
        [np.nan, 123.0],
    ]

    write_out_bin(results, header, str(out), dtype=np.float32)
    meta, arr = _read_bin_payload(out)

    assert meta["dtype"] == "float32"
    assert meta["shape"] == [4, 2]
    assert meta["columns"] == header

    assert arr.dtype == np.float32
    assert arr[0, 0] == np.float32(0.0)
    assert arr[0, 1] == np.float32(f32.max)
    assert arr[1, 0] == np.float32(f32.min)
    assert arr[1, 1] == np.float32(1.0)
    assert arr[2, 0] == np.float32(f32.max)
    assert arr[2, 1] == np.float32(f32.min)
    assert np.isnan(arr[3, 0])
    assert arr[3, 1] == np.float32(123.0)


def test_int32_casts_directly(tmp_path):
    out = tmp_path / "i.bin"
    header = ["x", "y"]

    results = [
        [1.9, -2.2],
        [3.0, 4.0],
    ]

    write_out_bin(results, header, str(out), dtype=np.int32)
    meta, arr = _read_bin_payload(out)

    assert meta["dtype"] == "int32"
    assert arr.dtype == np.int32
    assert arr.tolist() == [[1, -2], [3, 4]]


def test_header_length_mismatch_raises(tmp_path):
    out = tmp_path / "h.bin"
    results = [[1.0, 2.0]]
    header = ["only_one_col"]
    with pytest.raises(ValueError):
        write_out_bin(results, header, str(out), dtype=np.float32)


def test_1d_results_are_reshaped_to_column(tmp_path):
    out = tmp_path / "c.bin"
    header = ["x"]
    results = [1.0, 2.0, 3.0]

    write_out_bin(results, header, str(out), dtype=np.float32)
    meta, arr = _read_bin_payload(out)

    assert meta["shape"] == [3, 1]
    assert arr.shape == (3, 1)
    assert np.all(arr[:, 0] == np.array([1.0, 2.0, 3.0], dtype=np.float32))


def test_coerce_results_float32_clips_without_write():
    f32 = np.finfo(np.float32)
    big = np.float64(f32.max) * 10.0
    x = np.array([big, -big, np.inf, -np.inf, np.nan], dtype=np.float64)

    out = clip(x, np.dtype(np.float32))

    assert out.dtype == np.float32
    assert out[0] == np.float32(f32.max)
    assert out[1] == np.float32(f32.min)
    assert out[2] == np.float32(f32.max)
    assert out[3] == np.float32(f32.min)
    assert np.isnan(out[4])
