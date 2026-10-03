"""產生只含本頁用字的思源宋體（Noto Serif TC）子集字型。

修改 index.html 的中文內容後，重新執行一次：
    python tools/build_fonts.py
會更新 fonts/ 下的 woff2 檔，以及 index.html 中 <style id="tc-fonts"> 的 @font-face。
"""
import pathlib, re, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"
OUT = ROOT / "fonts"
WEIGHTS = (300, 400)
CHUNK = 420  # Google Fonts 的 text= 參數過長會失效，分段請求
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA})).read()


def main():
    html = HTML.read_text(encoding="utf-8")
    body = re.sub(r'<style id="tc-fonts">.*?</style>', "", html, flags=re.S)
    chars = sorted(set(c for c in body if ord(c) > 0x2E7F) | set(map(chr, range(0x20, 0x7F))))
    chunks = ["".join(chars[i:i + CHUNK]) for i in range(0, len(chars), CHUNK)]
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("noto-tc-*.woff2"):
        old.unlink()
    faces, first = [], []
    for w in WEIGHTS:
        for k, text in enumerate(chunks):
            css = get("https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@%d&text=%s"
                      % (w, urllib.parse.quote(text))).decode()
            urls = re.findall(r"url\((.*?)\)", css)
            assert len(urls) == 1, f"預期單一字型檔，實得 {len(urls)}"
            name = f"noto-tc-{w}-{k}.woff2"
            (OUT / name).write_bytes(get(urls[0]))
            ranges = ",".join("U+%X" % ord(c) for c in text)
            faces.append("@font-face{font-family:'Noto Serif TC Sub';font-style:normal;font-weight:%d;"
                         "font-display:swap;src:url(fonts/%s) format('woff2');unicode-range:%s}" % (w, name, ranges))
            if k == 0:
                first.append(name)
            print(name, (OUT / name).stat().st_size // 1024, "KB")
    block = '<style id="tc-fonts">\n' + "\n".join(faces) + "\n</style>"
    if '<style id="tc-fonts">' in html:
        html = re.sub(r'<style id="tc-fonts">.*?</style>', lambda m: block, html, flags=re.S)
    else:
        html = html.replace("</head>", block + "\n</head>", 1)
    HTML.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
