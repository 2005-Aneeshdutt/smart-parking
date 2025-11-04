import React, { useState } from "react";
import axios from "axios";
import { Card, Form, Button, Alert, Spinner } from "react-bootstrap";
import { useAuth } from "../context/AuthContext1";
import { useNavigate } from "react-router-dom"; // ✅ add navigation
import "../styles/Login.css";

function Login() {
  const { login } = useAuth();
  const navigate = useNavigate(); // ✅ React Router hook for redirect
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const res = await axios.post("http://127.0.0.1:8000/auth/login", formData);

      const userData = {
        user_id: res.data.user_id,
        name: res.data.name,
        role: res.data.role || "driver",
      };

  
      login(userData);

    
      setMessage({ type: "success", text: `Welcome ${res.data.name}!` });

    
      const redirectPath = userData.role === "admin" ? "/admin" : "/dashboard";
      setTimeout(() => navigate(redirectPath), 1000);
    } catch (err) {
      setMessage({
        type: "danger",
        text: err.response?.data?.detail || "Login failed",
      });
    }

    setLoading(false);
  };

  return (
    <div className="login-container d-flex justify-content-center align-items-center">
      <Card className="login-card shadow-lg p-5">
        <div className="login-icon">🅿️</div>
        <h3 className="text-center mb-4 text-primary">Smart Parking System</h3>
        <p className="text-center text-muted mb-4">Sign in to continue</p>
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Email</Form.Label>
            <Form.Control
              type="email"
              name="email"
              placeholder="Enter your email"
              onChange={handleChange}
              required
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Password</Form.Label>
            <Form.Control
              type="password"
              name="password"
              placeholder="Enter your password"
              onChange={handleChange}
              required
            />
          </Form.Group>

          <Button
            variant="primary"
            type="submit"
            className="w-100"
            disabled={loading}>
            {loading ? (
              <>
                <Spinner size="sm" animation="border" /> Logging in...
              </>
            ) : (
              "Login"
            )}
          </Button>
        </Form>

        {message && (
          <Alert variant={message.type} className="mt-3 text-center">
            {message.text}
          </Alert>
        )}
      </Card>
    </div>
  );
}

export default Login;
