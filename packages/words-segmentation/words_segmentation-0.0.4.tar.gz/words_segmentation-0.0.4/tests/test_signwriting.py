import pytest

from words_segmentation.signwriting import segment_signwriting


def test_segment_single_sign():
    sign = "𝠀񆄱񈠣񍉡𝠃𝤛𝤵񍉡𝣴𝣵񆄱𝤌𝤆񈠣𝤉𝤚"
    result = segment_signwriting(sign)
    assert result == [sign]

def test_segment_single_sign_no_prefix():
    sign = "𝠃𝤛𝤵񍉡𝣴𝣵񆄱𝤌𝤆񈠣𝤉𝤚"
    result = segment_signwriting(sign)
    assert result == [sign]

def test_segment_with_space():
    signs = [
        "𝠀񀀒񀀚񋚥񋛩𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭",
        "𝠀񂇢񂇈񆙡񋎥񋎵𝠃𝤛𝤬񂇈𝤀𝣺񂇢𝤄𝣻񋎥𝤄𝤗񋎵𝤃𝣟񆙡𝣱𝣸",
        "𝠃𝤙𝤞񀀙𝣷𝤀񅨑𝣼𝤀񆉁𝣳𝣮"
    ]
    result = segment_signwriting(" ".join(signs))
    assert result == signs

def test_segment_no_space():
    signs = [
        "𝠀񀀒񀀚񋚥񋛩𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭",
        "𝠀񂇢񂇈񆙡񋎥񋎵𝠃𝤛𝤬񂇈𝤀𝣺񂇢𝤄𝣻񋎥𝤄𝤗񋎵𝤃𝣟񆙡𝣱𝣸",
        "𝠃𝤙𝤞񀀙𝣷𝤀񅨑𝣼𝤀񆉁𝣳𝣮"
    ]
    result = segment_signwriting("".join(signs))
    assert result == signs

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
