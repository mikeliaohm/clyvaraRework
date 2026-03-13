import React from 'react'
import styled from 'styled-components'

const Button = styled.button`
  background-color: white;
  color: black;
  padding: 12.8px 15.2px;
  border: 1px solid black;
  border-radius: 40px;
  cursor: pointer;
  font-weight: 500;
  font-size: 1rem;
  font-family: 'General Sans', sans-serif;
  height: 48px;
  transition: background 0.2s ease;

  &:hover {
    background: #1A2B7A;
    color: #fff;
  }
`

export default function GoogleSignInButton() {
  function handleGoogleLogin() {
    alert('Google sign-in is not available on a local server. Please use email and password.')
  }

  return (
    <Button onClick={handleGoogleLogin}>
      Continue with Google
    </Button>
  )
}
