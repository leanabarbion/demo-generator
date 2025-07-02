import React from "react";
import TechnologyGrid from "../TechnologyGrid";
import { marked } from "marked";
import { JOB_LIBRARY } from "../jobLibrary";
import techCategories from "../categories";
import "../ManualWorkflowView.css";

const ManualWorkflowView = ({
  useCase,
  setUseCase,
  userCode,
  setUserCode,
  selectedTechnologies,
  setSelectedTechnologies,
  optimalOrder,
  setOptimalOrder,
  complexWorkflow,
  setComplexWorkflow,
  narrative,
  setNarrative,
  talkTrack,
  setTalkTrack,
  proposedWorkflow,
  setProposedWorkflow,
  selectedTechCategory,
  setSelectedTechCategory,
  deployConfig,
  setDeployConfig,
  showDeployModal,
  setShowDeployModal,
  showTemplateModal,
  setShowTemplateModal,
  showUseTemplateModal,
  setShowUseTemplateModal,
  showGithubModal,
  setShowGithubModal,
  templates,
  setTemplates,
  selectedCategory,
  setSelectedCategory,
  templateName,
  setTemplateName,
  templateCategory,
  setTemplateCategory,
  showConfirmModal,
  setShowConfirmModal,
  existingTemplateId,
  setExistingTemplateId,
  confirmAction,
  setConfirmAction,
  githubConfig,
  setGithubConfig,
  documentationFile,
  setDocumentationFile,
  analysisResult,
  setAnalysisResult,
  fileInputRef,
  status,
  setStatus,
  workflowType,
  showInstructions,
  setShowInstructions,
  documentationSkipped,
  setDocumentationSkipped,
  // Functions
  toggleTechnologyInWorkflow,
  generateManualWorkflow,
  generateNarrative,
  generateTalkTrack,
  generateProposedWorkflow,
  handleFileUpload,
  handleDocumentationUpload,
  analyzeDocumentation,
  handleDeployPersonalizedWorkflow,
  handlePersonalizedDeployConfirm,
  handleDownloadWorkflow,
  handleSaveAsTemplate,
  saveTemplate,
  handleConfirmAction,
  handleUseTemplate,
  handleLoadTemplate,
  handleDeleteTemplate,
  handleGithubUpload,
  handleWorkflowTypeChange,
  renderInstructions,
  renderWorkflowItem,
  templateCategories,
  onBackToSelector,
  restartWorkflow,
}) => {
  const filteredTechnologies = selectedTechnologies.filter((tech) =>
    selectedTechCategory === ""
      ? true
      : techCategories
          .find((cat) => cat.name === selectedTechCategory)
          ?.technologies.some((t) => t.name === tech)
  );

  const filteredTemplates = selectedCategory
    ? templates.filter((template) => template.category === selectedCategory)
    : templates;

  // Check if user has started the workflow (selected technologies or asked for AI suggestions)
  const hasStartedWorkflow =
    selectedTechnologies.length > 0 || proposedWorkflow;

  // Check if technologies are selected but no workflow has been generated yet
  const technologiesSelectedButNoWorkflow =
    selectedTechnologies.length > 0 && !complexWorkflow;

  // Check if workflow is generated but no documentation has been created
  const workflowGeneratedButNoDocumentation =
    complexWorkflow && !narrative && !talkTrack && !documentationSkipped;

  // Check if documentation is generated but not deployed
  const documentationGeneratedButNotDeployed =
    complexWorkflow && (narrative || talkTrack) && !deployConfig;

  // Check if workflow is ready for deployment (with or without documentation)
  const workflowReadyForDeployment =
    complexWorkflow && !workflowGeneratedButNoDocumentation; // Show deployment step when workflow is generated and documentation step is completed

  // Debug logging
  console.log("ManualWorkflowView Debug:", {
    complexWorkflow: !!complexWorkflow,
    selectedTechnologies: selectedTechnologies.length,
    hasStartedWorkflow,
    technologiesSelectedButNoWorkflow,
    workflowGeneratedButNoDocumentation,
    workflowReadyForDeployment,
    narrative: !!narrative,
    talkTrack: !!talkTrack,
    deployConfig,
    "Step 1 (techs selected)": technologiesSelectedButNoWorkflow,
    "Step 2 (doc generation)": workflowGeneratedButNoDocumentation,
    "Step 3 (deployment)": workflowReadyForDeployment,
    "Fallback (complete)":
      !technologiesSelectedButNoWorkflow &&
      !workflowGeneratedButNoDocumentation &&
      !workflowReadyForDeployment,
  });

  // State to control workflow actions visibility
  const [showWorkflowActions, setShowWorkflowActions] = React.useState(false);

  // State to control modal visibility
  const [showNarrativeModal, setShowNarrativeModal] = React.useState(false);
  const [showTalkTrackModal, setShowTalkTrackModal] = React.useState(false);

  // Utility: check if two arrays have the same elements in the same order
  const isCurrentSelectionAISuggested = React.useMemo(() => {
    // If there's a proposed workflow, consider it AI-suggested even if modified
    if (proposedWorkflow?.technologies && selectedTechnologies.length > 0) {
      return true;
    }
    return false;
  }, [proposedWorkflow, selectedTechnologies]);

  // Utility: determine which technologies were originally AI-suggested
  const getAISuggestedTechnologies = React.useMemo(() => {
    if (proposedWorkflow?.technologies) {
      return new Set(proposedWorkflow.technologies);
    }
    return new Set();
  }, [proposedWorkflow]);

  // Utility: check if a specific technology was AI-suggested
  const isTechnologyAISuggested = (tech) => {
    return getAISuggestedTechnologies.has(tech);
  };

  return (
    <div className="manual-workflow-view">
      <div className="page-header">
        <div className="header-content">
          <button
            className="back-button"
            onClick={onBackToSelector}
            title="Back to view selector"
          >
            ← Back to Selector
          </button>
          <div className="header-text">
            <h1>DemoGen AI</h1>
            <p className="page-subtitle">
              Build your workflow with AI guidance and expert control
            </p>
          </div>
          <div className="header-actions">
            <button
              className="workflow-actions-toggle"
              onClick={() => setShowWorkflowActions(!showWorkflowActions)}
              title={
                showWorkflowActions
                  ? "Hide Workflow Actions"
                  : "Show Workflow Actions"
              }
            >
              <span className="toggle-icon">Open for Full Menu</span>
              <span
                className={`toggle-arrow ${
                  showWorkflowActions ? "expanded" : ""
                }`}
              >
                ▼
              </span>
            </button>
            <button
              className="restart-button"
              onClick={restartWorkflow}
              title="Restart workflow"
            >
              ↻ Restart
            </button>
          </div>
        </div>
      </div>

      <div
        className={`content-container ${
          hasStartedWorkflow ? "with-right-column" : "full-width"
        }`}
      >
        {/* LEFT: Title + Use Case + Grid */}
        <div
          className={`left-column ${
            hasStartedWorkflow ? "with-right-column" : "full-width"
          }`}
        >
          {/* <div className="workflow-type-selector">
            <div className="workflow-type-header">
              <div className="header-content">
                <h3>Choose Your Workflow Type</h3>
                <p>Select how you want to start building your workflow</p>
              </div>
              <div className="workflow-type-buttons">
                <button
                  className={`workflow-type-button ${
                    workflowType === "new" ? "active" : ""
                  }`}
                  onClick={() => handleWorkflowTypeChange("new")}
                >
                  <span className="button-icon">✨</span>
                  <span className="button-text">Create New</span>
                </button>
                <button
                  className={`workflow-type-button ${
                    workflowType === "templates" ? "active" : ""
                  }`}
                  onClick={() => handleWorkflowTypeChange("templates")}
                >
                  <span className="button-icon">📋</span>
                  <span className="button-text">Use Templates</span>
                </button>
                <button
                  className={`workflow-type-button ${
                    workflowType === "upload" ? "active" : ""
                  }`}
                  onClick={() => handleWorkflowTypeChange("upload")}
                >
                  <span className="button-icon">📤</span>
                  <span className="button-text">Upload Existing</span>
                </button>
                <button
                  className={`workflow-type-button ${
                    workflowType === "documentation" ? "active" : ""
                  }`}
                  onClick={() => handleWorkflowTypeChange("documentation")}
                >
                  <span className="button-icon">📄</span>
                  <span className="button-text">Documentation Analysis</span>
                </button>
              </div>
            </div>
          </div> */}

          {/* {showInstructions && renderInstructions()} */}

          <div className="use-case-section">
            <div className="section-header">
              <h3>Start Your Workflow</h3>
              <p>Define your use case and requirements</p>
            </div>
            <div className="use-case-options">
              <div className="option-card new-use-case">
                <div className="card-header">
                  <div className="card-icon"></div>
                  <h4>Enter New Use Case</h4>
                </div>
                <p className="card-description">
                  Describe your specific workflow requirements by mentioning how
                  many jobs you want to generate
                </p>
                <div className="input-group">
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
                  <div className="use-case-input">
                    <label htmlFor="use-case">Use Case Description:</label>
                    <textarea
                      id="use-case"
                      value={useCase}
                      onChange={(e) => setUseCase(e.target.value)}
                      placeholder="Describe your use case..."
                      rows="3"
                    />
                  </div>
                </div>
              </div>
              <div className="option-card template-option">
                <div className="card-header">
                  <h4>Use Existing Template</h4>
                </div>
                <p className="card-description">
                  Start from a pre-configured workflow template
                </p>
                <button
                  className="action-button template-button"
                  onClick={handleUseTemplate}
                >
                  Browse Templates
                </button>
                <div className="documentation-upload">
                  <div className="upload-header">
                    <h5>Upload Documentation (Optional)</h5>
                    <p>
                      Upload additional documentation to enhance use case
                      analysis
                    </p>
                  </div>
                  <div className="upload-controls">
                    <input
                      type="file"
                      onChange={handleDocumentationUpload}
                      accept=".txt,.doc,.docx,.pdf,.xlsx,.xls"
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
                      <div className="file-info">
                        <span className="file-name">
                          {documentationFile.name}
                        </span>
                      </div>
                    )}
                    <button
                      className="action-button analyze-button"
                      onClick={analyzeDocumentation}
                      disabled={!documentationFile}
                    >
                      Analyze Documentation
                    </button>
                  </div>
                </div>
                {analysisResult && (
                  <div className="analysis-result">
                    <div className="result-header">
                      <h5>Analysis Summary</h5>
                    </div>
                    <p>{analysisResult.analysis_summary}</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="technology-selection">
            <div className="section-header">
              <h3>Select Your Technologies</h3>
              <p>
                Choose the technologies that best fit your workflow requirements
              </p>
            </div>
            <div className="technology-selection-header">
              <div className="selection-controls">
                <div className="technology-category-filter">
                  <label htmlFor="category-select">Filter by Category:</label>
                  <select
                    id="category-select"
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
                <div className="action-controls">
                  <button
                    className="action-button ai-suggest-button"
                    onClick={generateProposedWorkflow}
                    disabled={!useCase}
                  >
                    <span className="button-icon"></span>
                    Ask AI for Suggestions
                  </button>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept=".json"
                    style={{ display: "none" }}
                  />
                  {/* <button
                    className="action-button upload-button"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <span className="button-icon">📤</span>
                    Upload Workflow JSON
                  </button> */}
                </div>
              </div>
            </div>
            <TechnologyGrid
              selectedIcons={selectedTechnologies}
              onToggle={toggleTechnologyInWorkflow}
              selectedCategory={selectedTechCategory}
            />
          </div>
        </div>

        {/* RIGHT: Selected Techs + Logical order + Narrative */}
        {hasStartedWorkflow && (
          <div className="right-column">
            {/* Always Visible Next Step Guide */}
            <div
              className={`next-step-section ${
                technologiesSelectedButNoWorkflow
                  ? ""
                  : workflowGeneratedButNoDocumentation
                  ? "documentation-step"
                  : workflowReadyForDeployment
                  ? "deployment-step"
                  : ""
              }`}
            >
              <div className="next-step-header">
                <div
                  className={`step-indicator ${
                    technologiesSelectedButNoWorkflow ? "" : "completed"
                  }`}
                >
                  <span className="step-number">
                    {technologiesSelectedButNoWorkflow ? "1" : "✓"}
                  </span>
                  <span className="step-label">Technologies Selected</span>
                </div>
                <div className="step-arrow">→</div>
                <div
                  className={`step-indicator ${
                    technologiesSelectedButNoWorkflow
                      ? "current"
                      : workflowGeneratedButNoDocumentation
                      ? "completed"
                      : "completed"
                  }`}
                >
                  <span className="step-number">
                    {technologiesSelectedButNoWorkflow ? "2" : "✓"}
                  </span>
                  <span className="step-label">Generate Workflow</span>
                </div>
                <div className="step-arrow">→</div>
                <div
                  className={`step-indicator ${
                    technologiesSelectedButNoWorkflow
                      ? ""
                      : workflowGeneratedButNoDocumentation
                      ? "current"
                      : "completed"
                  }`}
                >
                  <span className="step-number">
                    {technologiesSelectedButNoWorkflow
                      ? "3"
                      : workflowGeneratedButNoDocumentation
                      ? "3"
                      : "✓"}
                  </span>
                  <span className="step-label">Documentation</span>
                </div>
                <div className="step-arrow">→</div>
                <div
                  className={`step-indicator ${
                    technologiesSelectedButNoWorkflow
                      ? ""
                      : workflowGeneratedButNoDocumentation
                      ? ""
                      : "current"
                  }`}
                >
                  <span className="step-number">
                    {technologiesSelectedButNoWorkflow
                      ? "4"
                      : workflowGeneratedButNoDocumentation
                      ? "4"
                      : "4"}
                  </span>
                  <span className="step-label">Deploy</span>
                </div>
              </div>

              <div className="next-step-content">
                {/* Step 1: Technologies Selected - Generate Workflow */}
                {technologiesSelectedButNoWorkflow && (
                  <>
                    <h3>Next Step: Generate Your Workflow</h3>
                    <p>
                      You've selected {selectedTechnologies.length} technology
                      {selectedTechnologies.length !== 1 ? "ies" : "y"}. Now
                      let's create an optimized workflow structure with logical
                      job dependencies.
                    </p>
                    <button
                      className="action-button optimize-button next-step-button"
                      onClick={generateManualWorkflow}
                      disabled={!selectedTechnologies.length || !useCase}
                    >
                      Generate Workflow
                    </button>
                  </>
                )}

                {/* Step 2: Workflow Generated - Generate Documentation */}
                {workflowGeneratedButNoDocumentation && (
                  <>
                    <h3>Next Step: Generate Documentation</h3>
                    <p>
                      Your workflow has been created! Now let's generate
                      professional documentation and presentation materials.
                    </p>
                    <div className="next-step-buttons">
                      <button
                        className="action-button narrative-button next-step-button"
                        onClick={generateNarrative}
                        disabled={!selectedTechnologies.length || !useCase}
                      >
                        Generate Documentation
                      </button>
                      <button
                        className="action-button talktrack-button next-step-button"
                        onClick={generateTalkTrack}
                        disabled={!selectedTechnologies.length || !useCase}
                      >
                        Generate Talk Track
                      </button>
                      <button
                        className="action-button skip-button"
                        onClick={() => {
                          setStatus(
                            "Documentation generation skipped. You can generate it later from the menu."
                          );
                          // Mark documentation as skipped to advance to deployment step
                          setDocumentationSkipped(true);
                        }}
                      >
                        Skip for Now
                      </button>
                    </div>
                  </>
                )}

                {/* Step 3: Ready for Deployment */}
                {workflowReadyForDeployment && (
                  <>
                    <h3>Next Step: Deploy or Export Your Workflow</h3>
                    <p>
                      Your workflow and documentation are ready! Choose how
                      you'd like to deploy or export your workflow.
                    </p>
                    <div className="next-step-buttons">
                      <button
                        className="action-button deploy-button next-step-button"
                        onClick={handleDeployPersonalizedWorkflow}
                        disabled={
                          !selectedTechnologies.length ||
                          !useCase ||
                          !complexWorkflow
                        }
                      >
                        Deploy to Control-M
                      </button>
                      <button
                        className="action-button download-button next-step-button"
                        onClick={handleDownloadWorkflow}
                        disabled={!selectedTechnologies.length || !useCase}
                      >
                        Download Workflow JSON
                      </button>
                      <button
                        className="action-button github-button next-step-button"
                        onClick={() => setShowGithubModal(true)}
                        disabled={
                          !selectedTechnologies.length || !useCase || !narrative
                        }
                      >
                        Upload to GitHub
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Workflow Actions - Conditionally Visible */}
            {showWorkflowActions && (
              <div className="workflow-actions">
                <div className="workflow-menu">
                  {/* Workflow Management Section */}
                  <div className="menu-section">
                    <div className="section-header">
                      <h4 className="menu-title">Manage Workflow</h4>
                      <p>Optimize and customize your workflow</p>
                    </div>
                    <div className="menu-buttons">
                      <button
                        className={`action-button optimize-button ${
                          technologiesSelectedButNoWorkflow
                            ? "next-step-highlight"
                            : ""
                        }`}
                        onClick={generateManualWorkflow}
                        disabled={!selectedTechnologies.length || !useCase}
                      >
                        {technologiesSelectedButNoWorkflow}
                        Generate Workflow
                      </button>
                    </div>
                  </div>

                  {/* Documentation Section */}
                  <div className="menu-section">
                    <div className="section-header">
                      <h4 className="menu-title">Documentation</h4>
                      <p>Generate documentation and talk track</p>
                    </div>
                    <div className="menu-buttons">
                      <button
                        className={`action-button narrative-button ${
                          workflowGeneratedButNoDocumentation
                            ? "next-step-highlight"
                            : ""
                        }`}
                        onClick={generateNarrative}
                        disabled={!selectedTechnologies.length || !useCase}
                      >
                        {workflowGeneratedButNoDocumentation}
                        Generate Documentation
                      </button>
                      <button
                        className={`action-button talktrack-button ${
                          workflowGeneratedButNoDocumentation
                            ? "next-step-highlight"
                            : ""
                        }`}
                        onClick={generateTalkTrack}
                        disabled={!selectedTechnologies.length || !useCase}
                      >
                        {workflowGeneratedButNoDocumentation}
                        Generate Talk Track
                      </button>
                    </div>
                  </div>

                  {/* Deployment Section */}
                  <div className="menu-section">
                    <div className="section-header">
                      <h4 className="menu-title">Deploy or Export</h4>
                      <p>Deploy to Control-M or export your workflow</p>
                    </div>
                    <div className="menu-buttons">
                      <button
                        className={`action-button download-button ${
                          workflowReadyForDeployment
                            ? "next-step-highlight"
                            : ""
                        }`}
                        onClick={handleDownloadWorkflow}
                        disabled={!selectedTechnologies.length || !useCase}
                      >
                        {workflowReadyForDeployment}
                        Download Workflow JSON
                      </button>
                      <button
                        className={`action-button deploy-button ${
                          workflowReadyForDeployment
                            ? "next-step-highlight"
                            : ""
                        }`}
                        onClick={handleDeployPersonalizedWorkflow}
                        disabled={
                          !selectedTechnologies.length ||
                          !useCase ||
                          !complexWorkflow
                        }
                      >
                        {workflowReadyForDeployment}
                        Deploy to Control-M
                      </button>
                      <button
                        className={`action-button github-button ${
                          workflowReadyForDeployment
                            ? "next-step-highlight"
                            : ""
                        }`}
                        onClick={() => setShowGithubModal(true)}
                        disabled={
                          !selectedTechnologies.length || !useCase || !narrative
                        }
                      >
                        {workflowReadyForDeployment}
                        Upload to GitHub
                      </button>
                      <button
                        className="action-button template-button"
                        onClick={() => {
                          setShowTemplateModal(true);
                        }}
                        disabled={!selectedTechnologies.length || !useCase}
                      >
                        Save as Template
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {status && <p className="status-message">{status}</p>}

            <div className="workflow-container">
              {complexWorkflow && (
                <>
                  {/* Selected Technologies - Horizontal Display */}
                  {selectedTechnologies.length > 0 && (
                    <div className="selected-technologies-horizontal">
                      <h3>
                        Selected Technologies ({selectedTechnologies.length})
                      </h3>
                      <div className="tech-chips">
                        {selectedTechnologies.map((tech, index) => (
                          <div
                            key={tech}
                            className={`tech-chip ${
                              isTechnologyAISuggested(tech)
                                ? "ai-suggested"
                                : ""
                            }`}
                            title={JOB_LIBRARY[tech]?.description || tech}
                          >
                            <span className="tech-name">{tech}</span>
                            <button
                              className="remove-tech"
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleTechnologyInWorkflow(tech);
                              }}
                              title="Remove technology"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                      {isCurrentSelectionAISuggested && (
                        <div className="ai-suggestion-note">
                          <span className="ai-badge">AI</span>
                          <span>
                            {getAISuggestedTechnologies.size > 0 &&
                            selectedTechnologies.length >
                              getAISuggestedTechnologies.size
                              ? `AI-suggested technologies are highlighted. ${
                                  selectedTechnologies.length -
                                  getAISuggestedTechnologies.size
                                } manually added.`
                              : "AI-suggested technologies are highlighted"}
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {(narrative || talkTrack) && (
                    <div className="documentation-sidebar">
                      <div className="documentation-row">
                        {narrative && (
                          <div
                            className="documentation-compact clickable-narrative"
                            onClick={() => setShowNarrativeModal(true)}
                            style={{ cursor: "pointer" }}
                          >
                            <div className="documentation-compact-header">
                              <h4>📄 Documentation</h4>
                              <span className="documentation-compact-hint">
                                Click to expand
                              </span>
                            </div>
                            <div className="documentation-compact-preview">
                              <div
                                dangerouslySetInnerHTML={{
                                  __html: marked(
                                    narrative.substring(0, 300) +
                                      (narrative.length > 300 ? "..." : "")
                                  ),
                                }}
                              />
                            </div>
                          </div>
                        )}

                        {talkTrack && (
                          <div
                            className="documentation-compact clickable-talktrack"
                            onClick={() => setShowTalkTrackModal(true)}
                            style={{ cursor: "pointer" }}
                          >
                            <div className="documentation-compact-header">
                              <h4>🎤 Talk Track</h4>
                              <span className="documentation-compact-hint">
                                Click to expand
                              </span>
                            </div>
                            <div className="documentation-compact-preview">
                              <div
                                dangerouslySetInnerHTML={{
                                  __html: marked(
                                    talkTrack.substring(0, 300) +
                                      (talkTrack.length > 300 ? "..." : "")
                                  ),
                                }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Complex Workflow Structure */}
                  <div className="complex-workflow">
                    <h3>Complex Workflow Structure</h3>
                    <div className="workflow-folder">
                      <h4>📁 {complexWorkflow.folder_name}</h4>
                      <div className="jobs-by-subfolder">
                        {complexWorkflow.subfolders.map(
                          (subfolder, subfolderIndex) => {
                            // Filter jobs for this subfolder
                            const subfolderJobs = complexWorkflow.jobs.filter(
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
                                      📂 {subfolder.name} (
                                      {subfolderJobs.length} jobs)
                                    </span>
                                    {subfolder.description && (
                                      <span className="subfolder-jobs-description">
                                        {subfolder.description}
                                      </span>
                                    )}
                                    <span className="subfolder-jobs-phase">
                                      Phase {subfolder.phase}
                                    </span>
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
                          const orphanJobs = complexWorkflow.jobs.filter(
                            (job) =>
                              !complexWorkflow.subfolders.some(
                                (subfolder) => subfolder.name === job.subfolder
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
                                  <div key={job.id} className="ai-workflow-job">
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
                                    <div className="job-details">
                                      <span className="job-group">
                                        Group: {job.concurrent_group}
                                      </span>
                                      {job.wait_for_jobs &&
                                        job.wait_for_jobs.length > 0 && (
                                          <span className="job-dependencies">
                                            Waits:{" "}
                                            {job.wait_for_jobs.join(", ")}
                                          </span>
                                        )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Fallback: Show selected technologies horizontally when no complex workflow */}
              {!complexWorkflow && selectedTechnologies.length > 0 && (
                <div className="selected-technologies-horizontal">
                  <h3>Selected Technologies ({selectedTechnologies.length})</h3>
                  <div className="tech-chips">
                    {selectedTechnologies.map((tech, index) => (
                      <div
                        key={tech}
                        className={`tech-chip ${
                          isTechnologyAISuggested(tech) ? "ai-suggested" : ""
                        }`}
                        title={JOB_LIBRARY[tech]?.description || tech}
                      >
                        <span className="tech-name">{tech}</span>
                        <button
                          className="remove-tech"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleTechnologyInWorkflow(tech);
                          }}
                          title="Remove technology"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                  {isCurrentSelectionAISuggested && (
                    <div className="ai-suggestion-note">
                      <span className="ai-badge">AI</span>
                      <span>
                        {getAISuggestedTechnologies.size > 0 &&
                        selectedTechnologies.length >
                          getAISuggestedTechnologies.size
                          ? `AI-suggested technologies are highlighted. ${
                              selectedTechnologies.length -
                              getAISuggestedTechnologies.size
                            } manually added.`
                          : "AI-suggested technologies are highlighted"}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
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
            {/* <div className="form-group">
              <label>User Code:</label>
              <input
                type="text"
                value={userCode}
                onChange={(e) => setUserCode(e.target.value)}
                placeholder="Enter user code (LBA)"
              />
            </div> */}
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
                    <div className="template-actions">
                      <button
                        className="action-button"
                        onClick={() => handleLoadTemplate(template)}
                      >
                        Use This Template
                      </button>
                      <button
                        className="action-button placeholder-button"
                        onClick={() =>
                          handleDeleteTemplate(template.templateId)
                        }
                      >
                        Delete Template
                      </button>
                    </div>
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
                  value={userCode}
                  onChange={(e) => setUserCode(e.target.value)}
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
              <div className="modal-buttons">
                <button onClick={() => setShowGithubModal(false)}>
                  Cancel
                </button>
                <button onClick={handleGithubUpload}>Upload</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Narrative Modal */}
      {showNarrativeModal && (
        <div
          className="modal-overlay narrative-modal-overlay"
          onClick={() => setShowNarrativeModal(false)}
        >
          <div
            className="modal-content narrative-modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h2>📄 Generated Documentation</h2>
              <button
                className="modal-close-button"
                onClick={() => setShowNarrativeModal(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body narrative-modal-body">
              <div className="narrative-full-content">
                <div dangerouslySetInnerHTML={{ __html: marked(narrative) }} />
              </div>
            </div>
            <div className="modal-footer">
              <button
                className="action-button"
                onClick={() => setShowNarrativeModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Talk Track Modal */}
      {showTalkTrackModal && (
        <div
          className="modal-overlay talktrack-modal-overlay"
          onClick={() => setShowTalkTrackModal(false)}
        >
          <div
            className="modal-content talktrack-modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h2>🎤 Generated Talk Track</h2>
              <button
                className="modal-close-button"
                onClick={() => setShowTalkTrackModal(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body talktrack-modal-body">
              <div className="talktrack-full-content">
                <div dangerouslySetInnerHTML={{ __html: marked(talkTrack) }} />
              </div>
            </div>
            <div className="modal-footer">
              <button
                className="action-button"
                onClick={() => setShowTalkTrackModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManualWorkflowView;
