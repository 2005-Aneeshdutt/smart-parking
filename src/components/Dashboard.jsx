import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Card, Spinner, Alert, Container, Row, Col, Button } from "react-bootstrap";
import "../styles/Dashboard.css";

function Dashboard() {
  const navigate = useNavigate()
  const [lots, setLots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const user = JSON.parse(localStorage.getItem("user"));

  useEffect(() => {
    const fetchLots = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:8000/parking/lots");
        setLots(res.data.parking_lots);
      } catch (err) {
        setError("Failed to load parking lots");
      } finally {
        setLoading(false);
      }
    };
    fetchLots();
  }, []);

  if (loading)
    return (
      <div className="text-center mt-5">
        <Spinner animation="border" /> Loading parking lots...
      </div>
    );

  if (error)
    return (
      <Alert variant="danger" className="mt-4 text-center">
        {error}
      </Alert>
    );

  return (
    <Container className="mt-4">
      <h2 className="text-center mb-4 text-primary">
        Welcome {user?.name || "User"} 👋
      </h2>
      <Row>
        {lots.map((lot) => (
          <Col md={4} key={lot.lot_id} className="mb-4">
            <Card className="shadow-lg p-3 text-center lot-card">
              <Card.Body>
                <Card.Title className="fw-bold">{lot.lot_name}</Card.Title>
                <Card.Text>{lot.location}</Card.Text>
                <Card.Text>
                  Available Spots:{" "}
                  <strong>{lot.available_spots}</strong> / {lot.total_spots}
                </Card.Text>
                <Button variant="success"
                 onClick={() => navigate(`/book/${lot.lot_id}`)} 
                >Book Now</Button>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>
    </Container>
  );
}

export default Dashboard;
