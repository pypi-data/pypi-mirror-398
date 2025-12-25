from langdetector import cli


def test_cli_text_output(capsys):
    rc = cli.main(["--text", "This is a simple English sentence."])
    assert rc == 0
    out = capsys.readouterr().out
    assert "en" in out or "English" in out


def test_cli_file_input(tmp_path, capsys):
    p = tmp_path / "sample.txt"
    p.write_text("Ceci est une phrase en français.", encoding="utf-8")
    rc = cli.main(["--file", str(p)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "fr" in out or "French" in out
