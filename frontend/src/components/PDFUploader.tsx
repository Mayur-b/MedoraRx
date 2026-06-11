import { useRef, useState, type DragEvent, type ChangeEvent } from "react";

interface PDFUploaderProps {
  selectedFile: File | null;
  onFileSelected: (file: File | null) => void;
  disabled?: boolean;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function PDFUploader({
  selectedFile,
  onFileSelected,
  disabled = false,
}: PDFUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function validateAndSelect(file: File | undefined) {
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are accepted.");
      return;
    }
    setError(null);
    onFileSelected(file);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    validateAndSelect(e.dataTransfer.files?.[0]);
  }

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    validateAndSelect(e.target.files?.[0]);
  }

  return (
    <div className="w-full">
      <div
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={[
          "flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors",
          disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer",
          isDragging
            ? "border-medora-accent bg-blue-50"
            : "border-slate-300 bg-slate-50 hover:border-medora-accent hover:bg-blue-50/40",
        ].join(" ")}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          onChange={handleChange}
          disabled={disabled}
          className="hidden"
        />

        <svg
          className="mb-3 h-12 w-12 text-medora-accent"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"
          />
        </svg>

        {selectedFile ? (
          <div className="space-y-1">
            <p className="font-semibold text-slate-800">{selectedFile.name}</p>
            <p className="text-sm text-slate-500">{formatBytes(selectedFile.size)}</p>
            {!disabled && (
              <p className="text-xs text-medora-accent">Click or drop to replace</p>
            )}
          </div>
        ) : (
          <div className="space-y-1">
            <p className="font-medium text-slate-700">
              Drag &amp; drop a PDF here, or{" "}
              <span className="text-medora-accent underline">browse</span>
            </p>
            <p className="text-sm text-slate-400">WHO guidelines, drug leaflets, clinical PDFs…</p>
          </div>
        )}
      </div>

      {error && <p className="mt-2 text-sm font-medium text-red-600">{error}</p>}
    </div>
  );
}
