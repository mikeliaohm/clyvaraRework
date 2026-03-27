import React, { useState, useMemo, useEffect, useRef } from "react";
import styled from "styled-components";
import { buildFormState } from "../utils/buildFormState";
import { supabase } from "../utils/supabaseClient";

const API_URL = import.meta.env.VITE_API_URL || "/api";

const PageWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  color: #0f172a;
`;

const HeaderCard = styled.div`
  background: #eef3ff;
  border: 1px solid #dbe2ff;
  border-radius: 8px;
  padding: 24px;
  font-family: 'Rethink Sans', system-ui, sans-serif;
`;

const Title = styled.h1`
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 600;
  color: #0f172a;
  text-align: center;
`;

const Subtitle = styled.p`
  margin: 0;
  font-size: 15px;
  font-weight: 400;
  color: #4b5563;
  text-align: center;
`;

const SectionCard = styled.div`
  background: #ffffff;
  border: 1px solid #dcdcdc;
  border-radius: 8px;
  padding: 24px;
  font-family: 'Rethink Sans', system-ui, sans-serif;
`;

const SectionHeader = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const SectionTitleRow = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0f172a;
`;

const SectionIcon = styled.span`
  font-size: 18px;
`;

const SectionTitle = styled.h2`
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #0f172a;
`;

const TabsBar = styled.div`
  display: flex;
  flex-wrap: wrap;
  background: #f8fafc;
  border: 1px solid #dcdcdc;
  border-radius: 6px;
  padding: 4px;
  width: 100%;
  max-width: 600px;
  gap: 5px;
`;

const TabButton = styled.button`
  flex: 1;
  min-width: max-content;
  background: ${p => (p.$active ? "#ffffff" : "transparent")};
  border: 0;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
  font-weight: ${p => (p.$active ? "600" : "500")};
  color: ${p => (p.$active ? "#0f172a" : "#4b5563")};
  text-align: center;
  cursor: pointer;

  &:hover {
    background: ${p => (p.$active ? "#ffffff" : "rgba(0,0,0,0.03)")};
  }

  &:focus {
    outline: 2px solid #4f46e5;
    outline-offset: 2px;
  }
`;

const FormGrid2 = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px 60px;
  margin-top: 16px;
  max-width: 800px;
`;

const VitalGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  row-gap: 16px;
  column-gap: 48px;
  max-width: 800px;
`;

const FormRowFull = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
  max-width: 800px;
`;

const FieldGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
`;

const SmallGrid3 = styled.div`
  display: grid;
  grid-template-columns: repeat(3, minmax(0,1fr));
  gap: 20px 40px;
  margin-top: 16px;
  max-width: 1000px;
`;

const SmallGrid2 = styled.div`
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 20px 24px;
  margin-top: 16px;
  max-width: 1000px;
`;

const LabelRow = styled.div`
  display: flex;
  align-items: baseline;
  gap: 4px;
`;

const Label = styled.label`
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
`;

const Req = styled.span`
  color: #dc2626;
  font-size: 14px;
  line-height: 1;
`;

const Input = styled.input`
  width: 100%;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 14px;
  color: #0f172a;
  font-family: inherit;

  &:focus {
    outline: 2px solid #4f46e5;
    border-color: #4f46e5;
  }
`;

const Select = styled.select`
  width: 100%;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 14px;
  color: #0f172a;
  font-family: inherit;

  &:focus {
    outline: 2px solid #4f46e5;
    border-color: #4f46e5;
  }
`;

const TextArea = styled.textarea`
  width: 100%;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 14px;
  color: #0f172a;
  min-height: 70px;
  font-family: inherit;
  resize: none;

  &:focus {
    outline: 2px solid #4f46e5;
    border-color: #4f46e5;
  }
`;

const SmallInput = styled(Input)`
  width: 60%;
  min-width: 180px;
`;

const TinyInput = styled.input`
  width: 70%;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 6px 8px;
  min-height: 24px;
  font-size: 13px;
  color: #0f172a;
  font-family: inherit;
  line-height: 1.3;

  &:focus {
    outline: 2px solid #4f46e5;
    border-color: #4f46e5;
  }
`;

const AirwayTextArea = styled.textarea`
  width: 100%;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 13px;
  color: #0f172a;
  min-height: 60px;
  font-family: inherit;
  resize: none;

  &:focus {
    outline: 2px solid #4f46e5;
    border-color: #4f46e5;
  }
`;

const AirwayGrid2x2 = styled.div`
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 24px;
  row-gap: 24px;
  max-width: 800px;
  margin-top: 16px;
  align-items: start;
`;

const AirwayRow3 = styled.div`
  display: grid;
  grid-template-columns: repeat(3, minmax(0,1fr));
  column-gap: 48px;
  row-gap: 24px;
  max-width: 1000px;
  margin-top: 24px;
`;

const HintRow = styled.p`
  font-size: 12px;
  color: #64748b;
  margin: 8px 0 0 0;
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 4px;
`;

const SubsectionTitle = styled.h3`
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin: 32px 0 16px 0;
`;

const FooterRow = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 32px;
  align-items: center;
`;

const BackButton = styled.button`
  background: #e5e7eb;
  color: #1f2937;
  font-size: 14px;
  font-weight: 500;
  border: 0;
  border-radius: 8px;
  padding: 10px 16px;
  cursor: pointer;

  &:hover {
    background: #d1d5db;
  }

  &:focus {
    outline: 2px solid #4f46e5;
    outline-offset: 2px;
  }
`;

const NextButton = styled.button`
  background: #4f46e5;
  color: white;
  font-size: 14px;
  font-weight: 500;
  border: 0;
  border-radius: 8px;
  padding: 10px 16px;
  cursor: pointer;

  &:hover {
    background: #4338ca;
  }

  &:focus {
    outline: 2px solid #4f46e5;
    outline-offset: 2px;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const ActionBar = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 12px;
  flex-wrap: wrap;
`;

const ActionButton = styled.button`
  background: ${props => props.$variant === 'primary' ? '#4f46e5' : props.$variant === 'danger' ? '#dc2626' : '#e5e7eb'};
  color: ${props => props.$variant === 'primary' ? 'white' : props.$variant === 'danger' ? 'white' : '#1f2937'};
  font-size: 14px;
  font-weight: 500;
  border: 0;
  border-radius: 8px;
  padding: 10px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;

  &:hover {
    background: ${props => props.$variant === 'primary' ? '#4338ca' : props.$variant === 'danger' ? '#b91c1c' : '#d1d5db'};
  }

  &:focus {
    outline: 2px solid #4f46e5;
    outline-offset: 2px;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const CarePlanList = styled.div`
  background: #ffffff;
  border: 1px solid #dcdcdc;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
`;

const CarePlanItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f3f4f6;

  &:last-child {
    border-bottom: none;
  }
`;

const CarePlanInfo = styled.div`
  flex: 1;
`;

const CarePlanTitle = styled.h3`
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #0f172a;
`;

const CarePlanMeta = styled.p`
  font-size: 14px;
  color: #64748b;
  margin: 0;
`;

const CarePlanActions = styled.div`
  display: flex;
  gap: 8px;
`;

const AIRecommendations = styled.div`
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 24px;
  margin-top: 24px;
`;

const AIRecommendationsTitle = styled.h3`
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: #0c4a6e;
`;

const AIRecommendationsContent = styled.div`
  font-size: 14px;
  line-height: 1.6;
  color: #0c4a6e;
  white-space: pre-wrap;
`;

const LoadingSpinner = styled.div`
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #4f46e5;
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

export default function CarePlanPage() {
  const pageTopRef = useRef(null);
  const [currentTab, setCurrentTab] = useState("info"); // "info" | "history" | "assessment" | "labs"
  
  // Database integration states
  const [carePlans, setCarePlans] = useState([]);
  const [currentCarePlanId, setCurrentCarePlanId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showCarePlanList, setShowCarePlanList] = useState(false);
  const [aiRecommendations, setAiRecommendations] = useState(null);
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);

  /* TAB 1: Patient Info */
  const [age, setAge] = useState("please-select");
  const [sex, setSex] = useState("please-select");
  const [height, setHeight] = useState("please-select");
  const [weight, setWeight] = useState("please-select");

  const [diagnosis, setDiagnosis] = useState("");
  const [tempF, setTempF] = useState("");
  const [bp, setBp] = useState("");
  const [hr, setHr] = useState("");
  const [rr, setRr] = useState("");

  /* TAB 2: History */
  const [pmh, setPmh] = useState("");
  const [psh, setPsh] = useState("");
  const [anesthesiaHx, setAnesthesiaHx] = useState("");
  const [meds, setMeds] = useState("");
  const [alcohol, setAlcohol] = useState("");
  const [substance, setSubstance] = useState("");

  /* TAB 3: Assessment */
  const [neuro, setNeuro] = useState("");
  const [heent, setHeent] = useState("");
  const [resp, setResp] = useState("");
  const [cardio, setCardio] = useState("");
  const [gi, setGi] = useState("");
  const [gu, setGu] = useState("");
  const [endo, setEndo] = useState("");
  const [otherFindings, setOtherFindings] = useState("");

  const [mallampati, setMallampati] = useState("please-select");
  const [ulbt, setUlbt] = useState("please-select");
  const [thyromental, setThyromental] = useState("");
  const [interincisor, setInterincisor] = useState("");
  const [dentition, setDentition] = useState("");
  const [neck, setNeck] = useState("");
  const [oralMucosa, setOralMucosa] = useState("");

  /* TAB 4: Labs / Tests */
  const [na, setNa] = useState("");
  const [k, setK] = useState("");
  const [cl, setCl] = useState("");
  const [co2, setCo2] = useState("");
  const [bun, setBun] = useState("");
  const [cr, setCr] = useState("");
  const [glu, setGlu] = useState("");
  const [wbc, setWbc] = useState("");
  const [hgb, setHgb] = useState("");
  const [hct, setHct] = useState("");
  const [plt, setPlt] = useState("");
  const [pt, setPt] = useState("");
  const [ptt, setPtt] = useState("");
  const [inr, setInr] = useState("");
  const [abg, setAbg] = useState("");
  const [otherLabs, setOtherLabs] = useState("");

  const [ekg, setEkg] = useState("");
  const [cxr, setCxr] = useState("");
  const [echo, setEcho] = useState("");
  const [otherImaging, setOtherImaging] = useState("");

  /* dropdown options */
  const sexOptions = ["Female", "Male", "Other"];

  const ageOptions = useMemo(() => {
    const arr = ["< 6 months"];
    for (let i = 1; i <= 100; i++) arr.push(`${i}`);
    return arr;
  }, []);

  const heightOptions = useMemo(() => {
    const arr = ["< 2 ft"];
    for (let feet = 2; feet <= 7; feet++) {
      for (let inch = 0; inch < 12; inch++) {
        arr.push(`${feet}'${inch}"`);
      }
    }
    arr.push("> 7 ft");
    return arr;
  }, []);

  const weightOptions = useMemo(() => {
    const arr = ["< 50 lbs"];
    let w = 50.0;
    while (w <= 250.0 + 0.001) {
      arr.push(`${w.toFixed(1)} lbs`);
      w += 2.5;
    }
    arr.push("> 250 lbs");
    return arr;
  }, []);

  const mallampatiOptions = ["Mallampati I", "Mallampati II", "Mallampati III", "Mallampati IV"];
  const ulbtOptions = ["Grade I", "Grade II", "Grade III"];

  // Database functions
  const loadCarePlans = async () => {
    try {
      setIsLoading(true);
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        console.error("No active session");
        return;
      }

      const response = await fetch(`${API_URL}/care-plans`, {
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCarePlans(data.care_plans || []);
      } else {
        console.error("Failed to load care plans");
      }
    } catch (error) {
      console.error("Error loading care plans:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveCarePlan = async () => {
    try {
      setIsSaving(true);
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        console.error("No active session");
        return null;
      }

      const formState = buildFormState({
        age, sex, height, weight, diagnosis, tempF, bp, hr, rr,
        pmh, psh, anesthesiaHx, meds, alcohol, substance,
        neuro, heent, resp, cardio, gi, gu, endo, otherFindings,
        mallampati, ulbt, thyromental, interincisor, dentition, neck, oralMucosa,
        na, k, cl, co2, bun, cr, glu, wbc, hgb, hct, plt, pt, ptt, inr, abg, otherLabs,
        ekg, cxr, echo, otherImaging
      });

      const carePlanData = {
        title: `Care Plan - ${diagnosis || 'Untitled'}`,
        patient_name: formState.patient_name || '',
        procedure: formState.procedure || '',
        diagnosis: diagnosis,
        ...formState
      };

      const response = await fetch(`${API_URL}/care-plans`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify(carePlanData)
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentCarePlanId(data.care_plan_id);
        await loadCarePlans(); // Refresh the list
        return data.care_plan_id;
      } else {
        console.error("Failed to save care plan");
        alert("Failed to save care plan");
        return null;
      }
    } catch (error) {
      console.error("Error saving care plan:", error);
      alert("Error saving care plan");
      return null;
    } finally {
      setIsSaving(false);
    }
  };

  const loadCarePlan = async (carePlanId) => {
    try {
      setIsLoading(true);
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        console.error("No active session");
        return;
      }

      const response = await fetch(`${API_URL}/care-plans/${carePlanId}`, {
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        const carePlan = data.care_plan;
        
        // Populate form fields
        setAge(carePlan.age || "please-select");
        setSex(carePlan.sex || "please-select");
        setHeight(carePlan.height || "please-select");
        setWeight(carePlan.weight || "please-select");
        setDiagnosis(carePlan.diagnosis || "");
        setTempF(carePlan.tempF || "");
        setBp(carePlan.bp || "");
        setHr(carePlan.hr || "");
        setRr(carePlan.rr || "");
        
        setPmh(carePlan.pmh || "");
        setPsh(carePlan.psh || "");
        setAnesthesiaHx(carePlan.anesthesiaHx || "");
        setMeds(carePlan.meds || "");
        setAlcohol(carePlan.alcohol || "");
        setSubstance(carePlan.substance || "");
        
        setNeuro(carePlan.neuro || "");
        setHeent(carePlan.heent || "");
        setResp(carePlan.resp || "");
        setCardio(carePlan.cardio || "");
        setGi(carePlan.gi || "");
        setGu(carePlan.gu || "");
        setEndo(carePlan.endo || "");
        setOtherFindings(carePlan.otherFindings || "");
        
        setMallampati(carePlan.mallampati || "please-select");
        setUlbt(carePlan.ulbt || "please-select");
        setThyromental(carePlan.thyromental || "");
        setInterincisor(carePlan.interincisor || "");
        setDentition(carePlan.dentition || "");
        setNeck(carePlan.neck || "");
        setOralMucosa(carePlan.oralMucosa || "");
        
        setNa(carePlan.na || "");
        setK(carePlan.k || "");
        setCl(carePlan.cl || "");
        setCo2(carePlan.co2 || "");
        setBun(carePlan.bun || "");
        setCr(carePlan.cr || "");
        setGlu(carePlan.glu || "");
        setWbc(carePlan.wbc || "");
        setHgb(carePlan.hgb || "");
        setHct(carePlan.hct || "");
        setPlt(carePlan.plt || "");
        setPt(carePlan.pt || "");
        setPtt(carePlan.ptt || "");
        setInr(carePlan.inr || "");
        setAbg(carePlan.abg || "");
        setOtherLabs(carePlan.otherLabs || "");
        
        setEkg(carePlan.ekg || "");
        setCxr(carePlan.cxr || "");
        setEcho(carePlan.echo || "");
        setOtherImaging(carePlan.otherImaging || "");
        
        setCurrentCarePlanId(carePlanId);
        setAiRecommendations(carePlan.ai_recommendations);
        setShowCarePlanList(false);
        
      } else {
        console.error("Failed to load care plan");
        alert("Failed to load care plan");
      }
    } catch (error) {
      console.error("Error loading care plan:", error);
      alert("Error loading care plan");
    } finally {
      setIsLoading(false);
    }
  };

  const generateAIRecommendations = async (carePlanIdOverride = null) => {
    const carePlanIdToUse = carePlanIdOverride ?? currentCarePlanId;

    if (!carePlanIdToUse) {
      alert("Please save the care plan first before generating AI recommendations");
      return;
    }

    try {
      setIsGeneratingAI(true);
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        console.error("No active session");
        return;
      }

      const response = await fetch(`${API_URL}/care-plans/${carePlanIdToUse}/generate-ai`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAiRecommendations(data.recommendations.anesthesia_plan);
      } else {
        console.error("Failed to generate AI recommendations");
        alert("Failed to generate AI recommendations");
      }
    } catch (error) {
      console.error("Error generating AI recommendations:", error);
      alert("Error generating AI recommendations");
    } finally {
      setIsGeneratingAI(false);
    }
  };

  const deleteCarePlan = async (carePlanId) => {
    if (!confirm("Are you sure you want to delete this care plan?")) {
      return;
    }

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        console.error("No active session");
        return;
      }

      const response = await fetch(`${API_URL}/care-plans/${carePlanId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (response.ok) {
        await loadCarePlans(); // Refresh the list
        if (currentCarePlanId === carePlanId) {
          setCurrentCarePlanId(null);
          setAiRecommendations(null);
        }
      } else {
        console.error("Failed to delete care plan");
        alert("Failed to delete care plan");
      }
    } catch (error) {
      console.error("Error deleting care plan:", error);
      alert("Error deleting care plan");
    }
  };

  const clearForm = () => {
    setAge("please-select");
    setSex("please-select");
    setHeight("please-select");
    setWeight("please-select");
    setDiagnosis("");
    setTempF("");
    setBp("");
    setHr("");
    setRr("");
    setPmh("");
    setPsh("");
    setAnesthesiaHx("");
    setMeds("");
    setAlcohol("");
    setSubstance("");
    setNeuro("");
    setHeent("");
    setResp("");
    setCardio("");
    setGi("");
    setGu("");
    setEndo("");
    setOtherFindings("");
    setMallampati("please-select");
    setUlbt("please-select");
    setThyromental("");
    setInterincisor("");
    setDentition("");
    setNeck("");
    setOralMucosa("");
    setNa("");
    setK("");
    setCl("");
    setCo2("");
    setBun("");
    setCr("");
    setGlu("");
    setWbc("");
    setHgb("");
    setHct("");
    setPlt("");
    setPt("");
    setPtt("");
    setInr("");
    setAbg("");
    setOtherLabs("");
    setEkg("");
    setCxr("");
    setEcho("");
    setOtherImaging("");
    setCurrentCarePlanId(null);
    setAiRecommendations(null);
  };

  // Load care plans on component mount
  useEffect(() => {
    loadCarePlans();
  }, []);

  const handleNext = () => {
    if (currentTab === "info") {
      setCurrentTab("history");
    } else if (currentTab === "history") {
      setCurrentTab("assessment");
    } else if (currentTab === "assessment") {
      setCurrentTab("labs");
    } else {
      console.log("Generate care plan!");
    }
  };

  const handleBack = () => {
    if (currentTab === "history") {
      setCurrentTab("info");
    } else if (currentTab === "assessment") {
      setCurrentTab("history");
    } else if (currentTab === "labs") {
      setCurrentTab("assessment");
    }
  };

  const handleGenerateCarePlan = async () => {
    if (isSaving || isGeneratingAI) return;
  
    const carePlanId = await saveCarePlan();
    if (!carePlanId) return;
  
    await generateAIRecommendations(carePlanId);
  
    setTimeout(() => {
      if (pageTopRef.current) {
        pageTopRef.current.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      } else {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    }, 0);
  };

  const renderFooter = (showBack, nextLabel) => (
    <FooterRow>
      <div>
        {showBack ? (
          <BackButton onClick={handleBack}>Back</BackButton>
        ) : (
          <span />
        )}
      </div>
      <NextButton onClick={handleNext}>{nextLabel}</NextButton>
    </FooterRow>
  );

  const renderInfoTab = () => (
    <>
      <HintRow>
        <Req>*</Req>
        <span>Suggested fields</span>
      </HintRow>

      <FormGrid2>
        <FieldGroup>
          <LabelRow>
            <Label>Age:</Label>
            <Req>*</Req>
          </LabelRow>
          <Select value={age} onChange={e => setAge(e.target.value)}>
            <option value="please-select" disabled>
              Please select
            </option>
            {ageOptions.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </Select>
        </FieldGroup>

        <FieldGroup>
          <LabelRow>
            <Label>Sex:</Label>
            <Req>*</Req>
          </LabelRow>
          <Select value={sex} onChange={e => setSex(e.target.value)}>
            <option value="please-select" disabled>
              Please select
            </option>
            {sexOptions.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </Select>
        </FieldGroup>

        <FieldGroup>
          <LabelRow>
            <Label>Height:</Label>
            <Req>*</Req>
          </LabelRow>
          <Select value={height} onChange={e => setHeight(e.target.value)}>
            <option value="please-select" disabled>
              Please select
            </option>
            {heightOptions.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </Select>
        </FieldGroup>

        <FieldGroup>
          <LabelRow>
            <Label>Weight:</Label>
            <Req>*</Req>
          </LabelRow>
          <Select value={weight} onChange={e => setWeight(e.target.value)}>
            <option value="please-select" disabled>
              Please select
            </option>
            {weightOptions.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </Select>
        </FieldGroup>
      </FormGrid2>

      <FormRowFull>
        <LabelRow>
          <Label>Allergies:</Label>
        </LabelRow>
        <TextArea placeholder="Enter allergies or type 'None' if not applicable" />
      </FormRowFull>

      <FormRowFull>
        <LabelRow>
          <Label>Diagnosis:</Label>
          <Req>*</Req>
        </LabelRow>
        <TextArea
          placeholder="Enter diagnosis"
          value={diagnosis}
          onChange={e => setDiagnosis(e.target.value)}
        />
      </FormRowFull>

      <FormRowFull>
        <LabelRow>
          <Label>Surgery/Procedure:</Label>
        </LabelRow>
        <TextArea placeholder="Enter surgery/procedure" />
      </FormRowFull>

      <FormRowFull>
        <LabelRow>
          <Label>Cultural/Religious Attributes:</Label>
        </LabelRow>
        <TextArea placeholder="Enter cultural/religious attributes or type 'None' if not applicable" />
      </FormRowFull>

      <SubsectionTitle>Vital Signs</SubsectionTitle>

      <VitalGrid>
        <FieldGroup>
          <LabelRow>
            <Label>Body Temperature (F):</Label>
            <Req>*</Req>
          </LabelRow>
          <Input
            placeholder="Enter temperature"
            value={tempF}
            onChange={e => setTempF(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow>
            <Label>Blood Pressure (mm Hg):</Label>
            <Req>*</Req>
          </LabelRow>
          <Input
            placeholder="Enter blood pressure"
            value={bp}
            onChange={e => setBp(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow>
            <Label>Heart Rate (bpm):</Label>
            <Req>*</Req>
          </LabelRow>
          <Input
            placeholder="Enter heart rate"
            value={hr}
            onChange={e => setHr(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow>
            <Label>Respiration Rate (bpm):</Label>
            <Req>*</Req>
          </LabelRow>
          <Input
            placeholder="Enter respiratory rate"
            value={rr}
            onChange={e => setRr(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow>
            <Label>Room Air O2 Sat (%):</Label>
          </LabelRow>
          <Input placeholder="Enter O₂ saturation" />
        </FieldGroup>

        <FieldGroup>
          <LabelRow>
            <Label>Date of LMP:</Label>
          </LabelRow>
          <Input placeholder="Enter LMP or type 'N/A' if not applicable" />
        </FieldGroup>
      </VitalGrid>

      {renderFooter(false, "Next Tab")}
    </>
  );

  const renderHistoryTab = () => (
    <>
      <HintRow>
        <Req>*</Req>
        <span>Suggested fields</span>
      </HintRow>

      <FormRowFull>
        <LabelRow><Label>Past Medical History:</Label></LabelRow>
        <TextArea
          placeholder="Enter past medical history or type 'None'"
          value={pmh}
          onChange={e => setPmh(e.target.value)}
        />
      </FormRowFull>

      <FormRowFull>
        <LabelRow><Label>Past Surgical History:</Label></LabelRow>
        <TextArea
          placeholder="Enter past surgical history or type 'None'"
          value={psh}
          onChange={e => setPsh(e.target.value)}
        />
      </FormRowFull>

      <FormRowFull>
        <LabelRow><Label>Anesthetic History / Family Anesthetic History:</Label></LabelRow>
        <TextArea
          placeholder="Enter anesthetic history or type 'None'"
          value={anesthesiaHx}
          onChange={e => setAnesthesiaHx(e.target.value)}
        />
      </FormRowFull>

      <FormRowFull>
        <LabelRow><Label>Current Medications:</Label></LabelRow>
        <TextArea
          placeholder="Enter current medications or type 'None'"
          value={meds}
          onChange={e => setMeds(e.target.value)}
        />
      </FormRowFull>

      <FormRowFull>
        <LabelRow><Label>Alcohol Use:</Label></LabelRow>
        <TextArea
          placeholder="Enter alcohol use or type 'None'"
          value={alcohol}
          onChange={e => setAlcohol(e.target.value)}
        />
      </FormRowFull>

      <FormRowFull>
        <LabelRow><Label>Substance Use:</Label></LabelRow>
        <TextArea
          placeholder="Enter substance use or type 'None'"
          value={substance}
          onChange={e => setSubstance(e.target.value)}
        />
      </FormRowFull>

      {renderFooter(true, "Next Tab")}
    </>
  );

  const renderAssessmentTab = () => (
    <>
      <HintRow>
        <Req>*</Req>
        <span>Suggested fields</span>
      </HintRow>

      <SubsectionTitle>Review of Systems</SubsectionTitle>

      <FormGrid2>
        <FieldGroup>
          <LabelRow><Label>Neuro:</Label></LabelRow>
          <TextArea
            placeholder="Enter neurological findings or type 'WNL'"
            value={neuro}
            onChange={e => setNeuro(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>HEENT:</Label></LabelRow>
          <TextArea
            placeholder="Enter HEENT findings or type 'WNL'"
            value={heent}
            onChange={e => setHeent(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Respiratory:</Label></LabelRow>
          <TextArea
            placeholder="Enter respiratory findings or type 'WNL'"
            value={resp}
            onChange={e => setResp(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Cardiovascular:</Label></LabelRow>
          <TextArea
            placeholder="Enter cardiovascular findings or type 'WNL'"
            value={cardio}
            onChange={e => setCardio(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Gastrointestinal:</Label></LabelRow>
          <TextArea
            placeholder="Enter gastrointestinal findings or type 'WNL'"
            value={gi}
            onChange={e => setGi(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Genitourinary:</Label></LabelRow>
          <TextArea
            placeholder="Enter genitourinary findings or type 'WNL'"
            value={gu}
            onChange={e => setGu(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Endocrine:</Label></LabelRow>
          <TextArea
            placeholder="Enter endocrine findings or type 'WNL'"
            value={endo}
            onChange={e => setEndo(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Other:</Label></LabelRow>
          <TextArea
            placeholder="Enter other findings or type 'WNL'"
            value={otherFindings}
            onChange={e => setOtherFindings(e.target.value)}
          />
        </FieldGroup>
      </FormGrid2>

      <SubsectionTitle>Airway Assessment</SubsectionTitle>

      {/* airway inputs grouped in 2x2 grid */}
      <AirwayGrid2x2>
        <FieldGroup>
          <LabelRow><Label>Airway/Mallampati:</Label></LabelRow>
          <Select
            value={mallampati}
            onChange={e => setMallampati(e.target.value)}
          >
            <option value="please-select" disabled>
              Select Mallampati
            </option>
            {mallampatiOptions.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </Select>
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>ULBT Grade:</Label></LabelRow>
          <Select
            value={ulbt}
            onChange={e => setUlbt(e.target.value)}
          >
            <option value="please-select" disabled>
              Select ULBT Grade
            </option>
            {ulbtOptions.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </Select>
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Thyromental Distance in cm:</Label></LabelRow>
          <SmallInput
            placeholder="Enter distance in cm"
            value={thyromental}
            onChange={e => setThyromental(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Interincisor Distance in cm:</Label></LabelRow>
          <SmallInput
            placeholder="Enter distance in cm"
            value={interincisor}
            onChange={e => setInterincisor(e.target.value)}
          />
        </FieldGroup>
      </AirwayGrid2x2>

      {/* row 2: dentition / neck / oral mucosa */}
      <AirwayRow3>
        <FieldGroup>
          <LabelRow><Label>Dentition:</Label></LabelRow>
          <AirwayTextArea
            placeholder="Enter dentition findings or type 'WNL'"
            value={dentition}
            onChange={e => setDentition(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Neck:</Label></LabelRow>
          <AirwayTextArea
            placeholder="Enter neck findings or type 'WNL'"
            value={neck}
            onChange={e => setNeck(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Oral Mucosa:</Label></LabelRow>
          <AirwayTextArea
            placeholder="Enter oral mucosa findings or type 'WNL'"
            value={oralMucosa}
            onChange={e => setOralMucosa(e.target.value)}
          />
        </FieldGroup>
      </AirwayRow3>

      {renderFooter(true, "Next Tab")}
    </>
  );

  const renderLabsTab = () => (
    <>
      <HintRow>
        <Req>*</Req>
        <span>Suggested fields</span>
      </HintRow>

      <SubsectionTitle>Labs</SubsectionTitle>

      <SmallGrid3>
        <FieldGroup>
          <LabelRow><Label>Na:</Label></LabelRow>
          <TinyInput
            value={na}
            onChange={e => setNa(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>K:</Label></LabelRow>
          <TinyInput
            value={k}
            onChange={e => setK(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Cl:</Label></LabelRow>
          <TinyInput
            value={cl}
            onChange={e => setCl(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>CO2:</Label></LabelRow>
          <TinyInput
            value={co2}
            onChange={e => setCo2(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>BUN:</Label></LabelRow>
          <TinyInput
            value={bun}
            onChange={e => setBun(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Cr:</Label></LabelRow>
          <TinyInput
            value={cr}
            onChange={e => setCr(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Glu:</Label></LabelRow>
          <TinyInput
            value={glu}
            onChange={e => setGlu(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>WBC:</Label></LabelRow>
          <TinyInput
            value={wbc}
            onChange={e => setWbc(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Hgb:</Label></LabelRow>
          <TinyInput
            value={hgb}
            onChange={e => setHgb(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Hct:</Label></LabelRow>
          <TinyInput
            value={hct}
            onChange={e => setHct(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>PLT:</Label></LabelRow>
          <TinyInput
            value={plt}
            onChange={e => setPlt(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>PT:</Label></LabelRow>
          <TinyInput
            value={pt}
            onChange={e => setPt(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>PTT:</Label></LabelRow>
          <TinyInput
            value={ptt}
            onChange={e => setPtt(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>INR:</Label></LabelRow>
          <TinyInput
            value={inr}
            onChange={e => setInr(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>ABG:</Label></LabelRow>
          <TinyInput
            value={abg}
            onChange={e => setAbg(e.target.value)}
          />
        </FieldGroup>
      </SmallGrid3>

      <FormRowFull style={{ maxWidth: "1000px" }}>
        <LabelRow><Label>Other Labs:</Label></LabelRow>
        <TinyInput
          value={otherLabs}
          onChange={e => setOtherLabs(e.target.value)}
        />
      </FormRowFull>

      <SubsectionTitle>Imaging/Tests</SubsectionTitle>

      <SmallGrid2>
        <FieldGroup>
          <LabelRow><Label>EKG:</Label></LabelRow>
          <TinyInput
            value={ekg}
            onChange={e => setEkg(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>CXR:</Label></LabelRow>
          <TinyInput
            value={cxr}
            onChange={e => setCxr(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Echo:</Label></LabelRow>
          <TinyInput
            value={echo}
            onChange={e => setEcho(e.target.value)}
          />
        </FieldGroup>

        <FieldGroup>
          <LabelRow><Label>Other Imaging:</Label></LabelRow>
          <TinyInput
            value={otherImaging}
            onChange={e => setOtherImaging(e.target.value)}
          />
        </FieldGroup>
      </SmallGrid2>

      <FooterRow>
        <BackButton onClick={handleBack}>Back</BackButton>

        <div style={{ display: 'flex', gap: '12px' }}>
          <NextButton
            onClick={handleGenerateCarePlan}
            disabled={isSaving || isGeneratingAI}
          >
            {isSaving || isGeneratingAI ? (
              <>
                <LoadingSpinner />&nbsp;Generating Care Plan...
              </>
            ) : (
              "Generate Care Plan"
            )}
          </NextButton>
        </div>
      </FooterRow>
    </>
  );

  let tabContent;
  if (currentTab === "info") tabContent = renderInfoTab();
  else if (currentTab === "history") tabContent = renderHistoryTab();
  else if (currentTab === "assessment") tabContent = renderAssessmentTab();
  else if (currentTab === "labs") tabContent = renderLabsTab();

  return (
    <PageWrapper ref={pageTopRef}>
      <HeaderCard>
        <Title>AI Anesthesia Care Plan Generator</Title>
        <Subtitle>
          Generate comprehensive, evidence-based anesthesia care plans with AI assistance
        </Subtitle>
      </HeaderCard>

      {/* Action Bar */}
      <ActionBar>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <ActionButton onClick={() => setShowCarePlanList(!showCarePlanList)}>
            {showCarePlanList ? 'Hide' : 'Show'} Care Plans ({carePlans.length})
          </ActionButton>
          <ActionButton onClick={clearForm}>
            New Care Plan
          </ActionButton>
          {currentCarePlanId && (
            <ActionButton
              onClick={() => generateAIRecommendations()}
              disabled={isGeneratingAI}
            >
              {isGeneratingAI ? <LoadingSpinner /> : null}
              Generate AI Recommendations
            </ActionButton>
          )}
        </div>
        {currentCarePlanId && (
          <div style={{ fontSize: '14px', color: '#64748b' }}>
            Current Care Plan ID: {currentCarePlanId}
          </div>
        )}
      </ActionBar>

      {/* Care Plan List */}
      {showCarePlanList && (
        <CarePlanList>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600' }}>
            Saved Care Plans
          </h3>
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <LoadingSpinner />
              <p style={{ margin: '8px 0 0 0', color: '#64748b' }}>Loading care plans...</p>
            </div>
          ) : carePlans.length === 0 ? (
            <p style={{ color: '#64748b', textAlign: 'center', padding: '20px' }}>
              No saved care plans yet. Create your first care plan below!
            </p>
          ) : (
            carePlans.map((carePlan) => (
              <CarePlanItem key={carePlan.id}>
                <CarePlanInfo>
                  <CarePlanTitle>{carePlan.title}</CarePlanTitle>
                  <CarePlanMeta>
                    {carePlan.patient_name && `Patient: ${carePlan.patient_name} • `}
                    {carePlan.diagnosis && `Diagnosis: ${carePlan.diagnosis} • `}
                    Created: {new Date(carePlan.created_at).toLocaleDateString()}
                  </CarePlanMeta>
                </CarePlanInfo>
                <CarePlanActions>
                  <ActionButton onClick={() => loadCarePlan(carePlan.id)}>
                    Load
                  </ActionButton>
                  <ActionButton 
                    $variant="danger" 
                    onClick={() => deleteCarePlan(carePlan.id)}
                  >
                    Delete
                  </ActionButton>
                </CarePlanActions>
              </CarePlanItem>
            ))
          )}
        </CarePlanList>
      )}

      {/* AI Recommendations */}
      {aiRecommendations && (
        <AIRecommendations>
          <AIRecommendationsTitle>🤖 AI-Generated Recommendations</AIRecommendationsTitle>
          <AIRecommendationsContent>{aiRecommendations}</AIRecommendationsContent>
        </AIRecommendations>
      )}

      <SectionCard>
        <SectionHeader>
          <SectionTitleRow>
            <SectionIcon>🩺</SectionIcon>
            <SectionTitle>Patient Assessment</SectionTitle>
          </SectionTitleRow>

          <TabsBar>
            <TabButton
              $active={currentTab === "info"}
              onClick={() => setCurrentTab("info")}
            >
              Patient Information
            </TabButton>

            <TabButton
              $active={currentTab === "history"}
              onClick={() => setCurrentTab("history")}
            >
              Patient History
            </TabButton>

            <TabButton
              $active={currentTab === "assessment"}
              onClick={() => setCurrentTab("assessment")}
            >
              Patient Assessment
            </TabButton>

            <TabButton
              $active={currentTab === "labs"}
              onClick={() => setCurrentTab("labs")}
            >
              Labs/Tests
            </TabButton>
          </TabsBar>
        </SectionHeader>

        <br />
        {tabContent}
      </SectionCard>
    </PageWrapper>
  );
}
