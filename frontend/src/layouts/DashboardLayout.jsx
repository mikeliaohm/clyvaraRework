//general layout for any page with the dashboard

import React from "react";
import styled from "styled-components";
import { Outlet } from "react-router-dom";
import DashboardSidebar from "../components/DashboardSidebar.jsx";
import { useAuth } from "../utils/useAuth.js";

const Shell = styled.div`
  display: grid;
  grid-template-columns: ${p => p.$collapsed ? '60px' : '200px'} 1fr;
  min-height: 100vh;
  background: #f8f9fa;
  transition: grid-template-columns 0.25s ease;
`;

const Main = styled.main`
  padding: 28px 32px;
  background: white;
  overflow-y: auto;
`;

export default function DashboardLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
  const { user } = useAuth();

  const isAdmin = user?.roles?.includes("admin") || false;

  return (
    <Shell $collapsed={sidebarCollapsed}>
      <DashboardSidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(prev => !prev)}
        isAdmin={isAdmin}
      />

      <Main>
        <Outlet context={{ isAdmin }} />
      </Main>
    </Shell>
  );
}
