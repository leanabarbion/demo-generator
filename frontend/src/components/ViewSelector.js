import React from "react";

const ViewSelector = ({ selectedView, onViewChange }) => {
  return (
    <div className="view-selector">
      <div className="view-selector-header">
        <h1 className="main-title">DemoGen AI</h1>
        <h2 className="subtitle">How would you like to build your workflow?</h2>
      </div>
      <div className="view-options">
        <div
          className={`view-option ai-option ${
            selectedView === "ai" ? "selected" : ""
          }`}
          onClick={() => onViewChange("ai")}
        >
          <div className="card-header">
            <div className="card-badge ai-badge">AI POWERED</div>
          </div>
          <h3>Full AI-Generated Workflow</h3>
          <p className="card-description">
            Simply describe your use case and let AI generate the complete
            workflow for you. Perfect for quick prototyping or when you're not
            sure which technologies to use.
          </p>
          <div className="card-features">
            <h4>What you get:</h4>
            <ul>
              <li>
                <span className="feature-icon">🚀</span>End-to-end workflow
                generation
              </li>
              <li>
                <span className="feature-icon">⚡</span>No manual technology
                selection needed
              </li>
              <li>
                <span className="feature-icon">🎯</span>Fastest path to a
                working demo
              </li>
              <li>
                <span className="feature-icon">🔧</span>Automatically optimized
                structure
              </li>
            </ul>
          </div>
          <div className="card-footer">
            <span className="recommended-tag">Recommended for beginners</span>
          </div>
        </div>

        <div
          className={`view-option manual-option ${
            selectedView === "manual" ? "selected" : ""
          }`}
          onClick={() => onViewChange("manual")}
        >
          <div className="card-header">
            <div className="card-badge manual-badge">EXPERT MODE</div>
          </div>
          <h3>Build It with AI Guidance</h3>
          <p className="card-description">
            Take control of your workflow creation while getting AI assistance
            for suggestions and optimization. Perfect for experienced users who
            want more control.
          </p>
          <div className="card-features">
            <h4>What you get:</h4>
            <ul>
              <li>
                <span className="feature-icon">🎛️</span>Manual technology
                selection
              </li>
              <li>
                <span className="feature-icon">💡</span>AI-powered suggestions
              </li>
              <li>
                <span className="feature-icon">📄</span>Auto-generated
                documentation & pitch script
              </li>
              <li>
                <span className="feature-icon">⚙️</span>Template management &
                advanced settings
              </li>
            </ul>
          </div>
          <div className="card-footer">
            <span className="recommended-tag">Recommended for experts</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ViewSelector;
