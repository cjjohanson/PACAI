import React, { useState } from 'react';
import './QuestionForm.css';
import topLogo from './topLogo.png'; // Replace with your top logo path
import bottomLogo from './bottomLogo.png'; // Replace with your bottom logo path

function QuestionForm() {
  const [question, setQuestion] = useState('');
  const [includeUrls, setIncludeUrls] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null); // Reset error state
    try {
      const response = await fetch('http://127.0.0.1:5000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question, includeUrls })
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setResult(data);
    } catch (error) {
      setError('There was a problem with the fetch operation: ' + error.message);
    }
  };

  return (
    <div className="question-form-container">
      <h3>CarePAC AI</h3>
      <h6>An AI-powered guide for parents of autistic children</h6>
      <img src={topLogo} alt="Top Logo" className="top-logo" />
      <form onSubmit={handleSubmit} className="question-form">
        <label>
          Question:
          <textarea
            className="question-input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={includeUrls}
            onChange={(e) => setIncludeUrls(e.target.checked)}
          />
          Include URLs
        </label>
        <div className="submit-button-container">
          <button type="submit" className="submit-button">Submit</button>
        </div>
      </form>
      {error && <p className="error">{error}</p>}
      {result && (
        <div className="result">
          <h2>Summary:</h2>
          <p>{result.summary}</p>
          {includeUrls && result.articles && (
            <div className="articles">
              <h3>Related Articles:</h3>
              {result.articles.map((article, index) => (
                <div key={index}>
                  <a href={article.url} target="_blank" rel="noopener noreferrer">
                    {article.title}
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      <div className="powered-by">
        <img src={bottomLogo} alt="Powered by Weaviate" className="bottom-logo" />
        <p>Powered by Weaviate</p>
      </div>
    </div>
  );
}

export default QuestionForm;
