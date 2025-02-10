import React, { useState } from "react";
import "./App.css";
import TechnologyGrid from "./TechnologyGrid";
import { marked } from "marked";


function App() {
  const [workflow, setWorkflow] = useState([]);
  const [useCase, setUseCase] = useState(""); // Store the use case
  const [status, setStatus] = useState(null); // Status messages
  const [savedJSON, setSavedJSON] = useState(null); // Store the saved JSON response
  const [optimalOrder, setOptimalOrder] = useState(null); // Store the optimal order from GPT
  const [narrative, setNarrative] = useState(""); // Store the generated narrative
  const [isPanelOpen, setIsPanelOpen] = useState(false); // Control panel visibility


  // Add or remove technologies from the workflow
  const toggleTechnologyInWorkflow = (techName) => {
    if (workflow.find((job) => job.name === techName)) {
      setWorkflow(workflow.filter((job) => job.name !== techName));
    } else {
      setWorkflow([...workflow, { name: techName }]);
    }
  };

  // Function to generate the best order for the workflow using GPT
  const generateWorkflowOrder = async () => {
    if (workflow.length === 0) {
      setStatus("Please select at least one technology.");
      return;
    }
  
    if (!useCase.trim()) {
      setStatus("Please enter a use case.");
      return;
    }
    setStatus("Generating optimal order...");
  
    try {
      const response = await fetch("http://localhost:5000/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          technologies: workflow.map((job) => job.name),
          use_case: useCase,
        }),
      });
  
      if (!response.ok) {
        throw new Error("Failed to generate workflow order.");
      }
  
      const data = await response.json();
      console.log("Generated Workflow Order:", data);
  
      // Handle different response formats
    if (data.optimal_order) {
      setOptimalOrder(data.optimal_order);
      setStatus("Optimal workflow order generated!");
    } else if (data.workflow) {
      setOptimalOrder(data.workflow);
      setStatus("Optimal workflow order generated!");
    } else {
      setStatus("Error generating workflow order.");
    }
  } catch (error) {
    console.error("Error generating workflow order:", error);
    setStatus("Error generating workflow order. Please try again.");
  }
  
    setTimeout(() => setStatus(null), 30000); // Automatically clear the status message after 30 seconds
  };
  

  const generateNarrative = async () => {
    if (!optimalOrder || workflow.length === 0 || !useCase.trim()) {
      setStatus("Please generate the workflow order first.");
      return;
    }
    setStatus("Generating workflow and narrative...");

    try {
      const response = await fetch("http://localhost:5000/generate-narrative", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          technologies: workflow.map((job) => job.name),
          use_case: useCase,
          optimal_order: optimalOrder,
        }),
      });

      if (!response.ok) throw new Error("Failed to generate narrative.");
      const data = await response.json();
      setNarrative(data.narrative);
      setIsPanelOpen(true); // Open the side panel
      setStatus(null);
    } catch (error) {
      console.error("Error generating narrative:", error);
      setStatus("Error generating narrative. Please try again.");
    }
  };

  

  
  // Save the workflow to the backend
  const saveWorkflowToBackend = async () => {
    setStatus("Saving workflow...");

    try {
       // Convert the workflow to an array of strings (job names)
      const formattedWorkflow = workflow.map((job) => job.name);

      const response = await fetch("http://localhost:5000/save-workflow", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ workflow: formattedWorkflow }),
      });

      if (!response.ok) {
        throw new Error("Failed to save workflow.");
      }

      const data = await response.json();
      console.log("Server Response:", data);
      setSavedJSON(data);
      setStatus("Workflow saved successfully!");
    } catch (error) {
      console.error("Error saving workflow:", error);
      setStatus("Error saving workflow. Please try again.");
    }

    setTimeout(() => setStatus(null), 30000); // Automatically clear the status message after 30 seconds
  };

  // Download the workflow as a JSON file
  const downloadWorkflowAsJSON = () => {
    const fileData = JSON.stringify(savedJSON, null, 2);
    const blob = new Blob([fileData], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "workflow.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className={`app ${isPanelOpen ? "panel-open" : ""}`}>
      

      {/* Technology Grid */}
      
      <div className="left-column">
      <h1>Job Workflow Creator</h1>
      <h3>Select your technologies and enter your use case:</h3>
      <TechnologyGrid
        selectedIcons={workflow.map((job) => job.name)}
        onToggle={toggleTechnologyInWorkflow}
      />
      </div>
{/* Input for use case */}
<div className="right-column">
  <div className="use-case-input">
    <label htmlFor="useCase">Enter Use Case:</label>
    <textarea
      id="useCase"
      value={useCase}
      onChange={(e) => setUseCase(e.target.value)}
      onInput={(e) => {
        e.target.style.height = "auto"; // Reset height to recalculate
        e.target.style.height = e.target.scrollHeight + "px"; // Set height dynamically
      }}
      placeholder="Input your Discovery Information"
      rows="1" // Start with one row, expands dynamically
    />
  </div>



{/* Wrapper for Selected Workflow & Optimal Workflow Order */}
<div className="workflow-container">
  {/* Selected Workflow Section */}
  <div className="selected-workflow">
    <h2>Selected Workflow</h2>
    <div className="workflow">
      {workflow.map((job, index) => (
        <div key={`${job.name}-${index}`} className="workflow-box">
          {job.name}
          <button className="delete-button" onClick={() => toggleTechnologyInWorkflow(job.name)}>
          ❌
          </button>
        </div>
      ))}
      {workflow.length > 0 && useCase && (
        <>
          <button className="generate-button" onClick={generateWorkflowOrder}
          disabled={workflow.length === 0 || !useCase.trim()}>
            Generate Optimal Order
          </button>
          
        </>
      )}
    </div>
  </div>

  {/* Optimal Workflow Order Section */}
  {optimalOrder && (
    <div className="optimal-workflow">
      <h2>Optimal Workflow Order</h2>
      <ul>
        {optimalOrder.map((job, index) => (
          <li key={index}>{job}</li>
        ))}
      </ul>
      <button className="save-button" onClick={saveWorkflowToBackend}>
        Save Workflow
      </button>
      <button className="save-button" onClick={generateNarrative}>
        Generate Workflow and Narrative
      </button>
      {/* Download button for JSON output */}
{savedJSON && (
  <button className="download-button" onClick={downloadWorkflowAsJSON}>
    Download Workflow as JSON
  </button>
)}
    </div>
  )}
</div>




{/* Display status messages */}
{status && <div className="status-message">{status}</div>}

{/* Side-by-side view for JSON and Narrative */}
{savedJSON && narrative && (
  <div className="output-container">
    {/* Workflow in JSON Box */}
    <div className="json-display">
      <h3>Workflow in JSON</h3>
      <pre>{JSON.stringify(savedJSON, null, 2)}</pre>
    </div>

    {/* Workflow Narrative Box */}
    <div className="narrative-display">
      <h3>Workflow Narrative</h3>
      <div dangerouslySetInnerHTML={{ __html: marked(narrative) }} />
    </div>
  </div>
)}

</div>
    </div>

  );
}

export default App;
