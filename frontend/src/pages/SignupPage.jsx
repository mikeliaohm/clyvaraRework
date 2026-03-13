import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import styled from "styled-components";
import { supabase } from "../utils/supabaseClient";
import GoogleSignInButton from "../components/GoogleSignInButton";
import Brainie from "../assets/brainie.png";
import { Eye, EyeOff } from "lucide-react";

const Page = styled.div`
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
  background: #ADCAF0;
  font-family: 'General Sans', sans-serif;
  color: #20359A;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const LeftSide = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  background: #ADCAF0;
`;

const LogoGroup = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  text-align: center;
`;

const Logo = styled.img`
  width: 200px;
  height: 200px;
  object-fit: contain;
`;

const Clyvara = styled.h1`
  font-size: 4rem;
  font-weight: 700;
  margin: 0;
  color: #E84797;
  font-family: 'Rethink Sans', sans-serif;
`;

const RightSide = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  background: #ADCAF0;
`;

const SignupContainer = styled.div`
  width: 100%;
  max-width: 400px;
  display: grid;
  gap: 2rem;
`;

const Title = styled.h1`
  margin: 0;
  font-size: 2rem;
  font-weight: 500;
  color: black;
  text-align: center;
  font-family: 'General Sans', sans-serif;
`;

const Subtitle = styled.p`
  margin: 0;
  font-size: 1.5rem;
  color: black;
  font-weight: 500;
  text-align: center;
  font-family: 'General Sans', sans-serif;
`;

const Form = styled.form`
  display: grid;
  gap: 1.5rem;
`;

const Input = styled.input`
  width: 100%;
  box-sizing: border-box;
  padding: 1rem 1.25rem;
  border: 2px solid #E5E7EB;
  border-radius: 8px;
  background: white;
  font-size: 1rem;
  color: #20359A;
  font-family: 'General Sans', sans-serif;
  font-weight: 500;

  &::placeholder {
    color: #9CA3AF;
    font-weight: 500;
  }

  &:focus {
    outline: none;
    border-color: #20359A;
  }
`;

const PasswordWrapper = styled.div`
  position: relative;
  width: 100%;
`;

const PasswordInput = styled(Input)`
  padding-right: 3rem;
`;

const EyeButton = styled.button`
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  background: transparent;
  color: #6B7280;
  padding: 0.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    color: #20359A;
  }
`;

const Button = styled.button`
  background-color: white;
  color: black;
  padding: 12.8px 15.2px;
  border: 1px solid black;
  border-radius: 40px;
  cursor: pointer;
  font-weight: 500;
  font-family: 'General Sans', sans-serif;
  transition: background 0.2s ease;
  height: 48px;

  &:hover {
    background: #1A2B7A;
    color: #fff;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const Divider = styled.div`
  display: flex;
  align-items: center;
  text-align: center;
  margin: 1rem 0;
  color: #20359A;
  font-weight: 600;
  font-family: 'General Sans', sans-serif;

  &::before,
  &::after {
    content: '';
    flex: 1;
    border-bottom: 1px solid #E5E7EB;
  }

  &::before {
    margin-right: 1rem;
  }

  &::after {
    margin-left: 1rem;
  }
`;

const AccountText = styled.p`
  margin: 0;
  text-align: center;
  color: black;
  font-weight: 500;
  font-family: 'General Sans', sans-serif;
`;

const LoginLink = styled(Link)`
  color: #20359A;
  font-weight: 600;
  text-decoration: underline;
  margin-left: 0.25rem;

  &:hover {
    opacity: 0.8;
  }
`;

const Message = styled.p`
  margin: 0;
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
  border-radius: 8px;
  text-align: center;
  font-weight: 500;
  font-family: 'General Sans', sans-serif;
  color: ${(p) => (p.$error ? "#DC2626" : "#20359A")};
  background: ${(p) => (p.$error ? "#FEF2F2" : "#F0F4FF")};
  border: 1px solid ${(p) => (p.$error ? "#FECACA" : "#DBEAFE")};
`;

// adding specialty for users in signup phase

const FieldGroup = styled.div`
  display: grid;
  gap: 0.35rem;
`;

const Label = styled.label`
  font-size: 0.9rem;
  font-weight: 600;
  color: #111827;
`;

const Select = styled.select`
  width: 100%;
  box-sizing: border-box;
  padding: 0.85rem 1.25rem;
  border: 2px solid #E5E7EB;
  border-radius: 8px;
  background: white;
  font-size: 0.95rem;
  color: ${props => (props.value === "" ? "#888" : "black")};

  font-family: 'General Sans', sans-serif;
  font-weight: 500;

  &:focus {
    outline: none;
    border-color: #20359A;
  }
`;


export default function SignupPage() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPass] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [specialty, setSpecialty] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [isError, setIsError] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setMsg("");
    setIsError(false);

    const { data, error } = await supabase.auth.signUp({ email, password, specialty });

    setLoading(false);
    if (error) {
      setIsError(true);
      setMsg(error.message);
    } else {
      setIsError(false);
      nav("/");
    }
  }

  return (
    <Page>
      <LeftSide>
        <LogoGroup>
          <Logo src={Brainie} alt="Brainie" />
          <Clyvara>Clyvara</Clyvara>
        </LogoGroup>
      </LeftSide>

      <RightSide>
        <SignupContainer>
          <div>
            <Title>Create your account</Title>
            <Subtitle>Get started with Clyvara.</Subtitle>
          </div>

          <Form onSubmit={handleSubmit}>
            <Input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />

            <PasswordWrapper>
              <PasswordInput
                type={showPass ? "text" : "password"}
                placeholder="Password"
                value={password}
                onChange={(e) => setPass(e.target.value)}
                autoComplete="new-password"
                required
                minLength={6}
              />
              <EyeButton
                type="button"
                onClick={() => setShowPass(v => !v)}
                aria-label={showPass ? "Hide password" : "Show password"}
                aria-pressed={showPass}
              >
                {showPass ? <EyeOff size={20} /> : <Eye size={20} />}
              </EyeButton>
            </PasswordWrapper>


            <FieldGroup>
              <Select id="specialty" value={specialty} onChange={(e) => setSpecialty(e.target.value)} required>
                <option value="" disabled>Specialty</option>
                <option value="" disabled hidden> Specialty </option>
                <option value="RN">Nursing (RN)</option>
                <option value="CRNA">Certified Registered Nurse Anesthetist (CRNA)</option>
                <option value="CNM">Nurse Midwife (CNM)</option>
                <option value="other">Other</option>
              </Select>
            </FieldGroup>

            <Button type="submit" disabled={loading}>
              {loading ? "Creating account…" : "Create Account"}
            </Button>

            <GoogleSignInButton />

            <AccountText>
              Already have an account?
              <LoginLink to="/login">Log In</LoginLink>
            </AccountText>
          </Form>

          {msg && <Message $error={isError}>{msg}</Message>}
        </SignupContainer>
      </RightSide>
    </Page>
  );
}