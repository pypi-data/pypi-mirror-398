"""
Absfuyu: Fun
------------
Rubik

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)


Version added: 5.4.0
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["RubikNotations", "Rubik3x3"]


# Library
# ---------------------------------------------------------------------------
from typing import ClassVar, Self, cast, final

# Data
# ---------------------------------------------------------------------------
PLL_PIC = {
    "Aa": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAICSURBVHhe7do9TsNAEIZhhwNQQEtJxf3PQkVJCwUXSPKFjFhZrD3e3/l7JUQiRFg9HlsOm9OyLOfrV7TRDen88/ukR6fH6x9Q/voP98fRRoHEyAXS99vr/VFZbiapBsoF0tP7x+17KZSbSaqBYt8C1J7X0iK0vdzeAnCBKDc3k3QmHAbyMkmlQNThScpdm3ILkDBJWHMxkJdJygEBL3fQ06qRsIDSo6SlaiTOkdBeMVI6PdahqibJC9RhpPU1yANU9TUJWYdqgoQsQzVDQlahmiIhi1DNkVAK9fWiH6rrvlsK9Pz5ByclWt/e2rr/qyQ95dIJa1XNG2ha29a6hrzBTY+S1mtUdySk/WI+BAlphhqGhLRCDUVCGqGGIyFtUFOQkCaoaUhIC9RUJKQBajoSkg4lAglJhhKDhKRCiUJCEqHEISFpUCKRkCQosUhICpRoJCQBSjwSmg2lAgnNhFKDhGZBqUJCM6DUIaEUasS+Xtd9t97V7uuJ2Xfr/cHS9JRLJ4wT/e7W75n4YOmIfT31SKj3xdwEEuoJZQYJ9YIyhYR6QJlDQq2hTCKhFKo2s0gIUOupyk3W1s9MI60jsDUGPc9Nn/o77pLX/29iskAW7rhLWoPkgCiXSIhg9oCQy9PtSG5Pt6MFEqNAYhRIjAKJUSAxCiRGgcQokBip3ncb07JcAGos+ItnN7h+AAAAAElFTkSuQmCC",
    "Ab": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAHuSURBVHhe7dtNTsMwEIbhlAOwgC1LVtz/LKxYsoUFFyj90o4URYkztmN7/l4JkQqlVE+dUVTDZZqm6+0rSjQjXf/uD1p0eb79AuXP//Q4jhIFEqNAYhRIjAKJUSAxCiRGgcQokBi5Rvr9eH8cpXOLREAcKJdIa5gjKHdIBPLy+TV/p1JQrpD2gOjxHpTpj0r2UKijnyPTH5WkLp/cTCItgVKrhJs5pLOBkCmkFkDIDFIrIGQCqSUQUo/089YWCKned1sCvX7nA9H5R+eqvZk84xKj50idr/ZmcglUsoJyU4fUekhvpQppBBBSgzQKCKlAGgmExCONBkKikSQAIbFIUoCQSCRJQEgckjQgJApJIhASgyQVCIlAkgyEhiNJB0JDkTQAoWFIWoDQECRNQKg7kjYg1BVJIxDqhqQVCHVB0gyEmiP12BdrXdN9t9p9sdYN33frdYnV7OvRa0y9vmb7bksgiSsot9ORtA/prU5FsgiETkOyCoROQbIMhLKRALJEsQ6EqlaSByBUjOQFCFXPJOtAqBppPaMsVo2kob03EVcB50ow/Q84FCGVjAa1fzOZG+GUjgX2SrI0d3JWlJuVtC73DXcxk6iS2eRqJdUMb1e3ACVAyM1KKgVCrmZSSa5mUk2BxGi+3O6H0XbT9A9hSvCXpdP6AwAAAABJRU5ErkJggg==",
    "E": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAFrSURBVHhe7dkxbsIwGEBhwwEYysrI1PufhYmxKx16gUCBf4mK8xwH1VbeJ1UlqhT/ehLUJpuU0nD7UcY90vDzuHiHze62QOf33z5fK8NIgJEAIwFGAowEFEX6/jw+X/Vp7vw4UizQa6ia+VGk8Y17C1U7/2SkuOHH6Xz/HXoJtcT82UivFojr1kMtNX/R2e3Vojktnd3mzl/0322tjAQYCTASYCTASICRACMBRgKMBBQ9d7scHtv6/Rff1rdk7vye3SZ4doOMBBgJMBJgJMBIgJEAIwFGAowEGAkwEmAkwEiAkQAjAUYCjAQYCTASYCTASIDP3QCfu03wuRtkJMBIgJEAIwFGAowEGAkwEpCN9LtDjV3qWO5vrVhq/myk2L6PbxbXJdv7/7DU/Ojs9ldxvEADZ7fa+dFn0viGdIFW1M6PP7jjxr0FCjXzF31VMkcLb7ca+O22dkYCjAQYCTASYCTASEDRc7d1SukKxuWXT5bSG9QAAAAASUVORK5CYII=",
    "F": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAF7SURBVHhe7dmxTcNAHEbxCwNQMAMVNQMwBUMyBQNQUzEDBQuEyPjK+N53EpL/zvtJKE5z+J590jk+tdbOlz9tWCKdf/6+/IfT/eUfFB//bj3WBiMBRgKMBBgJmIr0/fS4HtUzc+5xpMqBunQOUaQ++MPn1/JZUT/3JBSOdIRAXRoK7bjT27OarQuPd9xHuHuuIXOLnt1mltwen92SecTPbn3Qystv5kLHW4Bk8L1K5+BPJQPxcrtVRgKMBBgJMBJgJMBIgO/dADeTA24mISMBRgKMBBgJmIr08vqxHtUzc+5xpMqBunQOUaQ++Pvb8/JZUT/3JBSOdIRAXRoK7bjT27OarQuPd9xHuHuuIXOLnt1mltwen92SecTPbn3Qystv5kLHW4Bk8L1K5+BPJQPxcrtVRgKMBBgJMBJgJMBIgO/dADeTA24mISMBRgKMBBgJMBJgJMBIgJEAIwFGAowEGAkwEmAkwEiAkQAjAUYCjAQYCTAS4Hu3odZ+AfiyiXn4ccLwAAAAAElFTkSuQmCC",
    "Ga": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAALwSURBVHhe7Zq9jtQwFEazPAAFtJRUiHJ7KKkpEI+IKKgpoadEVFvSQsEL7O43k6u9O9jJ/bNjJz7Saj3SjJM5ud+Nk8zVNE2393+DBU6Sbv+dX5Tg6un9Bjqf/8k8HiwwJAkYkgQcQtLfVy/nkY3DVJJHVJNnt7cffsyjx3z7fD2PHpDOT5Ke/bo5/ZeC+U2SNEfl+e+b6c8L3VF8//rTPHrMl58f59EDlvk1orpZAkBOSpAVbfSaiRtFDJFKxS0VNaCJsyVyokryNDwpkh6Ue48Ua08Ci5Jo4pKi+JdPVUuEKI8gkI1bSoxlI0txWBPEyb1XEjd8F7OgXNxy5iMrSiMIeCrKKoj4T1JOEL2OEKUVRHhEeVg9u+WkSbmMg1UQh8/x/et1Nm7efQeis1skEYIA/+ybd+mKimwN1SRFCSKWoscFefsRqCIpWhCREhUtCBSXxOMQKYhATyL4wYgSBIpKKlVBl/C5cXEcKQgUk1RLEEDE+AUw33YERSTxneRxKE2qR0VwWiedh2noXg3u20jgPaimIE70PoQuJlMRk1xbWaD9wsFLzR8V99DFZNROSeCn+RyR0QuRtJWgteqOEuWW1KogIkKUShI2wjfUuiDCK8pcSb0IIjyiTJJ6E0RYRbl6Uk+CCMs+q9ZJOftLG7auk6SCSq3DiOo33aSUqCCg7UVE9du3a2gFaeYnSZrINVdJpSqIIDnaimpGUmlBhEWUOm7WXLfKWvSabdy1kPamTRt3RMS0JwZt8960kmr1II7l7AY2kbSFIEIrCFSX1JsgUFXSloI8VJPUqyBQRVLPgkBxSfznwz0KAqd10nmYRvvcjcMFWT7fCsUWk7Uipl1Maim2mOSCeq4gIlxS7006RaikPQoCYZL2KgiESNqzIKCWBCFcyt4FAVclHUEQMEs6iiDg7kl7FwTcki571B5xSzoCzT3B1dLttdveWK0kL6OSDsKQJGBIEjAkCRiSBAxJAoYkAUOSgNXnboNpugNSNscojmPPkQAAAABJRU5ErkJggg==",
    "Gb": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAALbSURBVHhe7ZqxbtwwDIadPECGZM3YqciYPR07dyj6iEWHzBmTvWORqWPWdugLXPJfTIAQTjZFUTLp6gMOp/MBsv2JpKXTnU3TdHh7DRY4Sjr8e//QgrOLtxME7/98bg8WGJIEDEkCqiT9/fhhbu0btaT/RRBQSSJBl8+/j+97p3gKED2CSge2eArQUtCXm+9zq4yrl/bRrI4k6YhIJnufvv6cW9P0+ON2br1D36XHCZeTSZJjFVVcEEg/E7njtUjuQ1W4rUSlN07Rwo/zCLIWRde/dh/qKUDtk41uOE2jXqJSMUuiXCxwc8JSTonT1KRUCAacjqWDr6pJW2IRUTkZSyWkWhI6PdVxK2pFQUYqiMh9ZxZJW4m6+2xTo5aolsTNR4qoEkwiae+izNJtK1FPD+1FmUkCe40oU0lgj6LMJQEu6s91fFFN9924oKWfNOgxzutLDXxaYNFn82UJTzkeYRwadR4JUnLLEh5JuX7p2nLXBbosS3gERa1RzSWB6MW8iyQQWVQ3SSCqqK6SgDdR2IBYE9ddEogWUZtIAlxUT7go6TbWZpKAB1ESNpUEeqce0qy0eG8uKaVnjZLiarfk/te34zuQpqJmt4SgAVk6l7vdkl6pV5py7tKttajSegTcSQKtRHFBJU84l5KAtSitIOBWErASVSMIuJYEakXVCgLuJQGtKAtBIIQkUCrKShAIIwlIRVkKAqEkgTVR1oJAOEmAi+K0EASa7rtJsdh3s95r44T6O+Ap0D8XVNIHpWsuMoG7Ba4GLoj/imBJaEm8BpGgknmUlLCS0iJdOo8qIaQkLogX6Vaiwklae8y3EBVK0pogIicKbY04t5IghEuRCiIsIypEJJUKIqxEuZekFURwUVrC1CSNIG0NSgkjKa1RPXGxdjtFTkgaUdr+AUXZUkqif7eSpAxJAnr0H6YmbcmQJGBIEjAkCRiSBAxJAoYkAUOSABf7br6ZpleZlqpZ7/HSYgAAAABJRU5ErkJggg==",
    "Gc": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAL8SURBVHhe7Zq/jtQwEIdzPAAFtJRUiJIeSmoKxCOerqCmhJ4SUVHSQsELHPvL7uhGudiZv9k48SetNtFqbefzzKyd7M0wDPenV6fCKOn+3/kkg5unpw4ab//J5bhToUsS0CUJ6JIEdEkCuiQBXZKALknAoqS/r16OryPTI0nA4raEoujZz1/jeymq6PMpfVtyENySEEGlKNoLbklHKOpmSTx69i7KFUlHEaWWNK1BRxDlrklg76JCJIE9iwqTBPYqKlQS2KOocEmAi/rzon1Ri8/d6CKf/364cClckOX7W0G9wdXCU87aRo1dbHB5BLVao9IlgdaL+SqSQMuiVpMEWhW1qiRwTVHvPn6/HOlYXRJoTdRVJIFriPp692Z814pSr5OsIbtFSFqNwz8IkE54+opbuiLmKafpy7LiJjnNRdJaNUojiNhUumWLsggCqnQr5XCtU0s6aFJP0z7Grxa0pXTjZEWUVhDhkoROrR0vkZl6iKhSVszhkqTpyEKGKMuYTZJ49LQkio9VkwHmSGpNlFUQcC8mlzq3/LqV4IJoPJL2XYIift22HlEeQYRbEtiqqAhBIEQSuJaoElGCwFiTzofzaJ+7vX3/MLhvX3yDsxI9hpS7AHwWMciowj0HCitNJMYYGUEgbVvCB8dnNZtoQUSKJLB2jfrw+vZyFisIpEkCa4nibX/+8Um8PJCSKgnwwpkhiqczn5RIUemSQFZE8baoD806SsoqkkC0qDlBRLSo1SSBKFH8u6V1kGbJssQjSTBfsl/7TIpXVC2CpkBUhKxHkqjRqQw6j+jUKkojKJLZdCuJihBEaEV5BHmjv1iTpkIiBRElUTienhPWCPKIqhZuEpMhiFiKqAhBNH6rqKokkCmIKF18hCDCI2rxLsAcmo5wi0X7X26+DwPYapSwtA+kk592FyAaSJuK86DNDlMkaZDcqJ8yV5vAXMpJ26foVws6tb9JSRok7VsFAbTfRLpFYBFEHCKSPBwqkjx0SQK6JAFjTTofduYZhv+H7r9QKUdxcgAAAABJRU5ErkJggg==",
    "Gd": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAALLSURBVHhe7dmxbtRAEMZxhweggJaSCqVMDyU1BeIREQU1ZdJTIipKWih4gSTfcSMNy+16ZnbWu2PvX0Lnu6AL/G68ts9Xy7LcP/6ZFToh3f/5+6RFV08ff0Hw939y3p4VmkiCJpKgQyD9fvXyvGXrMJNUA3UIpGfff5werVCmU4Da8e0doUna5BTg+U/5P4j37vrjecs/7Yfc9WTyzfuvp8fbTzenR4peR+nP0jQnk4TjPkmtdi0OwUtfz/09bRYgqohEb+wNlZsUer00WZZqgFAWKYXxgtIC0fNaKCsQurgmcfkUR/vL+JqRA7pUDi1NsyZZurgm5UaTnlsnSgM0Wv8hASM3LaWfleoFhA/U+qHyVo9utb1+2w/Iq6ZIPSeIskx+WjOkvQChJkgc6O5LbCDkjrSnCaJckfYIhNyQegH9etEWCLncd+OHea81iN6z9H4cyPqVjKTVr0polHOf0toEWS8b6H1zU9l6F6NEX5WUGmENajlBlBlpr4v0pUxIRwJCaqSjAaEiEkD4F/JHBELiSToqEBIh8WnaEojXCwip1qQjAiEVEnY5vtu1aoRdjKdC2iIONErVlyVraS5LOBCtg2u7eJe7Jbla72qj7WI89e7WAmpkICRG4mPvCTU6EFJNkjdUBCCk3t28oKIAITUSqoWKBIRMSMgKFQ0ImZGQFioiEKpCQlKoqECoGgmtQUUGQi5ISDJREYGQy303ntc9OMl9t61qcoHLJwn/yRb33aihLnA1ff724bz172RFzR2JJo9DlY56EXJFSo9i2vOoUXNDyh3m+cIbFcoFae08KPpEqZEAwlHWgKjIUFWTJAWiclDYHhnOjKQFoiJOVPWapAGiokFVI6VrlDQONXrVSJZGX4PSutyczAFZpmuLa7eh7uBaGgKptj0gdVmTojWRBE0kQRNJ0EQSNJEETSRBE0mQ+323/bUsD7Leq1kMq2/FAAAAAElFTkSuQmCC",
    "H": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAGJSURBVHhe7dlBboJAHEZx7AF6mu7bZU/QQ3oCl+2+p+kFrKizIYJvJlE+4L3EVNJE5ScY/syu67rj6WETnZGOf5eNR7R7Pb3Bwl//5frcJhIJJBJIJJBIIJFAUUgfX7/XZ1nFIBWgRKgIpCFMGtTsSAXke/92/ltKgpoVaQyobKdARc1uY2hTObuFJBJIJJBIIJFAIoFEAokEEgkkEihq3e398zKW/Bz4WPKMnN3u5OwGEwkkEkgkkEggkUAigaqRklYxamv97FVISwYqtewDRmq5Gk6rdakKjSVrOIJuRb5wNJasFaiP7lvVkdRyqiUOuDXvgwfc1nM5sZYvAv9wrwGqBaiv6hKg9sUTa9mHKqS+JUO1fvZqpC0mEkgkkEggkUCuu4Fcd7sTHku2nkggkUAigUQCiQQSCSQSSCTQrEj9FfbY7eCp/z27WZHK+DHEKNspd0EjZrdbRwwF2szsNgRJOYJKMT/cBSYNqC/qVklLmznd0hMJJBJIJJBIIJFAIoGi1t0y67p/nuaai10GTQQAAAAASUVORK5CYII=",
    "Ja": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAHlSURBVHhe7dkhT8NAGMbxjg+AAItEESQeJBpB+IgEgUaCRxLUJBYEX2Db07VJt2zrc2/fdnnvnl9COARt9+/ddllnVVUtVj9yQB1p8b/+Ywyz09UJgh//pBnLAYpEUCSCIhEUiaBIBEUimCL9XV02oxiGXm9ypGiBWkOuO2nH3Z7o7Hte/2b07YjvHj+b0ab3l5tmdBi747ZcO+D4dCTrnTj/mVe/F/v/9+H6uRltev16akb+Um8ytdzGXGKIMWaQXVJfT/JMskzXvuPvWnLeyw0sr4GeSdAe2HtWdQOxYSysNxmSPt28Q0UIBKbvk3BS9oT7loNXIGa5pVzvNhz/KF+6ec4gJtIQOL5pxz3EVEvM06SRIgaCySJFDQSTRIocCEaPdHsfOxDUn27rob9uoI+3mIFgtC3AVEss7BagGyjyDGq5R4r+Jr2La6QcA4FbpFwDgUuknAPB4Ei5B4JBkUoIBOZIpQQCKhKCdKOUFAiSZ1JpgSApUomBwPSeVFIgMEXafo/KnSlSaY7ytMRTlk9LIlIkgiIRFImgSARFIigSYdTnbrnQZrKHNpMkRSIoEkGRCIpEUCSCIhEUiaBIBEUiKBJBkQiKRFAkgiIRFImgSARFIigSQZEIikRQJIKeu/WqqiUCWr67jAaMcgAAAABJRU5ErkJggg==",
    "Jb": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAHJSURBVHhe7dsxTgMxEIXhDQeggJaSipoeSk6AOCMFNSX0lIiKkhYKLhAyiS0ZKzbPG5sdj98vIbyKBNIn72ayC6tpmtabL5Zpi7T+3h20aHW8+QWd//wjt2aZiAREJCAiAREJiEhARAIiEhCRgIZC+ro4d6uyhkHyQHOghkCKYUqhzCN5kJO39+13XwmUaaQUkD9GoYa6VZJCy8VbJWBEAiISEJGAiAREJCAiAQ313O3zbDcnnX7gc5LEYfKPOEyCEQmISEBEAiISEJGAiAREJCAiAZmfuK9vX9zqd0/3l26VjxM3mHkk2THorkk1xE5KnXJo5pFCoIfXO7cqyzRSCHTIKWf23W0fEO8nBdXaQT5zSLWBJFNILYAkM0itgCQTSC2BpO6Rrm7aAkldP3cLgZ4f2wBJ3c5Jc06xoeakEKjlDvJ1h9T6Ir2vrpCWAJK6QVoKSOoCaUkgST3S0kCSaiQNQJJaJC1AkgokAQlRNAFJ6nZSTSCZsP2UHZd7LU4VUu0dlPpHG3+MfjxReU2qeYqloEo+v6lEiq9RhxaDlABJKpFa5GFKgaSh/kR5TmYfKdWOSEBEAiISEJGAiAREJKCun7v9T9P0A4HGuqkeGiXTAAAAAElFTkSuQmCC",
    "Na": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAIqSURBVHhe7dsxTsQwEIXhLAeggJaSipoeSk7AITkBJfTUVJS0UHCBZR8kYojk7Njx2G8c/xIi0UogfbK9Sby7G4Zhf/jpLfSDtP/6PbFod3r4B87//sl43FuoIynqSIo6kqKOpKgjKepIilTXSZ9Xl+PR/85e38ajcLHXMbf3L8PTw/V4drzNXScBSP5mKQkJI0gzimKawzBBJSGFpl9qE8h8mrFARSHJ0ZMLKgQ0nTNARS3cE5IEOjbtUhZupF28aRbu+RpkMaKYS3532xJUMhLaCtQqJLQFqNVIqHWoLEioZahsSKhVqKxIqEWo7EhIQn1c+Icy3XeTQOfvf3BL3dz9XnE/P+ofl1hnvu8mp5wcYaHc3pasSY4gr2uUORLyvpgXQUKeoYohIa9QRZGQR6jiSMgbVBUk5AmqGhLyAlUVCXmAqo6EJBRjFEiIGYoGCbFOPSqkeSxQ1EiIAYoWiWnqUY8kFij66cYARY+EakO5QEI1odwgoVpQrpBQDSh3SEhCldjXM913Sylm3y1lXy8l8303648DyiknR1iuiuy7WVdiX889ErJezJtAQpZQzSAhK6imkJAFVHNIKDdUk0goJ1SzSCgEheMYuKaRUI4R1TwSWgtVHQm3IaGvay29FpuEiq06Uuh7bdO59h5uqdg1aB7FdAtB5QDKEdVTAImkBWri07cxTTAsI2iK7nlSbJsbSax1JEUdSVFHUtSRFHUkRXT7bnwNwzcsDAXYOLVy1wAAAABJRU5ErkJggg==",
    "Nb": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAIgSURBVHhe7dsxTsMwFMbxlAMwwMrIxMwOIyfgkJyAEXZmJkZWGLhA6UdjyURJ+uL42d9z3l+qSIoUpJ9sK8Htruu6/eHlzfSHtP85nmi0Oz/8AePXP+uPvZkcSZAjCXIkQY4kyJEEOZIguvuk+8e37uXptj87nfT63zfX/dH/Lt4/+qPx6O6TABT/ZIkGaQiTGwoj5tSomYoCaQgSpltuqKkpd6rqSAFiuA7lhoqBlo4oqoV7CmwuyfXHgMJ75hZujaZGEI6lI6pppDVTLK5ZpFxAqEmknECoOaTcQKgpJA0g1AySFhBqAkkTCJlH+rrSBUJU+253D8c77tdn2R13DHT5qQOEzD6WaE+xkNnHkhhIcwSFzCGVGkFxppBqACEzSLWAkAmkmkCIHqk2EKJGYgBCtEgsQIgSiQkIUU83BiBEi8QChGiQ2KZYHAVSDMRYdSR2IFQViXmKxVVDsgKEqiBZAkLFkawBoaJIFoFQMSSrQKgIkmUgpI5UYl9MO9V9t6X7Ykv33Uqltu+WMsW0Pg64JrV9txioxL6YdtmRrC/SY2VFahEIZUNqFQhlQWoZCK1Gah0IrULaAhASIwEkRtkKEEoaSVsCQouRtgaEktekXEB4FJn6utbc70qWjDRco1Kb+l5bOF/yHKdVMlLOhhBMQIjy07dICmT2vwCpBRiWERSiGkkpbW4kseZIghxJkCMJciRBjiRIdd+tjbruF/dWBdg2pAhsAAAAAElFTkSuQmCC",
    "Ra": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAHFSURBVHhe7do7UsMwFIVhhwVQsAYq6vRQsgIWyQoooadOxRoo2EDICfagMNg+V7ItXen8MwymIc6Xa+EHu67rjqcvNdEZ6fj188Ma7a5PL+D891/122oiIREJiUhIREIiEhKRkIiikD7vbvstH6XurxnJG9BQyn6bkIYXujl8nL97adjfWCj6ssTrBP2X5UOmL0tqAkLW92OeJOuhVtIFbsx7MF3gph7XuYv9kJFp4fYKlQKEzKcAsS+Uu5T91k23mUxrUssJiUhIREIiEhKRnrsR6RRgJp0CkAmJSEhEQiISEpGQiIRERJ0nPTy991uXvT7v+63xdJ7USFFImCBmimopCmns8Ks1E1I4PS1BmSepRajouwAh0NT61PRft5YmKhoJtQKVhIRagEpGQrVDLYKEaoZaDAnVCrUoEqoRanEkFELdP/qHWvW5Wwj09vIL563Vn7uFh1w4YUtVxf2kcIK8rlGrIyHvi/kmSMgz1GZIyCvUpkjII9TmSMgbVBYkNAaF7dLgsiEhLxOVFQl5gMqOhEKoEsuOVOIa9LciJqn09I+lM21ygVtDQiISEpGQiIREJCQiIREJiUhIRKs+d6ujrvsGdDW0Lec+UFYAAAAASUVORK5CYII=",
    "Rb": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAG9SURBVHhe7dqxUcNAEIVhmQIIqIGImBxCKqBIKiCEnJiIGghowPgZ3czhsa13K521e/f+GQaRIPnzSj4hNsMwbHdf6kx7pO3P3w812lzvdhD891+N2+pMQiISEpGQiIREJCQiIRHNQvq+ux23YmQ9XjNSNKCU5bhNSGlHN59f++9RSsdbClV8WxJ1go7FvMnFtyUtASH29ZgniT3VPN7glrwG0w2u9bz2UumbjEwX7qhQFiBkXgKU7shLluPWH90mMl2TekxIREIiEhKRkIj03I1IS4CJtAQgExKRkIiERCQkIiERCYmom3XS4/PHuPW/t5f7cet4WieRdYOEiZmamlN1NUmnTrmpukHKgUonqgukOUCo+U+32UCtf7rNBUo1i7QUEGoSaUkg1BzS0kCoKaQaQKgZpFpAqAmkmkAoPNLDU10gFPq5Ww70/loHCIVdcdc+xVJhV9w5UM0JSoVDutQE5YVCWgMIhUFaCwiFQFoTCLlHWhsIuUICSI7iAQi5nSQvQMglkicg5Pqa5AEIuUY6vEatlWskL+kfSydq/pHSUgmJSEhEQiISEpGQiIREJCQiIRGFfu52mYbhFyeGtC1UL+rcAAAAAElFTkSuQmCC",
    "T": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAGRSURBVHhe7dkxTsNAEEBRhwNQQEtJRc0BOAWH5BQcgDoVJS0UXCDETqaxYu+fFUh49z8pii0kR/tjI0+8G4bhcHxpxRTp8H3a+Qu76+MHbPz4V+dtrTASYCTASICRACMB3UT6erg/b+V1ESkC1YZqPtI8TE2opiNFkJv9+/QesqGajbQUKPYzobqZ3ZailTi7QUYCjAQYCTASYCTASICRACMBRgK6ee72eXcaS24/cmPJyNmtwNkNMhJgJMBIgJEAIwFVkZ6e385b20bXkY7USqBA1pOKFAd8fXmc3rcu1lEKhSO1FiiQUGgsIadkK+YnAR5LWjt7liytMzXg1lxy/33ALa0pPeDGgVq5/OiXnr4FyJxFW0DW4+9JBenLrVdGAowEGAkwEmAkwOdugPdJBd4nQUYCjAQYCTASYCTASICRACMBzUYa77DjLntu7W+XNBspxo95jNjPjCfNz26XzphUoB5mt3mQ7IA76uIfd4SpCTTq5qeSWl1cbr/BSICRACMBRgKMBBgJ6Oa5W71h+AGr6qDhlFnaCQAAAABJRU5ErkJggg==",
    "Ua": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAHySURBVHhe7dnLUcMwFIVhhwKohj0sqYAiqYAl7KmGBpIcJxo0mTg6V7562eebYXA2RPNbko19mKbpeP6RB+ZIx7/LhxIOz+cvGPzvP12P5QFFIigSQZEIikRQJIIiERSJoEgERSIoEkGRCIpEUCSCIhEUiaBIBEUiKBJBkQiKRFAkgt67EfTeLUHv3UiKRFAkgiIRsiK9ffxej/bBHGlvgcAUKQT6/nyZf+8FfZ+0pRlkOcn0fdIel1jMPJOsS21Xd9whjjbuhL2GyvoHF5HYZdd6uS2dUMv4zfdJYN2XRkdHwhkZcZnhhK49qeaZNGKotWM2X91gpFDxWHNnVNbVDUYI5REIsq9uQerLW13d3AJ5XN16nFFegYKsSNBrKO9AkB0JegtVIhDMe9LlMN/r+//gfr78BmdRcgxZG/c9S2exxsYdB/KcQZC9cd/TaumVDBS4RYLaoUrtQbdcI0GtULUCgXskiAcdLwcvcaAaF4oikaDUjKo5g4JikcA7VItAUDQSxMthTahWgaB4JFg7o1oGgiqRIDdU60BQLRJYQ/UQCKpGgqVQOL79HLQMBNUjQWpG9RQImkSCVCjoIRC4PQVYknoKcBvIGqbGU4ZmMwlxlmZQb5pFGknz5bbWppfbSBSJoEgERSIoEsHlvdu2TdMJn8jmJ8fDhbIAAAAASUVORK5CYII=",
    "Ub": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAHySURBVHhe7drBUcMwFIRhhwKohjscqYAiUwFHuFMNDYSsEw2aTGzvk/QkOdpvhsE5EIk/kmNiDtM0nc5fsmKOdPq9PPBweD4PsPPnf7oeywpFIigSQZEIikRQJIIiERSJoEgERSIoEkGRCIpEUCSCIhEUiaBIBEUiKBJBkQiKRFAkgu67EXTfbYPuu5EUiaBIBEUiDBXp7ePnemQz3EpKCTVUpK/jy/zdGsp8nZS6ZHsUoq0Z/jqJfcGHvOIOcbSSFlgCBUNeAlgCgWm7Le3htUF72m6YvznQaNvNGijIioRBUwduCStqaVfckxXJMlAvUuacFClePXsKFc/VsgOSV9LeQqUGguyLya3Be3h3ywpU4t2t9xWVEyjIjgS9hioRCIpEgt5ClQoE8znpcljG6/v/5L4/8yaXqvQcXD4FiF9FTLLmibvkCgK3P0viycWvqrfSgQKXSFD7HOUVCNwiQa1QnoHANRLEJ06PUPF29ggE7pHAa0V5r6CgSiQoHapWIKgWCUqFin+2xrVY1UiQG6rmCgqqR4LUUC0CQZNIYA3VKhA0iwRLoXB8+zioHQiaRoKtFdU6EDSPBEu/fA+BoMv/BbhdUWuBUp7fwu1TgNIQ7d5WrGUXkVrrcrtZaLt1QpEIikRQJIIiEYrfd3s80/QHRtfoJ68+66IAAAAASUVORK5CYII=",
    "V": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAIWSURBVHhe7doxTgMxEIXhDQeggJaSipoeSk7AITlBSuipqShpoeACIS/sKkPErsbrGXvGnl+KtDQgPo29FmYzDMNu/4kWOiDtvn+/0Ghzvv8Bzr//2fgcLRRIjAKJUSAxCiRGgcQokBiZOCfdP76OT397frodn+YzdU76urn+99NDJpcbJogzRaVajXTx9n74aDS3/Gq1GkljqdHpsQSVjESnpxco9tttApmQKNDSslv79qFAS/tTibdb1hGAA5XzS3CgSiBlvd16WXrZR4AeoLKRUOtQIkioZSgxJNQqlCgSahFKHAlRqM8rXai7B30o1Xs3CnT5cYSTigK9bI9w0qn/PYkuOTphUtElRydMquzDJCc6QRp7FJ0grT1KHQl538yLICHPUMWQkFeookjII1RxJOQNqgoS8gRVDQl5gaqKhGpB4ZkLVx0JWZ8oE0jIMpQZJFQSKiVTSEgLKmUPOs0cEtKeqNRM/OvNXBSIwtHM37tpZ2WiTCMhC1DmkVBtKBdIqCaUGyRUC8oVEqoB5Q4JUSiNe73TVO/dtNO+15syfZjkRJccnTCpzB8mOWnf6yH3SEh7M28CCWlCNYOEtKCaQkIaUM0hIWmoJpGQJFSzSEgKqmkkNAeFZy5c80god6K6QEI5UN0gIQqVUjdIKXvQaV1N0trc/6mk+3s3KwUSo0BiFEiMAolRIDEKJEau793KNAw/I0AwLpLA1aEAAAAASUVORK5CYII=",
    "Y": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAIvSURBVHhe7do9TsNAEIZhhwNQQEtJRU0PJSdAnJGCmhJ6SkRFSQsFFwj5gldMItuZ3ZnFM+t5pYilCdKj8fqPVdd1680nmmiLtP7+/aVGq+PNH3D+/Uf9OpookBgFEqNAYhRIjAKJUSAxYl0nfV2c96vdTt7e+9V43OuY69uXfrXb0/1lvxourpOMVISECeJMUU6YmENTM1dFSGOHn7SxQ27uspDo9GhDUSBrE5U9STWgLAOh4qcAFGhqfzp09pECmT67aUyU9QlKFSMhCZQXICRCQiVQnoCQGAnlQHkDQipIiAPlEQipIaEpKK9ASBUJDUF5BkLqSIhCXd34BkJV37tRoOdHn0Co2ns3eog9vN5tf9IJ08rt8yQKRCeIex1lLXWkoU2ac3lgOVWkqbOYZyg1JM5p3iuUChIHKOURSoyUA5TyBpWFBBCKUgKU8gRVPEkSoJQXqCIkDaCUByjRniQFSlmHEiHt71GSLEOJkLSzCmXyH0spEIUbyu0NrjRrE2USCVmCMouErECZRkIWoMwjobmhXCChOaHcIKG5oFwhoTmg3CEhCvV5Vh+q6nu32lGg048/OO1M3pbkRA85OmFamb0tyYlOUK09yj0Sqr2ZN4GEakI1g4RqQTWFhGpANYeEtKGaREKaUM0ioTEorHPgmkZCGhPVPBKSQi0CCVGo3BaBlLsH7beYSZLk/inAYl9OWiuQGAUSo0BiFEiMAolRIDEKJEau37v9T133A/cUFsjTSnS4AAAAAElFTkSuQmCC",
    "Z": "iVBORw0KGgoAAAANSUhEUgAAAEkAAABJCAYAAABxcwvcAAAABGdBTUEAAK/INwWK6QAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAHcSURBVHhe7drNTcNAEMVxhwKohjscqYAiqYAj3KmGBkJe4pUW5MQT79d74/lLSCYHY/0ytldaDtM0HU8/0Y3OSMefyy8tOjye/oD4+R/m4+hGgWQokAwFkqFAMhRIhgLJEM066eXtez762+f703y0XKyTSKJBwsSsTc2oqCbp2i03OhqkHIhtoiiQmIHQ8LdbKZD7txv7BKWGIakAoSFISkCoO5IaEOqKpAiEuiGpAqEuSMpAqDnS86s2EGq675YDfX1oAqFmK+5et5jsijsHUp6gVHUk9Yf0UlWRPAKhakhegVAVJM9AqBjJOxC6CwkgOcoegNBd66SEAhArUI91jOX8+fXmrX25m9dJe5mgVNEzSQkI17r1eouQMFHXxpixrdda/HZTqeQRQfMPE1uznH8JKH22Bobzu0cqmSCE87u+3UqBUm6RagEhl0g1gZA7pNpAyBVSCyDkBqkVEHKB1BIIySP12Ndruu/Wul77erIr7ta3WEp2xZ0D9djXk0PqNUF5UkgjgJAM0iggJIE0EgjRI40GQlRIAMlRGIAQ7SSxACFKJCYgRP1MYgBC1Ej/n1GjokZiaRf7biW531KqVSAZCiRDgWQokAwFkqFAMhRIhgLJkPS+W5+m6RfQoucBXsykVgAAAABJRU5ErkJggg==",
}


# Class
# ---------------------------------------------------------------------------
class RubikNotation:
    """
    Rubik Notation

    Parameters
    ----------
    notation : str
        Notation (abbreviated name)

    is_counter_clockwise : bool | None, optional
        Is counter clockwise, by default ``False``

    note : str | None, optional
        Note, by default ``None``
    """

    _BASIC_NOTATION: ClassVar[dict[str, str]] = {
        "L": "Left",
        "R": "Right",
        "U": "Up",
        "D": "Down",
        "F": "Front",
        "B": "Back",
        "M": "Middle",
        "E": "Equator",
        "S": "Side",
        "X": "x axis",
        "Y": "y axis",
        "Z": "z axis",
    }
    _COUNTER_CLOCKWISE_SYMBOL: ClassVar[str] = "'"

    def __init__(
        self,
        notation: str,
        is_counter_clockwise: bool = False,
        /,
        *,
        note: str | None = None,
    ) -> None:
        """
        Rubik Notation

        Parameters
        ----------
        notation : str
            Notation (abbreviated name)

        is_counter_clockwise : bool | None, optional
            Is counter clockwise, by default ``False``

        note : str | None, optional
            Note, by default ``None``
        """

        self.notation = notation.upper().strip()
        self.is_counter_clockwise = is_counter_clockwise

        self.direction = (
            "Counter Clockwise" if self.is_counter_clockwise else "Clockwise"
        )

        long_notation_name = self._BASIC_NOTATION.get(self.notation[0], self.notation)
        self.full_notation = long_notation_name + (
            f" ({self.direction})" if is_counter_clockwise else ""
        )

        self.note = None if note is None else note

    def __str__(self) -> str:
        # return f"{self.__class__.__name__}({self.notation})"
        notation = (
            f"{self.notation}{self._COUNTER_CLOCKWISE_SYMBOL}"
            if self.is_counter_clockwise
            else self.notation
        )
        return notation

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def from_str(cls, string: str) -> Self:
        if cls._COUNTER_CLOCKWISE_SYMBOL in string:
            return cls(string[:-1].upper(), True)
        return cls(string)


@final
class RubikNotations:
    """
    Constant Rubik Notations
    """

    U = RubikNotation("U")
    D = RubikNotation("D")
    L = RubikNotation("L")
    R = RubikNotation("R")
    F = RubikNotation("F")
    B = RubikNotation("B")

    M = RubikNotation("M", note=f"Rotate according to {L} face")
    E = RubikNotation("E", note=f"Rotate according to {D} face")
    S = RubikNotation("S", note=f"Rotate according to {F} face")

    U_REV = RubikNotation("U", True)
    D_REV = RubikNotation("D", True)
    L_REV = RubikNotation("L", True)
    R_REV = RubikNotation("R", True)
    F_REV = RubikNotation("F", True)
    B_REV = RubikNotation("B", True)

    M_REV = RubikNotation("M", True, note=f"Rotate according to {L} face")
    E_REV = RubikNotation("E", True, note=f"Rotate according to {D} face")
    S_REV = RubikNotation("S", True, note=f"Rotate according to {F} face")

    X = RubikNotation("x", note=f"Rotate according to {R} face")
    Y = RubikNotation("y", note=f"Rotate according to {U} face")
    Z = RubikNotation("z", note=f"Rotate according to {F} face")

    X_REV = RubikNotation("x", True, note=f"Rotate according to {R} face")
    Y_REV = RubikNotation("y", True, note=f"Rotate according to {U} face")
    Z_REV = RubikNotation("z", True, note=f"Rotate according to {F} face")


class RubikAlgorithm:
    """
    Rubik Algorithm

    Parameters
    ----------
    case : str
        Case name

    solution : str | list[str] | list[RubikNotation]
        Solution/Algorithm

    other_solutions : None | list[list[str]] | list[list[RubikNotation]] | list[Self], optional
        Other Solution/Algorithm, by default ``None``

    note : str | None, optional
        Note, by default ``None``

    picture : str | None, optional
        Picture of case (in base64 format), by default ``None``
    """

    def __init__(
        self,
        case: str,
        solution: str | list[str] | list[RubikNotation],
        other_solutions: (
            None | list[list[str]] | list[list[RubikNotation]] | list[Self]
        ) = None,
        note: str | None = None,
        picture: str | None = None,
    ) -> None:
        """
        Rubik Algorithm

        Parameters
        ----------
        case : str
            Case name

        solution : str | list[str] | list[RubikNotation]
            Solution/Algorithm

        other_solutions : None | list[list[str]] | list[list[RubikNotation]] | list[Self], optional
            Other Solution/Algorithm, by default ``None``

        note : str | None, optional
            Note, by default ``None``

        picture : str | None, optional
            Picture of case (in base64 format), by default ``None``
        """

        self.case = case.strip()
        self.solution = self._convert_solution(solution)

        self.other_solutions = other_solutions
        self.note = note
        self.picture = picture

    def __str__(self) -> str:
        # return f"{self.__class__.__name__}({self.case})"
        # return f"{self.solution}"
        return f"{self.__class__.__name__}({self.case} - {self.solution})"

    def __repr__(self) -> str:
        return self.__str__()

    def _convert_solution(
        self, solution: str | list[str] | list[RubikNotation], /
    ) -> list[RubikNotation]:
        if isinstance(solution, str):
            sols: list[str] = solution.replace("(", "").replace(")", "").split()
            return [RubikNotation.from_str(x) for x in sols]

        if isinstance(solution, list) and len(solution) > 0:
            if isinstance(solution[0], RubikNotation):
                return cast(list[RubikNotation], solution)
            else:
                return [RubikNotation.from_str(x) for x in solution]  # type: ignore[arg-type]

        raise ValueError("Wrong value type")


class Cross(RubikAlgorithm):
    """Cross Algorithm"""

    pass


class F2L(RubikAlgorithm):
    """F2L Algorithm"""

    pass


class OLL(RubikAlgorithm):
    """OLL Algorithm"""

    pass


class PLL(RubikAlgorithm):
    """PLL Algorithm"""

    pass


class PLLs:
    """
    Collection of PLLs
    """

    Aa = PLL(
        "Aa",
        "x (R' U R') D2 (R U' R') D2 R2",
        other_solutions=[
            PLL(
                "Aa",
                "(r U r' U') (r' F r2 U') r' U' (r U r' F')",
                note="Headlight at Left (solve like T perm but is `r` instead of `R`)",
            )
        ],
        note="Headlight at Back",
        picture=PLL_PIC["Aa"],
    )

    Ab = PLL(
        "Ab",
        "x (R2 D2) (R U R') D2 (R U' R)",
        note="Headlight at Right",
        picture=PLL_PIC["Ab"],
    )

    E = PLL(
        "E", "x' (R U' R' D) (R U R' D') (R U R' D) (R U' R' D')", picture=PLL_PIC["E"]
    )

    Ua = PLL(
        "Ua",
        "(R U' R U) R U (R U' R' U') R2",
        note="Finished face at Back",
        picture=PLL_PIC["Ua"],
    )

    Ub = PLL(
        "Ub",
        "R2 U (R U R' U') R' U' (R' U R')",
        note="Finished face at Back",
        picture=PLL_PIC["Ub"],
    )

    Z = PLL(
        "Z",
        "M2 U' M2 U' M' U2 M2 U2 M' U2",
        other_solutions=[
            PLL(
                "Z",
                "M' U' M2 U' M2 U' M' U2 M2 U",
                note="Switch edge at Right and Front",
            )
        ],
        note="Switch edge at Left and Front",
        picture=PLL_PIC["Z"],
    )

    H = PLL("H", "(M2 U' M2) U2 (M2 U' M2)", picture=PLL_PIC["H"])

    T = PLL(
        "T",
        "(R U R' U') (R' F R2 U') R' U' (R U R' F')",
        note="Headlight at Left",
        picture=PLL_PIC["T"],
    )

    F = PLL(
        "F",
        "R' U' F' (R U R' U') (R' F R2 U') (R' U' R U) (R' U R)",
        note="Finished face at Left",
        picture=PLL_PIC["F"],
    )

    Ja = PLL(
        "Ja",
        "(R' U L' U2) (R U' R' U2 R) L U'",
        note="Finished face at Front",
        picture=PLL_PIC["Ja"],
    )

    Jb = PLL(
        "Jb",
        "(R U R' F') (R U R' U') R' F R2 U' R' U'",
        note="Finished face at Left",
        picture=PLL_PIC["Jb"],
    )

    Ra = PLL(
        "Ra",
        "(R U R' F') (R U2' R' U2') (R' F R U) (R U2 R' U')",
        note="Headlight at Left",
        picture=PLL_PIC["Ra"],
    )

    Rb = PLL(
        "Rb",
        "(R' U2 R U2') R' F (R U R' U') R' F' R2 U'",
        note="Headlight at Front",
        picture=PLL_PIC["Rb"],
    )

    V = PLL(
        "V",
        "(R' U R' d') (R' F' R2 U') (R' U R' F) R F",
        note="Block at Left Front",
        picture=PLL_PIC["V"],
    )

    Y = PLL(
        "Y",
        "F (R U' R' U') (R U R' F') (R U R' U') (R' F R F')",
        note="2 pieces have same color at Front and Right",
        picture=PLL_PIC["Y"],
    )

    Na = PLL(
        "Na",
        "(R U R' U) (R U R' F') (R U R' U') (R' F R2 U') R' U2 (R U' R')",
        note="Edges need to swap at Left and Right",
        picture=PLL_PIC["Na"],
    )

    Nb = PLL(
        "Nb",
        "z R' U' R D' R2 U R' D U' R D' R2 U R' D z'",
        note="Edges need to swap at Left and Right",
        picture=PLL_PIC["Nb"],
    )

    Ga = PLL("Ga", "R2 u R' U R' U' R u' R2 y' R' U R", picture=PLL_PIC["Ga"])

    Gb = PLL(
        "Gb",
        "(R' U' R) y R2 u (R' U R U' R) u' R2",
        other_solutions=[
            PLL("Gb", "R' U' R U D' R2 U R' U R U' R U' R2 D", note="Headlight at Left")
        ],
        note="Headlight at Left",
        picture=PLL_PIC["Gb"],
    )

    Gc = PLL(
        "Gc",
        "R2 F2 R U2 R U2 R' F (R U R' U') R' F R2",
        note="Headlight at Right",
        picture=PLL_PIC["Gc"],
    )

    Gd = PLL(
        "Gd",
        "R U R' U' D R2 U' R U' R' U R' U R2 D'",
        note="Headlight at Left",
        picture=PLL_PIC["Gd"],
    )


class Rubik3x3:
    PLL = PLLs()
