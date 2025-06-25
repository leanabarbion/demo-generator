import React from "react";
import { marked } from "marked";
import "../AIWorkflowView.css";

const AIWorkflowView = ({
  useCase,
  setUseCase,
  userCode,
  setUserCode,
  aiResponseContent,
  isGeneratingAIWorkflow,
  isDeployingAIWorkflow,
  aiWorkflowData,
  deployConfig,
  setDeployConfig,
  showDeployModal,
  setShowDeployModal,
  generateAIWorkflow,
  regenerateAIWorkflow,
  deployAIWorkflow,
  handlePersonalizedDeployConfirm,
  status,
  parseAIWorkflow,
}) => {
  return (
    <div className="ai-workflow-view">
      <div className="page-header">
        <h1>DemoGen AI</h1>
        <p className="page-subtitle">Let AI generate a workflow for you</p>
      </div>

      <div className="use-case-section">
        <h2>Start Your AI Workflow</h2>
        <div className="use-case-options">
          <div className="option-card new-use-case">
            <h4>Enter Your Use Case</h4>
            <p>
              Describe your specific workflow requirements and let AI generate
              the complete workflow
            </p>
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
                  ? "Generating..."
                  : "Ask AI to Generate Workflow"}
              </button>
              {aiResponseContent && (
                <button
                  className="action-button ai-regenerate-button"
                  onClick={regenerateAIWorkflow}
                  disabled={!useCase.trim() || isGeneratingAIWorkflow}
                >
                  {isGeneratingAIWorkflow ? "🔄 Regenerating..." : "Regenerate"}
                </button>
              )}
              {aiResponseContent && (
                <button
                  className="action-button ai-deploy-button"
                  onClick={deployAIWorkflow}
                  disabled={!aiResponseContent || isDeployingAIWorkflow}
                >
                  {isDeployingAIWorkflow
                    ? "🚀 Deploying..."
                    : "Deploy AI Workflow"}
                </button>
              )}
            </div>
            {/* {aiResponseContent && (
              <div className="ai-workflow-status">
                <h5>AI Workflow Generated</h5>
                <p>
                  AI has generated a workflow based on your use case. You can
                  now deploy it using the button above.
                </p>
              </div>
            )} */}
          </div>
        </div>
      </div>

      {/* AI Workflow Display */}
      {aiResponseContent && (
        <div className="ai-workflow-display">
          <h3> AI Generated Workflow</h3>
          {/* Deployment Status */}
          {aiWorkflowData && (
            <div className="ai-deployment-status">
              <h4>✅ Deployment Status</h4>
              <div className="deployment-details">
                <p>
                  <strong>Folder:</strong> {aiWorkflowData.folder_name}
                </p>
                <p>
                  <strong>Environment:</strong> {aiWorkflowData.environment}
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
                  <p>Error parsing AI workflow: {parsedWorkflow.error}</p>
                </div>
              );
            }

            return (
              <div className="ai-workflow-content">
                {/* Jobs Section */}
                {parsedWorkflow.jobs.length > 0 && (
                  <div className="ai-jobs">
                    <h4>Workflow Jobs ({parsedWorkflow.jobs.length} total)</h4>
                    <div className="jobs-by-subfolder">
                      {parsedWorkflow.subfolders.map(
                        (subfolder, subfolderIndex) => {
                          // Filter jobs for this subfolder
                          const subfolderJobs = parsedWorkflow.jobs.filter(
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
                                    📁 {subfolder.name} ({subfolderJobs.length}{" "}
                                    jobs)
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
                                    <span className="job-name">{job.name}</span>
                                    <span className="job-type">{job.type}</span>
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

      {/* Status Message */}
      {status && <p className="status-message">{status}</p>}
    </div>
  );
};

export default AIWorkflowView;
