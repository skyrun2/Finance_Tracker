import urllib.request
import os

os.chdir(os.path.dirname(__file__))

boundary = "----TestBoundary"
lines = []

lines.append(f"--{boundary}")
lines.append('Content-Disposition: form-data; name="file"; filename="teste.csv"')
lines.append("Content-Type: text/csv")
lines.append("")
with open("teste.csv", "rb") as f:
    lines.append(f.read().decode("utf-8"))

lines.append(f"--{boundary}")
lines.append('Content-Disposition: form-data; name="account_id"')
lines.append("")
lines.append("c2763dc1-98a5-4629-a386-5c9df071197b")

lines.append(f"--{boundary}--")

body = "\r\n".join(lines)
req = urllib.request.Request(
    "http://localhost:8000/api/v1/imports/upload",
    body.encode("utf-8"),
)
req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
resp = urllib.request.urlopen(req)
print(resp.status, resp.read().decode())
