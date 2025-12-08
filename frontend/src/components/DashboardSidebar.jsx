import React, { useState } from "react";
import styled from "styled-components";
import { useNavigate, useLocation } from "react-router-dom";
import clyvaralogo from "../assets/clyvaranewlogo.svg";

const SidebarWrap = styled.aside`
  background: #20359A;
  color: white;
  padding: 24px ${p => p.$collapsed ? '12px' : '16px'};
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  transition: padding 0.3s ease;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
  font-family: 'Rethink Sans';
  font-size: 30px;
  white-space: nowrap;
  color: #E7A0CC;
  cursor: pointer; /* 👈 added */
  user-select: none;

  &:hover {
    opacity: 0.9;
  }
`;

const LogoImg = styled.img`
  width: 50px;
  height: 50px;
  object-fit: contain;
  flex-shrink: 0;
`;

const LogoText = styled.span`
  opacity: ${p => p.$collapsed ? 0 : 1};
  visibility: ${p => p.$collapsed ? 'hidden' : 'visible'};
  transition: all 0.3s ease;
`;

const Nav = styled.nav`
  display: flex;
  flex-direction: column;
  align: center;
  gap: 24px;
  margin-top: 24px;
`;

const NavItem = styled.div`
  all: unset;
  flex-direction: column;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 30px;
  justify-content: center;
  font-family: 'generak sans', sans-serif;
  cursor: pointer;
  background: ${p => (p.$active ? "rgba(255,255,255,.2)" : "transparent")};
  white-space: nowrap;
  transition: background 0.2s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.15);
  }
  &:focus {
    outline: none;
  }
`;

const NavIcon = styled.img`
  width: 30px;
  height: 30px;
  object-fit: contain;
  display: block;
`;

const NavText = styled.span`
  opacity: ${p => p.$collapsed ? 0 : 1};
  visibility: ${p => p.$collapsed ? 'hidden' : 'visible'};
  transition: all 0.3s ease;
  font-size: 20px;
`;

const ToggleButton = styled.button`
  all: unset;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  background: transparent;
  white-space: nowrap;
  margin-top: ${p => p.$collapsed ? '0' : '24px'};
  transition: background 0.2s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.15);
  }
  &:focus {
    outline: none;
  }
`;

const ToggleIcon = styled.svg`
  width: 20px;
  height: 20px;
  flex-shrink: 0;
`;

const ToggleText = styled.span`
  opacity: ${p => p.$collapsed ? 0 : 1};
  visibility: ${p => p.$collapsed ? 'hidden' : 'visible'};
  transition: all 0.3s ease;
  font-size: 20px;
`;

export default function DashboardSidebar({ collapsed, onToggle }) {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { label: "Account",       icon: "/src/assets/account.png",      path: "/account" },
    { label: "Dashboard",     icon: "/src/assets/dashboard.png",    path: "/dashboard" },
    { label: "Learning Plan", icon: "/src/assets/learningplan.png", path: "/learningplan" },
    { label: "Care Plan",     icon: "/src/assets/careplan.png",     path: "/careplan" },
  ];

  return (
    <SidebarWrap $collapsed={collapsed}>
      <div>
        {/* Logo → now clickable */}
        <Logo onClick={() => navigate("/dashboard")}>
          <LogoImg src={clyvaralogo} alt="Clyvara logo" />
          <LogoText $collapsed={collapsed}>Clyvara</LogoText>
        </Logo>

        {/* Nav items */}
        {!collapsed && (
          <Nav>
            {navItems.map(({ label, icon, path }) => (
              <NavItem
                key={label}
                $active={location.pathname === path}
                onClick={() => navigate(path)}
              >
                <NavIcon
                  src={icon}
                  alt=""
                  onError={(e) => (e.target.style.display = "none")}
                />
                <NavText $collapsed={collapsed}>{label}</NavText>
              </NavItem>
            ))}
          </Nav>
        )}

        <ToggleButton onClick={onToggle} $collapsed={collapsed}>
          <ToggleIcon viewBox="0 0 16 16">
            {collapsed ? (
              <>
                <line x1="2" y1="4" x2="14" y2="4" stroke="white" strokeWidth="2" />
                <line x1="2" y1="8" x2="14" y2="8" stroke="white" strokeWidth="2" />
                <line x1="2" y1="12" x2="14" y2="12" stroke="white" strokeWidth="2" />
              </>
            ) : (
              <path
                d="M11 2 L5 8 L11 14"
                stroke="white"
                strokeWidth="2"
                fill="none"
                strokeLinecap="round"
              />
            )}
          </ToggleIcon>
          {!collapsed && <ToggleText $collapsed={collapsed}>Collapse</ToggleText>}
        </ToggleButton>
      </div>
    </SidebarWrap>
  );
}
