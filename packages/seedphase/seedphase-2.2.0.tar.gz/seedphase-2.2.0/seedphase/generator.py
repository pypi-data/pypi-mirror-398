from bip_utils import Bip39MnemonicGenerator, Bip39WordsNum

def generate_seed():
    mnemonic_12 = Bip39MnemonicGenerator().FromWordsNumber(
        Bip39WordsNum.WORDS_NUM_12
    )
    mnemonic_24 = Bip39MnemonicGenerator().FromWordsNumber(
        Bip39WordsNum.WORDS_NUM_24
    )

    print("\n12-word seed:")
    print(mnemonic_12)

    print("\n24-word seed:")
    print(mnemonic_24)
