import { useEffect, useRef, useState } from "react";
import TrimiteAudio from "./TrimiteAudio";

export default function CapturaAudio() {
  const [stare, setStare] = useState("inactiv");
  const [eroare, setEroare] = useState("");
  const [inregistrare, setInregistrare] = useState(null);
  const [urlAudio, setUrlAudio] = useState("");

  // Referinte la captura si la obiectul care inregistreaza.
  const fluxRef = useRef(null);
  const recorderRef = useRef(null);
  const activRef = useRef(true);

  // Eliberam captura daca aceasta componenta este inchisa.
  useEffect(() => {
    activRef.current = true;

    return () => {
      activRef.current = false;

      const recorder = recorderRef.current;

      if (recorder && recorder.state !== "inactive") {
        recorder.stop();
      }

      fluxRef.current?.getTracks().forEach((pista) => pista.stop());
    };
  }, []);

  // Construim o adresa locala pentru ascultarea inregistrarii.
  useEffect(() => {
    if (!inregistrare) return;

    const url = URL.createObjectURL(inregistrare);
    setUrlAudio(url);

    return () => URL.revokeObjectURL(url);
  }, [inregistrare]);

  function opresteInregistrarea() {
    const recorder = recorderRef.current;

    if (recorder && recorder.state !== "inactive") {
      setStare("finalizare");
      recorder.stop();
    }

    // Oprim inclusiv partajarea ecranului.
    fluxRef.current?.getTracks().forEach((pista) => pista.stop());
  }

  async function pornesteInregistrarea(sursa) {
    setEroare("");

    if (!window.MediaRecorder) {
  setEroare("Browserul nu permite inregistrarea audio.");
  return;
}

if (
  sursa === "sistem" &&
  !navigator.mediaDevices?.getDisplayMedia
) {
  setEroare("Browserul nu permite partajarea ecranului.");
  return;
}

if (
  sursa === "microfon" &&
  !navigator.mediaDevices?.getUserMedia
) {
  setEroare("Browserul nu permite accesul la microfon.");
  return;
}

    // Pentru primul test folosim WebM cu audio Opus.
    const tipAudio = "audio/webm;codecs=opus";

    if (!MediaRecorder.isTypeSupported(tipAudio)) {
      setEroare("Formatul audio nu este acceptat. Testeaza in Chrome.");
      return;
    }

    setStare("selectare");

    let flux;

    try {
      if (sursa === "microfon") {
    flux = await navigator.mediaDevices.getUserMedia({
    video: false,
    audio: {
            echoCancellation: false,
            noiseSuppression: false,
            autoGainControl: false,
        },
        });
        } else {
        flux = await navigator.mediaDevices.getDisplayMedia({
            video: true,
            audio: true,
            systemAudio: "include",
     });
}
      // Dialogul poate ramane deschis dupa inchiderea componentei.
      if (!activRef.current) {
        flux.getTracks().forEach((pista) => pista.stop());
        return;
      }

      fluxRef.current = flux;

      const pisteAudio = flux.getAudioTracks();

        if (pisteAudio.length === 0) {
        throw new Error(
            sursa === "microfon"
        ? "Nu a fost primita o pista audio de la microfon."
        : "Nu a fost partajat sunetul. Activeaza partajarea audio in dialogul browserului."
        );
    }

      // Inregistram doar audio, desi browserul ofera si video.
      const fluxAudio = new MediaStream(pisteAudio);
      const recorder = new MediaRecorder(fluxAudio, {
        mimeType: tipAudio,
      });

      recorderRef.current = recorder;

      const bucati = [];
      let aEsuat = false;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          bucati.push(event.data);
        }
      };

      recorder.onerror = () => {
             aEsuat = true;

        if (activRef.current) {
            setEroare("A aparut o eroare in timpul inregistrarii.");
             }

            flux.getTracks().forEach((pista) => pista.stop());
        };

      recorder.onstop = () => {
        flux.getTracks().forEach((pista) => pista.stop());
        fluxRef.current = null;
        recorderRef.current = null;

        if (!activRef.current) return;

        setStare("inactiv");

        if (aEsuat) return;

        const rezultat = new Blob(bucati, {
          type: recorder.mimeType,
        });

        if (rezultat.size === 0) {
          setEroare("Inregistrarea este goala. Incearca din nou.");
          return;
        }

        setInregistrare(rezultat);
      };

      // Functioneaza si daca opresti partajarea din browser.
      flux.getTracks().forEach((pista) => {
        pista.addEventListener("ended", () => {
          if (recorder.state !== "inactive") {
            recorder.stop();
          }
        });
      });

      recorder.start();
      setStare("inregistrare");
     } catch (error) {
            flux?.getTracks().forEach((pista) => pista.stop());
            fluxRef.current = null;
            recorderRef.current = null;

        if (!activRef.current) return;

                setStare("inactiv");

             setEroare(
                    error.name === "NotAllowedError"
                     ? "Accesul a fost refuzat sau cererea a fost anulata."
                    : error.name === "NotFoundError"
                     ? "Nu a fost gasit un dispozitiv sau o sursa compatibila."
                     : error.message
                     );
            }
    }

  return (
    <section>
      <h2>Captura sunetului</h2>

    <button
        type="button"
         onClick={() => pornesteInregistrarea("sistem")}
         disabled={stare !== "inactiv"}
>
        Înregistrează audio din sursă
    </button>

        <button
             type="button"
             onClick={() => pornesteInregistrarea("microfon")}
            disabled={stare !== "inactiv"}
>
        Înregistrează microfon
        </button>

            <button
                type="button"
                onClick={opresteInregistrarea}
                disabled={stare !== "inregistrare"}
>
    Oprește
    </button>

      {stare === "selectare" && ( <p>Confirmă accesul sau alege sursa în dialogul browserului.</p>)}
      {stare === "inregistrare" && <p>Se înregistrează sunetul…</p>}
      {stare === "finalizare" && <p>Se finalizează înregistrarea…</p>}

      {eroare && <p role="alert">{eroare}</p>}

      {urlAudio && stare === "inactiv" && (
        <div>
          <p>Ultima înregistrare:</p>
          <audio controls src={urlAudio} />
          <TrimiteAudio fisier={inregistrare} />

          <p>
            <a href={urlAudio} download="inregistrare.webm">
              Descarcă înregistrarea
            </a>
          </p>
        </div>
      )}
    </section>
  );
}