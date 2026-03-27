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
} from "lucide-react";
import { supabase } from "../utils/supabaseClient";

const API_URL = import.meta.env.VITE_API_URL || "/api";

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

  &:hover {
    color: #20359A;
  }
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
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: ${p => p.$dragOver ? '#f0f4ff' : '#fafafa'};

  &:hover {
    border-color: #20359A;
    background: #f0f4ff;
  }
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

// ── Component ────────────────────────────────────────────────

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState("rag");
  const [users, setUsers] = useState([]);
  const [systemMaterials, setSystemMaterials] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef();

  const tabs = [
    { id: "rag",   label: "RAG Upload & Test", icon: Search },
    { id: "docs",  label: "System Documents",  icon: FileText },
    { id: "users", label: "Users",             icon: Users },
    { id: "questions", label: "Questions",      icon: ClipboardList },
  ];

  useEffect(() => {
    if (activeTab === "users") loadUsers();
    if (activeTab === "docs" || activeTab === "rag") loadSystemMaterials();
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
      if (resp.ok) {
        const data = await resp.json();
        setUsers(data.users || []);
      }
    } catch (err) {
      console.error("Error loading users:", err);
    }
  };

  const loadSystemMaterials = async () => {
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/admin/system-materials`, { headers });
      if (resp.ok) {
        const data = await resp.json();
        setSystemMaterials(data.materials || []);
      }
    } catch (err) {
      console.error("Error loading system materials:", err);
    }
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
        method: "POST",
        headers,
        body: formData,
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Upload failed");
      }

      const result = await resp.json();
      setUploadStatus({ type: "success", message: `Uploaded "${result.file_name}" - processing in background.` });
      setTimeout(() => loadSystemMaterials(), 2000);
    } catch (err) {
      setUploadStatus({ type: "error", message: err.message });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteSystemMaterial = async (materialId, title) => {
    if (!confirm(`Delete system material "${title}"?`)) return;
    try {
      const headers = await getAuthHeaders();
      const resp = await fetch(`${API_URL}/admin/system-materials/${materialId}`, {
        method: "DELETE",
        headers,
      });
      if (resp.ok) {
        setSystemMaterials(prev => prev.filter(m => m.id !== materialId));
      }
    } catch (err) {
      console.error("Error deleting material:", err);
    }
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

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || "Search failed");
      }

      const data = await resp.json();
      setSearchResults(data);
    } catch (err) {
      setSearchResults({ error: err.message });
    } finally {
      setSearching(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const formatBytes = (bytes) => {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  // ── Render tabs ────────────────────────────────────────────

  const renderRagTab = () => (
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
          {uploading ? (
            <Loader2 size={32} color="#20359A" style={{ animation: "spin 1s linear infinite" }} />
          ) : (
            <Upload size={32} color="#9ca3af" />
          )}
          <p style={{ margin: "12px 0 0", color: "#374151", fontWeight: 500 }}>
            {uploading ? "Uploading..." : "Drop a file here or click to browse"}
          </p>
          <UploadHint>PDF, DOCX, DOC, or TXT. System documents are visible to all users.</UploadHint>
        </UploadArea>
        <FileInput
          type="file"
          ref={fileInputRef}
          onChange={(e) => handleUpload(e.target.files[0])}
          accept=".pdf,.txt,.doc,.docx"
        />

        {systemMaterials.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <p style={{ fontSize: 13, color: "#6b7280", marginBottom: 8 }}>
              {systemMaterials.filter(m => m.status === "processed").length} system document(s) indexed
            </p>
          </div>
        )}
      </Section>

      <Section>
        <SectionTitle>Test RAG Retrieval</SectionTitle>
        <SearchBox>
          <Input
            placeholder="Enter a search query to test retrieval..."
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
            <p style={{ fontSize: 13, color: "#6b7280", marginBottom: 12 }}>
              {searchResults.total_results} result(s) for "{searchResults.query}"
            </p>
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
                  <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>
                    {r.heading_path}
                  </div>
                )}
                <ResultContent>{r.content}</ResultContent>
                <ResultMeta>
                  {r.chunk_kind && <span>Kind: {r.chunk_kind}</span>}
                  {r.page_start != null && <span>Pages: {r.page_start}{r.page_end && r.page_end !== r.page_start ? `–${r.page_end}` : ''}</span>}
                  {r.token_count && <span>Tokens: {r.token_count}</span>}
                </ResultMeta>
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
    </>
  );

  const renderDocsTab = () => (
    <Section>
      <SectionTitle>System Documents</SectionTitle>
      {systemMaterials.length === 0 ? (
        <EmptyState>
          <FileText size={32} />
          <p>No system documents uploaded yet.</p>
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
                    <DangerButton onClick={() => handleDeleteSystemMaterial(m.id, m.title)}>
                      <Trash2 size={14} /> Delete
                    </DangerButton>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}
    </Section>
  );

  const renderUsersTab = () => (
    <Section>
      <SectionTitle>All Users</SectionTitle>
      {users.length === 0 ? (
        <EmptyState>
          <Users size={32} />
          <p>Loading users...</p>
        </EmptyState>
      ) : (
        <Card style={{ padding: 0, overflow: "hidden" }}>
          <Table>
            <thead>
              <tr>
                <Th>ID</Th>
                <Th>Email</Th>
                <Th>Name</Th>
                <Th>Specialty</Th>
                <Th>Roles</Th>
                <Th>Status</Th>
                <Th>Joined</Th>
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
                      <Badge key={r} $variant={r === "admin" ? "admin" : "default"} style={{ marginRight: 4 }}>
                        {r}
                      </Badge>
                    ))}
                    {(!u.roles || u.roles.length === 0) && <span style={{ color: "#9ca3af" }}>user</span>}
                  </Td>
                  <Td>
                    <Badge $variant={u.is_active ? "success" : "error"}>
                      {u.is_active ? "active" : "inactive"}
                    </Badge>
                  </Td>
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
          This feature is currently being designed.
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

      {activeTab === "rag" && renderRagTab()}
      {activeTab === "docs" && renderDocsTab()}
      {activeTab === "users" && renderUsersTab()}
      {activeTab === "questions" && renderQuestionsTab()}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
}
