import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Container, Card, Button, Spinner, Alert, Form, Badge } from "react-bootstrap";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import "../styles/BookPage.css";
import "../styles/DatePickerOverride.css";
import { useAuth } from "../context/AuthContext1";

function BookPage() {
  const { user } = useAuth(); 
  const { lot_id } = useParams();
  const [lot, setLot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [startTime, setStartTime] = useState(null);
  const [endTime, setEndTime] = useState(null);
  const [bookingStatus, setBookingStatus] = useState("");
  const [isBooking, setIsBooking] = useState(false);
  const [bookingDetails, setBookingDetails] = useState(null);
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

    if (endTime <= startTime) {
      alert("End time must be after start time.");
      return;
    }

    if (!user || !user.user_id) {
      alert("You must be logged in to book a parking spot.");
      return;
    }

    setIsBooking(true);
    setBookingStatus("");
    setBookingDetails(null);

    try {
      // Format dates to match backend expected format: "YYYY-MM-DDTHH:MM"
      const formatDateTime = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
      };

      const bookingData = {
        user_id: user.user_id, 
        lot_id: parseInt(lot_id),
        start_time: formatDateTime(startTime),
        end_time: formatDateTime(endTime)
      };

      const res = await axios.post("http://127.0.0.1:8000/parking/book", bookingData);

      setBookingDetails(res.data.booking_summary);
      setBookingStatus("success");

      // Redirect after 2 seconds to show success message, and switch to bookings tab
      setTimeout(() => {
        navigate("/dashboard?refresh=" + Date.now() + "&tab=bookings", { replace: true });
      }, 2000);
    } catch (err) {
      console.error("Booking failed:", err);
      setBookingStatus("error");
      setBookingDetails({
        error: err.response?.data?.detail || "Booking failed. Please try again."
      });
    } finally {
      setIsBooking(false);
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
    <div className="book-page">
      <Container className="d-flex justify-content-center align-items-center">
        <Card className="book-card shadow-lg p-5">
          <Card.Body>
            <div className="text-center mb-4">
              <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🅿️</div>
              <Card.Title>{lot.lot_name}</Card.Title>
              <Card.Text className="text-muted">📍 {lot.location}</Card.Text>
              <div className="mt-3 mb-3">
                <Badge bg="info" className="me-2">
                  Available: {lot.available_spots} / {lot.total_spots}
                </Badge>
                <Badge bg="success">₹{lot.hourly_rate} per hour</Badge>
              </div>
            </div>

            {/* Start & End Time Inputs */}
            <Form className="mt-4" onSubmit={(e) => { e.preventDefault(); handleBooking(); }}>
              <Form.Group className="mb-3">
                <Form.Label>Start Time</Form.Label>
                <div className="date-picker-container">
                  <DatePicker
                    selected={startTime}
                    onChange={(date) => setStartTime(date)}
                    showTimeSelect
                    timeFormat="HH:mm"
                    timeIntervals={15}
                    dateFormat="MMMM d, yyyy h:mm aa"
                    minDate={new Date()}
                    placeholderText="Click to select start date and time"
                    className="form-control date-picker-input"
                    wrapperClassName="date-picker-wrapper"
                    calendarClassName="dark-theme-calendar"
                    required
                  />
                  <span className="calendar-icon">📅</span>
                </div>
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>End Time</Form.Label>
                <div className="date-picker-container">
                  <DatePicker
                    selected={endTime}
                    onChange={(date) => setEndTime(date)}
                    showTimeSelect
                    timeFormat="HH:mm"
                    timeIntervals={15}
                    dateFormat="MMMM d, yyyy h:mm aa"
                    minDate={startTime || new Date()}
                    placeholderText="Click to select end date and time"
                    className="form-control date-picker-input"
                    wrapperClassName="date-picker-wrapper"
                    calendarClassName="dark-theme-calendar"
                    required
                  />
                  <span className="calendar-icon">📅</span>
                </div>
              </Form.Group>
            
            <div className="button-group">
              <Button 
                variant="success" 
                type="submit"
                className="flex-fill"
                disabled={isBooking}
              >
                {isBooking ? (
                  <>
                    <Spinner size="sm" animation="border" className="me-2" />
                    Booking...
                  </>
                ) : (
                  "Confirm Booking"
                )}
              </Button>
              <Button 
                variant="secondary" 
                type="button"
                onClick={() => navigate("/dashboard")} 
                className="flex-fill"
                disabled={isBooking}
              >
                Cancel
              </Button>
            </div>
            </Form>

            {bookingStatus === "success" && bookingDetails && (
              <Alert variant="success" className="mt-3">
                <Alert.Heading>✅ Booking Successful!</Alert.Heading>
                <hr />
                <p className="mb-1"><strong>Total Cost:</strong> ₹{bookingDetails.total_cost}</p>
                <p className="mb-1"><strong>Start Time:</strong> {new Date(bookingDetails.start_time).toLocaleString()}</p>
                <p className="mb-0"><strong>End Time:</strong> {new Date(bookingDetails.end_time).toLocaleString()}</p>
                <p className="mt-2 mb-0"><small>Redirecting to dashboard...</small></p>
              </Alert>
            )}

            {bookingStatus === "error" && bookingDetails && (
              <Alert variant="danger" className="mt-3">
                <Alert.Heading>❌ Booking Failed</Alert.Heading>
                <p className="mb-0">{bookingDetails.error}</p>
              </Alert>
            )}
          </Card.Body>
        </Card>
      </Container>
    </div>
  );
}

export default BookPage;
