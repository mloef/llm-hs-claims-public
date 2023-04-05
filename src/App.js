import React, { useState } from 'react';
import Confetti from 'react-confetti';
import './App.css';

function HealthMoneyApp() {
  const [submitted, setSubmitted] = useState(false);
  const [confettiVisible, setConfettiVisible] = useState(false);
  const [responseMessage, setResponseMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setConfettiVisible(true);

    const formData = new FormData();
    formData.append('email', document.getElementById('email').value);
    formData.append("insurance_provider_letter", event.target.insuranceProviderLetter.files[0]);
    formData.append("insurance_terms", event.target.insuranceTerms.files[0]);

    try {
      const response = await fetch("http://localhost:5000/api/hello", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const message = await response.text();
        setResponseMessage(message);
        setSubmitted(true);
      } else {
        console.error('Error submitting form');
      }
    } catch (error) {
      console.error('Error submitting form', error);
    }

    setConfettiVisible(false);
  }; 
 
  const handleFormSubmit = async (event) => {
    event.preventDefault();
    await handleSubmit(event);
  }

  const formattedResponse = responseMessage.slice(1, -2).split('\\n').map((paragraph, index) => (
    <p key={index}>{paragraph}</p>
  ));

  const subtitleText = submitted ? "The AI has analyzed your claim and found the following." : "I'm an AI bot that helps you dispute your health insurance claim. Submit the following files and we will file a dispute with click.";

  return (
    <div className="container">
      <div className="title-container">
        <h1 className="title">Health Insurance AI Auto-Dispute</h1>
      </div>
      <h2 className="subtitle">{subtitleText}</h2>
      {submitted ? (
  <div className="success-message-container">
    {formattedResponse}
    {confettiVisible && <Confetti />}
  </div>
      ) : (
        <form onSubmit={handleFormSubmit}>
          <div className="form-item">
            <label htmlFor="email">Email:</label>
            <input type="email" id="email" required />
          </div>
          <div className="form-item">
            <label htmlFor="insuranceProviderLetter">Upload the letter from your healthcare insurance provider describing the reason your claim was rejected.</label>
            <input type="file" id="insuranceProviderLetter" accept=".rtf" required />
          </div>
          <div className="form-item">
            <label htmlFor="insuranceTerms">Upload the terms and conditions of your health insurance.</label>
            <input type="file" id="insuranceTerms" accept=".pdf" required />
          </div>
          <div className="submit-button-container">
            <button type="submit" className="submit-button" required>Submit</button>
            {confettiVisible && <Confetti />}
          </div>
        </form>
      )}
    </div>
  );
}

export default HealthMoneyApp;