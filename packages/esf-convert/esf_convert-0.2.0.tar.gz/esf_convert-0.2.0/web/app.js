// ESF Convert - Pyodide Integration

let pyodide = null;
let pyodideReady = false;

const fileInput = document.getElementById('xmlFile');
const formatSelect = document.getElementById('format');
const convertBtn = document.getElementById('convertBtn');
const status = document.getElementById('status');

// Initialize Pyodide
async function initPyodide() {
    setStatus('loading', '<span class="spinner"></span>Loading Python environment...');

    try {
        pyodide = await loadPyodide();

        setStatus('loading', '<span class="spinner"></span>Installing packages (this may take a moment)...');

        // Install required packages
        await pyodide.loadPackage('lxml');
        await pyodide.loadPackage('micropip');

        const micropip = pyodide.pyimport('micropip');

        // Install python-docx and esf-convert from PyPI
        await micropip.install('python-docx');
        await micropip.install('esf-convert');

        pyodideReady = true;
        updateButtonState();
        setStatus('success', 'Ready to convert files!');

        // Hide status after 2 seconds
        setTimeout(() => {
            status.style.display = 'none';
        }, 2000);

    } catch (error) {
        setStatus('error', 'Failed to load Python environment: ' + error.message);
        console.error('Pyodide init error:', error);
    }
}

// Handle file selection
fileInput.addEventListener('change', () => {
    updateButtonState();
});

function updateButtonState() {
    convertBtn.disabled = !pyodideReady || !fileInput.files.length;
}

// Handle conversion
convertBtn.addEventListener('click', async () => {
    if (!pyodideReady || !fileInput.files.length) return;

    const file = fileInput.files[0];
    const format = formatSelect.value;

    setStatus('loading', '<span class="spinner"></span>Converting...');
    convertBtn.disabled = true;

    try {
        // Read file as ArrayBuffer
        const arrayBuffer = await file.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);

        // Pass to Python
        pyodide.globals.set('xml_bytes', uint8Array);
        pyodide.globals.set('output_format', format);

        const result = await pyodide.runPythonAsync(`
from esf_convert.cli import parse_esf_xml, generate_markdown, generate_docx

# Parse the XML bytes directly (supported in esf-convert >= 0.2.0)
data = parse_esf_xml(bytes(xml_bytes))

# Get a suggested filename from the reference number
ref = data.get('metadata', {}).get('edoc_ref', 'output')
base_filename = ref.replace('/', '_').replace('\\\\', '_')

if output_format == 'md':
    md_text = generate_markdown(data)
    result = (
        md_text.encode('utf-8'),
        f"{base_filename}.md",
        'text/markdown'
    )
else:
    # generate_docx returns bytes when output_path is None (esf-convert >= 0.2.0)
    docx_bytes = generate_docx(data)
    result = (
        docx_bytes,
        f"{base_filename}.docx",
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
result
        `);

        // Extract result tuple
        const outputBytes = result.get(0);
        const filename = result.get(1);
        const mimeType = result.get(2);

        // Convert Python bytes to JavaScript Uint8Array
        const jsBytes = outputBytes.toJs();

        // Trigger download
        downloadFile(jsBytes, filename, mimeType);

        setStatus('success', 'Conversion complete! Download started.');

    } catch (error) {
        setStatus('error', 'Conversion failed: ' + error.message);
        console.error('Conversion error:', error);
    } finally {
        updateButtonState();
    }
});

function downloadFile(bytes, filename, mimeType) {
    const blob = new Blob([bytes], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
}

function setStatus(type, message) {
    status.className = type;
    status.innerHTML = message;
    status.style.display = 'block';
}

// Load Pyodide from CDN
const script = document.createElement('script');
script.src = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js';
script.onload = initPyodide;
document.head.appendChild(script);
