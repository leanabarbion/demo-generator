import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import TechnologyGrid from "./TechnologyGrid";
import { marked } from "marked";
import { JOB_LIBRARY } from "./jobLibrary";
import techCategories from "./categories";
import ViewSelector from "./components/ViewSelector";
import AIWorkflowView from "./components/AIWorkflowView";
import ManualWorkflowView from "./components/ManualWorkflowView";

// Get API URL from environment variable
const API_BASE_URL =
  process.env.REACT_APP_API_URL || "https://testdemogenai.vse.bmc.com/api";

function App() {
  const [workflow, setWorkflow] = useState([]);
  const [useCase, setUseCase] = useState("");
  const [userCode, setUserCode] = useState("");
  const [status, setStatus] = useState(null);
  const [optimalOrder, setOptimalOrder] = useState(null);
  const [complexWorkflow, setComplexWorkflow] = useState(null);
  const [narrative, setNarrative] = useState("");
  const [talkTrack, setTalkTrack] = useState("");
  const [proposedWorkflow, setProposedWorkflow] = useState(null);
  const [selectedTechnologies, setSelectedTechnologies] = useState([]);
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showUseTemplateModal, setShowUseTemplateModal] = useState(false);
  const [showGithubModal, setShowGithubModal] = useState(false);
  const [templateName, setTemplateName] = useState("");
  const [templateCategory, setTemplateCategory] = useState("");
  const [templates, setTemplates] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [workflowType, setWorkflowType] = useState("new"); // 'new', 'upload', 'ai', 'documentation', or 'templates'
  const [showInstructions, setShowInstructions] = useState(true);
  const [deployConfig, setDeployConfig] = useState({
    environment: "saas_dev",
    userCode: "LBA",
    controlm_server: "IN01", // Add default Control-M server
    folderName: "demo-genai",
    application: "demo-genai",
    subApplication: "demo-genai",
  });
  const fileInputRef = useRef(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [existingTemplateId, setExistingTemplateId] = useState(null);
  const [confirmAction, setConfirmAction] = useState(null);
  const [selectedTechCategory, setSelectedTechCategory] = useState("");
  const [githubConfig, setGithubConfig] = useState({
    repository: "leanabarbion/workflow-repo",
    branch: "main",
    path: "workflows",
    commitMessage: "Update workflow configuration",
    userCode: "LBA", // Default value, will be overridden by main userCode state
  });
  const [documentationFile, setDocumentationFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [aiResponseContent, setAiResponseContent] = useState(null);
  const [aiWorkflowData, setAiWorkflowData] = useState(null);
  const [isGeneratingAIWorkflow, setIsGeneratingAIWorkflow] = useState(false);
  const [isDeployingAIWorkflow, setIsDeployingAIWorkflow] = useState(false);
  const [documentationSkipped, setDocumentationSkipped] = useState(false);
  const [selectedView, setSelectedView] = useState(null); // 'ai' or 'manual'
  const [manualWorkflowData, setManualWorkflowData] = useState(null);

  // Debug logging for complex workflow state
  useEffect(() => {
    console.log("State Debug:", {
      selectedTechnologies: selectedTechnologies.length,
      complexWorkflow: !!complexWorkflow,
      optimalOrder: !!optimalOrder,
      proposedWorkflow: !!proposedWorkflow,
      useCase: !!useCase,
    });
  }, [
    selectedTechnologies,
    complexWorkflow,
    optimalOrder,
    proposedWorkflow,
    useCase,
  ]);

  const templateCategories = [
    "Banking, Financial Services, Insurance",
    "Telecommunication",
    "Consumer Goods",
    "Manufacturing & Industrial Automation",
    "Retail",
    "Travel, Transportation & Logistics",
  ];

  const toggleTechnologyInWorkflow = (techName) => {
    setSelectedTechnologies((prev) => {
      if (prev.includes(techName)) {
        return prev.filter((tech) => tech !== techName);
      } else {
        // If user manually adds a technology, clear the proposed workflow
        // to indicate they want to start fresh from manual selection
        if (proposedWorkflow) {
          setProposedWorkflow(null);
        }
        return [...prev, techName];
      }
    });
  };

  const generateManualWorkflow = async () => {
    if (selectedTechnologies.length === 0 || !useCase.trim()) {
      setStatus("Select technologies and provide a use case first.");
      setTimeout(() => setStatus(null), 30000);
      return;
    }

    try {
      setStatus("Generating manual workflow...");
      const response = await fetch(
        `${API_BASE_URL}/manualworkflow/generate_manual_workflow`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            technologies: selectedTechnologies,
            use_case: useCase,
            user_code: userCode,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Backend error:", errorData);
        throw new Error(
          errorData.error || "Failed to generate manual workflow"
        );
      }

      const data = await response.json();

      console.log("generateManualWorkflow response:", data);
      console.log("Response keys:", Object.keys(data));

      // Set the optimal order from the response
      if (data.optimal_order) {
        setOptimalOrder(data.optimal_order);
        setStatus("Manual workflow generated successfully!");
      } else {
        setOptimalOrder(selectedTechnologies);
        setStatus("Manual workflow generated with default order!");
      }

      // Set the complex workflow with the workflow data
      if (data.workflow) {
        setComplexWorkflow(data.workflow);
      }

      setManualWorkflowData(data);

      setTimeout(() => setStatus(null), 30000);
    } catch (error) {
      console.error("Error generating manual workflow:", error);
      setStatus("Failed to generate manual workflow. Please try again.");
      setTimeout(() => setStatus(null), 30000);
    }
  };

  const generateNarrative = async () => {
    if (selectedTechnologies.length === 0 || !useCase.trim()) {
      setStatus("Provide technologies and use case first.");
      setTimeout(() => setStatus(null), 30000);
      return;
    }

    setStatus("Generating narrative...");
    setNarrative("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/documentation/generate-narrative`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            technologies: selectedTechnologies,
            use_case: useCase,
            optimal_order: optimalOrder || selectedTechnologies,
          }),
        }
      );

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
      setDocumentationSkipped(false);
    } catch (error) {
      console.error("Narrative Generation Error:", error);
      setStatus("Failed to generate narrative.");
    }
    setTimeout(() => setStatus(null), 30000);
  };

  const generateTalkTrack = async () => {
    if (selectedTechnologies.length === 0 || !useCase.trim()) {
      setStatus("Provide technologies and use case first.");
      setTimeout(() => setStatus(null), 30000);
      return;
    }

    setStatus("Generating talk track...");
    setTalkTrack("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/documentation/generate-talktrack`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            technologies: selectedTechnologies,
            use_case: useCase,
            optimal_order: optimalOrder || selectedTechnologies,
          }),
        }
      );

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullTalkTrack = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunkText = decoder.decode(value, { stream: true });
        fullTalkTrack += chunkText;
        setTalkTrack(fullTalkTrack);
      }

      setStatus("Talk track generated!");
      setDocumentationSkipped(false);
    } catch (error) {
      console.error("Talk Track Generation Error:", error);
      setStatus("Failed to generate talk track.");
    }
    setTimeout(() => setStatus(null), 30000);
  };

  const handleDeployConfigChange = (field, value) => {
    setDeployConfig((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleDeployPersonalizedWorkflow = () => {
    // Show the deployment configuration modal
    setShowDeployModal(true);
  };

  const handlePersonalizedDeployConfirm = async () => {
    try {
      setShowDeployModal(false);
      setStatus("Deploying workflow...");

      // Use the output from generateManualWorkflow
      if (!optimalOrder || !selectedTechnologies.length) {
        throw new Error(
          "No workflow available for deployment. Please generate a workflow first."
        );
      }

      // Prepare the payload
      const payload = {
        environment: deployConfig.environment,
        user_code: userCode,
        folder_name: deployConfig.folderName,
        application: deployConfig.application,
        sub_application: deployConfig.subApplication,
        technologies: selectedTechnologies,
        optimal_order: optimalOrder,
        workflow: complexWorkflow, // Include the complex workflow structure
        sanitized_folder_name: null,
        sanitized_job_names: null,
      };

      // If you store sanitized names in state, add them here
      if (manualWorkflowData && manualWorkflowData.sanitized_folder_name) {
        payload.sanitized_folder_name =
          manualWorkflowData.sanitized_folder_name;
      }
      if (manualWorkflowData && manualWorkflowData.sanitized_job_names) {
        payload.sanitized_job_names = manualWorkflowData.sanitized_job_names;
      }

      const response = await fetch(
        `${API_BASE_URL}/manualworkflow/deploy_manual_workflow`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to deploy workflow");
      }

      const deployData = await response.json();
      setStatus("Workflow deployed successfully!");
      setTimeout(() => setStatus(""), 30000);
    } catch (error) {
      console.error("Deployment error:", error);
      setStatus(`Error: ${error.message}`);
      setTimeout(() => setStatus(""), 30000);
    }
  };

  const handleDownloadWorkflow = async () => {
    if (!selectedTechnologies.length || !useCase) {
      alert("Please select technologies and enter a use case first.");
      return;
    }

    try {
      setStatus("Preparing workflow download...");
      const response = await fetch(
        `${API_BASE_URL}/importexport/download_workflow`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            jobs: selectedTechnologies,
            environment: deployConfig.environment,
            folder_name: deployConfig.folderName,
            user_code: userCode,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to download workflow");
      }

      // Get the blob from the response
      const blob = await response.blob();

      // Create a download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `workflow_${userCode}_${deployConfig.folderName}.json`;
      document.body.appendChild(a);
      a.click();

      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setStatus("Workflow downloaded successfully!");
      setTimeout(() => setStatus(""), 30000);
    } catch (error) {
      console.error("Download error:", error);
      setStatus(`Error: ${error.message}`);
      setTimeout(() => setStatus(""), 30000);
    }
  };

  const generateProposedWorkflow = async () => {
    if (!useCase.trim()) {
      setStatus("Provide a use case first.");
      return;
    }

    setStatus("Generating proposed workflow...");
    setProposedWorkflow(null);
    setSelectedTechnologies([]); // Clear existing selected technologies
    setOptimalOrder(null); // Clear any existing Logical order

    try {
      const response = await fetch(
        `${API_BASE_URL}/manualworkflow/proposed_workflow`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ use_case: useCase }),
        }
      );

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
        if (data.technologies) {
          // Update the selected technologies with the suggested ones
          setSelectedTechnologies(data.technologies);
          // Set the optimal order to the same as suggested technologies (order will be optimized later in generate_manual_workflow)
          setOptimalOrder(data.technologies);
          setProposedWorkflow(data);

          // Add a small delay to ensure the UI updates smoothly
          setTimeout(() => {
            setStatus(
              "Technologies suggested! You can modify the selection and generate the workflow."
            );
          }, 100);
        } else {
          throw new Error(
            "Invalid response format - missing technologies array"
          );
        }
      } catch (parseError) {
        console.error("Error parsing response:", parseError);
        setStatus("Error parsing proposed workflow response.");
      }
    } catch (error) {
      console.error("Proposed Workflow Generation Error:", error);
      setStatus("Failed to generate proposed workflow.");
    }
    setTimeout(() => setStatus(null), 30000);
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith(".json")) {
      alert("Please upload a JSON file");
      return;
    }

    try {
      setStatus("Uploading workflow...");
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_BASE_URL}/importexport/upload_workflow`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to upload workflow");
      }

      const data = await response.json();

      // Update the selected technologies with the jobs from the uploaded workflow
      setSelectedTechnologies(data.jobs);

      setStatus("Workflow uploaded successfully!");
      setTimeout(() => setStatus(""), 30000);
    } catch (error) {
      console.error("Upload error:", error);
      setStatus(`Error: ${error.message}`);
      setTimeout(() => setStatus(""), 30000);
    }
  };

  const handleDocumentationUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setDocumentationFile(file);
      setStatus(
        "Documentation file selected. Click 'Analyze Documentation' to process."
      );
    }
  };

  const analyzeDocumentation = async () => {
    if (!documentationFile) {
      setStatus("Please select a documentation file first.");
      return;
    }

    setStatus("Analyzing documentation...");
    setAnalysisResult(null);

    try {
      const formData = new FormData();
      formData.append("file", documentationFile);
      formData.append("use_case", useCase);

      const response = await fetch(
        `${API_BASE_URL}/importexport/analyze_documentation`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to analyze documentation");
      }

      const result = await response.json();
      setAnalysisResult(result);

      // Update the workflow with the analysis results
      setUseCase(result.extracted_use_case);
      setSelectedTechnologies(result.suggested_technologies);
      setOptimalOrder(result.workflow_order);

      setStatus("Documentation analyzed successfully!");
    } catch (error) {
      console.error("Documentation Analysis Error:", error);
      setStatus(`Error: ${error.message}`);
    }
    setTimeout(() => setStatus(null), 30000);
  };

  const renderWorkflowItem = (tech, index) => {
    return (
      <li key={tech} className="ordered-item">
        <span className="step-number">{index + 1}</span>
        <span className="job-name">{tech}</span>
      </li>
    );
  };

  const renderInstructions = () => {
    switch (workflowType) {
      case "new":
        return (
          <div className="workflow-instructions">
            <h3>Create New Workflow:</h3>
            <ol>
              <li>
                <span className="step-number">1</span>
                <span className="step-text">
                  Enter your use case in the text area below
                </span>
              </li>
              <li>
                <span className="step-number">2</span>
                <span className="step-text">
                  Select technologies from the grid below
                </span>
              </li>
              <li>
                <span className="step-number">3</span>
                <span className="step-text">
                  Click "Generate Workflow" to create the workflow with optimal
                  execution sequence
                </span>
              </li>
              <li>
                <span className="step-number">4</span>
                <span className="step-text">
                  Generate narrative and talk track for presentations
                </span>
              </li>
              <li>
                <span className="step-number">5</span>
                <span className="step-text">
                  Deploy your workflow, save as template, or upload to GitHub
                </span>
              </li>
            </ol>
          </div>
        );
      case "templates":
        return (
          <div className="workflow-instructions">
            <h3>Use Templates:</h3>
            <ol>
              <li>
                <span className="step-number">1</span>
                <span className="step-text">
                  Click "Browse Templates" to view available templates
                </span>
              </li>
              <li>
                <span className="step-number">2</span>
                <span className="step-text">
                  Select a template to use or manage
                </span>
              </li>
              <li>
                <span className="step-number">3</span>
                <span className="step-text">
                  Use the template to create a new workflow
                </span>
              </li>
              <li>
                <span className="step-number">4</span>
                <span className="step-text">
                  Update or delete templates as needed
                </span>
              </li>
              <li>
                <span className="step-number">5</span>
                <span className="step-text">
                  Save new templates from your workflows
                </span>
              </li>
            </ol>
          </div>
        );
      case "upload":
        return (
          <div className="workflow-instructions">
            <h3>Upload Existing Workflow:</h3>
            <ol>
              <li>
                <span className="step-number">1</span>
                <span className="step-text">
                  Enter your use case in the text area below
                </span>
              </li>
              <li>
                <span className="step-number">2</span>
                <span className="step-text">
                  Upload your workflow JSON file
                </span>
              </li>
              <li>
                <span className="step-number">3</span>
                <span className="step-text">
                  Review the extracted technologies
                </span>
              </li>
              <li>
                <span className="step-number">4</span>
                <span className="step-text">
                  Modify the workflow if needed by adding or removing
                  technologies
                </span>
              </li>
              <li>
                <span className="step-number">5</span>
                <span className="step-text">
                  Generate Workflow, narrative, and talk track
                </span>
              </li>
              <li>
                <span className="step-number">6</span>
                <span className="step-text">
                  Deploy your workflow or save as template
                </span>
              </li>
            </ol>
          </div>
        );
      case "ai":
        return (
          <div className="workflow-instructions">
            <h3>AI-Assisted Workflow Creation:</h3>
            <ol>
              <li>
                <span className="step-number">1</span>
                <span className="step-text">
                  Enter your use case in the text area below
                </span>
              </li>
              <li>
                <span className="step-number">2</span>
                <span className="step-text">
                  Click "Ask AI for Technology Suggestions" to get technology
                  suggestions based on your use case
                </span>
              </li>
              <li>
                <span className="step-number">3</span>
                <span className="step-text">
                  Review and modify the suggested technologies if needed
                </span>
              </li>
              <li>
                <span className="step-number">4</span>
                <span className="step-text">Generate Workflow</span>
              </li>
              <li>
                <span className="step-number">5</span>
                <span className="step-text">
                  Generate narrative and talk track for presentations
                </span>
              </li>
              <li>
                <span className="step-number">6</span>
                <span className="step-text">
                  Deploy your workflow, save as template, or upload to GitHub
                </span>
              </li>
            </ol>
          </div>
        );
      case "documentation":
        return (
          <div className="workflow-instructions">
            <h3>Documentation Analysis:</h3>
            <ol>
              <li>
                <span className="step-number">1</span>
                <span className="step-text">
                  Enter your use case in the text area below
                </span>
              </li>
              <li>
                <span className="step-number">2</span>
                <span className="step-text">
                  Upload documentation files (PDF, DOC, DOCX, TXT, XLSX, XLS)
                  for analysis
                </span>
              </li>
              <li>
                <span className="step-number">3</span>
                <span className="step-text">
                  Review AI-extracted use case and suggested technologies
                </span>
              </li>
              <li>
                <span className="step-number">4</span>
                <span className="step-text">
                  Modify the suggested workflow if needed
                </span>
              </li>
              <li>
                <span className="step-number">5</span>
                <span className="step-text">
                  Generate Workflow, narrative, and talk track
                </span>
              </li>
              <li>
                <span className="step-number">6</span>
                <span className="step-text">
                  Deploy your workflow or save as template
                </span>
              </li>
            </ol>
          </div>
        );
      default:
        return null;
    }
  };

  const handleWorkflowTypeChange = (type) => {
    if (workflowType === type) {
      // If clicking the same button, toggle instructions
      setShowInstructions(!showInstructions);
    } else {
      // If clicking a different button, show instructions and change type
      setWorkflowType(type);
      setShowInstructions(true);
    }
  };

  // Add useEffect to monitor state changes
  useEffect(() => {
    console.log("Deployment modal state:", showDeployModal);
  }, [showDeployModal]);

  const filteredTechnologies = selectedTechnologies.filter((tech) =>
    selectedTechCategory === ""
      ? true
      : techCategories
          .find((cat) => cat.name === selectedTechCategory)
          ?.technologies.some((t) => t.name === tech)
  );

  const handleSaveAsTemplate = async () => {
    console.log("🔍 handleSaveAsTemplate called");
    console.log("Current states:", {
      templateName,
      templateCategory,
      showTemplateModal,
      showConfirmModal,
      selectedTechnologies,
      optimalOrder,
      useCase,
      narrative,
      deployConfig,
    });

    if (!templateName || !templateCategory) {
      console.log("❌ Missing required fields:", {
        templateName,
        templateCategory,
      });
      setStatus("Please enter both template name and category");
      return;
    }

    console.log("🔍 Checking for existing template...");
    try {
      const response = await fetch(
        `${API_BASE_URL}/templates/check_template_exists`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: templateName,
            category: templateCategory,
          }),
        }
      );

      const result = await response.json();
      console.log("📝 Template check response:", result);

      if (result.exists) {
        console.log("⚠️ Template exists, showing confirmation modal");
        console.log("Template details:", {
          templateId: result.templateId,
          name: templateName,
          category: templateCategory,
        });
        setExistingTemplateId(result.templateId);
        setShowConfirmModal(true);
      } else {
        console.log("✅ No existing template found, proceeding with save");
        await saveTemplate();
      }
    } catch (error) {
      console.error("❌ Error checking template existence:", error);
      setStatus("Error checking template existence");
    }
  };

  const saveTemplate = async () => {
    console.log("🔍 saveTemplate called");
    console.log("📦 Data being saved:", {
      name: templateName,
      category: templateCategory,
      technologies: selectedTechnologies,
      workflowOrder: optimalOrder,
      useCase: useCase,
      narrative: narrative,
      environment: deployConfig.environment,
      userCode: userCode,
      folderName: deployConfig.folderName,
      application: deployConfig.application,
      subApplication: deployConfig.subApplication,
    });

    try {
      const response = await fetch(`${API_BASE_URL}/templates/save_template`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: templateName,
          category: templateCategory,
          technologies: selectedTechnologies,
          workflowOrder: optimalOrder,
          useCase: useCase,
          narrative: narrative,
          environment: deployConfig.environment,
          userCode: userCode,
          folderName: deployConfig.folderName,
          application: deployConfig.application,
          subApplication: deployConfig.subApplication,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log("✅ Template saved successfully:", result);
        setShowTemplateModal(false);
        setTemplateName("");
        setTemplateCategory("");
        setStatus("Template saved successfully!");
      } else {
        const error = await response.json();
        console.error("❌ Error saving template:", error);
        setStatus(`Error saving template: ${error.error}`);
      }
    } catch (error) {
      console.error("❌ Error in saveTemplate:", error);
      setStatus("Error saving template");
    }
  };

  const handleConfirmAction = async (action) => {
    console.log("🔍 handleConfirmAction called with action:", action);
    console.log("Current states:", {
      confirmAction: action,
      existingTemplateId,
      showTemplateModal,
      showConfirmModal,
      templateName,
      templateCategory,
      selectedTechnologies,
      optimalOrder,
      useCase,
      narrative,
      deployConfig,
    });

    try {
      if (action === "update") {
        console.log("🔄 Updating existing template...");
        console.log("📦 Data being updated:", {
          templateId: existingTemplateId,
          name: templateName,
          category: templateCategory,
          technologies: selectedTechnologies,
          workflowOrder: optimalOrder,
          useCase: useCase,
          narrative: narrative,
          environment: deployConfig.environment,
          userCode: userCode,
          folderName: deployConfig.folderName,
          application: deployConfig.application,
          subApplication: deployConfig.subApplication,
        });

        // Close both modals immediately
        console.log("Closing modals...");
        setShowTemplateModal(false);
        setShowConfirmModal(false);

        // Update the existing template
        const response = await fetch(
          `${API_BASE_URL}/templates/update_template`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              templateId: existingTemplateId,
              name: templateName,
              category: templateCategory,
              technologies: selectedTechnologies,
              workflowOrder: optimalOrder,
              useCase: useCase,
              narrative: narrative,
              environment: deployConfig.environment,
              userCode: userCode,
              folderName: deployConfig.folderName,
              application: deployConfig.application,
              subApplication: deployConfig.subApplication,
            }),
          }
        );

        console.log("📝 Update response status:", response.status);

        if (!response.ok) {
          const error = await response.json();
          console.error("❌ Update failed:", error);
          throw new Error(error.error || "Failed to update template");
        }

        const result = await response.json();
        console.log("✅ Template updated successfully:", result);
        console.log("Resetting states after successful update");

        // Reset states after successful update
        setTemplateName("");
        setTemplateCategory("");
        setExistingTemplateId(null);
        setConfirmAction(null);
        setStatus("Template updated successfully!");
      } else if (action === "new") {
        console.log("🆕 Creating new template with modified name...");
        // Generate a new name by appending a timestamp
        const newName = `${templateName}_${Date.now()}`;
        console.log("New template name:", newName);
        setTemplateName(newName);
        await saveTemplate();
      }
    } catch (error) {
      console.error("❌ Error in handleConfirmAction:", error);
      setStatus(error.message || "Error updating template");
      // Reopen the modals on error
      console.log("Reopening modals due to error");
      setShowTemplateModal(true);
      setShowConfirmModal(true);
    }
  };

  const handleUseTemplate = async () => {
    console.log("🔍 handleUseTemplate called - fetching templates");
    try {
      const response = await fetch(`${API_BASE_URL}/templates/list_templates`);
      if (!response.ok) {
        throw new Error("Failed to fetch templates");
      }
      const data = await response.json();
      console.log("📦 Templates fetched:", data.templates);
      setTemplates(data.templates);
      setShowUseTemplateModal(true);
    } catch (error) {
      console.error("❌ Error fetching templates:", error);
      setStatus("Error loading templates: " + error.message);
    }
  };

  const handleLoadTemplate = (template) => {
    console.log("🔍 handleLoadTemplate called with template:", template);
    setSelectedTechnologies(template.technologies);
    setOptimalOrder(template.workflowOrder);
    setUseCase(template.useCase);
    setNarrative(template.narrative);
    setUserCode(template.userCode || "LBA");
    setDeployConfig({
      environment: template.environment || "saas_dev",
      userCode: "LBA", // Keep default for deployConfig
      folderName: template.folderName || "demo-genai",
      application: template.application || "demo-genai",
      subApplication: template.subApplication || "demo-genai",
    });
    // Only clear analysis results and talk track, keep file upload capability
    setAnalysisResult(null);
    setTalkTrack("");
    setShowUseTemplateModal(false);
    setStatus("Template loaded successfully!");
    setTimeout(() => setStatus(""), 30000);
  };

  const handleDeleteTemplate = async (templateId) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/templates/delete_template`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ templateId }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to delete template");
      }

      // Remove the template from the local state
      setTemplates(
        templates.filter((template) => template.templateId !== templateId)
      );
      setStatus("Template deleted successfully");
      setTimeout(() => setStatus(""), 30000);
    } catch (error) {
      console.error("Error deleting template:", error);
      setStatus("Error deleting template: " + error.message);
      setTimeout(() => setStatus(""), 30000);
    }
  };

  const filteredTemplates = selectedCategory
    ? templates.filter((template) => template.category === selectedCategory)
    : templates;

  const handleGithubUpload = async () => {
    if (!selectedTechnologies.length) {
      setStatus("Please select technologies first.");
      setTimeout(() => setStatus(""), 30000);
      return;
    }

    try {
      setStatus("Creating workflow...");

      // First, create the workflow
      const createResponse = await fetch(
        `${API_BASE_URL}/manualworkflow/create_workflow`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            technologies: selectedTechnologies,
            use_case: useCase,
            optimal_order: optimalOrder || selectedTechnologies,
            environment: deployConfig.environment,
            user_code: userCode,
            folder_name: deployConfig.folderName,
            application: deployConfig.application,
            sub_application: deployConfig.subApplication,
            controlm_server: deployConfig.controlm_server,
          }),
        }
      );

      if (!createResponse.ok) {
        const errorData = await createResponse.json();
        throw new Error(errorData.error || "Failed to create workflow");
      }

      // Now upload to GitHub
      const githubResponse = await fetch(
        `${API_BASE_URL}/importexport/upload-github`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            narrative_text: narrative,
            user_info: userCode,
          }),
        }
      );

      if (!githubResponse.ok) {
        const errorData = await githubResponse.json();
        throw new Error(errorData.error || "Failed to upload to GitHub");
      }

      const githubData = await githubResponse.json();
      setStatus("Successfully uploaded to GitHub!");
      setShowGithubModal(false);
      setTimeout(() => setStatus(""), 30000);
    } catch (error) {
      console.error("GitHub upload error:", error);
      setStatus(`Error: ${error.message}`);
      setTimeout(() => setStatus(""), 30000);
    }
  };

  const generateAIWorkflow = async () => {
    if (!useCase.trim()) {
      setStatus("Please enter a use case first.");
      setTimeout(() => setStatus(""), 30000);
      return;
    }

    try {
      setIsGeneratingAIWorkflow(true);
      setStatus("🤖 Generating AI workflow...");

      const response = await fetch(
        `${API_BASE_URL}/aiworkflow/ai_prompt_workflow`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            use_case: useCase,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to generate AI workflow");
      }

      const data = await response.json();
      setAiResponseContent(data.response_content);
      setStatus(
        "✅ AI workflow generated successfully! Review and deploy when ready."
      );
      setTimeout(() => setStatus(""), 30000);
    } catch (error) {
      console.error("AI workflow generation error:", error);
      setStatus(`❌ Error: ${error.message}`);
      setTimeout(() => setStatus(""), 30000);
    } finally {
      setIsGeneratingAIWorkflow(false);
    }
  };

  const regenerateAIWorkflow = async () => {
    if (!useCase.trim()) {
      setStatus("Please enter a use case first.");
      setTimeout(() => setStatus(""), 30000);
      return;
    }

    try {
      setIsGeneratingAIWorkflow(true);
      setStatus("🔄 Regenerating AI workflow...");

      // Clear the deployment status when regenerating
      setAiWorkflowData(null);

      const response = await fetch(
        `${API_BASE_URL}/aiworkflow/ai_prompt_workflow`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            use_case: useCase,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to regenerate AI workflow");
      }

      const data = await response.json();
      setAiResponseContent(data.response_content);
      setStatus("✅ AI workflow regenerated successfully!");
      setTimeout(() => setStatus(""), 30000);
    } catch (error) {
      console.error("AI workflow regeneration error:", error);
      setStatus(`❌ Error: ${error.message}`);
      setTimeout(() => setStatus(""), 30000);
    } finally {
      setIsGeneratingAIWorkflow(false);
    }
  };

  const deployAIWorkflow = async () => {
    if (!aiResponseContent) {
      setStatus("Please generate an AI workflow first.");
      setTimeout(() => setStatus(""), 30000);
      return;
    }

    try {
      setIsDeployingAIWorkflow(true);
      setStatus("🚀 Deploying AI workflow...");

      const response = await fetch(
        `${API_BASE_URL}/aiworkflow/deploy_ai_workflow`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            response_content: aiResponseContent,
            use_case: useCase,
            environment: deployConfig.environment,
            user_code: userCode,
            folder_name: deployConfig.folderName,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to deploy AI workflow");
      }

      const data = await response.json();
      setAiWorkflowData(data);
      setStatus("✅ AI workflow deployed successfully!");
      setTimeout(() => setStatus(""), 30000);
    } catch (error) {
      console.error("AI workflow deployment error:", error);
      setStatus(`❌ Error: ${error.message}`);
      setTimeout(() => setStatus(""), 30000);
    } finally {
      setIsDeployingAIWorkflow(false);
    }
  };

  const parseAIWorkflow = (responseContent) => {
    try {
      // Extract JSON from response
      const start = responseContent.indexOf("{");
      const end = responseContent.lastIndexOf("}") + 1;
      const jsonStr = responseContent.substring(start, end);
      const aiWorkflow = JSON.parse(jsonStr);

      return {
        subfolders: aiWorkflow.subfolders || [],
        jobs: aiWorkflow.jobs || [],
        isValid: true,
      };
    } catch (error) {
      console.error("Error parsing AI workflow:", error);
      return {
        subfolders: [],
        jobs: [],
        isValid: false,
        error: error.message,
      };
    }
  };

  const renderAIWorkflowItem = (job, index) => {
    return (
      <div key={job.id} className="ai-workflow-job">
        <div className="job-header">
          <span className="job-number">{index + 1}</span>
          <span className="job-name">{job.name}</span>
          <span className="job-type">{job.type}</span>
        </div>
      </div>
    );
  };

  const handleBackToSelector = () => {
    setSelectedView(null);
  };

  const restartWorkflow = () => {
    // Reset all workflow-related state to initial values
    setUseCase("");
    setUserCode("");
    setSelectedTechnologies([]);
    setOptimalOrder(null);
    setComplexWorkflow(null);
    setNarrative("");
    setTalkTrack("");
    setProposedWorkflow(null);
    setSelectedTechCategory("");
    setDeployConfig({
      environment: "saas_dev",
      userCode: "LBA",
      controlm_server: "IN01",
      folderName: "demo-genai",
      application: "demo-genai",
      subApplication: "demo-genai",
    });
    setDocumentationFile(null);
    setAnalysisResult(null);
    setDocumentationSkipped(false);
    setStatus("Workflow restarted successfully!");
    setTimeout(() => setStatus(""), 30000);
  };

  return (
    <div className="app-container">
      {selectedView === null && (
        <ViewSelector
          selectedView={selectedView}
          onViewChange={setSelectedView}
        />
      )}
      {selectedView === "ai" && (
        <AIWorkflowView
          useCase={useCase}
          setUseCase={setUseCase}
          userCode={userCode}
          setUserCode={setUserCode}
          aiResponseContent={aiResponseContent}
          isGeneratingAIWorkflow={isGeneratingAIWorkflow}
          isDeployingAIWorkflow={isDeployingAIWorkflow}
          aiWorkflowData={aiWorkflowData}
          deployConfig={deployConfig}
          setDeployConfig={setDeployConfig}
          showDeployModal={showDeployModal}
          setShowDeployModal={setShowDeployModal}
          generateAIWorkflow={generateAIWorkflow}
          regenerateAIWorkflow={regenerateAIWorkflow}
          deployAIWorkflow={deployAIWorkflow}
          handlePersonalizedDeployConfirm={handlePersonalizedDeployConfirm}
          status={status}
          parseAIWorkflow={parseAIWorkflow}
          onBackToSelector={handleBackToSelector}
        />
      )}
      {selectedView === "manual" && (
        <ManualWorkflowView
          useCase={useCase}
          setUseCase={setUseCase}
          userCode={userCode}
          setUserCode={setUserCode}
          selectedTechnologies={selectedTechnologies}
          setSelectedTechnologies={setSelectedTechnologies}
          optimalOrder={optimalOrder}
          setOptimalOrder={setOptimalOrder}
          complexWorkflow={complexWorkflow}
          setComplexWorkflow={setComplexWorkflow}
          narrative={narrative}
          setNarrative={setNarrative}
          talkTrack={talkTrack}
          setTalkTrack={setTalkTrack}
          proposedWorkflow={proposedWorkflow}
          setProposedWorkflow={setProposedWorkflow}
          selectedTechCategory={selectedTechCategory}
          setSelectedTechCategory={setSelectedTechCategory}
          deployConfig={deployConfig}
          setDeployConfig={setDeployConfig}
          showDeployModal={showDeployModal}
          setShowDeployModal={setShowDeployModal}
          showTemplateModal={showTemplateModal}
          setShowTemplateModal={setShowTemplateModal}
          showUseTemplateModal={showUseTemplateModal}
          setShowUseTemplateModal={setShowUseTemplateModal}
          showGithubModal={showGithubModal}
          setShowGithubModal={setShowGithubModal}
          templates={templates}
          setTemplates={setTemplates}
          selectedCategory={selectedCategory}
          setSelectedCategory={setSelectedCategory}
          templateName={templateName}
          setTemplateName={setTemplateName}
          templateCategory={templateCategory}
          setTemplateCategory={setTemplateCategory}
          showConfirmModal={showConfirmModal}
          setShowConfirmModal={setShowConfirmModal}
          existingTemplateId={existingTemplateId}
          setExistingTemplateId={setExistingTemplateId}
          confirmAction={confirmAction}
          setConfirmAction={setConfirmAction}
          githubConfig={githubConfig}
          setGithubConfig={setGithubConfig}
          documentationFile={documentationFile}
          setDocumentationFile={setDocumentationFile}
          analysisResult={analysisResult}
          setAnalysisResult={setAnalysisResult}
          fileInputRef={fileInputRef}
          status={status}
          setStatus={setStatus}
          workflowType={workflowType}
          showInstructions={showInstructions}
          setShowInstructions={setShowInstructions}
          documentationSkipped={documentationSkipped}
          setDocumentationSkipped={setDocumentationSkipped}
          toggleTechnologyInWorkflow={toggleTechnologyInWorkflow}
          generateManualWorkflow={generateManualWorkflow}
          generateNarrative={generateNarrative}
          generateTalkTrack={generateTalkTrack}
          generateProposedWorkflow={generateProposedWorkflow}
          handleFileUpload={handleFileUpload}
          handleDocumentationUpload={handleDocumentationUpload}
          analyzeDocumentation={analyzeDocumentation}
          handleDeployPersonalizedWorkflow={handleDeployPersonalizedWorkflow}
          handlePersonalizedDeployConfirm={handlePersonalizedDeployConfirm}
          handleDownloadWorkflow={handleDownloadWorkflow}
          handleSaveAsTemplate={handleSaveAsTemplate}
          saveTemplate={saveTemplate}
          handleConfirmAction={handleConfirmAction}
          handleUseTemplate={handleUseTemplate}
          handleLoadTemplate={handleLoadTemplate}
          handleDeleteTemplate={handleDeleteTemplate}
          handleGithubUpload={handleGithubUpload}
          handleWorkflowTypeChange={handleWorkflowTypeChange}
          renderInstructions={renderInstructions}
          renderWorkflowItem={renderWorkflowItem}
          templateCategories={templateCategories}
          onBackToSelector={handleBackToSelector}
          restartWorkflow={restartWorkflow}
        />
      )}
    </div>
  );
}

export default App;
