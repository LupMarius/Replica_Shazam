import { useRef, useState } from "react";
import CapturaAudio from "./CapturaAudio";
import TrimiteAudio from "./TrimiteAudio";

export default function App() {
  const [fisier, setFisier] = useState(null);
  const inputRef = useRef(null);

  return (
    <main>
      <h1>Recunoaștere muzicală</h1>

      <input
        ref={inputRef}
        type="file"
        accept=".mp3,.wav"
        hidden
        onChange={(event) => {
          setFisier(event.target.files[0] ?? null);
        }}
      />

      <button
        type="button"
        onClick={() => inputRef.current.click()}
      >
        Upload
      </button>

      <p>
        {fisier ? fisier.name : "Niciun fișier selectat."}
      </p>

      <TrimiteAudio fisier={fisier} />

      <CapturaAudio />
    </main>
  );
}