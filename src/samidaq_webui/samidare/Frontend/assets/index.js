let currentBoardStatus = null;
let lastFileSizeBytes = null;
let lastFileTimestamp = null;
let lastMonitorPath = null;

let isApplyingRemotePageInfo = false;
let lastLocalEditAt = 0;
let lastRemoteSavedAt = null;

const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:8000/api/samidare`;
const API_URL = `${API_BASE_URL}/run`;
const STATUS_URL = `${API_BASE_URL}/status`;
const INITIAL_PARAM_URL = `${STATUS_URL}/initial-param`;
const CURRENT_PAGEINFO_URL = `${STATUS_URL}/current-pageinfo`;
const DATA_NAME_URL = `${STATUS_URL}/data-name`;
const DATA_NAME_INCREMENT_URL = `${STATUS_URL}/data-name/increment`;

function markLocalEdit() {
  lastLocalEditAt = Date.now();
}

function updateCurrentTime() {
  const now = new Date();

  const text = now.toLocaleString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  document.getElementById("currentTime").textContent = text;
}

async function runFunction(functionName, params = {}, options = {}) {
  const {
    showResponse = true,
    refreshStatus = true,
  } = options;

  const payload = {
    function: functionName,
    params: params,
  };

  const responseBox = document.getElementById("response");

  if (showResponse) {
    responseBox.textContent = "Running...";
  }

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (showResponse) {
      responseBox.textContent = JSON.stringify(data, null, 2);
    }

    if (!res.ok) {
      throw new Error(data.message || "Request failed");
    }

    if (
      refreshStatus &&
      functionName !== "get_status" &&
      functionName !== "get_file_info"
    ) {
      getStatus();
    }

    return data;
  } catch (err) {
    if (showResponse) {
      responseBox.textContent = `ERROR: ${err.message}`;
    }
    throw err;
  }
}

async function getStatus() {
  try {
    const data = await runFunction("get_status", {}, {
      showResponse: false,
      refreshStatus: false,
    });

    const boardStatus = data?.command_result?.board_status;

    if (boardStatus) {
      currentBoardStatus = boardStatus;
      renderStatus(boardStatus);
    }
  } catch (err) {
    const table = document.getElementById("statusTable");
    table.innerHTML = `<tr><td colspan="2">Status update failed: ${escapeHtml(err.message)}</td></tr>`;
  }
}

function renderStatus(status) {
  const table = document.getElementById("statusTable");

  const rows = [
    ["IP Address", status.ip_address],
    ["Connected", status.connected ? "Yes" : "No"],
    ["Power", status.power],
    ["Trigger Type", status.trigger_type],
    ["Trigger Threshold", status.trigger_threshold],
    ["Polarity", status.polarity],
    ["Gain", status.gain],
    ["Shaping", status.shaping],
    ["Samples", status.samples],
    ["Pre Samples", status.pre_samples],
    ["External Clock", status.clock_type],
    ["Last Update", status.last_update],
    ["Output Directory", status.output_directory],
    ["Output Filename", status.output_filename],
    ["Acquisition", status.acquisition],
  ];

  table.innerHTML = rows
    .map(([key, value]) => {
      const valueText = value ?? "";
      return `<tr><th>${escapeHtml(key)}</th><td>${escapeHtml(String(valueText))}</td></tr>`;
    })
    .join("");
}

function setTriggerType(options = {}) {
  const triggerType = document.getElementById("triggerType").value;
  markLocalEdit();

  return runFunction("set_trigger_type", {
    trigger_type: triggerType,
  }, options);
}

function setTriggerThreshold(options = {}) {
  const threshold = Number(document.getElementById("triggerThreshold").value);
  markLocalEdit();

  return runFunction("set_trigger_threshold", {
    threshold: threshold,
  }, options);
}

function setPolarity(options = {}) {
  const polarity = document.getElementById("polarity").value;
  markLocalEdit();

  return runFunction("set_polarity", {
    polarity: polarity,
  }, options);
}

function setGain(options = {}) {
  const gain = Number(document.getElementById("gain").value);
  markLocalEdit();

  return runFunction("set_gain", {
    gain: gain,
  }, options);
}

function setSamples(options = {}) {
  const samples = Number(document.getElementById("samples").value);
  markLocalEdit();

  return runFunction("set_samples", {
    samples: samples,
  }, options);
}

function setPreSamples(options = {}) {
  const preSamples = Number(document.getElementById("preSamples").value);
  markLocalEdit();

  return runFunction("set_pre_samples", {
    pre_samples: preSamples,
  }, options);
}

function setExternalClk(options = {}) {
  const enabled = document.getElementById("externalClk").value === "true";
  markLocalEdit();

  return runFunction("set_external_clk", {
    enabled: enabled,
  }, options);
}

function setOutputDir(options = {}) {
  const outputDir = document.getElementById("outputDir").value.trim();
  markLocalEdit();

  if (!outputDir) {
    document.getElementById("response").textContent = "ERROR: output directory is empty";
    return Promise.reject(new Error("output directory is empty"));
  }

  return runFunction("set_output_dir", {
    output_dir: outputDir,
  }, options);
}

function setOutputFile(options = {}) {
  const outputFile = document.getElementById("outputFile").value.trim();
  markLocalEdit();

  if (!outputFile) {
    document.getElementById("response").textContent = "ERROR: output file is empty";
    return Promise.reject(new Error("output file is empty"));
  }

  return runFunction("set_output_file", {
    output_file: outputFile,
  }, options);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function sendCustomCommand() {
  const command = document.getElementById("customCommand").value.trim();
  markLocalEdit();

  if (!command) {
    const responseBox = document.getElementById("response");
    responseBox.textContent = "ERROR: command is empty";
    return;
  }

  return runFunction("send_command", {
    request: {
      command: command,
    },
  });
}

async function setAll() {
  const options = {
    showResponse: false,
    refreshStatus: false,
  };

  const steps = [
    ["Trigger Type", () => setTriggerType(options)],
    ["Trigger Threshold", () => setTriggerThreshold(options)],
    ["Polarity", () => setPolarity(options)],
    ["Gain", () => setGain(options)],
    ["Samples", () => setSamples(options)],
    ["Pre Samples", () => setPreSamples(options)],
    ["External Clock", () => setExternalClk(options)],
    ["Output Directory", () => setOutputDir(options)],
    ["Output Filename", () => setOutputFile(options)],
  ];

  const results = [];

  for (const [name, fn] of steps) {
    try {
      const result = await fn();
      results.push({ name, ok: true, result });
    } catch (err) {
      results.push({ name, ok: false, error: err.message });
    }
  }

  await getStatus();

  document.getElementById("response").textContent = JSON.stringify(
    {
      message: "Set All finished",
      results,
    },
    null,
    2
  );
}

async function startDaq() {
  const headerComment = document.getElementById("headerComment").value.trim();
  const incrementMode = document.getElementById("dataNameIncrementMode").checked;

  markLocalEdit();

  if (incrementMode) {
    const outputFile = buildIncrementOutputFile();

    document.getElementById("outputFile").value = outputFile;

    await runFunction(
      "set_output_file",
      {
        output_file: outputFile,
      },
      {
        showResponse: false,
        refreshStatus: false,
      }
    );

    await updateDataNameStateFromPage();
  }

  await runFunction("start_daq", {
    header_comment: headerComment,
  });

  await getStatus();
}

async function stopDaq() {
  const enderComment = document.getElementById("enderComment").value.trim();
  const incrementMode = document.getElementById("dataNameIncrementMode").checked;

  markLocalEdit();

  await runFunction("stop_daq", {
    ender_comment: enderComment,
  });

  if (incrementMode) {
    await incrementRunNumber();
  }

  await getStatus();
}

async function updateOutputFileMonitor() {
  if (!currentBoardStatus) {
    document.getElementById("fileMonitorPath").textContent = "No board status yet";
    document.getElementById("fileMonitorExists").textContent = "--";
    document.getElementById("fileMonitorSize").textContent = "--";
    document.getElementById("fileMonitorIncrease").textContent = "--";
    return;
  }

  const outputDir = currentBoardStatus.output_directory;
  const outputFile = currentBoardStatus.output_filename;

  if (!outputDir || !outputFile) {
    document.getElementById("fileMonitorPath").textContent = "Output path is not available";
    document.getElementById("fileMonitorExists").textContent = "--";
    document.getElementById("fileMonitorSize").textContent = "--";
    document.getElementById("fileMonitorIncrease").textContent = "--";
    return;
  }

  const inferredPath = `${outputDir}/${outputFile}.bin`;

  try {
    const data = await runFunction(
      "get_file_info",
      {
        path: inferredPath,
      },
      {
        showResponse: false,
        refreshStatus: false,
      }
    );

    const info = data?.command_result;

    if (!info) {
      return;
    }

    const sizeBytes = info.size_bytes;
    const timestamp = info.timestamp;

    if (lastMonitorPath !== info.path) {
      lastFileSizeBytes = null;
      lastFileTimestamp = null;
      lastMonitorPath = info.path;
    }

    let increaseText = "--";

    if (lastFileSizeBytes !== null && lastFileTimestamp !== null) {
      const diffBytes = sizeBytes - lastFileSizeBytes;
      const diffSec = timestamp - lastFileTimestamp;

      if (diffSec > 0) {
        const bytesPerSec = diffBytes / diffSec;
        increaseText = `${formatBytes(bytesPerSec)}/s`;
      }
    }

    lastFileSizeBytes = sizeBytes;
    lastFileTimestamp = timestamp;

    document.getElementById("fileMonitorPath").textContent = info.path;
    document.getElementById("fileMonitorExists").textContent = info.exists ? "Yes" : "No";
    document.getElementById("fileMonitorSize").textContent = formatBytes(sizeBytes);
    document.getElementById("fileMonitorIncrease").textContent = increaseText;
  } catch (err) {
    document.getElementById("fileMonitorExists").textContent = "Error";
    document.getElementById("fileMonitorIncrease").textContent = err.message;
  }
}

function formatBytes(bytes) {
  if (bytes < 1024) {
    return `${bytes.toFixed(0)} B`;
  }

  const kb = bytes / 1024;
  if (kb < 1024) {
    return `${kb.toFixed(2)} KB`;
  }

  const mb = kb / 1024;
  if (mb < 1024) {
    return `${mb.toFixed(2)} MB`;
  }

  const gb = mb / 1024;
  return `${gb.toFixed(2)} GB`;
}

async function loadInitialParams() {
  try {
    const res = await fetch(INITIAL_PARAM_URL, {
      cache: "no-store",
    });

    if (!res.ok) {
      throw new Error(`Failed to load initial params: ${res.status}`);
    }

    const data = await res.json();
    const params = data.params;

    if (!params) {
      throw new Error("Initial params not found in response");
    }

    applyInitialParams(params);

    document.getElementById("response").textContent = JSON.stringify(
      {
        message: "Loaded initial parameters",
        params_path: data.params_path,
        params: params,
      },
      null,
      2
    );
  } catch (err) {
    console.warn("Could not load initial params:", err);

    document.getElementById("response").textContent = JSON.stringify(
      {
        message: "Could not load initial parameters. Using HTML defaults.",
        error: err.message,
      },
      null,
      2
    );
  }
}

function applyInitialParams(params) {
  setElementValue("triggerType", params.trigger_type);
  setElementValue("triggerThreshold", params.trigger_threshold);
  setElementValue("polarity", params.polarity);
  setElementValue("gain", params.gain);
  setElementValue("samples", params.samples);
  setElementValue("preSamples", params.pre_samples);
  setElementValue("externalClk", params.external_clk);
  setElementValue("outputDir", params.output_dir);
  setElementValue("outputFile", params.output_file);
  setElementValue("customCommand", params.custom_command);
  setElementValue("headerComment", params.header_comment);
  setElementValue("enderComment", params.ender_comment);
}

function setElementValue(id, value) {
  if (value === undefined || value === null) {
    return;
  }

  const element = document.getElementById(id);

  if (!element) {
    return;
  }

  if (element.type === "checkbox") {
    element.checked = Boolean(value);
  } else if (element.tagName === "SELECT") {
    element.value = String(value);
  } else {
    element.value = value;
  }
}

function collectCurrentPageInfo() {
  return {
    timestamp: new Date().toISOString(),

    parameters: {
      trigger_type: document.getElementById("triggerType").value,
      trigger_threshold: Number(document.getElementById("triggerThreshold").value),
      polarity: document.getElementById("polarity").value,
      gain: Number(document.getElementById("gain").value),
      samples: Number(document.getElementById("samples").value),
      pre_samples: Number(document.getElementById("preSamples").value),
      external_clk: document.getElementById("externalClk").value === "true",
      output_dir: document.getElementById("outputDir").value,
      output_file: document.getElementById("outputFile").value,
    },

    data_name_increment: {
      enabled: document.getElementById("dataNameIncrementMode").checked,
      run_name: document.getElementById("runName").value,
      run_number: Number(document.getElementById("runNumber").value),
      locked: document.getElementById("lockRunNameNumber").checked,
    },

    daq: {
      header_comment: document.getElementById("headerComment").value,
      ender_comment: document.getElementById("enderComment").value,
    },

    custom_command: {
      command: document.getElementById("customCommand").value,
    },

    board_status: currentBoardStatus,

    file_monitor: {
      path: document.getElementById("fileMonitorPath").textContent,
      exists: document.getElementById("fileMonitorExists").textContent,
      total_size: document.getElementById("fileMonitorSize").textContent,
      increase_per_sec: document.getElementById("fileMonitorIncrease").textContent,
      last_size_bytes: lastFileSizeBytes,
      last_timestamp: lastFileTimestamp,
      last_monitor_path: lastMonitorPath,
    },
  };
}

async function postCurrentPageInfo() {
  if (isApplyingRemotePageInfo) {
    return;
  }

  try {
    await fetch(CURRENT_PAGEINFO_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(collectCurrentPageInfo()),
    });
  } catch (err) {
    console.warn("Could not post current page info:", err);
  }
}

async function loadCurrentPageInfo() {
  try {
    const res = await fetch(CURRENT_PAGEINFO_URL, {
      cache: "no-store",
    });

    if (!res.ok) {
      throw new Error(`Failed to load current page info: ${res.status}`);
    }

    const data = await res.json();
    const pageInfo = data.current_pageinfo;

    if (!pageInfo) {
      return;
    }

    const now = Date.now();

    if (now - lastLocalEditAt < 1500) {
      return;
    }

    if (data.saved_at && data.saved_at === lastRemoteSavedAt) {
      return;
    }

    lastRemoteSavedAt = data.saved_at ?? null;

    applyCurrentPageInfo(pageInfo);
  } catch (err) {
    console.warn("Could not load current page info:", err);
  }
}

function applyCurrentPageInfo(pageInfo) {
  if (!pageInfo) {
    return;
  }

  isApplyingRemotePageInfo = true;

  try {
    const params = pageInfo.parameters ?? {};

    setElementValue("triggerType", params.trigger_type);
    setElementValue("triggerThreshold", params.trigger_threshold);
    setElementValue("polarity", params.polarity);
    setElementValue("gain", params.gain);
    setElementValue("samples", params.samples);
    setElementValue("preSamples", params.pre_samples);
    setElementValue("externalClk", params.external_clk);
    setElementValue("outputDir", params.output_dir);
    setElementValue("outputFile", params.output_file);

    const dataName = pageInfo.data_name_increment ?? {};

    if (dataName.enabled !== undefined) {
      document.getElementById("dataNameIncrementMode").checked = Boolean(dataName.enabled);
    }

    setElementValue("runName", dataName.run_name);
    setElementValue("runNumber", dataName.run_number);

    if (dataName.locked !== undefined) {
      document.getElementById("lockRunNameNumber").checked = Boolean(dataName.locked);
      updateRunNameNumberLock();
    }

    const daq = pageInfo.daq ?? {};
    setElementValue("headerComment", daq.header_comment);
    setElementValue("enderComment", daq.ender_comment);

    const customCommand = pageInfo.custom_command ?? {};
    setElementValue("customCommand", customCommand.command);

    if (pageInfo.board_status) {
      currentBoardStatus = pageInfo.board_status;
      renderStatus(currentBoardStatus);
    }

    const fileMonitor = pageInfo.file_monitor ?? {};

    if (fileMonitor.path !== undefined) {
      document.getElementById("fileMonitorPath").textContent = fileMonitor.path;
    }

    if (fileMonitor.exists !== undefined) {
      document.getElementById("fileMonitorExists").textContent = fileMonitor.exists;
    }

    if (fileMonitor.total_size !== undefined) {
      document.getElementById("fileMonitorSize").textContent = fileMonitor.total_size;
    }

    if (fileMonitor.increase_per_sec !== undefined) {
      document.getElementById("fileMonitorIncrease").textContent = fileMonitor.increase_per_sec;
    }

    if (fileMonitor.last_size_bytes !== undefined) {
      lastFileSizeBytes = fileMonitor.last_size_bytes;
    }

    if (fileMonitor.last_timestamp !== undefined) {
      lastFileTimestamp = fileMonitor.last_timestamp;
    }

    if (fileMonitor.last_monitor_path !== undefined) {
      lastMonitorPath = fileMonitor.last_monitor_path;
    }
  } finally {
    isApplyingRemotePageInfo = false;
  }
}

async function loadDataNameState() {
  try {
    const res = await fetch(DATA_NAME_URL, {
      cache: "no-store",
    });

    if (!res.ok) {
      throw new Error(`Failed to load data name state: ${res.status}`);
    }

    const data = await res.json();
    const state = data.data_name_increment;

    applyDataNameState(state);
  } catch (err) {
    console.warn("Could not load data name state:", err);
  }
}

function applyDataNameState(state) {
  if (!state) {
    return;
  }

  document.getElementById("dataNameIncrementMode").checked = Boolean(state.enabled);
  document.getElementById("runName").value = state.run_name ?? "run";
  document.getElementById("runNumber").value = Number(state.run_number ?? 0);

  updateRunNameNumberLock();
}

async function updateDataNameStateFromPage() {
  if (isApplyingRemotePageInfo) {
    return;
  }

  markLocalEdit();

  const payload = {
    enabled: document.getElementById("dataNameIncrementMode").checked,
    run_name: document.getElementById("runName").value.trim(),
    run_number: Number(document.getElementById("runNumber").value),
  };

  try {
    const res = await fetch(DATA_NAME_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.message || "Failed to update data name state");
    }

    const data = await res.json();
    applyDataNameState(data.data_name_increment);
  } catch (err) {
    console.warn("Could not update data name state:", err);
  }
}

function updateRunNameNumberLock() {
  const locked = document.getElementById("lockRunNameNumber").checked;

  document.getElementById("runName").readOnly = locked;
  document.getElementById("runNumber").readOnly = locked;
}

function buildIncrementOutputFile() {
  const runName = document.getElementById("runName").value.trim();
  const runNumber = Number(document.getElementById("runNumber").value);

  if (!runName) {
    throw new Error("Run Name is empty");
  }

  return `${runName}${String(runNumber).padStart(4, "0")}`;
}

async function incrementRunNumber() {
  try {
    const res = await fetch(DATA_NAME_INCREMENT_URL, {
      method: "POST",
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.message || "Failed to increment run number");
    }

    const data = await res.json();
    applyDataNameState(data.data_name_increment);

    return data;
  } catch (err) {
    console.warn("Could not increment run number:", err);
    throw err;
  }
}

async function startSAMDaq() {
  await runFunction("start_samdaq");
  await getStatus();
}

async function restartSAMDaq() {
  await runFunction("quit_daq");
  await runFunction("start_samdaq");
  await getStatus();
}

async function initializePage() {
  await loadInitialParams();
  await loadDataNameState();
  await loadCurrentPageInfo();

  getStatus();
  updateCurrentTime();
  updateOutputFileMonitor();
  postCurrentPageInfo();

  setInterval(updateCurrentTime, 1000);
  setInterval(updateOutputFileMonitor, 1000);
  setInterval(postCurrentPageInfo, 1000);
  setInterval(loadCurrentPageInfo, 1000);
}

window.runFunction = runFunction;
window.setTriggerType = setTriggerType;
window.setTriggerThreshold = setTriggerThreshold;
window.setPolarity = setPolarity;
window.setGain = setGain;
window.setSamples = setSamples;
window.setPreSamples = setPreSamples;
window.setExternalClk = setExternalClk;
window.setOutputDir = setOutputDir;
window.setOutputFile = setOutputFile;
window.sendCustomCommand = sendCustomCommand;
window.setAll = setAll;
window.startDaq = startDaq;
window.stopDaq = stopDaq;
window.startSAMDaq = startSAMDaq;
window.restartSAMDaq = restartSAMDaq;
window.updateDataNameStateFromPage = updateDataNameStateFromPage;
window.updateRunNameNumberLock = updateRunNameNumberLock;
window.markLocalEdit = markLocalEdit;

initializePage();
