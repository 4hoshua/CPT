import { useRef, useState } from "react";
import type { ReactNode } from "react";
import { UnauthorizedError } from "../api";

type Props = {
  title: string;
  description: string;
  accept: string;
  buttonLabel: string;
  onConvert: (file: File) => Promise<void>;
  onUnauthorized: () => void;
  children?: ReactNode;
};

export default function ConvertCard({
  title,
  description,
  accept,
  buttonLabel,
  onConvert,
  onUnauthorized,
  children,
}: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit() {
    if (!file) return;
    setError(null);
    setBusy(true);
    try {
      await onConvert(file);
    } catch (err) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized();
        return;
      }
      setError(err instanceof Error ? err.message : "Conversion failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <h2>{title}</h2>
      <p className="muted">{description}</p>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={(e) => {
          setFile(e.target.files?.[0] ?? null);
          setError(null);
        }}
      />
      <button onClick={handleSubmit} disabled={!file || busy}>
        {busy ? "Working…" : buttonLabel}
      </button>
      {error && <p className="error">{error}</p>}
      {children}
    </div>
  );
}
