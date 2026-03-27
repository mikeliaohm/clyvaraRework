import React from "react";
import styled from "styled-components";
import { useNavigate, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  BookOpen,
  ClipboardList,
  GraduationCap,
  User,
  Shield,
  ChevronLeft,
  Menu,
  LogOut,
} from "lucide-react";
import { supabase } from "../utils/supabaseClient";
import clyvaralogo from "../assets/clyvaranewlogo.svg";

const SidebarWrap = styled.aside`
  background: #20359A;
  color: white;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  transition: all 0.25s ease;
  overflow: hidden;
`;

const TopSection = styled.div`
  display: flex;
  flex-direction: column;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  padding: ${p => p.$collapsed ? '16px 0' : '16px 20px'};
  justify-content: ${p => p.$collapsed ? 'center' : 'flex-start'};
  cursor: pointer;
  user-select: none;
  &:hover { opacity: 0.9; }
`;

const LogoImg = styled.img`
  width: 32px;
  height: 32px;
  object-fit: contain;
  flex-shrink: 0;
`;

const LogoText = styled.span`
  font-family: 'Rethink Sans', sans-serif;
  font-size: 20px;
  font-weight: 600;
  color: #E7A0CC;
  opacity: ${p => p.$collapsed ? 0 : 1};
  width: ${p => p.$collapsed ? 0 : 'auto'};
  overflow: hidden;
  transition: opacity 0.25s ease;
`;

const Divider = styled.hr`
  border: none;
  border-top: 1px solid rgba(255,255,255,0.12);
  margin: 0 ${p => p.$collapsed ? '8px' : '16px'};
`;

const NavSection = styled.nav`
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px;
`;

const SectionLabel = styled.span`
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255,255,255,0.4);
  padding: ${p => p.$collapsed ? '12px 0 4px' : '12px 12px 4px'};
  text-align: ${p => p.$collapsed ? 'center' : 'left'};
  opacity: ${p => p.$collapsed ? 0 : 1};
  height: ${p => p.$collapsed ? 0 : 'auto'};
  overflow: hidden;
  transition: opacity 0.25s ease;
`;

const NavItem = styled.button`
  all: unset;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: ${p => p.$collapsed ? '10px 0' : '10px 12px'};
  justify-content: ${p => p.$collapsed ? 'center' : 'flex-start'};
  border-radius: 8px;
  cursor: pointer;
  font-family: 'General Sans', sans-serif;
  font-size: 14px;
  font-weight: ${p => p.$active ? 600 : 400};
  color: ${p => p.$active ? '#fff' : 'rgba(255,255,255,0.7)'};
  background: ${p => p.$active ? 'rgba(255,255,255,0.15)' : 'transparent'};
  transition: all 0.15s ease;

  &:hover {
    background: rgba(255,255,255,0.1);
    color: #fff;
  }
`;

const NavText = styled.span`
  opacity: ${p => p.$collapsed ? 0 : 1};
  width: ${p => p.$collapsed ? 0 : 'auto'};
  overflow: hidden;
  white-space: nowrap;
  transition: opacity 0.25s ease;
`;

const BottomSection = styled.div`
  padding: 8px;
`;

const ToggleButton = styled.button`
  all: unset;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: ${p => p.$collapsed ? '10px 0' : '10px 12px'};
  justify-content: ${p => p.$collapsed ? 'center' : 'flex-start'};
  width: 100%;
  box-sizing: border-box;
  border-radius: 8px;
  cursor: pointer;
  color: rgba(255,255,255,0.5);
  transition: all 0.15s ease;

  &:hover {
    background: rgba(255,255,255,0.1);
    color: #fff;
  }
`;

export default function DashboardSidebar({ collapsed, onToggle, isAdmin }) {
  const navigate = useNavigate();
  const location = useLocation();

  const mainNav = [
    { label: "Dashboard",     icon: LayoutDashboard, path: "/dashboard" },
    { label: "Study",         icon: GraduationCap,   path: "/study" },
    { label: "Learning Plan", icon: BookOpen,         path: "/learningplan" },
    { label: "Care Plan",     icon: ClipboardList,    path: "/careplan" },
  ];

  const adminNav = [
    { label: "Admin Panel",   icon: Shield,          path: "/admin" },
  ];

  const isActive = (path) => {
    if (path === "/dashboard") return location.pathname === path;
    return location.pathname.startsWith(path);
  };

  return (
    <SidebarWrap>
      <TopSection>
        <Logo $collapsed={collapsed} onClick={() => navigate("/dashboard")}>
          <LogoImg src={clyvaralogo} alt="Clyvara" />
          <LogoText $collapsed={collapsed}>Clyvara</LogoText>
        </Logo>

        <Divider $collapsed={collapsed} />

        <NavSection>
          {mainNav.map(({ label, icon: Icon, path }) => (
            <NavItem
              key={path}
              $active={isActive(path)}
              $collapsed={collapsed}
              onClick={() => navigate(path)}
              title={collapsed ? label : undefined}
            >
              <Icon size={18} strokeWidth={isActive(path) ? 2.2 : 1.8} />
              <NavText $collapsed={collapsed}>{label}</NavText>
            </NavItem>
          ))}

          <NavItem
            $active={isActive("/account")}
            $collapsed={collapsed}
            onClick={() => navigate("/account")}
            title={collapsed ? "Account" : undefined}
          >
            <User size={18} strokeWidth={isActive("/account") ? 2.2 : 1.8} />
            <NavText $collapsed={collapsed}>Account</NavText>
          </NavItem>

          {isAdmin && (
            <>
              <SectionLabel $collapsed={collapsed}>Admin</SectionLabel>
              {adminNav.map(({ label, icon: Icon, path }) => (
                <NavItem
                  key={path}
                  $active={isActive(path)}
                  $collapsed={collapsed}
                  onClick={() => navigate(path)}
                  title={collapsed ? label : undefined}
                >
                  <Icon size={18} strokeWidth={isActive(path) ? 2.2 : 1.8} />
                  <NavText $collapsed={collapsed}>{label}</NavText>
                </NavItem>
              ))}
            </>
          )}
        </NavSection>
      </TopSection>

      <BottomSection>
        <NavSection>
          <NavItem
            $collapsed={collapsed}
            onClick={async () => { await supabase.auth.signOut(); navigate("/login"); }}
            title={collapsed ? "Sign out" : undefined}
            style={{ color: "rgba(255,255,255,0.5)" }}
          >
            <LogOut size={18} strokeWidth={1.8} />
            <NavText $collapsed={collapsed}>Sign out</NavText>
          </NavItem>
          <NavItem
            $collapsed={collapsed}
            onClick={onToggle}
            title={collapsed ? "Expand" : "Collapse"}
            style={{ color: "rgba(255,255,255,0.5)" }}
          >
            {collapsed ? <Menu size={18} /> : <ChevronLeft size={18} />}
            <NavText $collapsed={collapsed}>Collapse</NavText>
          </NavItem>
        </NavSection>
      </BottomSection>
    </SidebarWrap>
  );
}
