import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import {
  Upload,
  Loader2,
  FileText,
  Trash2,
  Eye,
  Download,
} from "lucide-react";
import ChatBot from "../components/ChatBot.jsx";
import { supabase } from "../utils/supabaseClient";

const API_URL = import.meta.env.VITE_API_URL || "/api";

// ── Styled components ────────────────────────────────────────

const PageTitle = styled.h1`
  font-size: 28px;
  font-family: 'Rethink Sans', sans-serif;
  margin: 0 0 24px;
  color: #1a1a1a;
`;

const Section = styled.div`
  margin-bottom: 32px;
`;

const SectionTitle = styled.h2`
  font-size: 18px;
  font-family: 'Rethink Sans', sans-serif;
  margin: 0 0 16px;
  color: #333;
`;

const UploadArea = styled.div`
  border: 2px dashed ${p => p.$dragOver ? '#20359A' : '#d1d5db'};
  border-radius: 10px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: ${p => p.$dragOver ? '#f0f4ff' : '#fafafa'};
  &:hover { border-color: #20359A; background: #f0f4ff; }
`;

const UploadHint = styled.p`
  color: #9ca3af;
  font-size: 13px;
  margin: 8px 0 0;
`;

const FileInput = styled.input`
  display: none;
`;

const Card = styled.div`
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  margin-bottom: 16px;
`;

const ClassGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 8px;
`;

const ClassCard = styled.div`
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.2s ease;
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  }
`;

const ClassHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
`;

const ClassTitle = styled.h3`
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #333;
  font-family: 'Rethink Sans', sans-serif;
`;

const ClassBadge = styled.div`
  background: ${p => {
    if (p.$status === "processed") return "#d1fae5";
    if (p.$status === "processing") return "#dbeafe";
    if (p.$status === "failed") return "#fee2e2";
    return "#f3f4f6";
  }};
  color: ${p => {
    if (p.$status === "processed") return "#065f46";
    if (p.$status === "processing") return "#1e40af";
    if (p.$status === "failed") return "#991b1b";
    return "#6b7280";
  }};
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
`;

const ClassDescription = styled.p`
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  margin: 0 0 12px 0;
`;

const ProgressBar = styled.div`
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  margin: 16px 0;
  overflow: hidden;
`;

const ProgressFill = styled.div`
  height: 100%;
  background: #20359A;
  border-radius: 3px;
  width: ${p => p.$progress}%;
  transition: width 0.3s ease;
`;

const ActionRow = styled.div`
  display: flex;
  gap: 6px;
  justify-content: center;
`;

const IconButton = styled.button`
  all: unset;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s ease;
`;

const PrimaryBtn = styled(IconButton)`
  background: #20359A;
  color: white;
  &:hover { background: #1a2a7a; }
`;

const DangerBtn = styled(IconButton)`
  color: #dc2626;
  &:hover { background: #fef2f2; }
`;

const SecondaryBtn = styled(IconButton)`
  color: #20359A;
  &:hover { background: #f0f4ff; }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 48px 20px;
  color: #9ca3af;
  p { margin: 4px 0; }
`;

const StatusMessage = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 16px;
  background: ${p => p.$type === "success" ? "#d1fae5" : "#fee2e2"};
  color: ${p => p.$type === "success" ? "#065f46" : "#991b1b"};
`;

// ── Modal ────────────────────────────────────────────────────

const ModalOverlay = styled.div`
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`;

const ModalContent = styled.div`
  background: white;
  border-radius: 12px;
  width: 95%;
  max-width: 1100px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
`;

const ModalTitle = styled.h2`
  margin: 0;
  font-size: 18px;
  font-family: 'Rethink Sans', sans-serif;
`;

const ModalBody = styled.div`
  padding: 20px;
  overflow: auto;
  flex: 1;
`;

const ModalButtons = styled.div`
  display: flex;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid #e5e7eb;
  justify-content: flex-end;
`;

const CloseButton = styled.button`
  all: unset;
  cursor: pointer;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  background: #f3f4f6;
  color: #374151;
  &:hover { background: #e5e7eb; }
`;

const DownloadButton = styled.button`
  all: unset;
  cursor: pointer;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  background: #10B981;
  color: white;
  &:hover { background: #059669; }
`;

// ── Component ────────────────────────────────────────────────

export default function StudyPage() {
  const [materials, setMaterials] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef();

  // Preview modal state
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [previewBlobUrl, setPreviewBlobUrl] = useState(null);

  useEffect(() => {
    loadMaterials();
  }, []);

  const getAuthHeaders = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error("Not authenticated");
    return { Authorization: `Bearer ${session.access_token}` };
  };

  const loadMaterials = async () => {
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/materials`, { headers });
      if (resp.ok) {
        const data = await resp.json();
        setMaterials(Array.isArray(data) ? data : data.materials || []);
      }
    } catch (err) { console.error("Error loading materials:", err); }
  };

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setUploadStatus(null);
    try {
      const headers = await getAuthHeaders();
      const formData = new FormData();
      formData.append("file", file);
      const resp = await fetch(`${API_URL}/upload`, {
        method: "POST", headers, body: formData,
      });
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Upload failed");
      }
      const result = await resp.json();
      setUploadStatus({ type: "success", message: `Uploaded "${result.file_name}" — processing in background.` });
      setTimeout(() => loadMaterials(), 3000);
    } catch (err) {
      setUploadStatus({ type: "error", message: err.message });
    } finally { setUploading(false); }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files[0]) handleUpload(e.dataTransfer.files[0]);
  };

  const handlePreview = async (material) => {
    try {
      if (previewBlobUrl) { URL.revokeObjectURL(previewBlobUrl); setPreviewBlobUrl(null); }

      const headers = await getAuthHeaders();
      const detailResp = await fetch(`${API_URL}/materials/${material.id}`, { headers });
      if (!detailResp.ok) return;
      const detail = await detailResp.json();
      setSelectedMaterial({ ...material, ...detail });

      if (detail.has_file && detail.file_type === "pdf") {
        const fileResp = await fetch(`${API_URL}/materials/${material.id}/download`, { headers });
        if (fileResp.ok) {
          const blob = await fileResp.blob();
          setPreviewBlobUrl(URL.createObjectURL(blob));
        }
      }
    } catch (err) { console.error("Preview error:", err); }
  };

  const handleDownload = async (materialId, title) => {
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/materials/${materialId}/download`, { headers });
      if (!resp.ok) { alert((await resp.json()).detail || "Download failed"); return; }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = title; document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch (err) { console.error("Download error:", err); }
  };

  const handleDelete = async (materialId, title) => {
    if (!confirm(`Delete "${title}"?`)) return;
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/materials/${materialId}`, { method: "DELETE", headers });
      if (resp.ok) {
        setMaterials(prev => prev.filter(m => m.id !== materialId));
      } else {
        const err = await resp.json();
        alert(err.detail || "Delete failed");
      }
    } catch (err) { console.error("Delete error:", err); }
  };

  const closeModal = () => {
    setSelectedMaterial(null);
    if (previewBlobUrl) { URL.revokeObjectURL(previewBlobUrl); setPreviewBlobUrl(null); }
  };

  return (
    <>
      <PageTitle>Study</PageTitle>

      {/* Upload area */}
      <Section>
        <SectionTitle>Upload Study Material</SectionTitle>
        {uploadStatus && (
          <StatusMessage $type={uploadStatus.type}>
            {uploadStatus.message}
          </StatusMessage>
        )}
        <UploadArea
          $dragOver={dragOver}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          {uploading
            ? <Loader2 size={32} color="#20359A" style={{ animation: "spin 1s linear infinite" }} />
            : <Upload size={32} color="#9ca3af" />
          }
          <p style={{ margin: "12px 0 0", color: "#374151", fontWeight: 500 }}>
            {uploading ? "Uploading..." : "Drop a file here or click to browse"}
          </p>
          <UploadHint>PDF, DOCX, DOC, or TXT</UploadHint>
        </UploadArea>
        <FileInput
          type="file"
          ref={fileInputRef}
          onChange={(e) => { handleUpload(e.target.files[0]); e.target.value = ""; }}
          accept=".pdf,.txt,.doc,.docx"
        />
      </Section>

      {/* Materials list */}
      <Section>
        <SectionTitle>
          My Materials
          {materials.length > 0 && (
            <span style={{ fontWeight: 400, fontSize: 14, color: "#6b7280", marginLeft: 8 }}>
              ({materials.filter(m => m.status === "processed").length} ready)
            </span>
          )}
        </SectionTitle>

        {materials.length === 0 ? (
          <EmptyState>
            <FileText size={28} />
            <p>No materials yet. Upload one above to get started.</p>
          </EmptyState>
        ) : (
          <ClassGrid>
            {materials.map(material => (
              <ClassCard key={material.id}>
                <ClassHeader>
                  <ClassTitle>{material.title}</ClassTitle>
                  <ClassBadge $status={material.status}>
                    {material.status === "processed" ? "Ready"
                      : material.status === "processing" ? "Processing"
                      : material.status === "failed" ? "Failed"
                      : "Uploaded"}
                  </ClassBadge>
                </ClassHeader>

                <ClassDescription>
                  {material.status === "processed"
                    ? `${material.chunk_count || 0} chunks processed`
                    : material.status === "processing"
                    ? "Processing content..."
                    : material.status === "failed"
                    ? "Processing failed"
                    : `Uploaded ${material.uploaded_at ? new Date(material.uploaded_at).toLocaleDateString() : ""}`
                  }
                </ClassDescription>

                <ProgressBar>
                  <ProgressFill $progress={material.status === "processed" ? 100 : material.processing_progress || 0} />
                </ProgressBar>

                <ActionRow>
                  <PrimaryBtn onClick={() => handlePreview(material)}>
                    <Eye size={14} /> {material.status === "processed" ? "Study" : "View"}
                  </PrimaryBtn>
                  <SecondaryBtn onClick={() => handleDownload(material.id, material.title)}>
                    <Download size={14} /> Download
                  </SecondaryBtn>
                  <DangerBtn onClick={() => handleDelete(material.id, material.title)}>
                    <Trash2 size={14} /> Delete
                  </DangerBtn>
                </ActionRow>
              </ClassCard>
            ))}
          </ClassGrid>
        )}
      </Section>

      {/* Preview modal */}
      {selectedMaterial && (
        <ModalOverlay onClick={closeModal}>
          <ModalContent onClick={(e) => e.stopPropagation()}>
            <ModalHeader>
              <ModalTitle>{selectedMaterial.title}</ModalTitle>
            </ModalHeader>
            <ModalBody>
              {previewBlobUrl && selectedMaterial.file_type === "pdf" ? (
                <iframe
                  src={previewBlobUrl}
                  title={selectedMaterial.title}
                  style={{ width: "100%", height: "70vh", border: "1px solid #e5e7eb", borderRadius: 8 }}
                />
              ) : selectedMaterial.extracted_text ? (
                <pre style={{
                  whiteSpace: "pre-wrap", wordBreak: "break-word",
                  maxHeight: "70vh", overflow: "auto", padding: 16,
                  background: "#f9fafb", borderRadius: 8, border: "1px solid #e5e7eb",
                  fontSize: 14, lineHeight: 1.6,
                }}>
                  {selectedMaterial.extracted_text}
                </pre>
              ) : (
                <EmptyState><p>Loading content...</p></EmptyState>
              )}
            </ModalBody>
            <ModalButtons>
              {selectedMaterial.has_file && (
                <DownloadButton onClick={() => handleDownload(selectedMaterial.id, selectedMaterial.title)}>
                  Download
                </DownloadButton>
              )}
              <CloseButton onClick={closeModal}>Close</CloseButton>
            </ModalButtons>
          </ModalContent>
        </ModalOverlay>
      )}

      <ChatBot />

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
}
