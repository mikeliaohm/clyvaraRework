import React, { useState, useEffect } from "react";
import styled from "styled-components";
import ChatBot from "../components/ChatBot.jsx";
import { supabase } from "../utils/supabaseClient";

const API_URL = import.meta.env.VITE_API_URL || "/api";

const Title = styled.h1`
  font-size: 36px;
  font-family: 'Rethink Sans';
  margin: 0 0 24px;
`;

const WelcomeMessage = styled.div`
  text-align: center;
  padding: 16px;
  background: linear-gradient(135deg, #20359A, #4A90E2);
  color: white;
  margin: 0 0 32px;
  border-radius: 12px;
  h2, p {
    font-size: 20px;
    font-family: 'Rethink Sans';
  }
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
`;

const StatCard = styled.div`
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
`;

const StatValue = styled.div`
  font-size: 32px;
  font-weight: 700;
  color: #20359A;
  font-family: 'Rethink Sans';
`;

const StatLabel = styled.div`
  font-size: 14px;
  color: #6b7280;
  margin-top: 4px;
`;

const PlaceholderCard = styled.div`
  border: 1px dashed #d1d5db;
  border-radius: 12px;
  padding: 48px 24px;
  text-align: center;
  color: #9ca3af;
  h3 { color: #6b7280; margin: 12px 0 4px; font-family: 'Rethink Sans'; }
  p { font-size: 14px; margin: 0; }
`;

export default function Dashboard() {
  const [userEmail, setUserEmail] = useState(null);
  const [firstName, setFirstName] = useState(null);
  const [stats, setStats] = useState({ materials: 0, processed: 0 });

  useEffect(() => {
    const init = async () => {
      const { data } = await supabase.auth.getUser();
      setUserEmail(data?.user?.email ?? null);

      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return;

        // Fetch profile
        const profileResp = await fetch(`${API_URL}/profile/me`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (profileResp.ok) {
          const profileData = await profileResp.json();
          if (profileData.success && profileData.profile?.full_name) {
            const first = profileData.profile.full_name.trim().split(" ")[0];
            setFirstName(first || null);
          }
        }

        // Fetch materials for stats
        const matResp = await fetch(`${API_URL}/materials`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (matResp.ok) {
          const matData = await matResp.json();
          const list = Array.isArray(matData) ? matData : matData.materials || [];
          setStats({
            materials: list.length,
            processed: list.filter(m => m.status === "processed").length,
          });
        }
      } catch (err) {
        console.error("Dashboard init error:", err);
      }
    };
    init();
  }, []);

  return (
    <>
      <Title>Dashboard</Title>

      {(firstName || userEmail) && (
        <WelcomeMessage>
          <h2>Welcome back, {firstName || userEmail}!</h2>
        </WelcomeMessage>
      )}

      <StatsGrid>
        <StatCard>
          <StatValue>{stats.materials}</StatValue>
          <StatLabel>Materials Uploaded</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{stats.processed}</StatValue>
          <StatLabel>Ready to Study</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>0</StatValue>
          <StatLabel>Questions Attempted</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>--</StatValue>
          <StatLabel>Study Streak</StatLabel>
        </StatCard>
      </StatsGrid>

      <PlaceholderCard>
        <h3>Learning Trends</h3>
        <p>Activity charts and learning progress will appear here as you study.</p>
      </PlaceholderCard>

      <ChatBot />
    </>
  );
}
