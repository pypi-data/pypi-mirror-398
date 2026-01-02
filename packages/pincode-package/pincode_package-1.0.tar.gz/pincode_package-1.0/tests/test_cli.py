import pytest
from pincode_package import cli
from pincode_package.exceptions import APIUnavailableError


# -------------------------------------------------
# PINCODE PATH
# -------------------------------------------------

def test_cli_uses_fetch_by_pincode(monkeypatch, capsys):
    def mock_fetch(pincode):
        assert pincode == "682001"
        return [{
            "Name": "Ernakulam",
            "Region": "Kochi",
            "District": "Ernakulam",
            "State": "Kerala",
            "Division": "Ernakulam",
            "Pincode": "682001",
        }]

    monkeypatch.setattr(cli, "fetch_by_pincode", mock_fetch)
    monkeypatch.setattr("sys.argv", ["pincode", "682001"])

    cli.main()

    out = capsys.readouterr().out
    assert "Ernakulam" in out
    assert "Kerala" in out


# -------------------------------------------------
# POST OFFICE PATH
# -------------------------------------------------

def test_cli_uses_fetch_by_postoffice(monkeypatch, capsys):
    def mock_fetch(name):
        assert name == "Ernakulam"
        return [{
            "Name": "Ernakulam",
            "Region": "Kochi",
            "District": "Ernakulam",
            "State": "Kerala",
            "Division": "Ernakulam",
            "Pincode": "682001",
        }]

    monkeypatch.setattr(cli, "fetch_by_postoffice_name", mock_fetch)
    monkeypatch.setattr("sys.argv", ["pincode", "Ernakulam"])

    cli.main()

    out = capsys.readouterr().out
    assert "Kerala" in out


# -------------------------------------------------
# ERROR PATH
# -------------------------------------------------

def test_cli_api_error(monkeypatch, capsys):
    def raise_error(_):
        raise APIUnavailableError("API down")

    monkeypatch.setattr(cli, "fetch_by_pincode", raise_error)
    monkeypatch.setattr("sys.argv", ["pincode", "682001"])

    with pytest.raises(SystemExit):
        cli.main()

    out = capsys.readouterr().out
    assert "Error:" in out
