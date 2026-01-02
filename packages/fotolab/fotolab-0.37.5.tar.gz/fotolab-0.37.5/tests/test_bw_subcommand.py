def test_bw_subcommand_deep_black(cli_runner, image_file):
    img_path = image_file("sample.png")
    ret = cli_runner("bw", "--filter", "DEEP_BLACK", str(img_path))
    assert ret.returncode == 0


def test_bw_subcommand_required_filter(cli_runner, image_file):
    img_path = image_file("sample.png")
    ret = cli_runner("bw", str(img_path))
    assert ret.returncode != 0


def test_bw_subcommand_all_filters(cli_runner, image_file, tmp_path):
    img_path = image_file("sample.png")
    output_dir = tmp_path / "output"

    ret = cli_runner(
        "bw",
        "--all-filters",
        "-od",
        str(output_dir),
        str(img_path),
    )

    assert ret.returncode == 0

    expected_files = [
        "bw_deep_black_sample.png",
        "bw_true_gray_sample.png",
        "bw_soft_light_sample.png",
    ]

    for filename in expected_files:
        assert (output_dir / filename).exists()
