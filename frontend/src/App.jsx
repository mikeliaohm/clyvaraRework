//main entry point for frontend

import { Routes, Route } from "react-router-dom";

import HomePage from "./pages/HomePage.jsx";
import TestingPage from "./pages/TestingPage.jsx";
import SignupPage from "./pages/SignupPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import PricingPage from "./pages/PricingPage.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

//Dashboard
import DashboardLayout from "./layouts/DashboardLayout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import CarePlanPage from "./pages/CarePlanPage.jsx";
import LearningPlanPage from "./pages/LearningPlanPage.jsx";
import Account from "./pages/Account.jsx";
import StudyPage from "./pages/StudyPage.jsx";
import AdminPage from "./pages/AdminPage.jsx";

//Topics
import OpioidsLearningPlan from "./learningplans/OpioidsLearningPlan.jsx";
import InhaledAnestheticsLearningPlan from "./learningplans/InhaledAnestheticsLearningPlan.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/testing" element={<TestingPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/pricing" element={<PricingPage />} />

      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/study" element={<StudyPage />} />
        <Route path="/careplan" element={<CarePlanPage />} />
        <Route path="/learningplan" element={<LearningPlanPage />} />

        <Route path="/learningplan/opioids" element={<OpioidsLearningPlan />}/>
        <Route path="/learningplan/inhaledanesthetics" element={<InhaledAnestheticsLearningPlan />}/>

        <Route path="/account" element={<Account />} />
        <Route path="/admin" element={<AdminPage />} />
      </Route>
    </Routes>
  );
}
