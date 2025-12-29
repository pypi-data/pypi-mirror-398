from marsel import Marsel


def test_generate_random_otp_default_length():
    otp = Marsel.generate_random_otp()
    assert len(otp) == 6
    assert otp.isdigit()


def test_generate_random_otp_custom_length():
    otp = Marsel.generate_random_otp(length=4)
    assert len(otp) == 4
    assert otp.isdigit()
