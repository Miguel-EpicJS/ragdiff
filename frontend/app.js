const exampleRequest = {
  report_id: "report-demo",
  k: 10,
  dataset: {
    schema_version: 1,
    dataset_id: "dataset-demo",
    version: "v1",
    queries: [{ query_id: "q-1", relevant_ids: ["chunk-a"] }]
  },
  baseline: {
    schema_version: 1,
    run_id: "run-baseline",
    dataset_id: "dataset-demo",
    dataset_version: "v1",
    pipeline_version: "old",
    queries: [{ query_id: "q-1", items: [{ item_id: "chunk-a", rank: 1 }] }]
  },
  candidate: {
    schema_version: 1,
    run_id: "run-candidate",
    dataset_id: "dataset-demo",
    dataset_version: "v1",
    pipeline_version: "new",
    queries: [{ query_id: "q-1", items: [{ item_id: "other", rank: 1 }] }]
  }
};

document.querySelector("#request").value = JSON.stringify(exampleRequest, null, 2);

const form = document.querySelector("#comparison-form");
const error = document.querySelector("#error");
const report = document.querySelector("#report");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  error.hidden = true;
  try {
    const response = await fetch("/v1/comparisons", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${document.querySelector("#token").value}`
      },
      body: document.querySelector("#request").value
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error?.message ?? "Comparison failed");
    renderReport(body);
  } catch (requestError) {
    error.textContent = requestError.message;
    error.hidden = false;
  }
});

function renderReport(body) {
  const comparison = body.result.comparison;
  const summary = comparison.summary;
  document.querySelector("#decision").textContent = body.deployment_status.toUpperCase();
  document.querySelector("#report-id").textContent = body.report_id;
  document.querySelector("#summary").innerHTML = Object.entries(summary)
    .map(([label, value]) => `<div><strong>${value}</strong><span>${label}</span></div>`)
    .join("");
  document.querySelector("#details").textContent = JSON.stringify(comparison, null, 2);
  report.hidden = false;
}
