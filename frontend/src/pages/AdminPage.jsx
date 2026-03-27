import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import {
  Upload,
  Search,
  Users,
  FileText,
  ClipboardList,
  Trash2,
  Loader2,
  CheckCircle,
  AlertCircle,
  ChevronRight,
  ChevronDown,
  Eye,
  X,
  RotateCcw,
  FolderOpen,
  Download,
} from "lucide-react";
import { supabase } from "../utils/supabaseClient";

const API_URL = import.meta.env.VITE_API_URL || "/api";

/** Render simple markdown (headings, bold, italic) as HTML */
function renderMarkdown(text) {
  if (!text) return null;
  const lines = text.split("\n");
  const elements = [];
  let key = 0;

  for (const line of lines) {
    if (line.startsWith("# ")) {
      elements.push(<h3 key={key++} style={{ fontSize: 16, fontWeight: 700, margin: "12px 0 4px" }}>{formatInline(line.slice(2))}</h3>);
    } else if (line.startsWith("## ")) {
      elements.push(<h4 key={key++} style={{ fontSize: 15, fontWeight: 600, margin: "10px 0 4px" }}>{formatInline(line.slice(3))}</h4>);
    } else if (line.trim() === "") {
      elements.push(<br key={key++} />);
    } else {
      elements.push(<p key={key++} style={{ margin: "2px 0", lineHeight: 1.6 }}>{formatInline(line)}</p>);
    }
  }
  return elements;
}

function formatInline(text) {
  // Bold+italic: ***text***
  // Bold: **text**
  // Italic: *text*
  const parts = [];
  let remaining = text;
  let key = 0;

  const regex = /(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    if (match[2]) {
      parts.push(<strong key={key++}><em>{match[2]}</em></strong>);
    } else if (match[3]) {
      parts.push(<strong key={key++}>{match[3]}</strong>);
    } else if (match[4]) {
      parts.push(<em key={key++}>{match[4]}</em>);
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts.length ? parts : text;
}

// ── Styled components ────────────────────────────────────────

const PageTitle = styled.h1`
  font-size: 28px;
  font-family: 'Rethink Sans', sans-serif;
  margin: 0 0 24px;
  color: #1a1a1a;
`;

const Tabs = styled.div`
  display: flex;
  gap: 0;
  border-bottom: 2px solid #e5e7eb;
  margin-bottom: 24px;
`;

const Tab = styled.button`
  all: unset;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  font-family: 'General Sans', sans-serif;
  font-size: 14px;
  font-weight: ${p => p.$active ? 600 : 400};
  color: ${p => p.$active ? '#20359A' : '#6b7280'};
  border-bottom: 2px solid ${p => p.$active ? '#20359A' : 'transparent'};
  margin-bottom: -2px;
  cursor: pointer;
  transition: all 0.15s ease;
  &:hover { color: #20359A; }
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

const Card = styled.div`
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 16px;
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

const PrimaryButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #20359A;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s ease;
  &:hover:not(:disabled) { background: #1a2a7a; }
  &:disabled { opacity: 0.6; cursor: not-allowed; }
`;

const SecondaryButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  &:hover:not(:disabled) { background: #e5e7eb; }
  &:disabled { opacity: 0.6; cursor: not-allowed; }
`;

const DangerButton = styled.button`
  all: unset;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  color: #dc2626;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s ease;
  &:hover { background: #fef2f2; }
`;

const IconButton = styled.button`
  all: unset;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  color: #20359A;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s ease;
  &:hover { background: #f0f4ff; }
`;

const SearchBox = styled.div`
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
`;

const Input = styled.input`
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  font-family: 'General Sans', sans-serif;
  &:focus {
    outline: none;
    border-color: #20359A;
    box-shadow: 0 0 0 2px rgba(32,53,154,0.1);
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  font-family: 'General Sans', sans-serif;
`;

const Th = styled.th`
  text-align: left;
  padding: 10px 12px;
  border-bottom: 2px solid #e5e7eb;
  color: #6b7280;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
`;

const Td = styled.td`
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  color: #374151;
`;

const Badge = styled.span`
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: ${p => {
    if (p.$variant === "admin") return "#fef3c7";
    if (p.$variant === "success") return "#d1fae5";
    if (p.$variant === "processing") return "#dbeafe";
    if (p.$variant === "error") return "#fee2e2";
    return "#f3f4f6";
  }};
  color: ${p => {
    if (p.$variant === "admin") return "#92400e";
    if (p.$variant === "success") return "#065f46";
    if (p.$variant === "processing") return "#1e40af";
    if (p.$variant === "error") return "#991b1b";
    return "#6b7280";
  }};
`;

const ResultCard = styled.div`
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
`;

const ResultMeta = styled.div`
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
`;

const ResultContent = styled.p`
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
  margin: 8px 0 0;
  white-space: pre-wrap;
`;

const ScoreBadge = styled.span`
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  background: ${p => {
    const s = p.$score;
    if (s >= 0.7) return "#d1fae5";
    if (s >= 0.4) return "#fef3c7";
    return "#fee2e2";
  }};
  color: ${p => {
    const s = p.$score;
    if (s >= 0.7) return "#065f46";
    if (s >= 0.4) return "#92400e";
    return "#991b1b";
  }};
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 48px 20px;
  color: #9ca3af;
  p { margin: 4px 0; }
`;

const FileInput = styled.input`
  display: none;
`;

const StatusMessage = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 16px;
  background: ${p => p.$type === "success" ? "#d1fae5" : p.$type === "error" ? "#fee2e2" : "#dbeafe"};
  color: ${p => p.$type === "success" ? "#065f46" : p.$type === "error" ? "#991b1b" : "#1e40af"};
`;

const PlaceholderCard = styled(Card)`
  text-align: center;
  padding: 48px;
  color: #9ca3af;
  border-style: dashed;
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
  width: 94%;
  max-width: 1200px;
  max-height: 85vh;
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
  overflow: hidden;
  flex: 1;
`;

const CloseButton = styled.button`
  all: unset;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  color: #6b7280;
  &:hover { background: #f3f4f6; color: #1a1a1a; }
`;

// ── Tree styles ──────────────────────────────────────────────

const TreeNode = styled.div`
  margin-left: ${p => p.$depth * 20}px;
  padding: 4px 0;
`;

const TreeRow = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 6px;
  cursor: ${p => p.$hasChunks ? 'pointer' : 'default'};
  font-size: 14px;
  &:hover { background: ${p => p.$hasChunks ? '#f3f4f6' : 'transparent'}; }
`;

const TreeLabel = styled.span`
  font-weight: ${p => p.$isHeading ? 600 : 400};
  color: ${p => p.$isHeading ? '#1a1a1a' : '#374151'};
`;

const TreeMeta = styled.span`
  font-size: 12px;
  color: #9ca3af;
  margin-left: 8px;
`;

const ChunkList = styled.div`
  margin-left: 28px;
  border-left: 2px solid #e5e7eb;
  padding-left: 12px;
  margin-top: 4px;
  margin-bottom: 4px;
`;

const ChunkItem = styled.div`
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  border: 1px solid transparent;
  &:hover {
    background: #f0f4ff;
    border-color: #d1d5db;
  }
`;

const ChunkPreview = styled.p`
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
  white-space: pre-wrap;
`;

const ChunkDetail = styled.div`
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  max-height: 50vh;
  overflow-y: auto;
`;

const ChunkNavButton = styled.button`
  all: unset;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  font-size: 12px;
  color: #20359A;
  border-radius: 6px;
  cursor: pointer;
  &:hover { background: #f0f4ff; }
`;

// ── Component ────────────────────────────────────────────────

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState("docs");
  const [users, setUsers] = useState([]);
  const [systemMaterials, setSystemMaterials] = useState([]);
  const [userMaterials, setUserMaterials] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef();

  // Tree modal state
  const [treeModal, setTreeModal] = useState(null);
  const [treeLoading, setTreeLoading] = useState(false);
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [selectedChunk, setSelectedChunk] = useState(null);
  const [chunkDetail, setChunkDetail] = useState(null);

  // Preview modal state
  const [previewModal, setPreviewModal] = useState(null);
  const [previewBlobUrl, setPreviewBlobUrl] = useState(null);

  // RAG result chunk modal
  const [ragChunkModal, setRagChunkModal] = useState(null);

  const tabs = [
    { id: "docs",      label: "Documents",       icon: FileText },
    { id: "userdocs",  label: "User Materials",   icon: FolderOpen },
    { id: "rag",       label: "RAG Test",         icon: Search },
    { id: "users",     label: "Users",            icon: Users },
    { id: "questions", label: "Questions",         icon: ClipboardList },
  ];

  useEffect(() => {
    if (activeTab === "users") loadUsers();
    if (activeTab === "docs") loadSystemMaterials();
    if (activeTab === "userdocs") loadUserMaterials();
  }, [activeTab]);

  const getAuthHeaders = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error("Not authenticated");
    return { Authorization: `Bearer ${session.access_token}` };
  };

  const loadUsers = async () => {
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/admin/users`, { headers });
      if (resp.ok) setUsers((await resp.json()).users || []);
    } catch (err) { console.error("Error loading users:", err); }
  };

  const loadSystemMaterials = async () => {
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/admin/system-materials`, { headers });
      if (resp.ok) setSystemMaterials((await resp.json()).materials || []);
    } catch (err) { console.error("Error loading system materials:", err); }
  };

  const loadUserMaterials = async () => {
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/admin/user-materials`, { headers });
      if (resp.ok) setUserMaterials((await resp.json()).materials || []);
    } catch (err) { console.error("Error loading user materials:", err); }
  };

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setUploadStatus(null);
    try {
      const headers = await getAuthHeaders();
      const formData = new FormData();
      formData.append("file", file);
      const resp = await fetch(`${API_URL}/admin/upload-system-material`, {
        method: "POST", headers, body: formData,
      });
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Upload failed");
      }
      const result = await resp.json();
      setUploadStatus({ type: "success", message: `Uploaded "${result.file_name}" — processing in background.` });
      setTimeout(() => loadSystemMaterials(), 3000);
    } catch (err) {
      setUploadStatus({ type: "error", message: err.message });
    } finally { setUploading(false); }
  };

  const handleDeleteSystemMaterial = async (materialId, title) => {
    if (!confirm(`Delete system material "${title}"?`)) return;
    try {
      const headers = await getAuthHeaders();
      await fetch(`${API_URL}/admin/system-materials/${materialId}`, { method: "DELETE", headers });
      setSystemMaterials(prev => prev.filter(m => m.id !== materialId));
    } catch (err) { console.error("Error deleting material:", err); }
  };

  const handleReprocess = async (materialId, title) => {
    if (!confirm(`Reprocess "${title}"? This will clear existing RAG data and re-run the pipeline.`)) return;
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/admin/system-materials/${materialId}/reprocess`, {
        method: "POST", headers,
      });
      if (resp.ok) {
        setSystemMaterials(prev => prev.map(m =>
          m.id === materialId ? { ...m, status: "processing", chunk_count: 0 } : m
        ));
        setTimeout(() => loadSystemMaterials(), 5000);
      }
    } catch (err) { console.error("Error reprocessing:", err); }
  };

  const handleUserMaterialPreview = async (materialId, title) => {
    try {
      const headers = await getAuthHeaders();
      const detailResp = await fetch(`${API_URL}/admin/user-materials/${materialId}/detail`, { headers });
      if (!detailResp.ok) return;
      const detail = await detailResp.json();

      if (previewBlobUrl) { URL.revokeObjectURL(previewBlobUrl); setPreviewBlobUrl(null); }

      // For PDFs, fetch blob before opening modal to avoid flash of raw text
      let blobUrl = null;
      if (detail.has_file && detail.file_type === "pdf") {
        const fileResp = await fetch(`${API_URL}/admin/user-materials/${materialId}/download`, { headers });
        if (fileResp.ok) {
          const blob = await fileResp.blob();
          blobUrl = URL.createObjectURL(blob);
        }
      }

      setPreviewBlobUrl(blobUrl);
      setPreviewModal({ ...detail, title, _userMaterial: true });
    } catch (err) { console.error("Preview error:", err); }
  };

  const handleUserMaterialDownload = async (materialId, title) => {
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/admin/user-materials/${materialId}/download`, { headers });
      if (!resp.ok) { alert((await resp.json()).detail || "Download failed"); return; }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = title; document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch (err) { console.error("Download error:", err); }
  };

  const handleUserMaterialReprocess = async (materialId, title) => {
    if (!confirm(`Reprocess "${title}"? This will clear existing RAG data and re-run the pipeline.`)) return;
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/admin/user-materials/${materialId}/reprocess`, {
        method: "POST", headers,
      });
      if (resp.ok) {
        setUserMaterials(prev => prev.map(m =>
          m.id === materialId ? { ...m, status: "processing", chunk_count: 0 } : m
        ));
        setTimeout(() => loadUserMaterials(), 5000);
      }
    } catch (err) { console.error("Error reprocessing:", err); }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setSearchResults(null);
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/admin/rag-search`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery, top_k: 5 }),
      });
      if (!resp.ok) throw new Error((await resp.json()).detail || "Search failed");
      setSearchResults(await resp.json());
    } catch (err) {
      setSearchResults({ error: err.message });
    } finally { setSearching(false); }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files[0]) handleUpload(e.dataTransfer.files[0]);
  };

  const handlePreview = async (materialId, title) => {
    try {
      const headers = await getAuthHeaders();
      const detailResp = await fetch(`${API_URL}/admin/system-materials/${materialId}/detail`, { headers });
      if (!detailResp.ok) return;
      const detail = await detailResp.json();

      // Clean up old blob
      if (previewBlobUrl) { URL.revokeObjectURL(previewBlobUrl); setPreviewBlobUrl(null); }

      // For PDFs, fetch blob before opening modal to avoid flash of raw text
      let blobUrl = null;
      if (detail.has_file && detail.file_type === "pdf") {
        const fileResp = await fetch(`${API_URL}/admin/system-materials/${materialId}/download`, { headers });
        if (fileResp.ok) {
          const blob = await fileResp.blob();
          blobUrl = URL.createObjectURL(blob);
        }
      }

      setPreviewBlobUrl(blobUrl);
      setPreviewModal({ ...detail, title });
    } catch (err) { console.error("Preview error:", err); }
  };

  const handleDownload = async (materialId, title) => {
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/admin/system-materials/${materialId}/download`, { headers });
      if (!resp.ok) { alert((await resp.json()).detail || "Download failed"); return; }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = title; document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch (err) { console.error("Download error:", err); }
  };

  const formatBytes = (bytes) => {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  // ── Tree modal ─────────────────────────────────────────────

  const openTreeModal = async (materialId, title) => {
    setTreeLoading(true);
    setTreeModal({ title, data: null });
    setExpandedNodes(new Set());
    setSelectedChunk(null);
    setChunkDetail(null);
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/admin/documents/${materialId}/tree`, { headers });
      if (!resp.ok) throw new Error((await resp.json()).detail || "Failed to load tree");
      const data = await resp.json();
      setTreeModal({ title, data });
    } catch (err) {
      setTreeModal({ title, error: err.message });
    } finally { setTreeLoading(false); }
  };

  const toggleNode = (nodeId) => {
    setExpandedNodes(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  };

  const loadChunkDetail = async (chunkId) => {
    setSelectedChunk(chunkId);
    setChunkDetail(null);
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/admin/chunks/${chunkId}`, { headers });
      if (resp.ok) setChunkDetail(await resp.json());
    } catch (err) { console.error("Error loading chunk:", err); }
  };

  // ── Render tree ────────────────────────────────────────────

  const renderTreeNodes = (nodes, parentId = null, depth = 0) => {
    const children = nodes.filter(n =>
      parentId === null ? n.node_type === "root" : n.parent_id === parentId
    );

    return children.map(node => {
      const hasChunks = node.chunks && node.chunks.length > 0;
      const hasChildren = nodes.some(n => n.parent_id === node.id);
      const isExpanded = expandedNodes.has(node.id);
      const canExpand = hasChunks || hasChildren;

      const label = node.ordinal_label
        ? `${node.ordinal_label}. ${node.heading_text || ""}`
        : node.heading_text || node.node_type;

      return (
        <TreeNode key={node.id} $depth={depth}>
          <TreeRow
            $hasChunks={canExpand}
            onClick={() => canExpand && toggleNode(node.id)}
          >
            {canExpand ? (
              isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />
            ) : <span style={{ width: 14 }} />}
            <TreeLabel $isHeading={node.depth < 3}>{label}</TreeLabel>
            <TreeMeta>
              {node.token_count ? `${node.token_count} tok` : ""}
              {hasChunks ? ` · ${node.chunks.length} chunk${node.chunks.length > 1 ? 's' : ''}` : ""}
            </TreeMeta>
          </TreeRow>

          {isExpanded && hasChunks && (
            <ChunkList>
              {node.chunks.map(c => (
                <ChunkItem
                  key={c.id}
                  onClick={(e) => { e.stopPropagation(); loadChunkDetail(c.id); }}
                  style={{
                    background: selectedChunk === c.id ? '#f0f4ff' : undefined,
                    borderColor: selectedChunk === c.id ? '#20359A' : undefined,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontWeight: 500 }}>
                      Chunk #{c.chunk_index}
                      <Badge $variant="default" style={{ marginLeft: 6 }}>{c.chunk_kind}</Badge>
                    </span>
                    <span style={{ fontSize: 11, color: "#9ca3af" }}>
                      {c.token_count} tok · p.{c.page_start}{c.page_end && c.page_end !== c.page_start ? `-${c.page_end}` : ""}
                    </span>
                  </div>
                  <ChunkPreview>{c.content_preview}…</ChunkPreview>
                </ChunkItem>
              ))}
            </ChunkList>
          )}

          {isExpanded && renderTreeNodes(nodes, node.id, depth + 1)}
        </TreeNode>
      );
    });
  };

  // ── Render tabs ────────────────────────────────────────────

  const renderDocsTab = () => (
    <>
      <Section>
        <SectionTitle>Upload System Document</SectionTitle>
        {uploadStatus && (
          <StatusMessage $type={uploadStatus.type}>
            {uploadStatus.type === "success" ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
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
          <UploadHint>PDF, DOCX, DOC, or TXT — visible to all users.</UploadHint>
        </UploadArea>
        <FileInput
          type="file"
          ref={fileInputRef}
          onChange={(e) => handleUpload(e.target.files[0])}
          accept=".pdf,.txt,.doc,.docx"
        />
      </Section>

      <Section>
        <SectionTitle>
          System Documents
          {systemMaterials.length > 0 && (
            <span style={{ fontWeight: 400, fontSize: 14, color: "#6b7280", marginLeft: 8 }}>
              ({systemMaterials.filter(m => m.status === "processed").length} indexed)
            </span>
          )}
        </SectionTitle>

        {systemMaterials.length === 0 ? (
          <EmptyState>
            <FileText size={28} />
            <p>No system documents yet. Upload one above.</p>
          </EmptyState>
        ) : (
          <Card style={{ padding: 0, overflow: "hidden" }}>
            <Table>
              <thead>
                <tr>
                  <Th>Title</Th>
                  <Th>Type</Th>
                  <Th>Size</Th>
                  <Th>Status</Th>
                  <Th>Chunks</Th>
                  <Th>Uploaded</Th>
                  <Th></Th>
                </tr>
              </thead>
              <tbody>
                {systemMaterials.map((m) => (
                  <tr key={m.id}>
                    <Td style={{ fontWeight: 500 }}>{m.title}</Td>
                    <Td>{m.file_type?.toUpperCase()}</Td>
                    <Td>{formatBytes(m.file_size)}</Td>
                    <Td>
                      <Badge $variant={m.status === "processed" ? "success" : m.status === "processing" ? "processing" : m.status === "failed" ? "error" : "default"}>
                        {m.status}
                      </Badge>
                    </Td>
                    <Td>{m.chunk_count ?? "—"}</Td>
                    <Td>{m.uploaded_at ? new Date(m.uploaded_at).toLocaleDateString() : "—"}</Td>
                    <Td>
                      <div style={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
                        {m.status === "processed" && (
                          <>
                            <IconButton onClick={() => handlePreview(m.id, m.title)}>
                              <Eye size={14} /> Preview
                            </IconButton>
                            <IconButton onClick={() => openTreeModal(m.id, m.title)}>
                              <ChevronRight size={14} /> Tree
                            </IconButton>
                          </>
                        )}
                        {(m.status === "processed" || m.status === "uploaded" || m.status === "failed") && (
                          <IconButton onClick={() => handleReprocess(m.id, m.title)}>
                            <RotateCcw size={14} /> Reprocess
                          </IconButton>
                        )}
                        <DangerButton onClick={() => handleDeleteSystemMaterial(m.id, m.title)}>
                          <Trash2 size={14} /> Delete
                        </DangerButton>
                      </div>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card>
        )}

        {systemMaterials.length > 0 && (
          <SecondaryButton onClick={loadSystemMaterials} style={{ marginTop: 8 }}>
            <RotateCcw size={14} /> Refresh
          </SecondaryButton>
        )}
      </Section>
    </>
  );

  const renderUserDocsTab = () => (
    <Section>
      <SectionTitle>
        User Uploaded Materials
        {userMaterials.length > 0 && (
          <span style={{ fontWeight: 400, fontSize: 14, color: "#6b7280", marginLeft: 8 }}>
            ({userMaterials.filter(m => m.status === "processed").length} indexed)
          </span>
        )}
      </SectionTitle>

      {userMaterials.length === 0 ? (
        <EmptyState>
          <FolderOpen size={28} />
          <p>No user-uploaded materials found.</p>
        </EmptyState>
      ) : (
        <Card style={{ padding: 0, overflow: "hidden" }}>
          <Table>
            <thead>
              <tr>
                <Th>User</Th>
                <Th>Title</Th>
                <Th>Type</Th>
                <Th>Size</Th>
                <Th>Status</Th>
                <Th>Chunks</Th>
                <Th>Uploaded</Th>
                <Th></Th>
              </tr>
            </thead>
            <tbody>
              {userMaterials.map((m) => (
                <tr key={m.id}>
                  <Td style={{ fontSize: 13 }}>{m.user_email || m.user_id}</Td>
                  <Td style={{ fontWeight: 500 }}>{m.title}</Td>
                  <Td>{m.file_type?.toUpperCase()}</Td>
                  <Td>{formatBytes(m.file_size)}</Td>
                  <Td>
                    <Badge $variant={m.status === "processed" ? "success" : m.status === "processing" ? "processing" : m.status === "failed" ? "error" : "default"}>
                      {m.status}
                    </Badge>
                    {m.status === "failed" && m.processing_error && (
                      <span title={m.processing_error} style={{ marginLeft: 4, cursor: "help" }}>
                        <AlertCircle size={12} color="#991b1b" />
                      </span>
                    )}
                  </Td>
                  <Td>{m.chunk_count ?? "—"}</Td>
                  <Td>{m.uploaded_at ? new Date(m.uploaded_at).toLocaleDateString() : "—"}</Td>
                  <Td>
                    <div style={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
                      {m.status === "processed" && (
                        <>
                          <IconButton onClick={() => handleUserMaterialPreview(m.id, m.title)}>
                            <Eye size={14} /> Preview
                          </IconButton>
                          <IconButton onClick={() => openTreeModal(m.id, m.title)}>
                            <ChevronRight size={14} /> Tree
                          </IconButton>
                        </>
                      )}
                      <IconButton onClick={() => handleUserMaterialDownload(m.id, m.title)}>
                        <Download size={14} /> Download
                      </IconButton>
                      {(m.status === "processed" || m.status === "uploaded" || m.status === "failed") && (
                        <IconButton onClick={() => handleUserMaterialReprocess(m.id, m.title)}>
                          <RotateCcw size={14} /> Reprocess
                        </IconButton>
                      )}
                    </div>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      {userMaterials.length > 0 && (
        <SecondaryButton onClick={loadUserMaterials} style={{ marginTop: 8 }}>
          <RotateCcw size={14} /> Refresh
        </SecondaryButton>
      )}
    </Section>
  );

  const renderRagTab = () => (
    <Section>
      <SectionTitle>Test RAG Retrieval</SectionTitle>
      <p style={{ fontSize: 13, color: "#6b7280", marginBottom: 16 }}>
        Query the pgvector pipeline against all system documents.
      </p>
      <SearchBox>
        <Input
          placeholder="Enter a search query..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <PrimaryButton onClick={handleSearch} disabled={searching || !searchQuery.trim()}>
          {searching ? <Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} /> : <Search size={16} />}
          Search
        </PrimaryButton>
      </SearchBox>

      {searchResults && searchResults.error && (
        <StatusMessage $type="error">
          <AlertCircle size={16} />
          {searchResults.error}
        </StatusMessage>
      )}

      {searchResults && !searchResults.error && (
        <>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <span style={{ fontSize: 13, color: "#6b7280" }}>
              {searchResults.total_results} result(s) for "{searchResults.query}"
            </span>
            {searchResults.timing_ms && (
              <span style={{ fontSize: 12, color: "#9ca3af", fontFamily: "monospace" }}>
                {searchResults.timing_ms.total}ms total
                (embed: {searchResults.timing_ms.embedder}ms, search: {searchResults.timing_ms.search}ms)
              </span>
            )}
          </div>
          {searchResults.results?.map((r, i) => (
            <ResultCard key={r.chunk_id || i}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontWeight: 600, fontSize: 14, color: "#1a1a1a" }}>
                  {r.document_title || "Unknown Document"}
                </span>
                <ScoreBadge $score={r.score}>
                  {(r.score * 100).toFixed(1)}% match
                </ScoreBadge>
              </div>
              {r.heading_path && (
                <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>{r.heading_path}</div>
              )}
              <ResultContent style={{
                maxHeight: 72, overflow: "hidden",
                WebkitMaskImage: "linear-gradient(to bottom, black 60%, transparent 100%)",
                maskImage: "linear-gradient(to bottom, black 60%, transparent 100%)",
              }}>
                {(r.content || "").slice(0, 300)}
              </ResultContent>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 4 }}>
                <ResultMeta style={{ marginTop: 0 }}>
                  {r.chunk_kind && <span>Kind: {r.chunk_kind}</span>}
                  {r.page_start != null && <span>Pages: {r.page_start}{r.page_end && r.page_end !== r.page_start ? `-${r.page_end}` : ''}</span>}
                  {r.token_count && <span>Tokens: {r.token_count}</span>}
                </ResultMeta>
                <IconButton onClick={() => setRagChunkModal(r)} style={{ fontSize: 12 }}>
                  <Eye size={13} /> View full chunk
                </IconButton>
              </div>
            </ResultCard>
          ))}
          {searchResults.results?.length === 0 && (
            <EmptyState>
              <p>No results found.</p>
              <p>Make sure system documents have been uploaded and processed.</p>
            </EmptyState>
          )}
        </>
      )}
    </Section>
  );

  const renderUsersTab = () => (
    <Section>
      <SectionTitle>All Users</SectionTitle>
      {users.length === 0 ? (
        <EmptyState><Users size={32} /><p>Loading users...</p></EmptyState>
      ) : (
        <Card style={{ padding: 0, overflow: "hidden" }}>
          <Table>
            <thead>
              <tr>
                <Th>ID</Th><Th>Email</Th><Th>Name</Th><Th>Specialty</Th><Th>Roles</Th><Th>Status</Th><Th>Joined</Th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <Td>{u.id}</Td>
                  <Td>{u.email}</Td>
                  <Td>{u.full_name || "—"}</Td>
                  <Td>{u.specialty || "—"}</Td>
                  <Td>
                    {u.roles?.map(r => (
                      <Badge key={r} $variant={r === "admin" ? "admin" : "default"} style={{ marginRight: 4 }}>{r}</Badge>
                    ))}
                    {(!u.roles || u.roles.length === 0) && <span style={{ color: "#9ca3af" }}>user</span>}
                  </Td>
                  <Td><Badge $variant={u.is_active ? "success" : "error"}>{u.is_active ? "active" : "inactive"}</Badge></Td>
                  <Td>{u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}
    </Section>
  );

  const renderQuestionsTab = () => (
    <Section>
      <PlaceholderCard>
        <ClipboardList size={40} color="#d1d5db" />
        <h3 style={{ color: "#6b7280", margin: "12px 0 4px" }}>Practice Questions</h3>
        <p style={{ color: "#9ca3af", fontSize: 14 }}>
          Question generation and management will be available here.
        </p>
      </PlaceholderCard>
    </Section>
  );

  return (
    <>
      <PageTitle>Admin Panel</PageTitle>

      <Tabs>
        {tabs.map(({ id, label, icon: Icon }) => (
          <Tab key={id} $active={activeTab === id} onClick={() => setActiveTab(id)}>
            <Icon size={16} />
            {label}
          </Tab>
        ))}
      </Tabs>

      {activeTab === "docs" && renderDocsTab()}
      {activeTab === "userdocs" && renderUserDocsTab()}
      {activeTab === "rag" && renderRagTab()}
      {activeTab === "users" && renderUsersTab()}
      {activeTab === "questions" && renderQuestionsTab()}

      {/* ── Tree Modal ── */}
      {treeModal && (
        <ModalOverlay onClick={() => setTreeModal(null)}>
          <ModalContent onClick={(e) => e.stopPropagation()}>
            <ModalHeader>
              <ModalTitle>{treeModal.title} — Document Structure</ModalTitle>
              <CloseButton onClick={() => setTreeModal(null)}><X size={18} /></CloseButton>
            </ModalHeader>
            <ModalBody>
              {treeLoading && (
                <EmptyState><Loader2 size={24} style={{ animation: "spin 1s linear infinite" }} /><p>Loading...</p></EmptyState>
              )}
              {treeModal.error && (
                <StatusMessage $type="error"><AlertCircle size={16} />{treeModal.error}</StatusMessage>
              )}
              {treeModal.data && (
                <>
                  <div style={{ fontSize: 13, color: "#6b7280", marginBottom: 16 }}>
                    {treeModal.data.page_count} pages · {treeModal.data.total_nodes} nodes · {treeModal.data.total_chunks} chunks
                  </div>

                  <div style={{ display: "flex", gap: 0, height: "calc(85vh - 140px)" }}>
                    {/* Left: tree (scrollable) */}
                    <div style={{ flex: 1, minWidth: 0, overflowY: "auto", paddingRight: 16 }}>
                      {renderTreeNodes(treeModal.data.nodes)}
                    </div>

                    {/* Right: chunk detail (fixed dimensions) */}
                    {chunkDetail && (
                      <div style={{
                        width: 440, flexShrink: 0,
                        borderLeft: "1px solid #e5e7eb", paddingLeft: 20,
                        display: "flex", flexDirection: "column",
                      }}>
                        {/* Header: heading + close */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8, flexShrink: 0 }}>
                          <div style={{ fontSize: 12, color: "#6b7280", flex: 1 }}>
                            {chunkDetail.chunk?.heading_path}
                          </div>
                          <CloseButton onClick={() => { setChunkDetail(null); setSelectedChunk(null); }} style={{ marginLeft: 8 }}>
                            <X size={16} />
                          </CloseButton>
                        </div>

                        {/* Meta */}
                        <div style={{ flexShrink: 0, marginBottom: 8 }}>
                          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>
                            Chunk #{chunkDetail.chunk?.chunk_index}
                            <Badge $variant="default" style={{ marginLeft: 6 }}>{chunkDetail.chunk?.chunk_kind}</Badge>
                          </div>
                          <ResultMeta style={{ marginTop: 0 }}>
                            <span>{chunkDetail.chunk?.token_count} tokens</span>
                            <span>Pages {chunkDetail.chunk?.page_start}-{chunkDetail.chunk?.page_end}</span>
                          </ResultMeta>
                        </div>

                        {/* Content (scrollable, fills remaining space) */}
                        <ChunkDetail style={{ flex: 1, minHeight: 0, marginTop: 0 }}>
                          {chunkDetail.chunk?.content_display
                            ? renderMarkdown(chunkDetail.chunk.content_display)
                            : chunkDetail.chunk?.content}
                        </ChunkDetail>

                        {/* Nav buttons (always at bottom) */}
                        <div style={{ display: "flex", gap: 8, marginTop: 8, flexShrink: 0 }}>
                          {chunkDetail.prev_chunk_id && (
                            <ChunkNavButton onClick={() => loadChunkDetail(chunkDetail.prev_chunk_id)}>
                              ← Prev chunk
                            </ChunkNavButton>
                          )}
                          {chunkDetail.next_chunk_id && (
                            <ChunkNavButton onClick={() => loadChunkDetail(chunkDetail.next_chunk_id)}>
                              Next chunk →
                            </ChunkNavButton>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              )}
            </ModalBody>
          </ModalContent>
        </ModalOverlay>
      )}

      {/* ── RAG Chunk Modal ── */}
      {ragChunkModal && (
        <ModalOverlay onClick={() => setRagChunkModal(null)}>
          <ModalContent onClick={(e) => e.stopPropagation()} style={{ maxWidth: 800 }}>
            <ModalHeader>
              <div>
                <ModalTitle>{ragChunkModal.document_title || "Chunk Detail"}</ModalTitle>
                {ragChunkModal.heading_path && (
                  <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>{ragChunkModal.heading_path}</div>
                )}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <ScoreBadge $score={ragChunkModal.score}>
                  {(ragChunkModal.score * 100).toFixed(1)}% match
                </ScoreBadge>
                <CloseButton onClick={() => setRagChunkModal(null)}><X size={18} /></CloseButton>
              </div>
            </ModalHeader>
            <ModalBody style={{ overflow: "auto" }}>
              <ResultMeta style={{ marginBottom: 12 }}>
                {ragChunkModal.chunk_kind && <span>Kind: {ragChunkModal.chunk_kind}</span>}
                {ragChunkModal.page_start != null && <span>Pages: {ragChunkModal.page_start}{ragChunkModal.page_end && ragChunkModal.page_end !== ragChunkModal.page_start ? `-${ragChunkModal.page_end}` : ''}</span>}
                {ragChunkModal.token_count && <span>Tokens: {ragChunkModal.token_count}</span>}
              </ResultMeta>
              <div style={{ fontSize: 14, lineHeight: 1.7, color: "#374151" }}>
                {ragChunkModal.content_display
                  ? renderMarkdown(ragChunkModal.content_display)
                  : <pre style={{ whiteSpace: "pre-wrap", margin: 0, fontFamily: "inherit" }}>{ragChunkModal.content}</pre>}
              </div>
            </ModalBody>
          </ModalContent>
        </ModalOverlay>
      )}

      {/* ── Preview Modal ── */}
      {previewModal && (
        <ModalOverlay onClick={() => { setPreviewModal(null); if (previewBlobUrl) { URL.revokeObjectURL(previewBlobUrl); setPreviewBlobUrl(null); } }}>
          <ModalContent onClick={(e) => e.stopPropagation()} style={{ maxWidth: 1100 }}>
            <ModalHeader>
              <ModalTitle>{previewModal.title}</ModalTitle>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                {previewModal.has_file && (
                  <SecondaryButton onClick={() =>
                    previewModal._userMaterial
                      ? handleUserMaterialDownload(previewModal.id, previewModal.title)
                      : handleDownload(previewModal.id, previewModal.title)
                  }>
                    Download
                  </SecondaryButton>
                )}
                <CloseButton onClick={() => { setPreviewModal(null); if (previewBlobUrl) { URL.revokeObjectURL(previewBlobUrl); setPreviewBlobUrl(null); } }}>
                  <X size={18} />
                </CloseButton>
              </div>
            </ModalHeader>
            <ModalBody>
              {previewBlobUrl && previewModal.file_type === "pdf" ? (
                <iframe
                  src={previewBlobUrl}
                  title={previewModal.title}
                  style={{ width: "100%", height: "70vh", border: "1px solid #e5e7eb", borderRadius: 8 }}
                />
              ) : previewModal.extracted_text ? (
                <pre style={{
                  whiteSpace: "pre-wrap", wordBreak: "break-word",
                  maxHeight: "70vh", overflow: "auto", padding: 16,
                  background: "#f9fafb", borderRadius: 8, border: "1px solid #e5e7eb",
                  fontSize: 14, lineHeight: 1.6,
                }}>
                  {previewModal.extracted_text}
                </pre>
              ) : (
                <EmptyState><p>No content available.</p></EmptyState>
              )}
            </ModalBody>
          </ModalContent>
        </ModalOverlay>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
}
