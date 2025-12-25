from .decryption import decrypt


def test_decrypt():
    key = "8iY5gyHxPH0YYyBgOd2AvwT1pcHl3EGtvN5jAi9JwoA"
    enc_message = "sIqpGK6UgzKOkThtlvBGqkb046EtB+HxcBsO3nDiKZAJcszfqqxTgSyH+SXAALznfuMSnZjdX9yzpGe77+ByYuCVlXHkMilkUe6tkFsFkBPW5CPirp0kqLdyp1yHXrv3NmXCtGZcef2fC0v89huRMSgFcm8M6Zf3JjSDEludLUo="
    dec_message = '{"db":"zip:/app/metabase.jar!/sample-dataset.db;USER=GUEST;PASSWORD=guest"}'

    dec = decrypt(enc_message, key)
    assert dec == dec_message

    key = "TkZFBIEqRM/C+qB20+lDv+zISuAXFVvBzsr5NrD6rgo="
    dec = decrypt(enc_message, key)
    assert dec != dec_message
