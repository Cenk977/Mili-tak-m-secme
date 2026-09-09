/* Basit şifre kapısı — GitHub Pages statik hosting için.
 *
 * NOT: Gerçek güvenlik DEĞİLDİR. Şifre burada SHA-256 hash'i olarak duruyor,
 * düz metin görünmüyor; ama kararlı biri devtools ile aşabilir ve
 * results_data.js dosyasına doğrudan URL ile erişilebilir. Amaç: URL'e
 * rastlayan birini durdurmak.
 *
 * Şifreyi değiştirmek için: yeni hash'i üret
 *   python -c "import hashlib;print(hashlib.sha256('YENISIFRE'.encode()).hexdigest())"
 * ve PASS_HASH'i güncelle; sonra generate_static_site.py + git push.
 */
(function () {
  "use strict";

  var PASS_HASH = "61b8d3688b4a4b3b9fba98a32be0ee05e002bc4e6089d1281fb10c2bb0c1eb57";
  var KEY = "mts_auth_ok";

  // Yerelde (localhost) çalışırken kapıyı atla — geliştirme kolaylığı.
  var h = location.hostname;
  if (h === "localhost" || h === "127.0.0.1" || h === "") return;

  try {
    if (sessionStorage.getItem(KEY) === PASS_HASH) return;
  } catch (e) { /* sessionStorage yoksa devam, kapı gösterilir */ }

  // Sayfa içeriğini gizle (overlay yüklenene kadar boş görünsün)
  var hideStyle = document.createElement("style");
  hideStyle.id = "mts-auth-hide";
  hideStyle.textContent = "body>*:not(#mts-auth){display:none!important}";
  (document.head || document.documentElement).appendChild(hideStyle);

  async function sha256Hex(str) {
    var buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
    return Array.from(new Uint8Array(buf))
      .map(function (b) { return b.toString(16).padStart(2, "0"); })
      .join("");
  }

  function buildGate() {
    var wrap = document.createElement("div");
    wrap.id = "mts-auth";
    wrap.setAttribute("style", [
      "position:fixed", "inset:0", "z-index:2147483647",
      "display:flex", "align-items:center", "justify-content:center",
      "background:#f4f5f7", "font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif"
    ].join(";"));
    wrap.innerHTML =
      '<form id="mts-auth-form" style="background:#fff;border:1px solid #e3e3e6;border-radius:10px;' +
        'padding:26px 22px;max-width:320px;width:calc(100% - 32px);box-shadow:0 6px 24px rgba(0,0,0,.08);text-align:center">' +
        '<div style="font-size:15px;font-weight:700;margin-bottom:4px">Milli Takım Seçme 2026</div>' +
        '<div style="font-size:12px;color:#888;margin-bottom:16px">Devam etmek için şifre girin</div>' +
        '<input id="mts-auth-pass" type="password" autocomplete="current-password" inputmode="text" ' +
          'placeholder="Şifre" style="width:100%;font-size:14px;padding:9px 11px;border:1px solid #ccc;' +
          'border-radius:7px;outline:none;margin-bottom:10px">' +
        '<button type="submit" style="width:100%;font-size:14px;font-weight:600;padding:9px;border:none;' +
          'border-radius:7px;background:#1a1a1a;color:#fff;cursor:pointer">Gir</button>' +
        '<div id="mts-auth-err" style="color:#b00020;font-size:12px;margin-top:9px;min-height:14px"></div>' +
      '</form>';
    document.body.appendChild(wrap);

    var form = wrap.querySelector("#mts-auth-form");
    var input = wrap.querySelector("#mts-auth-pass");
    var err = wrap.querySelector("#mts-auth-err");
    input.focus();

    form.addEventListener("submit", async function (ev) {
      ev.preventDefault();
      err.textContent = "";
      var hex;
      try {
        hex = await sha256Hex(input.value);
      } catch (e) {
        err.textContent = "Tarayıcı desteklemiyor (HTTPS gerekli).";
        return;
      }
      if (hex === PASS_HASH) {
        try { sessionStorage.setItem(KEY, PASS_HASH); } catch (e) {}
        wrap.remove();
        var s = document.getElementById("mts-auth-hide");
        if (s) s.remove();
      } else {
        err.textContent = "Şifre yanlış.";
        input.value = "";
        input.focus();
      }
    });
  }

  if (document.body) buildGate();
  else document.addEventListener("DOMContentLoaded", buildGate);
})();
