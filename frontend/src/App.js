import React, { useState } from "react";
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

  const toggleTechnologyInWorkflow = (techName) => {
    if (workflow.includes(techName)) {
      setWorkflow(workflow.filter((name) => name !== techName));
    } else {
      setWorkflow([...workflow, techName]);
    }
  };

  const generateOptimalOrder = async () => {
    if (workflow.length === 0 || !useCase.trim()) {
      setStatus("Select technologies and provide a use case first.");
      setTimeout(() => setStatus(null), 3000);
      return;
    }

    setStatus("Generating optimal order...");
    try {
      const response = await fetch("http://localhost:5000/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          technologies: workflow,
          use_case: useCase,
        }),
      });

      if (!response.ok) throw new Error("Failed to generate order.");

      const data = await response.json();
      setOptimalOrder(data.optimal_order);
      setStatus("Optimal order generated!");
    } catch (error) {
      console.error("Order Generation Error:", error);
      setStatus("Error generating optimal order.");
    }
    setTimeout(() => setStatus(null), 3000);
  };

  const generateNarrative = async () => {
    if (workflow.length === 0 || !useCase.trim()) {
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
          technologies: workflow,
          use_case: useCase,
          optimal_order: optimalOrder || workflow,
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

  const deployWorkflow = async () => {
    if (!workflow.length || !useCase) {
      alert("Please select technologies and enter a use case first.");
      return;
    }

    try {
      setStatus("Deploying workflow...");
      const response = await fetch("http://localhost:5000/generate_workflow", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          jobs: workflow,
          use_case: useCase,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to deploy workflow");
      }

      const data = await response.json();
      setStatus("Workflow deployed successfully!");
      console.log("Deployed workflow:", data);
    } catch (error) {
      console.error("Error deploying workflow:", error);
      setStatus("Failed to deploy workflow. Please try again.");
    }
  };

  const deployPersonalizedWorkflow = async () => {
    if (
      !workflow.length ||
      !useCase ||
      Object.keys(renamedTechnologies).length === 0
    ) {
      alert(
        "Please select technologies, enter a use case, and personalize the workflow first."
      );
      return;
    }

    try {
      setStatus("Deploying personalized workflow...");
      const response = await fetch(
        "http://localhost:5000/deploy_personalized_workflow",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            technologies: workflow,
            use_case: useCase,
            optimal_order: optimalOrder,
            renamed_technologies: renamedTechnologies,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to deploy personalized workflow");
      }

      const data = await response.json();
      setStatus("Personalized workflow deployed successfully!");
      console.log("Deployed personalized workflow:", data);
    } catch (error) {
      console.error("Error deploying personalized workflow:", error);
      setStatus("Failed to deploy personalized workflow. Please try again.");
    }
  };

  const generateProposedWorkflow = async () => {
    if (!useCase.trim()) {
      setStatus("Provide a use case first.");
      return;
    }

    setStatus("Generating proposed workflow...");
    setProposedWorkflow(null);
    setWorkflow([]); // Clear existing workflow
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
          setWorkflow(data.technologies);
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
    if (!workflow.length || !useCase) {
      alert("Please select technologies and enter a use case first.");
      return;
    }

    try {
      const response = await fetch(
        "http://localhost:5000/rename_technologies",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            technologies: workflow,
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
    } catch (error) {
      console.error("Error renaming technologies:", error);
      alert("Failed to rename technologies. Please try again.");
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

  return (
    <div className="app">
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
            selectedIcons={workflow}
            onToggle={toggleTechnologyInWorkflow}
          />
        </div>

        {/* RIGHT: Selected Techs + Optimal Order + Narrative */}
        <div className="right-column">
          <div className="workflow-container">
            {workflow.length > 0 && (
              <div className="selected-technologies">
                <h3>Selected Technologies:</h3>
                <div className="workflow-list">
                  {workflow.map((tech, index) => (
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
              disabled={!workflow.length || !useCase}
            >
              Generate Optimal Order
            </button>
            <button
              className="action-button"
              onClick={handlePersonalizeUseCase}
              disabled={!workflow.length || !useCase}
            >
              Personalize Workflow To Use Case
            </button>
            <button
              className="action-button"
              onClick={deployWorkflow}
              disabled={!workflow.length || !useCase}
            >
              Deploy Workflow
            </button>
            <button
              className="action-button"
              onClick={deployPersonalizedWorkflow}
              disabled={
                !workflow.length ||
                !useCase ||
                Object.keys(renamedTechnologies).length === 0
              }
            >
              Deploy Personalized Workflow
            </button>
            <button
              className="action-button"
              onClick={generateNarrative}
              disabled={!workflow.length || !useCase}
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
    </div>
  );
}

export default App;
