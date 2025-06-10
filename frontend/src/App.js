import React, { useState, useEffect } from "react";
import "./App.css";
import TechnologyGrid from "./TechnologyGrid";
import { marked } from "marked";
import { JOB_LIBRARY } from "./jobLibrary";

function App() {
  const [workflow, setWorkflow] = useState([]);
  const [useCase, setUseCase] = useState("");
  const [status, setStatus] = useState(null);
  const [optimalOrder, setOptimalOrder] = useState(null);
  const [narrative, setNarrative] = useState("");
  const [proposedWorkflow, setProposedWorkflow] = useState(null);
  const [renamedTechnologies, setRenamedTechnologies] = useState({});
  const [selectedTechnologies, setSelectedTechnologies] = useState([]);
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [deployConfig, setDeployConfig] = useState({
    environment: "saas_dev",
    userCode: "LBA",
    folderName: "DEMGEN_VB",
  });

  const toggleTechnologyInWorkflow = (techName) => {
    setSelectedTechnologies((prev) => {
      if (prev.includes(techName)) {
        return prev.filter((tech) => tech !== techName);
      } else {
        return [...prev, techName];
      }
    });
  };

  const generateOptimalOrder = async () => {
    if (selectedTechnologies.length === 0 || !useCase.trim()) {
      setStatus("Select technologies and provide a use case first.");
      setTimeout(() => setStatus(null), 3000);
      return;
    }

    try {
      setStatus("Generating optimal order...");
      const response = await fetch(
        "http://localhost:5000/generate_optimal_order",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            technologies: selectedTechnologies,
            use_case: useCase,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to generate optimal order");
      }

      const data = await response.json();
      setOptimalOrder(data.optimal_order);
      setStatus("Optimal order generated successfully!");
      setTimeout(() => setStatus(null), 3000);
    } catch (error) {
      console.error("Error generating optimal order:", error);
      setStatus("Failed to generate optimal order. Please try again.");
      setTimeout(() => setStatus(null), 3000);
    }
  };

  const generateNarrative = async () => {
    if (selectedTechnologies.length === 0 || !useCase.trim()) {
      setStatus("Provide technologies and use case first.");
      setTimeout(() => setStatus(null), 3000);
      return;
    }

    setStatus("Generating narrative...");
    setNarrative("");

    try {
      const response = await fetch("http://localhost:5000/generate-narrative", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          technologies: selectedTechnologies,
          use_case: useCase,
          optimal_order: optimalOrder || selectedTechnologies,
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullNarrative = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunkText = decoder.decode(value, { stream: true });
        fullNarrative += chunkText;
        setNarrative(fullNarrative);
      }

      setStatus("Narrative generated!");
    } catch (error) {
      console.error("Narrative Generation Error:", error);
      setStatus("Failed to generate narrative.");
    }
    setTimeout(() => setStatus(null), 3000);
  };

  const handleDeployConfigChange = (field, value) => {
    setDeployConfig((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleDeployWorkflow = async () => {
    console.log("Deploy workflow button clicked");
    console.log("Current state:", {
      selectedTechnologies,
      useCase,
      deployConfig,
    });

    if (!selectedTechnologies.length || !useCase) {
      console.log("Missing prerequisites:", {
        hasTechnologies: selectedTechnologies.length > 0,
        hasUseCase: !!useCase,
      });
      alert("Please select technologies and enter a use case first.");
      return;
    }

    try {
      console.log("Starting workflow deployment with config:", deployConfig);
      setStatus("Deploying workflow...");

      const requestBody = {
        jobs: selectedTechnologies,
        environment: deployConfig.environment,
        folder_name: deployConfig.folderName,
        user_code: deployConfig.userCode,
      };

      console.log("Sending deployment request with body:", requestBody);

      const response = await fetch("http://localhost:5000/generate_workflow", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      console.log("Received response:", response.status);

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Deployment failed:", errorData);
        throw new Error(errorData.error || "Failed to deploy workflow");
      }

      const data = await response.json();
      console.log("Deployment successful:", data);
      setStatus("Workflow deployed successfully!");
      setTimeout(() => setStatus(""), 3000);
    } catch (error) {
      console.error("Deployment error:", error);
      setStatus(`Error: ${error.message}`);
      setTimeout(() => setStatus(""), 3000);
    }
  };

  const handlePersonalizedDeployConfirm = async () => {
    try {
      // Close modal immediately when deploy is clicked
      setShowDeployModal(false);

      console.log("Starting deployment with config:", deployConfig);
      setStatus("Deploying personalized workflow...");

      const requestBody = {
        technologies: selectedTechnologies,
        use_case: useCase,
        renamed_technologies: renamedTechnologies,
        optimal_order: workflow,
        environment: deployConfig.environment,
        user_code: deployConfig.userCode,
        folder_name: deployConfig.folderName,
        application: deployConfig.application,
        sub_application: deployConfig.subApplication,
      };

      console.log("Request body:", JSON.stringify(requestBody, null, 2));

      const response = await fetch(
        "http://localhost:5000/deploy_personalized_workflow",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
        }
      );

      console.log("Response status:", response.status);
      console.log(
        "Response headers:",
        Object.fromEntries(response.headers.entries())
      );

      const responseText = await response.text();
      console.log("Raw response:", responseText);

      if (!response.ok) {
        let errorMessage;
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.error || "Failed to deploy workflow";
        } catch (e) {
          errorMessage = `Server error: ${responseText}`;
        }
        console.error("Deployment failed:", errorMessage);
        throw new Error(errorMessage);
      }

      let data;
      try {
        data = JSON.parse(responseText);
        console.log("Parsed response data:", data);
      } catch (e) {
        console.error("Failed to parse response as JSON:", e);
        throw new Error("Invalid response from server");
      }

      setStatus("Workflow deployed successfully!");
      setTimeout(() => setStatus(""), 3000);
    } catch (error) {
      console.error("Deployment error:", error);
      setStatus(`Error: ${error.message}`);
      setTimeout(() => setStatus(""), 3000);
    }
  };

  const handleDeployPersonalizedWorkflow = () => {
    console.log("Deploy button clicked");
    console.log("Current state:", {
      selectedTechnologies,
      useCase,
      renamedTechnologies,
      workflow,
    });

    if (!selectedTechnologies.length || !useCase) {
      console.log("Missing prerequisites:", {
        hasTechnologies: selectedTechnologies.length > 0,
        hasUseCase: !!useCase,
      });
      alert("Please select technologies and enter a use case first.");
      return;
    }
    if (!renamedTechnologies) {
      console.log("Workflow not personalized");
      alert("Please personalize the workflow names first.");
      return;
    }
    console.log("Opening deployment modal");
    setShowDeployModal(true);
  };

  const generateProposedWorkflow = async () => {
    if (!useCase.trim()) {
      setStatus("Provide a use case first.");
      return;
    }

    setStatus("Generating proposed workflow...");
    setProposedWorkflow(null);
    setSelectedTechnologies([]); // Clear existing selected technologies
    setOptimalOrder(null); // Clear any existing optimal order

    try {
      const response = await fetch("http://localhost:5000/proposed_workflow", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ use_case: useCase }),
      });

      if (!response.ok)
        throw new Error("Failed to generate proposed workflow.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunkText = decoder.decode(value, { stream: true });
        fullResponse += chunkText;
      }

      try {
        const data = JSON.parse(fullResponse);
        if (data.technologies && data.workflow_order) {
          // Update both the workflow and optimal order
          setSelectedTechnologies(data.technologies);
          setOptimalOrder(data.workflow_order);
          setProposedWorkflow(data);

          // Add a small delay to ensure the UI updates smoothly
          setTimeout(() => {
            setStatus("Technologies and workflow order generated!");
          }, 100);
        } else {
          throw new Error("Invalid response format");
        }
      } catch (parseError) {
        console.error("Error parsing response:", parseError);
        setStatus("Error parsing proposed workflow response.");
      }
    } catch (error) {
      console.error("Proposed Workflow Generation Error:", error);
      setStatus("Failed to generate proposed workflow.");
    }
    setTimeout(() => setStatus(null), 3000);
  };

  const handlePersonalizeUseCase = async () => {
    if (!selectedTechnologies.length || !useCase) {
      alert("Please select technologies and enter a use case first.");
      return;
    }

    try {
      setStatus("Personalizing workflow names to match use case...");
      const response = await fetch(
        "http://localhost:5000/rename_technologies",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            technologies: selectedTechnologies,
            use_case: useCase,
            optimal_order: optimalOrder,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to rename technologies");
      }

      const data = await response.json();
      setRenamedTechnologies(data.renamed_technologies);
      setStatus(
        "Workflow names have been personalized to match your use case!"
      );
      setTimeout(() => setStatus(null), 3000);
    } catch (error) {
      console.error("Error renaming technologies:", error);
      setStatus("Failed to personalize workflow names. Please try again.");
      setTimeout(() => setStatus(null), 3000);
    }
  };

  const renderWorkflowItem = (tech, index) => {
    const displayName = renamedTechnologies[tech] || tech;
    return (
      <li key={tech} className="ordered-item">
        <span className="step-number">{index + 1}</span>
        <span className="job-name">{displayName}</span>
      </li>
    );
  };

  // Add useEffect to monitor state changes
  useEffect(() => {
    console.log("Deployment modal state:", showDeployModal);
  }, [showDeployModal]);

  return (
    <div className="app-container">
      <div className="content-container">
        {/* LEFT: Title + Use Case + Grid */}
        <div className="left-column">
          <h1>Demonstration Generator</h1>
          <div className="use-case-input">
            <h3>Enter Use Case:</h3>
            <textarea
              value={useCase}
              onChange={(e) => setUseCase(e.target.value)}
              placeholder="Describe your use case here..."
              rows="3"
            />
            <button
              onClick={generateProposedWorkflow}
              className="propose-tech-button"
            >
              Ask AI to Generate a list of Technologies based on Use Case
            </button>
          </div>

          <h3>Select your technologies:</h3>
          <TechnologyGrid
            selectedIcons={selectedTechnologies}
            onToggle={toggleTechnologyInWorkflow}
          />
        </div>

        {/* RIGHT: Selected Techs + Optimal Order + Narrative */}
        <div className="right-column">
          <div className="workflow-container">
            {selectedTechnologies.length > 0 && (
              <div className="selected-technologies">
                <h3>Selected Technologies:</h3>
                <div className="workflow-list">
                  {selectedTechnologies.map((tech, index) => (
                    <div
                      key={tech}
                      className={`workflow-item ${
                        proposedWorkflow?.technologies?.includes(tech)
                          ? "ai-suggested"
                          : ""
                      }`}
                      title={JOB_LIBRARY[tech]?.description || tech}
                    >
                      <span className="tech-name">
                        {renamedTechnologies[tech] || tech}
                        <span className="original-name">({tech})</span>
                      </span>
                      <button
                        className="remove-tech"
                        onClick={() => toggleTechnologyInWorkflow(tech)}
                        title="Remove technology"
                      >
                        ❌
                      </button>
                    </div>
                  ))}
                </div>
                {proposedWorkflow?.technologies && (
                  <div className="ai-suggestion-note">
                    <span className="ai-badge">AI</span>
                    <span>AI-suggested technologies are highlighted</span>
                  </div>
                )}
              </div>
            )}

            {optimalOrder && (
              <div className="optimal-workflow">
                <h3>Optimal Order:</h3>
                <ol className="ordered-list">
                  {optimalOrder.map((tech, index) =>
                    renderWorkflowItem(tech, index)
                  )}
                </ol>
              </div>
            )}
          </div>

          <div className="workflow-actions">
            <button
              className="action-button"
              onClick={generateOptimalOrder}
              disabled={!selectedTechnologies.length || !useCase}
            >
              Generate Optimal Order
            </button>
            <button
              className="action-button"
              onClick={handlePersonalizeUseCase}
              disabled={!selectedTechnologies.length || !useCase}
            >
              Personalize Workflow to Use Case
            </button>
            {/* <button
              className="action-button"
              onClick={handleDeployWorkflow}
              disabled={!selectedTechnologies.length || !useCase}
            >
              Deploy Workflow
            </button> */}
            <button
              className="action-button"
              onClick={handleDeployPersonalizedWorkflow}
              disabled={
                !selectedTechnologies.length || !useCase || !renamedTechnologies
              }
            >
              Deploy Personalized Workflow
            </button>
            <button
              className="action-button"
              onClick={generateNarrative}
              disabled={!selectedTechnologies.length || !useCase}
            >
              Generate Narrative
            </button>
          </div>

          {status && <p className="status-message">{status}</p>}

          {narrative && (
            <div className="narrative-display">
              <div dangerouslySetInnerHTML={{ __html: marked(narrative) }} />
            </div>
          )}
        </div>
      </div>

      {/* Deployment Configuration Modal */}
      {showDeployModal && (
        <div className="modal">
          <div className="modal-content">
            <h3>Deployment Configuration</h3>
            <div className="form-group">
              <label>Environment:</label>
              <select
                value={deployConfig.environment}
                onChange={(e) =>
                  setDeployConfig((prev) => ({
                    ...prev,
                    environment: e.target.value,
                  }))
                }
              >
                <option value="saas_dev">SaaS Dev</option>
                <option value="saas_preprod">SaaS Preprod</option>
                <option value="saas_prod">SaaS Prod</option>
                <option value="vse_dev">VSE Dev</option>
                <option value="vse_qa">VSE QA</option>
                <option value="vse_prod">VSE Prod</option>
              </select>
            </div>
            <div className="form-group">
              <label>User Code:</label>
              <input
                type="text"
                value={deployConfig.userCode}
                onChange={(e) =>
                  setDeployConfig((prev) => ({
                    ...prev,
                    userCode: e.target.value,
                  }))
                }
                placeholder="Enter user code"
              />
            </div>
            <div className="form-group">
              <label>Folder Name:</label>
              <input
                type="text"
                value={deployConfig.folderName}
                onChange={(e) =>
                  setDeployConfig((prev) => ({
                    ...prev,
                    folderName: e.target.value,
                  }))
                }
                placeholder="Enter folder name"
              />
            </div>
            <div className="form-group">
              <label>Application:</label>
              <input
                type="text"
                value={deployConfig.application}
                onChange={(e) =>
                  setDeployConfig((prev) => ({
                    ...prev,
                    application: e.target.value,
                  }))
                }
                placeholder="Enter application name"
              />
            </div>
            <div className="form-group">
              <label>Sub-Application:</label>
              <input
                type="text"
                value={deployConfig.subApplication}
                onChange={(e) =>
                  setDeployConfig((prev) => ({
                    ...prev,
                    subApplication: e.target.value,
                  }))
                }
                placeholder="Enter sub-application name"
              />
            </div>
            <div className="modal-buttons">
              <button onClick={() => setShowDeployModal(false)}>Cancel</button>
              <button onClick={handlePersonalizedDeployConfirm}>Deploy</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
