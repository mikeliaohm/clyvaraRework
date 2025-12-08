// src/pages/LearningPlanPage.jsx
import React from "react";
import styled from "styled-components";
import { useNavigate } from "react-router-dom";

const PageWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
  color: #0f172a;
  font-family: 'Rethink Sans', system-ui, sans-serif;
`;

const PageHeader = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Title = styled.h1`
  margin: 0;
  font-size: 28px;
  font-weight: 600;
`;

const Subtitle = styled.p`
  margin: 0;
  font-size: 14px;
  color: #6b7280;
`;

const ModuleGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-top: 8px;
`;

const ModuleCard = styled.div`
  position: relative;
  border: 1px solid #e5e7eb;
  padding: 20px;
  background: #f9fafb;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 180px;
  text-align: left;
`;

const AccentBar = styled.div`
  height: 16px;
  background: #DFF4A6;
  margin: -20px -20px 12px -20px;
`;


const ModuleTitle = styled.h2`
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
`;

const ModuleTag = styled.span`
  display: inline-flex;
  align-items: center;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 4px 8px;
  color: #20359A;
  background: #e0e7ff;
  margin-bottom: 8px;
`;

const ModuleDescription = styled.p`
  margin: 0;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
`;

const ModuleFooter = styled.div`
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #6b7280;
`;

const StartText = styled.span`
  font-weight: 500;
  font-size: 14px;
  color: #20359A;
`;

export default function LearningPlanPage() {
  const navigate = useNavigate();

  const modules = [
    {
      id: "opioids",
      title: "Opioids",
      tag: "Anesthesia Pharmacology",
      description:
        "Learn more about opioids and their relation to anesthesia pharmacology.",
      path: "/learningplan/opioids",
    },
    {
      id: "inhaledanesthetics",
      title: "Inhaled Anesthetics",
      tag: "Anesthesia Pharmacology",
      description:
        "Learn more about inhaled anesthetics and their relation to anesthesia pharmacology.",
      path: "/learningplan/inhaledanesthetics",
    },
  ];

  const handleOpenModule = (path) => {
    navigate(path);
  };

  return (
    <PageWrapper>
      <PageHeader>
        <Title>Learning Plans</Title>
        <Subtitle>
          Choose a module to explore videos, concept maps, and knowledge checks.
        </Subtitle>
      </PageHeader>

      <ModuleGrid>
        {modules.map((m) => (
          <ModuleCard
            key={m.id}
            type="button"
            onClick={() => handleOpenModule(m.path)}
          >
            <div>
              <AccentBar />
              <ModuleTag>{m.tag}</ModuleTag>
              <ModuleTitle>{m.title}</ModuleTitle>
              <ModuleDescription>{m.description}</ModuleDescription>
            </div>
            <ModuleFooter>
              <StartText>Resume →</StartText>
            </ModuleFooter>
          </ModuleCard>
        ))}
      </ModuleGrid>
    </PageWrapper>
  );
}
