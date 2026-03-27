import React, { useEffect, useState } from "react";
import styled from "styled-components";
import { supabase } from "../utils/supabaseClient";


const API_URL = import.meta.env.VITE_API_URL || '/api';

const getAccessToken = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token;
};


const Container = styled.div`
  max-width: 900px;
  margin: 24px auto;
  padding: 24px;
`;

const Card = styled.div`
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.06);
`;

const Title = styled.h2`
  margin: 0 0 12px 0;
  font-family: 'Rethink Sans';
`;

const Field = styled.div`
  margin-bottom: 12px;
`;

const Label = styled.label`
  display: block;
  font-size: 13px;
  color: #555;
  margin-bottom: 6px;
`;

const Input = styled.input`
  width: 100%;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #ddd;
  font-size: 14px;
  background: white;
  color: #000;
  
  &:read-only {
    background: #f5f5f5;
    color: #333;
  }
`;

const Select = styled.select`
  width: 100%;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #ddd;
  font-size: 14px;
  background: white;
  color: #000;
  
  option {
    background: white;
    color: #000;
  }
`;

const Row = styled.div`
  display:flex;
  gap:12px;
  margin-top: 16px;
`;

const Button = styled.button`
  background: ${p => p.$primary ? '#20359A' : '#e0e0e0'};
  color: ${p => p.$primary ? 'white' : '#333'};
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  &:disabled { opacity: 0.7; cursor: not-allowed; }
`;

const Pill = styled.span`
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: #03989e1a;
  color: #0f766e;
  font-size: 12px;
  font-weight: 600;
`;

const InfoText = styled.p`
  margin: 4px 0 0;
  font-size: 13px;
  color: #111827;
`;

const SchoolSearchContainer = styled.div`
  position: relative;
`;

const SchoolSuggestions = styled.div`
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
`;

const SchoolSuggestion = styled.div`
  padding: 10px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  &:hover {
    background: #f5f5f5;
  }
  &:last-child {
    border-bottom: none;
  }
`;

// Common specialties
const SPECIALTIES = [
  "Nursing (RN)",
  "Certified Registered Nurse Anesthetist (CRNA)", 
  "Nurse Midwife (CNM)"
];

// Common schools (you can expand this list)
const COMMON_SCHOOLS = [
  "Columbia University",
  "American International University of West Africa", 
  "Hofstra University",
  "Hunter College",
];

export default function Account() {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState({
    full_name: "",
    institution: "",
    grad_year: "",
    specialty: "",
  });
  const [loading, setLoading] = useState(false);
  const [schoolSearch, setSchoolSearch] = useState("");
  const [showSchoolSuggestions, setShowSchoolSuggestions] = useState(false);
  const [filteredSchools, setFilteredSchools] = useState([]);


  useEffect(() => {
  const load = async () => {
    const { data } = await supabase.auth.getUser();
    const user = data?.user ?? null;
    setUser(user);

    if (!user) {
      setProfile({
        full_name: "",
        institution: "",
        grad_year: "",
        specialty: "",
      });
      return;
    }

    try {
      const token = await getAccessToken();
      if (!token) return;

      const response = await fetch(`${API_URL}/profile/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.profile) {
          setProfile({
            full_name: data.profile.full_name || "",
            institution: data.profile.institution || "",
            grad_year: data.profile.grad_year || "",
            specialty: data.profile.specialty || "",
          });
          setSchoolSearch(data.profile.institution || "");
          return;
        }
      }
    } catch (error) {
      console.error("Error loading profile from backend:", error);
    }

  };

  load();
}, []);

  // Filter schools based on search input
  useEffect(() => {
    if (schoolSearch.trim() === "") {
      setFilteredSchools(COMMON_SCHOOLS);
    } else {
      const filtered = COMMON_SCHOOLS.filter(school =>
        school.toLowerCase().includes(schoolSearch.toLowerCase())
      );
      setFilteredSchools(filtered);
    }
  }, [schoolSearch]);

  const handleSave = async () => {
  if (!user) return;
  setLoading(true);
  try {
    const token = await getAccessToken();
    if (!token) {
      throw new Error('No access token available');
    }

    const response = await fetch(`${API_URL}/profile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        full_name: profile.full_name,
        institution: profile.institution,
        grad_year: profile.grad_year,
        specialty: profile.specialty
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to save profile');
    }

    alert("Profile saved successfully!");
  } catch (err) {
    console.error("Save profile error", err);
    alert("Failed to save profile: " + (err.message || err));
  } finally {
    setLoading(false);
  }
};




  const handleSchoolSelect = (school) => {
    setProfile({ ...profile, institution: school });
    setSchoolSearch(school);
    setShowSchoolSuggestions(false);
  };

  const currentYear = new Date().getFullYear();
  const gradYears = Array.from({ length: 10 }, (_, i) => currentYear + i);

  return (
    <Container>
      <Card>
        <Title>Account</Title>

        <Field>
          <Label>Email</Label>
          <Input value={user?.email ?? ""} readOnly />
        </Field>

        <Field>
          <Label>Full name</Label>
          <Input
            value={profile.full_name}
            onChange={(e) =>
              setProfile({ ...profile, full_name: e.target.value })
            }
            placeholder="Your full name"
          />
        </Field>

        <Field>
          <Label>Specialty</Label>
          <Select
            value={profile.specialty}
            onChange={(e) =>
              setProfile({ ...profile, specialty: e.target.value })
            }
          >
            <option value="">Select your specialty</option>
            {SPECIALTIES.map(specialty => (
              <option key={specialty} value={specialty}>{specialty}</option>
            ))}
          </Select>
        </Field>

        <Field>
          <Label>Institution</Label>
          <SchoolSearchContainer>
            <Input
              value={schoolSearch}
              onChange={(e) => {
                setSchoolSearch(e.target.value);
                setProfile({ ...profile, institution: e.target.value });
                setShowSchoolSuggestions(true);
              }}
              onFocus={() => setShowSchoolSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSchoolSuggestions(false), 200)}
              placeholder="Search for your school or university..."
            />
            {showSchoolSuggestions && filteredSchools.length > 0 && (
              <SchoolSuggestions>
                {filteredSchools.map((school, index) => (
                  <SchoolSuggestion
                    key={index}
                    onMouseDown={() => handleSchoolSelect(school)}
                  >
                    {school}
                  </SchoolSuggestion>
                ))}
              </SchoolSuggestions>
            )}
          </SchoolSearchContainer>
          <InfoText>Start typing to see suggestions</InfoText>
        </Field>

        <Field>
          <Label>Graduation Year</Label>
          <Select
            value={profile.grad_year}
            onChange={(e) =>
              setProfile({ ...profile, grad_year: e.target.value })
            }
          >
            <option value="">Select graduation year</option>
            {gradYears.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </Select>
        </Field>

        <Row>
          <Button $primary onClick={handleSave} disabled={loading}>
            {loading ? "Saving..." : "Save Profile"}
          </Button>
        </Row>
      </Card>
    </Container>
  );
}
