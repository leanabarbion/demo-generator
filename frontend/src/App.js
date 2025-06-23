import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import TechnologyGrid from "./TechnologyGrid";
import { marked } from "marked";
import { JOB_LIBRARY } from "./jobLibrary";
import techCategories from "./categories";

function App() {
  const [workflow, setWorkflow] = useState([]);
  const [useCase, setUseCase] = useState("");
  const [userCode, setUserCode] = useState("");
  const [status, setStatus] = useState(null);
  const [optimalOrder, setOptimalOrder] = useState(null);
  const [narrative, setNarrative] = useState("");
  const [talkTrack, setTalkTrack] = useState("");
  const [proposedWorkflow, setProposedWorkflow] = useState(null);
  const [renamedTechnologies, setRenamedTechnologies] = useState({});
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
    userCode: deployConfig.userCode, // Initialize with deployConfig userCode
  });
  const [documentationFile, setDocumentationFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [aiResponseContent, setAiResponseContent] = useState(null);
  const [aiWorkflowData, setAiWorkflowData] = useState(null);
  const [isGeneratingAIWorkflow, setIsGeneratingAIWorkflow] = useState(false);
  const [isDeployingAIWorkflow, setIsDeployingAIWorkflow] = useState(false);

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
      setStatus("Generating Logical order...");
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
        throw new Error("Failed to generate Logical order");
      }

      const data = await response.json();
      setOptimalOrder(data.optimal_order);
      setStatus("Logical order generated successfully!");
      setTimeout(() => setStatus(null), 3000);
    } catch (error) {
      console.error("Error generating Logical order:", error);
      setStatus("Failed to generate Logical order. Please try again.");
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

  const generateTalkTrack = async () => {
    if (selectedTechnologies.length === 0 || !useCase.trim()) {
      setStatus("Provide technologies and use case first.");
      setTimeout(() => setStatus(null), 3000);
      return;
    }

    setStatus("Generating talk track...");
    setTalkTrack("");

    try {
      const response = await fetch("http://localhost:5000/generate-talktrack", {
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
      let fullTalkTrack = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunkText = decoder.decode(value, { stream: true });
        fullTalkTrack += chunkText;
        setTalkTrack(fullTalkTrack);
      }

      setStatus("Talk track generated!");
    } catch (error) {
      console.error("Talk Track Generation Error:", error);
      setStatus("Failed to generate talk track.");
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

  const handlePersonalizedDeployConfirm = async () => {
    try {
      // Close modal immediately when deploy is clicked
      setShowDeployModal(false);

      console.log("Starting deployment with config:", deployConfig);
      setStatus("Deploying workflow...");

      // Deploy the workflow directly
      const deployResponse = await fetch(
        "http://localhost:5000/deploy_personalized_workflow",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            technologies: selectedTechnologies,
            use_case: useCase,
            renamed_technologies: renamedTechnologies,
            optimal_order: optimalOrder || selectedTechnologies,
            environment: deployConfig.environment,
            user_code: deployConfig.userCode,
            folder_name: deployConfig.folderName,
            application: deployConfig.application,
            sub_application: deployConfig.subApplication,
            controlm_server: deployConfig.controlm_server,
          }),
        }
      );

      if (!deployResponse.ok) {
        const errorData = await deployResponse.json();
        throw new Error(errorData.error || "Failed to deploy workflow");
      }

      const deployData = await deployResponse.json();
      console.log("Workflow deployed successfully:", deployData);

      setStatus("Workflow deployed successfully!");
      setTimeout(() => setStatus(""), 3000);
    } catch (error) {
      console.error("Deployment error:", error);
      setStatus(`Error: ${error.message}`);
      setTimeout(() => setStatus(""), 3000);
    }
  };

  const handleDownloadWorkflow = async () => {
    if (!selectedTechnologies.length || !useCase) {
      alert("Please select technologies and enter a use case first.");
      return;
    }

    try {
      setStatus("Preparing workflow download...");
      const response = await fetch("http://localhost:5000/download_workflow", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          jobs: selectedTechnologies,
          environment: deployConfig.environment,
          folder_name: deployConfig.folderName,
          user_code: deployConfig.userCode,
        }),
      });

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
      a.download = `workflow_${deployConfig.userCode}_${deployConfig.folderName}.json`;
      document.body.appendChild(a);
      a.click();

      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setStatus("Workflow downloaded successfully!");
      setTimeout(() => setStatus(""), 3000);
    } catch (error) {
      console.error("Download error:", error);
      setStatus(`Error: ${error.message}`);
      setTimeout(() => setStatus(""), 3000);
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
          // Update both the workflow and Logical order
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

      const response = await fetch("http://localhost:5000/upload_workflow", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to upload workflow");
      }

      const data = await response.json();

      // Update the selected technologies with the jobs from the uploaded workflow
      setSelectedTechnologies(data.jobs);

      setStatus("Workflow uploaded successfully!");
      setTimeout(() => setStatus(""), 3000);
    } catch (error) {
      console.error("Upload error:", error);
      setStatus(`Error: ${error.message}`);
      setTimeout(() => setStatus(""), 3000);
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
        "http://localhost:5000/analyze_documentation",
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
    setTimeout(() => setStatus(null), 3000);
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
                  Click "Generate Logical order" to determine the best execution
                  sequence
                </span>
              </li>
              <li>
                <span className="step-number">4</span>
                <span className="step-text">
                  Personalize the workflow names to match your use case
                </span>
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
                  Generate Logical order, narrative, and talk track
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
                <span className="step-text">
                  Generate Logical order and personalize workflow names
                </span>
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
                  Upload documentation files (PDF, DOC, DOCX, TXT) for analysis
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
                  Generate Logical order, narrative, and talk track
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
      renamedTechnologies,
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
        "http://localhost:5000/check_template_exists",
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
      renamedTechnologies: renamedTechnologies,
      environment: deployConfig.environment,
      userCode: deployConfig.userCode,
      folderName: deployConfig.folderName,
      application: deployConfig.application,
      subApplication: deployConfig.subApplication,
    });

    try {
      const response = await fetch("http://localhost:5000/save_template", {
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
          renamedTechnologies: renamedTechnologies,
          environment: deployConfig.environment,
          userCode: deployConfig.userCode,
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
      renamedTechnologies,
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
          renamedTechnologies: renamedTechnologies,
          environment: deployConfig.environment,
          userCode: deployConfig.userCode,
          folderName: deployConfig.folderName,
          application: deployConfig.application,
          subApplication: deployConfig.subApplication,
        });

        // Close both modals immediately
        console.log("Closing modals...");
        setShowTemplateModal(false);
        setShowConfirmModal(false);

        // Update the existing template
        const response = await fetch("http://localhost:5000/update_template", {
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
            renamedTechnologies: renamedTechnologies,
            environment: deployConfig.environment,
            userCode: deployConfig.userCode,
            folderName: deployConfig.folderName,
            application: deployConfig.application,
            subApplication: deployConfig.subApplication,
          }),
        });

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
      const response = await fetch("http://localhost:5000/list_templates");
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
    setRenamedTechnologies(template.renamedTechnologies);
    setDeployConfig({
      environment: template.environment || "saas_dev",
      userCode: template.userCode || "LBA",
      folderName: template.folderName || "DEMGEN_VB",
      application: template.application || "DMO-GEN",
      subApplication: template.subApplication || "TEST-APP",
    });
    // Only clear analysis results and talk track, keep file upload capability
    setAnalysisResult(null);
    setTalkTrack("");
    setShowUseTemplateModal(false);
    setStatus("Template loaded successfully!");
  };

  const handleDeleteTemplate = async (templateId) => {
    try {
      const response = await fetch("http://localhost:5000/delete_template", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ templateId }),
      });

      if (!response.ok) {
        throw new Error("Failed to delete template");
      }

      // Remove the template from the local state
      setTemplates(
        templates.filter((template) => template.templateId !== templateId)
      );
      setStatus("Template deleted successfully");
    } catch (error) {
      console.error("Error deleting template:", error);
      setStatus("Error deleting template: " + error.message);
    }
  };

  const filteredTemplates = selectedCategory
    ? templates.filter((template) => template.category === selectedCategory)
    : templates;

  const handleGithubUpload = async () => {
    if (!selectedTechnologies.length) {
      setStatus("Please select technologies first.");
      setTimeout(() => setStatus(""), 3000);
      return;
    }

    try {
      setStatus("Creating workflow...");

      // First, create the workflow
      const createResponse = await fetch(
        "http://localhost:5000/create_workflow",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            technologies: selectedTechnologies,
            use_case: useCase,
            renamed_technologies: renamedTechnologies,
            optimal_order: optimalOrder || selectedTechnologies,
            environment: deployConfig.environment,
            user_code: githubConfig.userCode,
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
        "http://localhost:5000/upload-github",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            narrative_text: narrative,
            user_info: githubConfig.userCode,
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
      setTimeout(() => setStatus(""), 3000);
    } catch (error) {
      console.error("GitHub upload error:", error);
      setStatus(`Error: ${error.message}`);
      setTimeout(() => setStatus(""), 3000);
    }
  };

  const generateAIWorkflow = async () => {
    if (!useCase.trim()) {
      setStatus("Please enter a use case first.");
      setTimeout(() => setStatus(""), 3000);
      return;
    }

    try {
      setIsGeneratingAIWorkflow(true);
      setStatus("🤖 Generating AI workflow...");

      const response = await fetch("http://localhost:5000/ai_prompt_workflow", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          use_case: useCase,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to generate AI workflow");
      }

      const data = await response.json();
      setAiResponseContent(data.response_content);
      setStatus(
        "✅ AI workflow generated successfully! Review and deploy when ready."
      );
      setTimeout(() => setStatus(""), 5000);
    } catch (error) {
      console.error("AI workflow generation error:", error);
      setStatus(`❌ Error: ${error.message}`);
      setTimeout(() => setStatus(""), 3000);
    } finally {
      setIsGeneratingAIWorkflow(false);
    }
  };

  const regenerateAIWorkflow = async () => {
    if (!useCase.trim()) {
      setStatus("Please enter a use case first.");
      setTimeout(() => setStatus(""), 3000);
      return;
    }

    try {
      setIsGeneratingAIWorkflow(true);
      setStatus("🔄 Regenerating AI workflow...");

      // Clear the deployment status when regenerating
      setAiWorkflowData(null);

      const response = await fetch("http://localhost:5000/ai_prompt_workflow", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          use_case: useCase,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to regenerate AI workflow");
      }

      const data = await response.json();
      setAiResponseContent(data.response_content);
      setStatus("✅ AI workflow regenerated successfully!");
      setTimeout(() => setStatus(""), 3000);
    } catch (error) {
      console.error("AI workflow regeneration error:", error);
      setStatus(`❌ Error: ${error.message}`);
      setTimeout(() => setStatus(""), 3000);
    } finally {
      setIsGeneratingAIWorkflow(false);
    }
  };

  const deployAIWorkflow = async () => {
    if (!aiResponseContent) {
      setStatus("Please generate an AI workflow first.");
      setTimeout(() => setStatus(""), 3000);
      return;
    }

    try {
      setIsDeployingAIWorkflow(true);
      setStatus("🚀 Deploying AI workflow...");

      const response = await fetch("http://localhost:5000/deploy_ai_workflow", {
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
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to deploy AI workflow");
      }

      const data = await response.json();
      setAiWorkflowData(data);
      setStatus("✅ AI workflow deployed successfully!");
      setTimeout(() => setStatus(""), 3000);
    } catch (error) {
      console.error("AI workflow deployment error:", error);
      setStatus(`❌ Error: ${error.message}`);
      setTimeout(() => setStatus(""), 3000);
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

  return (
    <div className="app-container">
      <div className="content-container">
        {/* LEFT: Title + Use Case + Grid */}
        <div className="left-column">
          <h1>Demonstration Generator</h1>

          <div className="workflow-type-selector">
            <button
              className={`workflow-type-button ${
                workflowType === "new" ? "active" : ""
              }`}
              onClick={() => handleWorkflowTypeChange("new")}
            >
              Create New
            </button>
            <button
              className={`workflow-type-button ${
                workflowType === "templates" ? "active" : ""
              }`}
              onClick={() => handleWorkflowTypeChange("templates")}
            >
              Use Templates
            </button>
            <button
              className={`workflow-type-button ${
                workflowType === "upload" ? "active" : ""
              }`}
              onClick={() => handleWorkflowTypeChange("upload")}
            >
              Upload Existing
            </button>
            <button
              className={`workflow-type-button ${
                workflowType === "ai" ? "active" : ""
              }`}
              onClick={() => handleWorkflowTypeChange("ai")}
            >
              Ask AI
            </button>
            <button
              className={`workflow-type-button ${
                workflowType === "documentation" ? "active" : ""
              }`}
              onClick={() => handleWorkflowTypeChange("documentation")}
            >
              Documentation Analysis
            </button>
          </div>

          {showInstructions && renderInstructions()}

          <div className="use-case-section">
            <h3>Start Your Workflow</h3>
            <div className="use-case-options">
              <div className="option-card new-use-case">
                <h4>Enter New Use Case</h4>
                <p>Describe your specific workflow requirements</p>
                <div className="user-code-input">
                  <label htmlFor="user-code">User Code:</label>
                  <input
                    type="text"
                    id="user-code"
                    value={userCode}
                    onChange={(e) => setUserCode(e.target.value)}
                    placeholder="Enter user code (e.g., LBA)"
                    maxLength="10"
                  />
                </div>
                <textarea
                  value={useCase}
                  onChange={(e) => setUseCase(e.target.value)}
                  placeholder="Describe your use case..."
                  rows="3"
                />
                <div className="ai-workflow-buttons">
                  <button
                    className="action-button ai-generate-button"
                    onClick={generateAIWorkflow}
                    disabled={!useCase.trim() || isGeneratingAIWorkflow}
                  >
                    {isGeneratingAIWorkflow
                      ? "🤖 Generating..."
                      : "Ask AI to Generate Workflow"}
                  </button>
                  {aiResponseContent && (
                    <button
                      className="action-button ai-regenerate-button"
                      onClick={regenerateAIWorkflow}
                      disabled={!useCase.trim() || isGeneratingAIWorkflow}
                    >
                      {isGeneratingAIWorkflow
                        ? "🔄 Regenerating..."
                        : "Regenerate"}
                    </button>
                  )}
                </div>
                {aiResponseContent && (
                  <div className="ai-workflow-status">
                    <h5>✅ AI Workflow Generated</h5>
                    <p>
                      AI has generated a workflow based on your use case. You
                      can now deploy it in the "Deploy or Export" section.
                    </p>
                  </div>
                )}
                <div className="documentation-upload">
                  <h5>Upload Documentation (Optional)</h5>
                  <p>
                    Upload additional documentation to enhance use case analysis
                  </p>
                  <div className="upload-controls">
                    <input
                      type="file"
                      onChange={handleDocumentationUpload}
                      accept=".txt,.doc,.docx,.pdf"
                      id="documentation-upload"
                      style={{ display: "none" }}
                    />
                    <label
                      htmlFor="documentation-upload"
                      className="upload-button"
                    >
                      Choose File
                    </label>
                    {documentationFile && (
                      <span className="file-name">
                        {documentationFile.name}
                      </span>
                    )}
                    <button
                      className="action-button"
                      onClick={analyzeDocumentation}
                      disabled={!documentationFile}
                    >
                      Analyze Documentation
                    </button>
                  </div>
                </div>
                {analysisResult && (
                  <div className="analysis-result">
                    <h5>Analysis Summary</h5>
                    <p>{analysisResult.analysis_summary}</p>
                  </div>
                )}
              </div>
              <div className="option-card template-option">
                <h4>Use Existing Template</h4>
                <p>Start from a pre-configured workflow template</p>
                <button
                  className="action-button template-button"
                  onClick={handleUseTemplate}
                >
                  Browse Templates
                </button>
              </div>
            </div>
          </div>

          <div className="technology-selection">
            <h3>Select your technologies</h3>
            <div className="technology-selection-header">
              <div className="technology-category-filter">
                <select
                  value={selectedTechCategory}
                  onChange={(e) => setSelectedTechCategory(e.target.value)}
                  className="category-select"
                >
                  <option value="">All Categories</option>
                  {techCategories.map((category) => (
                    <option key={category.name} value={category.name}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>
              <button
                className="action-button"
                onClick={generateProposedWorkflow}
                disabled={!useCase}
              >
                Ask AI for Technology Suggestions
              </button>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".json"
                style={{ display: "none" }}
              />
              <button
                className="action-button"
                onClick={() => fileInputRef.current?.click()}
              >
                Upload Workflow JSON
              </button>
            </div>
            <TechnologyGrid
              selectedIcons={selectedTechnologies}
              onToggle={toggleTechnologyInWorkflow}
              selectedCategory={selectedTechCategory}
            />
          </div>
        </div>

        {/* RIGHT: Selected Techs + Logical order + Narrative */}
        <div className="right-column">
          <div className="workflow-actions">
            <div className="workflow-menu">
              {/* Workflow Management Section */}
              <div className="menu-section">
                <h4 className="menu-title">Manage Workflow</h4>
                <div className="menu-buttons">
                  <button
                    className="action-button"
                    onClick={generateOptimalOrder}
                    disabled={!selectedTechnologies.length || !useCase}
                  >
                    Generate Logical Order
                  </button>
                  <button
                    className="action-button"
                    onClick={handlePersonalizeUseCase}
                    disabled={!selectedTechnologies.length || !useCase}
                  >
                    Personalize Workflow Names
                  </button>
                </div>
              </div>

              {/* Deployment Section */}
              <div className="menu-section">
                <h4 className="menu-title">Deploy or Export</h4>
                <div className="menu-buttons">
                  <button
                    className="action-button"
                    onClick={handleDownloadWorkflow}
                    disabled={!selectedTechnologies.length || !useCase}
                  >
                    Download Workflow JSON
                  </button>
                  <button
                    className="action-button"
                    onClick={handleDeployPersonalizedWorkflow}
                    disabled={
                      !selectedTechnologies.length ||
                      !useCase ||
                      !renamedTechnologies
                    }
                  >
                    Deploy Workflow to Control-M
                  </button>
                  <button
                    className="action-button"
                    onClick={() => setShowGithubModal(true)}
                    disabled={
                      !selectedTechnologies.length || !useCase || !narrative
                    }
                  >
                    Upload to GitHub
                  </button>
                  <button
                    className="action-button"
                    onClick={() => {
                      setShowTemplateModal(true);
                    }}
                    disabled={!selectedTechnologies.length || !useCase}
                  >
                    Save as Template
                  </button>
                  <button
                    className="action-button ai-deploy-button"
                    onClick={deployAIWorkflow}
                    disabled={!aiResponseContent || isDeployingAIWorkflow}
                  >
                    {isDeployingAIWorkflow
                      ? "🚀 Deploying..."
                      : "Deploy AI Workflow"}
                  </button>
                </div>
              </div>

              {/* Documentation Section */}
              <div className="menu-section">
                <h4 className="menu-title">Documentation</h4>
                <div className="menu-buttons">
                  <button
                    className="action-button"
                    onClick={generateNarrative}
                    disabled={!selectedTechnologies.length || !useCase}
                  >
                    Generate Documentation
                  </button>
                  <button
                    className="action-button"
                    onClick={generateTalkTrack}
                    disabled={!selectedTechnologies.length || !useCase}
                  >
                    Generate Talk Track
                  </button>
                </div>
              </div>
            </div>
          </div>
          {status && <p className="status-message">{status}</p>}

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
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleTechnologyInWorkflow(tech);
                        }}
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
                <h3>Logical Order based on Use Case:</h3>
                <ol className="ordered-list">
                  {optimalOrder.map((tech, index) =>
                    renderWorkflowItem(tech, index)
                  )}
                </ol>
              </div>
            )}

            {aiResponseContent && (
              <div className="ai-workflow-display">
                <h3>🤖 AI Generated Workflow</h3>
                {/* Deployment Status - Moved before AI workflow */}
                {aiWorkflowData && (
                  <div className="ai-deployment-status">
                    <h4>✅ Deployment Status</h4>
                    <div className="deployment-details">
                      <p>
                        <strong>Folder:</strong> {aiWorkflowData.folder_name}
                      </p>
                      <p>
                        <strong>Environment:</strong>{" "}
                        {aiWorkflowData.environment}
                      </p>
                      <p>
                        <strong>Control-M Server:</strong>{" "}
                        {aiWorkflowData.controlm_server}
                      </p>
                      <p>
                        <strong>Status:</strong>{" "}
                        {aiWorkflowData.workflow?.name
                          ? "Successfully deployed"
                          : "Deployment failed"}
                      </p>
                    </div>
                  </div>
                )}
                {(() => {
                  const parsedWorkflow = parseAIWorkflow(aiResponseContent);
                  if (!parsedWorkflow.isValid) {
                    return (
                      <div className="ai-workflow-error">
                        <p>
                          ❌ Error parsing AI workflow: {parsedWorkflow.error}
                        </p>
                      </div>
                    );
                  }

                  return (
                    <div className="ai-workflow-content">
                      {/* Subfolders Section */}

                      {/* Jobs Section */}
                      {parsedWorkflow.jobs.length > 0 && (
                        <div className="ai-jobs">
                          <h4>
                            Workflow Jobs ({parsedWorkflow.jobs.length} total)
                          </h4>
                          <div className="jobs-by-subfolder">
                            {parsedWorkflow.subfolders.map(
                              (subfolder, subfolderIndex) => {
                                // Filter jobs for this subfolder
                                const subfolderJobs =
                                  parsedWorkflow.jobs.filter(
                                    (job) => job.subfolder === subfolder.name
                                  );

                                if (subfolderJobs.length === 0) return null;

                                return (
                                  <div
                                    key={subfolderIndex}
                                    className="subfolder-jobs"
                                  >
                                    <div className="subfolder-jobs-header">
                                      <div className="subfolder-jobs-info">
                                        <span className="subfolder-jobs-title">
                                          📁 {subfolder.name} (
                                          {subfolderJobs.length} jobs)
                                        </span>
                                        {subfolder.description && (
                                          <span className="subfolder-jobs-description">
                                            {subfolder.description}
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                    <div className="subfolder-jobs-list">
                                      {subfolderJobs.map((job, jobIndex) => (
                                        <div
                                          key={job.id}
                                          className="ai-workflow-job"
                                        >
                                          <div className="job-header">
                                            <span className="job-number">
                                              {jobIndex + 1}
                                            </span>
                                            <span className="job-name">
                                              {job.name}
                                            </span>
                                            <span className="job-type">
                                              {job.type}
                                            </span>
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                );
                              }
                            )}

                            {/* Show jobs that don't belong to any subfolder */}
                            {(() => {
                              const orphanJobs = parsedWorkflow.jobs.filter(
                                (job) =>
                                  !parsedWorkflow.subfolders.some(
                                    (subfolder) =>
                                      subfolder.name === job.subfolder
                                  )
                              );

                              if (orphanJobs.length === 0) return null;

                              return (
                                <div className="subfolder-jobs">
                                  <div className="subfolder-jobs-header">
                                    <span className="subfolder-jobs-title">
                                      📁 Main Folder ({orphanJobs.length} jobs)
                                    </span>
                                  </div>
                                  <div className="subfolder-jobs-list">
                                    {orphanJobs.map((job, jobIndex) => (
                                      <div
                                        key={job.id}
                                        className="ai-workflow-job"
                                      >
                                        <div className="job-header">
                                          <span className="job-number">
                                            {jobIndex + 1}
                                          </span>
                                          <span className="job-name">
                                            {job.name}
                                          </span>
                                          <span className="job-type">
                                            {job.type}
                                          </span>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              );
                            })()}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>
            )}
          </div>

          {narrative && (
            <div className="narrative-display">
              <div dangerouslySetInnerHTML={{ __html: marked(narrative) }} />
            </div>
          )}

          {talkTrack && (
            <div className="talk-track-display">
              <div dangerouslySetInnerHTML={{ __html: marked(talkTrack) }} />
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
                    // Update Control-M server based on environment
                    controlm_server: e.target.value.startsWith("saas")
                      ? "IN01"
                      : e.target.value === "vse_dev"
                      ? "DEV"
                      : e.target.value === "vse_qa"
                      ? "QA"
                      : e.target.value === "vse_prod"
                      ? "PROD"
                      : "IN01",
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
              <label>Control-M Server:</label>
              <select
                value={deployConfig.controlm_server}
                onChange={(e) =>
                  setDeployConfig((prev) => ({
                    ...prev,
                    controlm_server: e.target.value,
                  }))
                }
              >
                <option value="IN01">IN01</option>
                <option value="DEV">DEV</option>
                <option value="QA">QA</option>
                <option value="PROD">PROD</option>
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
                placeholder="Enter user code (LBA)"
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
                placeholder="Enter folder name (DEMGEN_VB)"
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

      {/* Template Save Modal */}
      {showTemplateModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Save as Template</h2>
            <div className="modal-form">
              <div className="form-group">
                <label>Template Name:</label>
                <input
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  placeholder="Enter template name"
                />
              </div>
              <div className="form-group">
                <label>Category:</label>
                <select
                  value={templateCategory}
                  onChange={(e) => setTemplateCategory(e.target.value)}
                >
                  <option value="">Select a category</option>
                  {templateCategories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>
              <div className="modal-actions">
                <button onClick={() => setShowTemplateModal(false)}>
                  Cancel
                </button>
                <button onClick={handleSaveAsTemplate}>Save Template</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Template Already Exists</h2>
            <p>
              A template with this name and category already exists. What would
              you like to do?
            </p>
            <div className="modal-actions">
              <button
                onClick={() => {
                  console.log("Update button clicked");
                  handleConfirmAction("update");
                }}
              >
                Update Existing Template
              </button>
              <button
                onClick={() => {
                  console.log("New button clicked");
                  handleConfirmAction("new");
                }}
              >
                Create New Template
              </button>
              <button
                onClick={() => {
                  console.log("Cancel button clicked");
                  setShowConfirmModal(false);
                  setConfirmAction(null);
                  setExistingTemplateId(null);
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Use Template Modal */}
      {showUseTemplateModal && (
        <div className="modal-overlay">
          <div className="modal-content template-modal">
            <h3>Select a Template</h3>
            <div className="template-categories">
              <button
                className={`category-button ${
                  !selectedCategory ? "active" : ""
                }`}
                onClick={() => setSelectedCategory("")}
              >
                All Categories
              </button>
              {templateCategories.map((category) => (
                <button
                  key={category}
                  className={`category-button ${
                    selectedCategory === category ? "active" : ""
                  }`}
                  onClick={() => setSelectedCategory(category)}
                >
                  {category}
                </button>
              ))}
            </div>
            <div className="template-list">
              {filteredTemplates.length > 0 ? (
                filteredTemplates.map((template) => (
                  <div key={template.templateId} className="template-card">
                    <h4>{template.name}</h4>
                    <p className="template-category">{template.category}</p>
                    <p className="template-description">
                      {template.description}
                    </p>
                    <div className="template-technologies">
                      <strong>Technologies:</strong>
                      <div className="tech-tags">
                        {template.technologies.map((tech) => (
                          <span key={tech} className="tech-tag">
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                    <button
                      className="action-button"
                      onClick={() => handleLoadTemplate(template)}
                    >
                      Use This Template
                    </button>
                    <button
                      className="action-button placeholder-button"
                      onClick={() => handleDeleteTemplate(template.templateId)}
                    >
                      Delete Template
                    </button>
                  </div>
                ))
              ) : (
                <p className="no-templates">
                  No templates found in this category
                </p>
              )}
            </div>
            <div className="modal-actions">
              <button
                className="action-button"
                onClick={() => setShowUseTemplateModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* GitHub Upload Modal */}
      {showGithubModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Upload to GitHub</h2>
            <div className="modal-form">
              <div className="form-group">
                <label>User Code:</label>
                <input
                  type="text"
                  value={githubConfig.userCode}
                  onChange={(e) =>
                    setGithubConfig((prev) => ({
                      ...prev,
                      userCode: e.target.value,
                    }))
                  }
                  placeholder="Enter your user code"
                />
              </div>
              <div className="form-group">
                <label>Repository:</label>
                <input
                  type="text"
                  value={githubConfig.repository}
                  onChange={(e) =>
                    setGithubConfig((prev) => ({
                      ...prev,
                      repository: e.target.value,
                    }))
                  }
                  placeholder="owner/repository"
                />
              </div>
              <div className="form-group">
                <label>Branch:</label>
                <input
                  type="text"
                  value={githubConfig.branch}
                  onChange={(e) =>
                    setGithubConfig((prev) => ({
                      ...prev,
                      branch: e.target.value,
                    }))
                  }
                  placeholder="main"
                />
              </div>
              <div className="form-group">
                <label>Path:</label>
                <input
                  type="text"
                  value={githubConfig.path}
                  onChange={(e) =>
                    setGithubConfig((prev) => ({
                      ...prev,
                      path: e.target.value,
                    }))
                  }
                  placeholder="path/to/workflow.json"
                />
              </div>
              <div className="form-group">
                <label>Commit Message:</label>
                <input
                  type="text"
                  value={githubConfig.commitMessage}
                  onChange={(e) =>
                    setGithubConfig((prev) => ({
                      ...prev,
                      commitMessage: e.target.value,
                    }))
                  }
                  placeholder="Update workflow configuration"
                />
              </div>
              <div className="modal-actions">
                <button onClick={() => setShowGithubModal(false)}>
                  Cancel
                </button>
                <button onClick={handleGithubUpload}>Upload</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
