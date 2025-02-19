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
  const [userCode, setUserCode] = useState(""); // Store the user code
  const [isWorkflowSaved, setIsWorkflowSaved] = useState(false);
  const [isNarrativeGenerated, setIsNarrativeGenerated] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState(null);
  const [isJsonUploaded, setIsJsonUploaded] = useState(false);

  // Add or remove technologies from the workflow
  const toggleTechnologyInWorkflow = (techName) => {
    if (!userCode.trim()) {
      setStatus("Please enter your User Code before selecting technologies.");
      setTimeout(() => setStatus(null), 3000);
      return;
    }
    setIsJsonUploaded(false);

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
    if (workflow.length === 0 || !useCase.trim()) {
      setStatus("Enter Use Case first. ");
      setTimeout(() => setStatus(null), 5000);
      return;
    }
    setStatus("Saving workflow before generating the narrative...");

    try {
      // First, save the workflow automatically
      await saveWorkflowToBackend();

      setStatus("Generating workflow and narrative...");
      setNarrative(""); // Clear the narrative before generating a new one

      const response = await fetch("http://localhost:5000/generate-narrative", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          technologies: workflow.map((job) => job.name),
          use_case: useCase,
          optimal_order: optimalOrder || workflow.map((job) => job.name),
        }),
      });

      if (!response.ok) throw new Error("Failed to generate narrative.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullNarrative = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        let chunkText = decoder.decode(value, { stream: true });

        chunkText = chunkText.replace(/\n([A-Z][^\n:]+):/g, "\n\n**$1**\n");

        chunkText = chunkText.replace(/\n{3,}/g, "\n\n");

        fullNarrative += chunkText;

        setNarrative(fullNarrative); // ✅ Update UI with cleaned narrative
      }

      setStatus(null); // ✅ Clear status as soon as the narrative appears
      setIsNarrativeGenerated(true);
    } catch (error) {
      console.error("Error generating narrative:", error);
      setStatus("Error generating narrative. Please try again.");
      setTimeout(() => setStatus(null), 5000);
    }

    //   if (!response.ok) throw new Error("Failed to generate narrative.");
    //   const data = await response.json();
    //   setNarrative(data.narrative);
    //   setStatus(null);
    //   setIsNarrativeGenerated(true);
    //   setTimeout(() => setStatus(null), 2000);
    // } catch (error) {
    //   console.error("Error generating narrative:", error);
    //   setStatus("Error generating narrative. Please try again.");
    //   setTimeout(() => setStatus(null), 5000);
    // }
  };

  // Save the workflow to the backend
  const saveWorkflowToBackend = async () => {
    setStatus("Saving workflow...");

    // Log both workflow and optimal order before sending request
    console.log("🟢 Saving Workflow...");
    console.log(
      "✅ Selected Technologies:",
      workflow.map((job) => job.name)
    );
    console.log("🔵 Optimal Order:", optimalOrder);

    try {
      // If optimal order exists, use it. Otherwise, use selected technologies.
      let finalWorkflow = optimalOrder?.length
        ? optimalOrder
        : workflow.map((job) => job.name);

      // Convert the workflow to an array of strings (job names)
      // const formattedWorkflow = workflow.map((job) => job.name);

      console.log("🚀 Final Workflow Sent to Backend:", finalWorkflow);

      const response = await fetch("http://localhost:5000/save-workflow", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ workflow: finalWorkflow }),
      });

      if (!response.ok) {
        throw new Error("Failed to save workflow.");
      }

      const data = await response.json();
      console.log("Server Response:", data);
      setSavedJSON(data);
      setStatus("Workflow saved successfully!");
      setIsWorkflowSaved(true);
    } catch (error) {
      console.error("Error saving workflow:", error);
      setStatus("Error saving workflow. Please try again.");
    }

    setTimeout(() => setStatus(null), 3000); // Automatically clear the status message after 3 seconds
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

  const uploadWorkflowToGitHub = async () => {
    if (!savedJSON || !narrative) {
      setStatus("No workflow or narrative to upload!");
      return;
    }

    setStatus("Uploading workflow to GitHub...");

    try {
      const response = await fetch("http://localhost:5000/upload-github", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          workflow_json: savedJSON,
          narrative_text: narrative,
          user_info: userCode?.trim() || "unknown_user",
        }),
      });

      const data = await response.json();

      if (
        data.workflow?.status === "success" &&
        data.narrative?.status === "success"
      ) {
        setStatus("Workflow and Narrative uploaded to GitHub successfully!");
      } else {
        setStatus("Upload failed. Check console for details.");
        console.error("Upload Error:", data);
      }
    } catch (error) {
      console.error("Error uploading to GitHub:", error);
      setStatus("An error occurred while uploading.");
    }

    setTimeout(() => setStatus(null), 3000);
  };

  // const handleFileUpload = (event) => {
  //   const file = event.target.files[0];

  //   if (!file) {
  //     console.log("❌ No file detected.");
  //     return;
  //   }

  //   console.log("📂 File selected:", file.name);

  //   processJsonFile(file);
  // };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) {
      processJsonFile(file);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0]; // Get the uploaded file
    if (file) {
      processJsonFile(file);
    }
  };

  const processJsonFile = (file) => {
    // if (!file) return;

    setUploadedFileName(file.name); // Display file name

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const jsonData = JSON.parse(e.target.result);

        // To eventually update to the user code given etc
        if (
          !jsonData.WZA_DEMO_GEN ||
          typeof jsonData.WZA_DEMO_GEN !== "object"
        ) {
          console.error("❌ Invalid JSON structure.");
          setStatus(
            "Invalid JSON format. Expected a Control-M workflow structure."
          );
          return;
        }

        console.log("Uploading JSON to Backend:", jsonData);

        // Extract job names from the Control-M JSON structure
        const jobNames = Object.keys(jsonData.WZA_DEMO_GEN).filter(
          (key) => key.startsWith("Run") // Only extract job names
        );

        if (jobNames.length === 0) {
          console.error("❌ No technologies found in JSON.");
          setStatus("No technologies found in the uploaded JSON.");
          return;
        }

        console.log("📋 Extracted Job Names:", jobNames);

        // Send JSON to backend for validation and processing
        const response = await fetch(
          "http://localhost:5000/upload-workflow-json",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ jobs: jobNames }),
          }
        );

        const result = await response.json();

        console.log("Backend Response:", result);

        if (response.ok) {
          setWorkflow(result.workflow.map((tech) => ({ name: tech }))); // Update UI workflow
          setIsJsonUploaded(true);
          setStatus("Workflow successfully loaded from JSON.");
        } else {
          setStatus(result.error || "Failed to process JSON file.");
        }

        setTimeout(() => setStatus(null), 3000);
      } catch (error) {
        console.error("Error parsing JSON:", error);
        setStatus("Error reading JSON file. Ensure it is properly formatted.");
        setTimeout(() => setStatus(null), 3000);
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className={`app ${isPanelOpen ? "panel-open" : ""}`}>
      {/* Header Section (Title & User Code Input) */}
      <div className="content-container">
        <div className="left-column">
          <div className="header-container">
            <h1>Demonstration Generator</h1>
            <div className="user-code-container">
              <h3 htmlFor="userCode">Enter User Code:</h3>
              <input
                type="text"
                id="userCode"
                value={userCode}
                onChange={(e) => setUserCode(e.target.value)}
                placeholder="Example: zzz"
              />
            </div>
          </div>
          <div className="use-case-input">
            <h3 htmlFor="useCase">Enter Use Case to Save Workflow:</h3>
            <textarea
              id="useCase"
              value={useCase}
              onChange={(e) => setUseCase(e.target.value)}
              onInput={(e) => {
                e.target.style.height = "auto";
                e.target.style.height = e.target.scrollHeight + "px";
              }}
              placeholder="Input your Discovery Information"
              rows="1"
            />
          </div>

          {/* Main Content Section (FIX: Both Left & Right columns inside content-container) */}
          <h3>Select your technologies:</h3>
          <TechnologyGrid
            selectedIcons={workflow.map((job) => job.name)}
            onToggle={toggleTechnologyInWorkflow}
            disabled={!userCode.trim()} // Disable selection if user code is empty
          />
        </div>

        {/* Right Column - Use Case & Workflow */}
        <div className="right-column">
          {/* Upload JSON Section */}
          {!isJsonUploaded && workflow.length === 0 && (
            <div className="upload-section">
              <h3>Or Upload a JSON File:</h3>
              <div
                className="drop-area"
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
              >
                <label className="upload-label">
                  <input
                    type="file"
                    accept=".json"
                    onChange={handleFileUpload}
                    style={{ display: "none" }}
                  />
                  <span className="upload-button">Browse File</span>
                </label>
              </div>
              {uploadedFileName && <p>Uploaded File: {uploadedFileName}</p>}
            </div>
          )}

          {/* Workflow Sections */}
          {workflow.length > 0 && (
            <div className="workflow-container">
              {/* Selected Workflow */}
              <div className="selected-workflow">
                <h2>Selected Workflow</h2>
                <div className="workflow">
                  {workflow.map((job, index) => (
                    <div key={`${job.name}-${index}`} className="workflow-box">
                      {job.name}
                      <button
                        className="delete-button"
                        onClick={() => toggleTechnologyInWorkflow(job.name)}
                      >
                        ❌
                      </button>
                    </div>
                  ))}
                  {workflow.length > 0 && useCase && (
                    <div className="workflow-buttons">
                      <button
                        className="generate-button"
                        onClick={generateWorkflowOrder}
                        disabled={workflow.length === 0 || !useCase.trim()}
                      >
                        Generate Optimal Order
                      </button>

                      {workflow.length > 0 && (
                        <button
                          className="save-button"
                          onClick={generateNarrative}
                        >
                          Generate Workflow and Narrative
                        </button>
                      )}
                      {savedJSON && isNarrativeGenerated && (
                        <div className="workflow-actions">
                          <button
                            className="download-button"
                            onClick={downloadWorkflowAsJSON}
                          >
                            Download Workflow as JSON
                          </button>
                          <button
                            className="upload-button"
                            onClick={uploadWorkflowToGitHub}
                          >
                            Upload Workflow on GitHub
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Optimal Workflow Order */}
              {optimalOrder && (
                <div className="optimal-workflow">
                  <h2>Optimal Workflow Order</h2>
                  <ul>
                    {optimalOrder.map((job, index) => (
                      <li key={index}>{job}</li>
                    ))}
                  </ul>

                  {workflow.length > 0 && (
                    <button className="save-button" onClick={generateNarrative}>
                      Generate Workflow and Narrative
                    </button>
                  )}
                  {savedJSON && isNarrativeGenerated && (
                    <div className="workflow-actions">
                      <button
                        className="download-button"
                        onClick={downloadWorkflowAsJSON}
                      >
                        Download Workflow as JSON
                      </button>
                      <button
                        className="upload-button"
                        onClick={uploadWorkflowToGitHub}
                      >
                        Upload Workflow on GitHub
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Display status messages */}
          {status && <div className="status-message">{status}</div>}
          {/* Side-by-side view for JSON and Narrative */}
          {savedJSON && narrative && (
            <div className="output-container">
              <div className="json-display">
                <h3>Workflow in JSON</h3>
                <pre>{JSON.stringify(savedJSON, null, 2)}</pre>
              </div>
              <div className="narrative-display">
                <h3>Workflow Narrative</h3>
                <div dangerouslySetInnerHTML={{ __html: marked(narrative) }} />
              </div>
            </div>
          )}
        </div>
      </div>{" "}
    </div>
  );
}
export default App;
