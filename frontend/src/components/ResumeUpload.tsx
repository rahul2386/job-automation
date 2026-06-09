import { ChangeEvent, useRef } from "react";
import { Upload } from "lucide-react";

type ResumeUploadProps = {
  isUploading: boolean;
  onUpload: (file: File) => void;
};

export function ResumeUpload({ isUploading, onUpload }: ResumeUploadProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      onUpload(file);
      event.target.value = "";
    }
  }

  return (
    <div className="upload-panel">
      <input
        ref={inputRef}
        className="sr-only"
        type="file"
        accept="application/pdf"
        onChange={handleFileChange}
      />
      <button
        className="primary-button"
        type="button"
        disabled={isUploading}
        onClick={() => inputRef.current?.click()}
      >
        <Upload size={18} />
        {isUploading ? "Uploading..." : "Upload Resume"}
      </button>
    </div>
  );
}
