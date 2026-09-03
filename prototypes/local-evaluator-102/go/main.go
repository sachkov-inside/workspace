package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

const (
	evaluatorVersion = "0.1.0-prototype"
	caseSchema       = "inside.case-spec.v1"
	assignmentSchema = "inside.assignment.v1"
	reportSchema     = "inside.evaluation-report.v1"
)

type caseSpec struct {
	SchemaVersion  string        `json:"schemaVersion"`
	Case           caseIdentity  `json:"case"`
	Variants       []caseVariant `json:"variants"`
	PublicScenario struct {
		ID                   string `json:"id"`
		OrderAcceptanceMaxMS int    `json:"orderAcceptanceMaxMs"`
		PartnerResponses     []int  `json:"partnerResponses"`
		DeliveryDeadlineMS   int    `json:"deliveryDeadlineMs"`
	} `json:"publicScenario"`
	Integration         map[string]any `json:"integration"`
	ReliabilityEnvelope map[string]any `json:"reliabilityEnvelope"`
	LoadProfile         map[string]any `json:"loadProfile"`
}

type caseIdentity struct {
	ID      string `json:"id"`
	Version string `json:"version"`
	Title   string `json:"title,omitempty"`
}

type caseVariant struct {
	ID        string `json:"id"`
	Runtime   string `json:"runtime"`
	Framework string `json:"framework"`
	Database  string `json:"database"`
}

type assignment struct {
	SchemaVersion string `json:"schemaVersion"`
	ID            string `json:"id"`
	RepositoryID  string `json:"repositoryId"`
	RemoteURL     string `json:"remoteUrl"`
	CaseID        string `json:"caseId"`
	CaseVersion   string `json:"caseVersion"`
	VariantID     string `json:"variantId"`
}

type diagnostic struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

type scenarioResult struct {
	ID         string      `json:"id"`
	Status     string      `json:"status"`
	DurationMS int         `json:"durationMs"`
	Diagnostic *diagnostic `json:"diagnostic"`
}

type report struct {
	SchemaVersion string `json:"schemaVersion"`
	Case          struct {
		ID      string `json:"id"`
		Version string `json:"version"`
	} `json:"case"`
	VariantID string `json:"variantId"`
	Evaluator struct {
		ID       string `json:"id"`
		Version  string `json:"version"`
		Language string `json:"language"`
	} `json:"evaluator"`
	Assignment struct {
		ID           string `json:"id"`
		RepositoryID string `json:"repositoryId"`
	} `json:"assignment"`
	Source struct {
		CommitSHA string `json:"commitSha"`
	} `json:"source"`
	Execution struct {
		Method      string `json:"method"`
		StartedAt   string `json:"startedAt"`
		FinishedAt  string `json:"finishedAt"`
		Environment struct {
			OS            string `json:"os"`
			Arch          string `json:"arch"`
			DockerServer  string `json:"dockerServer"`
			DockerCompose string `json:"dockerCompose"`
		} `json:"environment"`
	} `json:"execution"`
	Scenarios []scenarioResult `json:"scenarios"`
	Verdict   string           `json:"verdict"`
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: evaluator <version|run>")
		os.Exit(2)
	}

	var err error
	switch os.Args[1] {
	case "version":
		fmt.Println(evaluatorVersion)
		return
	case "run":
		err = run(os.Args[2:])
	default:
		err = fmt.Errorf("unknown command %q", os.Args[1])
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run(args []string) error {
	flags := flag.NewFlagSet("run", flag.ContinueOnError)
	root := flags.String("prototype-root", "", "prototype directory")
	repositoryRoot := flags.String("repository-root", "", "assignment checkout")
	casePath := flags.String("case", "", "CaseSpec JSON")
	assignmentPath := flags.String("assignment", "", "assignment JSON")
	mode := flags.String("fixture-mode", "pass", "pass or bad-signature")
	output := flags.String("output", "", "report JSON")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if *root == "" || *repositoryRoot == "" || *casePath == "" || *assignmentPath == "" || *output == "" {
		return errors.New("prototype-root, repository-root, case, assignment, and output are required")
	}
	if *mode != "pass" && *mode != "bad-signature" {
		return fmt.Errorf("unsupported fixture mode %q", *mode)
	}

	var spec caseSpec
	if err := readStrictJSON(*casePath, &spec); err != nil {
		return fmt.Errorf("invalid CaseSpec: %w", err)
	}
	var assigned assignment
	if err := readStrictJSON(*assignmentPath, &assigned); err != nil {
		return fmt.Errorf("invalid assignment: %w", err)
	}
	if err := validateInputs(spec, assigned); err != nil {
		return err
	}

	started := time.Now().UTC()
	dockerServer, err := commandText(*root, "docker", "version", "--format", "{{.Server.Os}}/{{.Server.Arch}} {{.Server.Version}}")
	if err != nil {
		return fmt.Errorf("preflight docker server: %w", err)
	}
	dockerCompose, err := commandText(*root, "docker", "compose", "version", "--short")
	if err != nil {
		return fmt.Errorf("preflight docker compose: %w", err)
	}
	commitSHA, err := commandText(*repositoryRoot, "git", "rev-parse", "HEAD")
	if err != nil || !isSHA(commitSHA) {
		return fmt.Errorf("preflight git HEAD: expected a 40-character commit SHA")
	}
	remoteURL, err := commandText(*repositoryRoot, "git", "remote", "get-url", "origin")
	if err != nil {
		return fmt.Errorf("preflight git remote: %w", err)
	}
	if remoteURL != assigned.RemoteURL {
		return fmt.Errorf("preflight repository mismatch: expected %q, got %q", assigned.RemoteURL, remoteURL)
	}

	scenario, composeErr := runScenario(*root, *mode)
	result := report{SchemaVersion: reportSchema, VariantID: assigned.VariantID, Scenarios: []scenarioResult{scenario}}
	result.Case.ID = spec.Case.ID
	result.Case.Version = spec.Case.Version
	result.Evaluator.ID = "inside-local-evaluator"
	result.Evaluator.Version = evaluatorVersion
	result.Evaluator.Language = "go"
	result.Assignment.ID = assigned.ID
	result.Assignment.RepositoryID = assigned.RepositoryID
	result.Source.CommitSHA = commitSHA
	result.Execution.Method = "local"
	result.Execution.StartedAt = started.Format(time.RFC3339Nano)
	result.Execution.FinishedAt = time.Now().UTC().Format(time.RFC3339Nano)
	result.Execution.Environment.OS = runtime.GOOS
	result.Execution.Environment.Arch = runtime.GOARCH
	result.Execution.Environment.DockerServer = dockerServer
	result.Execution.Environment.DockerCompose = dockerCompose
	result.Verdict = scenario.Status

	if err := writeJSON(*output, result); err != nil {
		return err
	}
	fmt.Printf("%s: %s (%s) -> %s\n", scenario.ID, scenario.Status, result.Evaluator.Language, *output)
	if composeErr != nil || scenario.Status != "passed" {
		if scenario.Diagnostic != nil {
			return fmt.Errorf("scenario failed [%s]: %s", scenario.Diagnostic.Code, scenario.Diagnostic.Message)
		}
		return fmt.Errorf("scenario failed: %w", composeErr)
	}
	return nil
}

func validateInputs(spec caseSpec, assigned assignment) error {
	if spec.SchemaVersion != caseSchema {
		return fmt.Errorf("incompatible CaseSpec schema %q", spec.SchemaVersion)
	}
	if assigned.SchemaVersion != assignmentSchema {
		return fmt.Errorf("incompatible assignment schema %q", assigned.SchemaVersion)
	}
	if spec.Case.ID == "" || spec.Case.Version == "" || spec.PublicScenario.ID != "temporary-partner-failure" {
		return errors.New("CaseSpec is missing the prototype case or public scenario")
	}
	if assigned.CaseID != spec.Case.ID || assigned.CaseVersion != spec.Case.Version {
		return errors.New("assignment does not match the CaseSpec identity/version")
	}
	for _, variant := range spec.Variants {
		if variant.ID == assigned.VariantID {
			return nil
		}
	}
	return fmt.Errorf("assignment variant %q is not supported by the CaseSpec", assigned.VariantID)
}

func runScenario(root, mode string) (scenarioResult, error) {
	evidenceDir, err := os.MkdirTemp("", "inside-evaluator-evidence-")
	if err != nil {
		return scenarioResult{}, err
	}
	defer os.RemoveAll(evidenceDir)

	project := fmt.Sprintf("inside-eval-%d", time.Now().UnixNano())
	compose := []string{"compose", "-p", project, "-f", filepath.Join(root, "compose.yaml")}
	environment := append(os.Environ(), "EVIDENCE_DIR="+evidenceDir, "PROTOTYPE_FIXTURE_MODE="+mode)
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, "docker", append(compose, "up", "--build", "--abort-on-container-exit", "--exit-code-from", "scenario")...)
	command.Dir = root
	command.Env = environment
	composeErr := command.Run()

	downCtx, downCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer downCancel()
	down := exec.CommandContext(downCtx, "docker", append(compose, "down", "--volumes", "--remove-orphans", "--rmi", "local")...)
	down.Dir = root
	down.Env = environment
	_ = down.Run()

	var result scenarioResult
	if err := readStrictJSON(filepath.Join(evidenceDir, "scenario.json"), &result); err != nil {
		message := "Docker scenario exited without structured evidence; inspect local Compose logs"
		if ctx.Err() != nil {
			message = "Docker scenario exceeded 90 seconds"
		}
		result = scenarioResult{
			ID:         "temporary-partner-failure",
			Status:     "failed",
			Diagnostic: &diagnostic{Code: "scenario_runtime_failed", Message: message},
		}
	}
	return result, composeErr
}

func readStrictJSON(path string, destination any) error {
	contents, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	decoder := json.NewDecoder(bytes.NewReader(contents))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(destination); err != nil {
		return err
	}
	if decoder.More() {
		return errors.New("multiple JSON values")
	}
	return nil
}

func writeJSON(path string, value any) error {
	contents, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	contents = append(contents, '\n')
	if err := os.WriteFile(path, contents, 0o600); err != nil {
		return fmt.Errorf("write report: %w", err)
	}
	return nil
}

func commandText(directory, name string, args ...string) (string, error) {
	command := exec.Command(name, args...)
	command.Dir = directory
	output, err := command.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("%s: %s", err, strings.TrimSpace(string(output)))
	}
	return strings.TrimSpace(string(output)), nil
}

func isSHA(value string) bool {
	if len(value) != 40 {
		return false
	}
	for _, character := range value {
		if !strings.ContainsRune("0123456789abcdef", character) {
			return false
		}
	}
	return true
}
