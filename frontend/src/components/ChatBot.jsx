//brainie chatbot assistant feature

import { useEffect, useRef, useState, useMemo } from "react";
import styled from "styled-components";
import { buildDomManifest, summarizePageContext } from "../utils/pageContext.js";
import { supabase } from "../utils/supabaseClient.js";
import brainie from "../assets/brainie.png";

const CHAT_API_URL =
  (import.meta.env.VITE_API_URL || "/api").replace(/\/api$/, "") || "";

// New design styled components
const FloatingContainer = styled.div`
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
`;

const ChatToggleButton = styled.button`
  all: unset;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #20359A;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  
  &:hover {
    transform: scale(1.1);
    background: #1a2a7a;
  }
`;

const BrainieIcon = styled.img`
  width: 40px;
  height: 40px;
  object-fit: contain;
`;

const ChatWindow = styled.div`
  width: 350px;
  height: 500px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const ChatHeader = styled.div`
  padding: 12px 16px;
  background: #20359A;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const ChatTitle = styled.h3`
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  font-family: "Rethink Sans";
`;

const CloseButton = styled.button`
  all: unset;
  color: white;
  cursor: pointer;
  padding: 4px;
  font-size: 20px;
  
  &:hover {
    opacity: 0.8;
  }
`;

const MessagesContainer = styled.div`
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const MessageBubble = styled.div`
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 18px;
  word-wrap: break-word;
  font-size: 14px;
  font-family: 'General Sans';
  font-weight: 400;
  line-height: 1.4;
  
  ${p => p.$isUser ? `
    align-self: flex-end;
    background: #20359A;
    color: white;
    border-bottom-right-radius: 4px;
  ` : `
    align-self: flex-start;
    background: #f0f0f0;
    color: #333;
    border-bottom-left-radius: 4px;
  `}
`;

const InputContainer = styled.div`
  padding: 16px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 8px;
  background: white;
`;

const ChatInput = styled.input`
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 24px;
  font-size: 14px;
  font-family: 'General Sans';
  font-weight: 400;
  
  &:focus {
    outline: none;
    border-color: #20359A;
  }
`;

const SendButton = styled.button`
  all: unset;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #20359A;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  
  &:hover {
    background: #1a2a7a;
  }
  
  &:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
`;

// Status indicator for connection
const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
`;

const Dot = styled.span`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${({ $ok }) => ($ok ? "#10b981" : "#f59e0b")};
`;

export default function Chat() {
  // New minimizable state
  const [isOpen, setIsOpen] = useState(false);
  
  // Keep all existing working state and functionality
  const [messages, setMessages] = useState([
    { 
      role: "assistant", 
      text: "Hi! I'm Brainie! Ask me about Clyvara or anything related to your studies!" 
    },
  ]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState(() => sessionStorage.getItem("thread_id") || null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Keep all existing useEffect hooks
  useEffect(() => {
    if (threadId) sessionStorage.setItem("thread_id", threadId);
  }, [threadId]);

  const pageContext = useMemo(() => {
    const ctx = buildDomManifest();
    return summarizePageContext(ctx);
  }, [window.location.pathname, document.title]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Keep the existing working send function
  async function handleSend(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setMessages(prev => [...prev, { role: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      // Get the current session token
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        throw new Error("Not authenticated");
      }

      const res = await fetch(`${CHAT_API_URL}/chat-rag`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          message: text,
          thread_id: threadId,
          page_context: pageContext,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      setThreadId(data.thread_id);
      setMessages(prev => [...prev, { role: "assistant", text: data.reply }]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          text: "Sorry, I'm having trouble connecting right now. Please try again later.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  // Use new design but keep existing functionality
  return (
    <FloatingContainer>
      {isOpen ? (
        <ChatWindow>
          <ChatHeader>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              
              <ChatTitle>Brainie Assistant</ChatTitle>
            </div>
            <CloseButton onClick={() => setIsOpen(false)}>×</CloseButton>
          </ChatHeader>
          
          <MessagesContainer>
            {messages.map((message, index) => (
              <MessageBubble key={index} $isUser={message.role === "user"}>
                {message.text}
              </MessageBubble>
            ))}
            {loading && (
              <MessageBubble $isUser={false}>
                Thinking... 
              </MessageBubble>
            )}
            <div ref={messagesEndRef} />
          </MessagesContainer>
          
          <InputContainer>
            <ChatInput
              type="text"
              placeholder="Ask Brainie anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') handleSend(e);
              }}
              disabled={loading}
            />
            <SendButton 
              onClick={handleSend} 
              disabled={!input.trim() || loading}
            >
              ↑
            </SendButton>
          </InputContainer>
        </ChatWindow>
      ) : (
        <ChatToggleButton onClick={() => setIsOpen(true)}>
          <BrainieIcon src={brainie} alt="Brainie" />
        </ChatToggleButton>
      )}
    </FloatingContainer>
  );
}
