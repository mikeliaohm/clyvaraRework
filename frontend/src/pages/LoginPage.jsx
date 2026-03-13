import { useState } from "react";
import styled from "styled-components";
import { Link, useNavigate } from "react-router-dom";
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
  color: var(--times-square-pink);
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

const LoginContainer = styled.div`
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

const SignUpLink = styled(Link)`
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

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPass] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [isError, setIsError] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setMsg("");
    setIsError(false);
    setLoading(true);

    const { error } = await supabase.auth.signInWithPassword({ email, password });

    setLoading(false);
    if (error) {
      setIsError(true);
      setMsg(error.message || "Unable to log in. Please check your credentials.");
      return;
    }
    nav("/dashboard", { replace: true });
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
        <LoginContainer>
          <div>
            <Title>Welcome back!</Title>
            <Subtitle>Log in to your account.</Subtitle>
          </div>

          <Form onSubmit={onSubmit}>
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
                autoComplete="current-password"
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

            <Button type="submit" disabled={loading}>
              {loading ? "Signing in…" : "Log In"}
            </Button>

            <GoogleSignInButton />

            <AccountText>
              Don't have an account?
              <SignUpLink to="/signup">Sign Up</SignUpLink>
            </AccountText>
          </Form>

          {msg && <Message $error={isError}>{msg}</Message>}
        </LoginContainer>
      </RightSide>
    </Page>
  );
}