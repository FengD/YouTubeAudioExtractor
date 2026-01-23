function setStatus(msg, cls) {
  const el = document.getElementById("status");
  el.className = "statusText" + (cls ? " " + cls : "");
  el.textContent = msg || "";
}

function setBusy(busy) {
  const btn = document.getElementById("btn");
  const url = document.getElementById("url");
  const format = document.getElementById("format");
  btn.disabled = busy;
  url.disabled = busy;
  format.disabled = busy;
  if (busy) {
    btn.textContent = "Working...";
  } else {
    btn.textContent = `Extract ${getFormat().toUpperCase()}`;
  }
}

function getFormat() {
  const select = document.getElementById("format");
  return (select && select.value ? select.value : "mp3").toLowerCase();
}

async function extract() {
  const url = document.getElementById("url").value.trim();
  const format = getFormat();
  if (!url) {
    setStatus("Paste a YouTube URL first.", "err");
    return;
  }

  setBusy(true);
  setStatus(`Downloading audio and converting to ${format.toUpperCase()}… this can take a bit.`, "");

  try {
    const res = await fetch(`/api/extract?format=${encodeURIComponent(format)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, format }),
    });

    if (!res.ok) {
      let detail = "Request failed.";
      try {
        const data = await res.json();
        if (data && data.detail) detail = data.detail;
      } catch (_) {}
      throw new Error(detail);
    }

    const blob = await res.blob();
    const dispo = res.headers.get("content-disposition") || "";
    const match = dispo.match(/filename="([^"]+)"/i);
    const filename = match ? match[1] : `audio.${format}`;

    const a = document.createElement("a");
    const objectUrl = URL.createObjectURL(blob);
    a.href = objectUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(objectUrl);

    setStatus(`Done. Your ${format.toUpperCase()} download should have started.`, "ok");
  } catch (e) {
    setStatus(String(e && e.message ? e.message : e), "err");
  } finally {
    setBusy(false);
  }
}

document.getElementById("btn").addEventListener("click", extract);
document.getElementById("url").addEventListener("keydown", (e) => {
  if (e.key === "Enter") extract();
});
document.getElementById("format").addEventListener("change", () => {
  if (!document.getElementById("btn").disabled) {
    document.getElementById("btn").textContent = `Extract ${getFormat().toUpperCase()}`;
  }
});

