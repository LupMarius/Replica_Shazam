import { useEffect, useState } from "react";

export default function TrimiteAudio({ fisier }) {
  const [trimite, setTrimite] = useState(false);
  const [rezultat, setRezultat] = useState(null);
  const [eroare, setEroare] = useState("");
  const [urlAmprenta, setUrlAmprenta] = useState("");

  useEffect(() => {
  if (!rezultat?.amprenta_npz) {
    setUrlAmprenta("");
    return;
  }

  const continut = atob(rezultat.amprenta_npz);

  const octeti = Uint8Array.from(
    continut,
    (caracter) => caracter.charCodeAt(0)
  );

  const arhiva = new Blob([octeti], {
    type: "application/octet-stream",
  });

  const url = URL.createObjectURL(arhiva);
  setUrlAmprenta(url);

  return () => URL.revokeObjectURL(url);
}, [rezultat]);

  async function trimiteAudio() {
    if (!fisier || trimite) return;

    setTrimite(true);
    setEroare("");
    setRezultat(null);

    try {
      const formular = new FormData();

      formular.append(
        "fisier",
        fisier,
        fisier.name || "inregistrare.webm"
      );

      const raspuns = await fetch("/api/analizeaza", {
        method: "POST",
        body: formular,
      });

      const date = await raspuns.json().catch(() => {
        throw new Error(
          "Raspuns invalid. Verifica serverul Python si configuratia Vite."
        );
      });

      if (!raspuns.ok) {
        throw new Error(
          typeof date.detail === "string"
            ? date.detail
            : "Cererea nu a putut fi procesata."
        );
      }

      setRezultat(date);
    } catch (error) {
      setEroare(error.message);
    } finally {
      setTrimite(false);
    }
  }

   return (
    <div>
      <button
        type="button"
        onClick={trimiteAudio}
        disabled={!fisier || trimite}
      >
        {trimite ? "Se trimite…" : "Trimite pentru analiză"}
      </button>

      {eroare && <p role="alert">{eroare}</p>}

      {rezultat && (
        <div>
          <p>Ultimul audio analizat: {rezultat.nume_fisier}</p>
          <p>Durată: {rezultat.durata_secunde} secunde</p>
          <p>Frecvență de eșantionare: {rezultat.fs} Hz</p>
          <p>Canale: {rezultat.canale}</p>
          <p>Timp în backend: {rezultat.timp_backend_ms} ms</p>
          <p>Repere extrase: {rezultat.numar_repere}</p>

          {Array.isArray(rezultat.candidati) && (
            <section>
              <h3>Candidate pentru verificare</h3>

              <p>
                Timp comparație: {rezultat.timp_comparatie_ms} ms
              </p>

              <p>
                Scorurile indică similaritatea, nu confirmă identificarea.
              </p>

              {rezultat.candidati.length === 0 ? (
                <p>Nu au fost găsite categorii comune.</p>
              ) : (
                <ol>
                  {rezultat.candidati.map((piesa) => (
                    <li key={piesa.piesa_id}>
                      <strong>{piesa.nume}</strong>

                      <p>
                        Scor: {piesa.scor.toFixed(3)}
                        {" — "}
                        Decalaj: {piesa.decalaj_secunde} s
                      </p>

                      <p>
                        Fragmente cu categorii comune:{" "}
                        {piesa.fragmente_cu_categorii_comune}
                        {" / "}
                        {piesa.fragmente_analizate}
                      </p>
                    </li>
                  ))}
                </ol>
              )}
            </section>
          )}

          {urlAmprenta && (
            <p>
              <a href={urlAmprenta} download="amprenta_interogare.npz">
                Descarcă amprenta numerică
              </a>
            </p>
          )}
        </div>
      )}
    </div>
  );
}