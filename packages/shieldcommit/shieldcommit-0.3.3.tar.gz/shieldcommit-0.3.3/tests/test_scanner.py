from shieldcommit.scanner import scan_text

def test_scan_detects_aws_key():
    text = 'my_key = "AKIAAAAAAAAAAAAAAAAA"'
    results = scan_text(text)
    assert any(name == 'AWS Access Key ID' for name, _ in results)
