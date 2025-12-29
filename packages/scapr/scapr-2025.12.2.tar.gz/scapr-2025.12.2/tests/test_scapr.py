from re import match

import scapr


def test_version():
    version = scapr.__version__
    assert isinstance(version, str), "Version should be a string"


def test_capture_to_output_dir(tmp_path):
    out_path = tmp_path / "output"
    out_path.mkdir()
    assert out_path.exists(), "Output folder should exist"

    args = [
        "--auto",
        "--folder",
        str(out_path),
        "--count",
        "2",
        "--seconds",
        "1",
    ]
    scapr.scap.main(args)

    out_dirs = list(out_path.glob("*"))
    assert len(out_dirs) == 1, "Should have one folder"

    out_subdir = out_dirs[0]
    assert match(r"scapr_\d{8}_\d{6}", out_subdir.name), (
        "Folder name should match 'scapr_yyyymmdd_hhmmss` pattern"
    )
    assert len(list(out_subdir.glob("*.jpg"))) == 2, "Should have two .jpg files"


def test_capture_to_output_dir_with_log(tmp_path):
    out_path = tmp_path / "output"
    out_path.mkdir()
    assert out_path.exists(), "Output folder should exist"

    args = [
        "--auto",
        "--folder",
        str(out_path),
        "--count",
        "2",
        "--seconds",
        "1",
        "--do-log",
    ]
    scapr.scap.main(args)

    out_dirs = list(out_path.glob("*"))
    assert len(out_dirs) == 1, "Should have one folder"

    out_subdir = out_dirs[0]
    assert match(r"scapr_\d{8}_\d{6}", out_subdir.name), (
        "Folder name should match 'scapr_yyyymmdd_hhmmss` pattern"
    )
    assert len(list(out_subdir.glob("*.jpg"))) == 2, "Should have two .jpg files"

    assert len(list(out_subdir.glob("*-log.txt"))) == 1, "Should have one log file"


def test_capture_to_output_dir_no_subdir(tmp_path):
    out_path = tmp_path / "output"
    out_path.mkdir()
    assert out_path.exists(), "Output folder should exist"

    args = [
        "--auto",
        "--folder",
        str(out_path),
        "--count",
        "2",
        "--seconds",
        "1",
        "--flat",
    ]
    scapr.scap.main(args)

    assert len(list(out_path.glob("*.jpg"))) == 2, "Should have two .jpg files"
