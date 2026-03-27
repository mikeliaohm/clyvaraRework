import React from "react";
import styled from "styled-components";
import { GraduationCap, BookOpen, ClipboardList } from "lucide-react";

const PageTitle = styled.h1`
  font-size: 28px;
  font-family: 'Rethink Sans', sans-serif;
  margin: 0 0 24px;
  color: #1a1a1a;
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 8px;
`;

const Card = styled.div`
  border: 1px dashed #d1d5db;
  border-radius: 12px;
  padding: 32px 24px;
  text-align: center;
  color: #9ca3af;
`;

const CardTitle = styled.h3`
  color: #6b7280;
  margin: 12px 0 4px;
  font-family: 'Rethink Sans', sans-serif;
  font-size: 16px;
`;

const CardDesc = styled.p`
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
`;

export default function StudyPage() {
  return (
    <>
      <PageTitle>Study</PageTitle>

      <Grid>
        <Card>
          <ClipboardList size={36} color="#d1d5db" />
          <CardTitle>Practice Questions</CardTitle>
          <CardDesc>
            Test your knowledge with AI-generated practice questions
            based on your study materials.
          </CardDesc>
        </Card>

        <Card>
          <BookOpen size={36} color="#d1d5db" />
          <CardTitle>Flashcards</CardTitle>
          <CardDesc>
            Review key concepts with spaced-repetition flashcards.
          </CardDesc>
        </Card>

        <Card>
          <GraduationCap size={36} color="#d1d5db" />
          <CardTitle>Mock Exams</CardTitle>
          <CardDesc>
            Simulate exam conditions with timed practice tests.
          </CardDesc>
        </Card>
      </Grid>
    </>
  );
}
