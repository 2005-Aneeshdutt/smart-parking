import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Container, Card, Button, Spinner, Alert, Form } from "react-bootstrap";
import "../styles/BookPage.css";
import { useAuth } from "../context/AuthContext1";

function BookPage() {
  const { user } = useAuth(); 
  const { lot_id } = useParams();
  const [lot, setLot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [bookingStatus, setBookingStatus] = useState("");
  const navigate = useNavigate();

  
  useEffect(() => {
    const fetchLot = async () => {
      try {
        const res = await axios.get(`http://127.0.0.1:8000/parking/lots/${lot_id}`);
        setLot(res.data.parking_lot);
      } catch (err) {
        console.error("Error fetching lot:", err);
        setError("Failed to load parking lot details");
      } finally {
        setLoading(false);
      }
    };
    fetchLot();
  }, [lot_id]);

  
  const handleBooking = async () => {
    if (!startTime || !endTime) {
      alert("Please select both start and end times before booking.");
      return;
    }

    if (!user || !user.user_id) {
      alert("You must be logged in to book a parking spot.");
      return;
    }

    try {
      const bookingData = {
        user_id: user.user_id, 
        lot_id: parseInt(lot_id),
        start_time: startTime,
        end_time: endTime
      };

      console.log("Booking data being sent:", bookingData);

      const res = await axios.post("http://127.0.0.1:8000/parking/book", bookingData);

      console.log("Booking response:", res.data);
      setBookingStatus("Booking successful!");

      
      setTimeout(() => navigate("/dashboard"), 1500);
    } catch (err) {
      console.error("Booking failed:", err);
      setBookingStatus(err.response?.data?.detail || "Booking failed. Please try again.");
    }
  };


  if (loading)
    return (
      <div className="text-center mt-5">
        <Spinner animation="border" /> Loading lot details...
      </div>
    );

  if (error)
    return (
      <Alert variant="danger" className="text-center mt-5">
        {error}
      </Alert>
    );

  
  return (
    <Container className="mt-5 d-flex justify-content-center">
      <Card style={{ width: "28rem" }} className="shadow p-4 text-center">
        <Card.Body>
          <Card.Title className="fw-bold mb-3">{lot.lot_name}</Card.Title>
          <Card.Text>{lot.location}</Card.Text>
          <Card.Text>
            Available Spots: {lot.available_spots} / {lot.total_spots}
          </Card.Text>
          <Card.Text>Rate: ₹{lot.hourly_rate} per hour</Card.Text>

          {/* Start & End Time Inputs */}
          <Form className="text-start mt-3">
            <Form.Group className="mb-3">
              <Form.Label>Start Time</Form.Label>
              <Form.Control
                type="datetime-local"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>End Time</Form.Label>
              <Form.Control
                type="datetime-local"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
              />
            </Form.Group>
          </Form>

          <Button variant="success" className="me-2" onClick={handleBooking}>
            Confirm Booking
          </Button>
          <Button variant="secondary" onClick={() => navigate("/dashboard")}>
            Cancel
          </Button>

          {bookingStatus && (
            <Alert variant="info" className="mt-3">
              {bookingStatus}
            </Alert>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
}

export default BookPage;
