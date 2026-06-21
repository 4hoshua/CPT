import { useState } from "react";
import { convertToJson, convertToXml } from "../api";
import { clearToken } from "../auth";
import ConvertCard from "./ConvertCard";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default function Dashboard({ onLogout }: { onLogout: () => void }) {
  const [json, setJson] = useState<string | null>(null);

  function logout() {
    clearToken();
    onLogout();
  }

  function handleUnauthorized() {
    logout();
  }

  return (
    <div className="page">
      <header className="topbar">
        <h1>Packet Tracer Extractor</h1>
        <button className="secondary" onClick={logout}>
          Log out
        </button>
      </header>

      <main className="grid">
        <ConvertCard
          title="1 · .pkt → XML"
          description="Upload a Packet Tracer .pkt/.pka file to decode it into XML."
          accept=".pkt,.pka"
          buttonLabel="Decode & download XML"
          onUnauthorized={handleUnauthorized}
          onConvert={async (file) => {
            const blob = await convertToXml(file);
            const stem = file.name.replace(/\.[^.]+$/, "") || "output";
            downloadBlob(blob, `${stem}.xml`);
          }}
        />

        <ConvertCard
          title="2 · XML → JSON"
          description="Upload a Packet Tracer XML file to extract devices and cables."
          accept=".xml,application/xml,text/xml"
          buttonLabel="Extract JSON"
          onUnauthorized={handleUnauthorized}
          onConvert={async (file) => {
            const data = await convertToJson(file);
            setJson(JSON.stringify(data, null, 2));
          }}
        >
          {json && (
            <div className="result">
              <div className="result-actions">
                <button
                  className="secondary"
                  onClick={() =>
                    downloadBlob(
                      new Blob([json], { type: "application/json" }),
                      "topologia.json"
                    )
                  }
                >
                  Download JSON
                </button>
              </div>
              <pre>{json}</pre>
            </div>
          )}
        </ConvertCard>
      </main>
    </div>
  );
}
