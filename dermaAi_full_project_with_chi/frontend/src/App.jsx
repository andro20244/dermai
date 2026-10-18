import { useEffect, useState } from 'react';
import {
  Activity, ArrowLeft, ArrowRight, BookOpen, Camera, Check, ClipboardList,
  Database, ImagePlus, LogIn, LogOut, Pill, Search, ShieldCheck, Snowflake,
  Stethoscope, Syringe, Sun, Upload, Zap,
} from 'lucide-react';

const API_ROOT = '/api/v1/';
const PAGE_SIZE = 25;

const modules = [
  { id: 'dermoscopy', label: 'Dermoscopy', group: 'CLINICAL TOOLS', icon: Camera },
  { id: 'medication', label: 'Medication reference', group: 'CLINICAL TOOLS', icon: Pill },
  { id: 'cryotherapy', label: 'Cryotherapy', group: 'PROCEDURES', icon: Snowflake },
  { id: 'electrosurgery', label: 'Electrosurgery', group: 'PROCEDURES', icon: Zap },
  { id: 'laser', label: 'Laser', group: 'PROCEDURES', icon: Zap },
  { id: 'fillers', label: 'Fillers', group: 'PROCEDURES', icon: Syringe },
  { id: 'botox', label: 'Botox', group: 'PROCEDURES', icon: Activity },
  { id: 'uvb', label: 'UVB phototherapy', group: 'PROCEDURES', icon: Sun },
];

const procedures = {
  cryotherapy: {
    title: 'Cryotherapy',
    intro: 'Review a case for an indication-specific freeze and thaw protocol.',
    fields: [
      ['age', 'Age', 'number'], ['site', 'Treatment site', 'text'],
      ['disease', 'Diagnosis', 'text'], ['lesion_type', 'Lesion type', 'text'],
    ],
  },
  electrosurgery: {
    title: 'Electrosurgery',
    intro: 'Record lesion and device context for a device-specific electrosurgery review.',
    fields: [
      ['age', 'Age', 'number'], ['sex', 'Sex', 'select', ['Select', 'Female', 'Male', 'Other']],
      ['disease', 'Diagnosis', 'text'], ['site', 'Treatment site', 'text'],
      ['lesion_type', 'Lesion type', 'text'], ['lesion_count', 'Number of lesions', 'number'],
      ['device_type', 'Device / handpiece', 'text'],
    ],
  },
  laser: {
    title: 'Laser planning',
    intro: 'Capture patient and device details for a device-specific review.',
    fields: [
      ['age', 'Age', 'number'], ['sex', 'Sex', 'select', ['Select', 'Female', 'Male', 'Other']],
      ['disease', 'Indication', 'text'], ['site', 'Treatment site', 'text'],
      ['skin_phototype', 'Fitzpatrick skin type', 'select', ['Select', 'I', 'II', 'III', 'IV', 'V', 'VI']],
      ['hair_color', 'Hair colour', 'select', ['Select', 'Black', 'Brown', 'Blonde', 'Red', 'Grey', 'White']],
      ['hair_thickness', 'Hair thickness', 'select', ['Select', 'Fine', 'Medium', 'Coarse']],
      ['device_type', 'Device / modality', 'text'],
    ],
  },
  fillers: {
    title: 'Filler planning',
    intro: 'Capture context for a product- and anatomy-specific review.',
    fields: [
      ['age', 'Age', 'number'], ['sex', 'Sex', 'select', ['Select', 'Female', 'Male', 'Other']],
      ['disease', 'Indication / history', 'text'], ['site', 'Anatomical site', 'text'],
      ['product', 'Product under consideration', 'text'],
    ],
  },
  botox: {
    title: 'Botulinum toxin',
    intro: 'Capture context for a product- and indication-specific review.',
    fields: [
      ['age', 'Age', 'number'], ['sex', 'Sex', 'select', ['Select', 'Female', 'Male', 'Other']],
      ['disease', 'Indication / history', 'text'], ['site', 'Anatomical site', 'text'],
      ['product', 'Product under consideration', 'text'],
    ],
  },
  uvb: {
    title: 'UVB phototherapy',
    intro: 'Capture patient and diagnosis details for a phototherapy review.',
    fields: [
      ['age', 'Age', 'number'], ['disease', 'Diagnosis', 'text'],
      ['site', 'Treatment area', 'text'],
      ['skin_phototype', 'Fitzpatrick skin type', 'select', ['Select', 'I', 'II', 'III', 'IV', 'V', 'VI']],
      ['treatment_history', 'Phototherapy history', 'text'],
    ],
  },
};

async function apiRequest(path, options = {}, token = '') {
  const headers = new Headers(options.headers || {});
  if (token) headers.set('Authorization', `Token ${token}`);
  const response = await fetch(`${API_ROOT}${path}`, { ...options, headers });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail || data?.error || `Request failed (${response.status}).`);
  return data;
}

function App() {
  const [activeModule, setActiveModule] = useState('dermoscopy');
  const [token, setToken] = useState(() => sessionStorage.getItem('dermaai-token') || '');
  const [username, setUsername] = useState(() => sessionStorage.getItem('dermaai-username') || '');
  const [login, setLogin] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [caseList, setCaseList] = useState([]);
  const [reviewImage, setReviewImage] = useState('');
  const [reviewingCase, setReviewingCase] = useState(0);
  const [dermoscopyCase, setDermoscopyCase] = useState({ age: '', sex: '', skin_phototype: '', localization: '', confirmed_diagnosis: '', clinical_notes: '', consent_for_training: false });
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [modelStatus, setModelStatus] = useState(null);
  const [consentToExternalProcessing, setConsentToExternalProcessing] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [predictionError, setPredictionError] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const [uploadError, setUploadError] = useState('');
  const [savingCase, setSavingCase] = useState(false);
  const [medicineQuery, setMedicineQuery] = useState('');
  const [medicineMode, setMedicineMode] = useState('diagnosis');
  const [medicineResults, setMedicineResults] = useState([]);
  const [medicineCount, setMedicineCount] = useState(0);
  const [medicineLoading, setMedicineLoading] = useState(false);
  const [medicineError, setMedicineError] = useState('');
  const [procedureValues, setProcedureValues] = useState({});
  const [procedureState, setProcedureState] = useState('');
  const [procedureError, setProcedureError] = useState('');

  useEffect(() => {
    setConsentToExternalProcessing(false);
    setPrediction(null);
    setPredictionError('');
    if (!imageFile) {
      setImagePreview('');
      return undefined;
    }
    const url = URL.createObjectURL(imageFile);
    setImagePreview(url);
    return () => URL.revokeObjectURL(url);
  }, [imageFile]);

  useEffect(() => () => {
    if (reviewImage) URL.revokeObjectURL(reviewImage);
  }, [reviewImage]);

  useEffect(() => {
    if (!token) {
      setCaseList([]);
      return;
    }
    apiRequest('dermoscopy/submissions/', {}, token)
      .then((data) => setCaseList(data.results || []))
      .catch(() => setCaseList([]));
  }, [token]);

  useEffect(() => {
    if (activeModule !== 'dermoscopy') return undefined;
    const controller = new AbortController();
    fetch(`${API_ROOT}dermoscopy/model-status/`, { signal: controller.signal })
      .then((response) => response.json())
      .then(setModelStatus)
      .catch((error) => {
        if (error.name !== 'AbortError') setModelStatus({ available: false, detail: 'Could not check the hosted model status.' });
      });
    return () => controller.abort();
  }, [activeModule]);

  useEffect(() => {
    if (activeModule !== 'medication') return undefined;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      if (!medicineQuery.trim()) {
        setMedicineResults([]);
        setMedicineCount(0);
        return;
      }
      const params = new URLSearchParams({ q: medicineQuery.trim(), page: '1' });
      setMedicineLoading(true);
      setMedicineError('');
      fetch(`${API_ROOT}formulary/search-by-diagnosis/?${params}`, { signal: controller.signal })
        .then(async (response) => {
          const data = await response.json();
          if (!response.ok) throw new Error(data.detail || 'Could not search the formulary.');
          return data;
        })
        .then((data) => {
          setMedicineResults(data.results || []);
          setMedicineCount(data.count || 0);
        })
        .catch((error) => { if (error.name !== 'AbortError') setMedicineError(error.message); })
        .finally(() => { if (!controller.signal.aborted) setMedicineLoading(false); });
    }, 250);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [activeModule, medicineQuery]);

  const selectedModule = modules.find((item) => item.id === activeModule);

  async function handleLogin(event) {
    event.preventDefault();
    setLoginError('');
    try {
      const result = await apiRequest('auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(login),
      });
      sessionStorage.setItem('dermaai-token', result.token);
      sessionStorage.setItem('dermaai-username', result.username);
      setToken(result.token);
      setUsername(result.username);
      setLogin({ username: '', password: '' });
    } catch (error) {
      setLoginError(error.message);
    }
  }

  async function handleLogout() {
    try { await apiRequest('auth/logout/', { method: 'POST' }, token); } catch { /* Expired tokens are cleared locally. */ }
    sessionStorage.removeItem('dermaai-token');
    sessionStorage.removeItem('dermaai-username');
    setToken('');
    setUsername('');
    setCaseList([]);
  }

  async function handleDermoscopySubmit(event) {
    event.preventDefault();
    setUploadError('');
    setUploadMessage('');
    if (!token) {
      setUploadError('Sign in with a clinician account to save a case.');
      return;
    }
    if (!imageFile) {
      setUploadError('Choose a dermoscopy image first.');
      return;
    }
    const form = new FormData();
    Object.entries(dermoscopyCase).forEach(([key, value]) => form.append(key, String(value)));
    form.append('image', imageFile);
    setSavingCase(true);
    try {
      const saved = await apiRequest('dermoscopy/submissions/', { method: 'POST', body: form }, token);
      setUploadMessage(`Case ${saved.id} saved. Any prediction must be requested separately and reviewed by a clinician.`);
      setCaseList((current) => [saved, ...current]);
      setImageFile(null);
      setDermoscopyCase({ age: '', sex: '', skin_phototype: '', localization: '', confirmed_diagnosis: '', clinical_notes: '', consent_for_training: false });
    } catch (error) {
      setUploadError(error.message);
    } finally {
      setSavingCase(false);
    }
  }

  async function handleReviewImage(id) {
    setReviewingCase(id);
    setUploadError('');
    try {
      const response = await fetch(`${API_ROOT}dermoscopy/submissions/${id}/image/`, {
        headers: { Authorization: `Token ${token}` },
      });
      if (!response.ok) throw new Error('Could not open this private case image.');
      const imageUrl = URL.createObjectURL(await response.blob());
      setReviewImage((current) => {
        if (current) URL.revokeObjectURL(current);
        return imageUrl;
      });
    } catch (error) {
      setUploadError(error.message);
    } finally {
      setReviewingCase(0);
    }
  }

  async function handlePrediction() {
    setPrediction(null);
    setPredictionError('');
    if (!token) {
      setPredictionError('Sign in with a verified clinician account to request a prediction.');
      return;
    }
    if (!imageFile || !consentToExternalProcessing) return;
    const form = new FormData();
    form.append('image', imageFile);
    form.append('consent_to_external_processing', 'true');
    setAnalyzing(true);
    try {
      const result = await apiRequest('dermoscopy/predict/', { method: 'POST', body: form }, token);
      setPrediction(result);
    } catch (error) {
      setPredictionError(error.message);
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleProcedureSubmit(event) {
    event.preventDefault();
    setProcedureState('');
    setProcedureError('');
    if (!token) {
      setProcedureError('Sign in with a clinician account to review procedure cases.');
      return;
    }
    try {
      await apiRequest(`protocols/${activeModule}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(procedureValues),
      }, token);
    } catch (error) {
      if (error.message.includes('clinically validated') || error.message.includes('No verified protocol')) {
        setProcedureState('No validated protocol source is configured. No settings or instructions were generated.');
      } else {
        setProcedureError(error.message);
      }
    }
  }

  function renderField([name, label, type, choices]) {
    return (
      <label className="field" key={name}>
        <span>{label}</span>
        {type === 'select' ? (
          <select required value={procedureValues[name] || ''} onChange={(event) => setProcedureValues((values) => ({ ...values, [name]: event.target.value }))}>
            {choices.map((choice) => <option key={choice} value={choice === 'Select' ? '' : choice}>{choice}</option>)}
          </select>
        ) : (
          <input required min={type === 'number' ? 0 : undefined} max={type === 'number' ? 120 : undefined} type={type} value={procedureValues[name] || ''} onChange={(event) => setProcedureValues((values) => ({ ...values, [name]: event.target.value }))} />
        )}
      </label>
    );
  }

  const procedure = procedures[activeModule];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#main" aria-label="DermaAI home">
          <span className="brand-mark"><Activity size={21} strokeWidth={2.4} /></span>
          <span className="brand-name">derma<span>ai</span></span>
        </a>
        {['CLINICAL TOOLS', 'PROCEDURES'].map((group) => (
          <div className="nav-group" key={group}>
            <div className="workspace-label">{group}</div>
            <nav aria-label={group.toLowerCase()}>
              {modules.filter((item) => item.group === group).map(({ id, label, icon: Icon }) => (
                <button className={`nav-link ${activeModule === id ? 'active' : ''}`} key={id} onClick={() => setActiveModule(id)}>
                  <Icon size={17} /><span>{label}</span>
                </button>
              ))}
            </nav>
          </div>
        ))}
        <div className="sidebar-bottom">
          <div className="support-link"><ShieldCheck size={16} /><span>Local, private workspace</span></div>
          <div className="sidebar-rule" />
          <div className="profile">
            <div className="profile-icon"><Stethoscope size={16} /></div>
            <div><strong>{username || 'Clinician workspace'}</strong><span>{token ? 'Signed in' : 'Not signed in'}</span></div>
            <span className={`online-dot ${token ? '' : 'offline'}`} aria-label={token ? 'Signed in' : 'Signed out'} />
          </div>
        </div>
      </aside>

      <main id="main" className="main-area">
        <header className="topbar">
          <div className="breadcrumb"><span>DermaAI</span><span className="crumb-divider">/</span><strong>{selectedModule?.label}</strong></div>
          <div className="account-actions">
            <div className="secure-label"><ShieldCheck size={15} /> Private local workspace</div>
            {token && <button className="text-action" onClick={handleLogout}><LogOut size={15} /> Sign out</button>}
          </div>
        </header>

        <div className="content">
          {activeModule === 'dermoscopy' && (
            <>
              <PageHeading eyebrow="IMAGE REVIEW" title="Dermoscopy" intro="Capture a lesion image and clinical context for clinician review." badge={modelStatus?.available ? 'Hosted HAM10000 · Online' : 'Hosted HAM10000 · Unavailable'} />
              <div className="dermoscopy-layout">
                <form className="workspace-panel" onSubmit={handleDermoscopySubmit}>
                  <div className="panel-heading"><div><h2>New case</h2><p>Patient details and lesion image</p></div><span className="step-label">01 <i>/</i> CASE</span></div>
                  <label className={`image-drop ${imagePreview ? 'has-preview' : ''}`}>
                    {imagePreview ? <img src={imagePreview} alt="Selected dermoscopy case" /> : <><span className="drop-icon"><ImagePlus size={22} /></span><strong>Choose dermoscopy image</strong><span>JPEG or PNG · up to 10 MB</span></>}
                    <input accept="image/jpeg,image/png,image/webp" onChange={(event) => setImageFile(event.target.files?.[0] || null)} type="file" />
                  </label>
                  <div className="field-grid two-col">
                    <label className="field"><span>Age</span><input max="120" min="0" onChange={(event) => setDermoscopyCase((value) => ({ ...value, age: event.target.value }))} type="number" value={dermoscopyCase.age} /></label>
                    <label className="field"><span>Sex</span><select onChange={(event) => setDermoscopyCase((value) => ({ ...value, sex: event.target.value }))} value={dermoscopyCase.sex}><option value="">Not specified</option><option>Female</option><option>Male</option><option>Other</option></select></label>
                    <label className="field"><span>Skin phototype</span><select onChange={(event) => setDermoscopyCase((value) => ({ ...value, skin_phototype: event.target.value }))} value={dermoscopyCase.skin_phototype}><option value="">Not specified</option>{['I', 'II', 'III', 'IV', 'V', 'VI'].map((type) => <option key={type}>{type}</option>)}</select></label>
                    <label className="field"><span>Lesion site</span><input onChange={(event) => setDermoscopyCase((value) => ({ ...value, localization: event.target.value }))} required type="text" value={dermoscopyCase.localization} /></label>
                  </div>
                  <label className="field"><span>Clinician-confirmed diagnosis <em>Optional until reviewed</em></span><input onChange={(event) => setDermoscopyCase((value) => ({ ...value, confirmed_diagnosis: event.target.value }))} type="text" value={dermoscopyCase.confirmed_diagnosis} /></label>
                  <label className="field"><span>Clinical notes</span><textarea onChange={(event) => setDermoscopyCase((value) => ({ ...value, clinical_notes: event.target.value }))} rows="3" value={dermoscopyCase.clinical_notes} /></label>
                  <label className="consent-field"><input checked={dermoscopyCase.consent_for_training} onChange={(event) => setDermoscopyCase((value) => ({ ...value, consent_for_training: event.target.checked }))} type="checkbox" /><span>Patient has consented to use this image for future model training. A confirmed clinician diagnosis is also required.</span></label>
                  <label className="consent-field external-consent"><input checked={consentToExternalProcessing} onChange={(event) => { setConsentToExternalProcessing(event.target.checked); setPrediction(null); setPredictionError(''); }} type="checkbox" /><span>I consent to send this image to the third-party Hugging Face HAM10000 research model for analysis. Do not use patient-identifiable images.</span></label>
                  <div className="prediction-actions"><button className="secondary-button" disabled={!token || !imageFile || !consentToExternalProcessing || !modelStatus?.available || analyzing} onClick={handlePrediction} type="button">{analyzing ? 'Analyzing image…' : 'Analyze with hosted model'}</button><span>Image is sent only when you select Analyze.</span></div>
                  {predictionError && <div className="inline-message error-message">{predictionError}</div>}
                  {prediction && <div className="prediction-result"><div className="result-heading"><div><div className="status-eyebrow">RESEARCH MODEL OUTPUT</div><h3>{prediction.predicted_class}</h3></div><strong>{Math.round(prediction.confidence * 100)}%</strong></div><div className="probability-list">{Object.entries(prediction.all_probabilities).sort((first, second) => second[1] - first[1]).slice(0, 4).map(([label, score]) => <div className="probability-row" key={label}><span>{label}</span><span>{Math.round(score * 100)}%</span><div><i style={{ width: `${Math.max(0, Math.min(100, score * 100))}%` }} /></div></div>)}</div><p>{prediction.disclaimer}</p></div>}
                  {uploadError && <div className="inline-message error-message">{uploadError}</div>}
                  {uploadMessage && <div className="inline-message info-message">{uploadMessage}</div>}
                  <div className="form-actions"><span>{token ? `Saving as ${username}` : 'Sign in required to save a private case'}</span><button className="primary-button" disabled={!token || savingCase} type="submit"><Upload size={16} />{savingCase ? 'Saving case…' : 'Save case'}</button></div>
                </form>

                <aside className="insight-column">
                  <div className="model-status-panel">
                    <div className="status-icon"><Activity size={19} /></div>
                    <div className="status-eyebrow">IMAGE CLASSIFIER</div>
                    <h2>{modelStatus?.available ? 'Hosted model available' : 'Model unavailable'}</h2>
                    <p>{modelStatus?.available ? 'A community-hosted HAM10000 classifier is reachable. Its output is research-only and images leave this device only after explicit consent.' : modelStatus?.detail || 'Checking the hosted HAM10000 model…'}</p>
                    <div className="status-rule" />
                    <div className="status-foot"><span className={`status-dot ${modelStatus?.available ? '' : 'warning'}`} /> {modelStatus?.available ? 'Hugging Face community endpoint' : 'Hosted endpoint unavailable'}</div>
                  </div>
                  {token ? (
                    <div className="recent-panel"><div className="recent-heading"><h2>Recent cases</h2><span>{caseList.length}</span></div>{caseList.slice(0, 5).map((item) => <div className="case-row" key={item.id}><div><strong>{item.confirmed_diagnosis || 'Awaiting clinician review'}</strong><span>{item.localization} · {new Date(item.submitted_at).toLocaleDateString()}</span></div><button disabled={reviewingCase === item.id} onClick={() => handleReviewImage(item.id)} aria-label={`Review case ${item.id} image`}><Camera size={15} /></button></div>)}{reviewImage && <img className="review-image" src={reviewImage} alt="Private dermoscopy case selected for review" />}{uploadError && <div className="inline-message error-message">{uploadError}</div>}{caseList.length === 0 && <p className="muted-copy">Saved cases will appear here.</p>}</div>
                  ) : <LoginPanel login={login} onChange={setLogin} onSubmit={handleLogin} error={loginError} />}
                </aside>
              </div>
              <ClinicalNote>Images are stored locally in the Docker data volume and can only be reviewed by the authenticated clinician who submitted them or an administrator.</ClinicalNote>
            </>
          )}

          {activeModule === 'medication' && (
            <>
              <PageHeading eyebrow="CHI EDITION 59" title="Medication reference" intro="Find formulary medicines by diagnosis, or review the indications recorded for a medicine." badge="26,134 CHI entries" />
              <div className="mode-switch" role="group" aria-label="Medication search direction">
                <button className={medicineMode === 'diagnosis' ? 'selected' : ''} onClick={() => { setMedicineMode('diagnosis'); setMedicineQuery(''); }}><Stethoscope size={15} /> Diagnosis to medicines</button>
                <button className={medicineMode === 'medicine' ? 'selected' : ''} onClick={() => { setMedicineMode('medicine'); setMedicineQuery(''); }}><Pill size={15} /> Medicine to indications</button>
              </div>
              <section className="search-panel" aria-label="Search CHI formulary"><div className="search-icon"><Search size={20} /></div><input aria-label={medicineMode === 'diagnosis' ? 'Search diagnoses or ICD-10 code' : 'Search medicines'} autoComplete="off" onChange={(event) => setMedicineQuery(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && event.currentTarget.blur()} placeholder={medicineMode === 'diagnosis' ? 'Diagnosis, indication, or ICD-10 code' : 'Generic name or pharmacological class'} type="search" value={medicineQuery} /><kbd>CHI</kbd></section>
              <section className="summary-row"><div className="summary-title"><span className="summary-icon"><Database size={17} /></span><div><strong>{medicineCount.toLocaleString()} formulary matches</strong><span>{medicineQuery ? `For “${medicineQuery}”` : 'Start typing to search the reference'}</span></div></div><div className="summary-meta"><span className="availability"><span /> Edition 59</span></div></section>
              <div className="medicine-results">
                {medicineLoading && <div className="empty-state"><span className="spinner" /> Searching CHI formulary…</div>}
                {!medicineLoading && medicineError && <div className="empty-state error-message">{medicineError}</div>}
                {!medicineLoading && !medicineError && medicineQuery && medicineResults.length === 0 && <div className="empty-state">No matching CHI entries. Try a broader term.</div>}
                {!medicineLoading && medicineResults.map((entry) => <article className="medicine-card" key={entry.id}><div className="medicine-card-top"><span className="indication-tag">{entry.icd_10_code || 'INDICATION'}</span><span className="route-label">{entry.administration_route || 'Route not listed'}</span></div><h2>{medicineMode === 'diagnosis' ? entry.scientific_name : entry.indication}</h2><p>{medicineMode === 'diagnosis' ? entry.indication : `Medicine: ${entry.scientific_name}`} · {entry.pharmacological_class || 'Class not specified'}</p><div className="medicine-card-meta"><span>{entry.pharmaceutical_form || 'Form not listed'}</span><strong>{[entry.strength, entry.strength_unit].filter(Boolean).join(' ') || 'Strength not listed'}</strong>{entry.mdd_adults && <span>Adult MDD: {entry.mdd_adults}</span>}</div>{entry.notes && <div className="entry-notes">{entry.notes}</div>}</article>)}
                {!medicineQuery && !medicineLoading && <div className="empty-state search-hint"><Search size={20} /><strong>Search the CHI reference</strong><span>Results show the source indication and medicine details. They are not AI-generated prescribing advice.</span></div>}
              </div>
              <ClinicalNote>Formulary results are reference matches, not personalized prescriptions. Verify the current CHI source, product information, contraindications, and patient-specific factors.</ClinicalNote>
            </>
          )}

          {procedure && (
            <>
              <PageHeading eyebrow="PROCEDURE REVIEW" title={procedure.title} intro={procedure.intro} badge="Protocol source · Not configured" />
              <div className="procedure-layout">
                <form className="workspace-panel" onSubmit={handleProcedureSubmit}>
                  <div className="panel-heading"><div><h2>Case details</h2><p>Patient and treatment context</p></div><span className="step-label">CASE <i>/</i> REVIEW</span></div>
                  <div className="field-grid two-col">{procedure.fields.map(renderField)}</div>
                  {procedureError && <div className="inline-message error-message">{procedureError}</div>}
                  {procedureState && <div className="protocol-unavailable"><ShieldCheck size={19} /><div><strong>Parameters withheld</strong><span>{procedureState}</span>{activeModule === 'electrosurgery' && <div className="arabic-guidance" dir="rtl"><div><strong>تعليمات ما قبل الإجراء</strong><span>غير متاحة حتى إضافة بروتوكول معتمد خاص بالجهاز.</span></div><div><strong>تعليمات ما بعد الإجراء</strong><span>غير متاحة حتى إضافة بروتوكول معتمد خاص بالجهاز.</span></div></div>}</div></div>}
                  <div className="form-actions"><span>Requires an authenticated clinician account</span><button className="primary-button" disabled={!token} type="submit"><ClipboardList size={16} />Review protocol</button></div>
                </form>
                <aside className="insight-column"><div className="model-status-panel protocol-panel"><div className="status-icon"><ShieldCheck size={19} /></div><div className="status-eyebrow">CLINICAL SOURCE</div><h2>{activeModule === 'electrosurgery' ? 'Power & anaesthesia withheld' : 'Protocol not configured'}</h2><p>{activeModule === 'electrosurgery' ? 'Power settings depend on the exact generator, waveform, electrode, and indication. Anaesthesia and Arabic instructions require an approved device-specific protocol.' : 'The supplied archive contains no validated procedure parameters, device manuals, or Arabic patient instructions for this module.'}</p>{activeModule === 'electrosurgery' && <div className="arabic-guidance" dir="rtl"><div><strong>قبل الإجراء</strong><span>لا توجد تعليمات معتمدة مُعدّة لهذا الجهاز.</span></div><div><strong>بعد الإجراء</strong><span>لا توجد تعليمات معتمدة مُعدّة لهذا الجهاز.</span></div></div>}<div className="status-rule" /><div className="status-foot"><span className="status-dot warning" /> No settings will be generated</div></div><LoginPanel login={login} onChange={setLogin} onSubmit={handleLogin} error={loginError} compact /></aside>
              </div>
              <ClinicalNote>Patient details are not saved by these procedure forms. No freeze/thaw cycles, electrosurgery power or anaesthesia, laser settings, injectable products or amounts, UVB dose, or pre/post instructions are available until reviewed sources are supplied.</ClinicalNote>
            </>
          )}

          <footer className="page-footer"><span>DERMAAI <i>·</i> CLINICIAN WORKSPACE</span><span>Local reference build</span></footer>
        </div>
      </main>
    </div>
  );
}

function PageHeading({ eyebrow, title, intro, badge }) {
  return <section className="page-heading"><div><div className="eyebrow"><span className="eyebrow-line" /> {eyebrow}</div><h1>{title}</h1><p className="intro">{intro}</p></div><div className="source-badge"><span className="source-dot" />{badge}</div></section>;
}

function LoginPanel({ login, onChange, onSubmit, error, compact = false }) {
  return (
    <form className={`login-panel ${compact ? 'compact' : ''}`} onSubmit={onSubmit}>
      <div className="login-heading"><LogIn size={17} /><h2>Clinician sign in</h2></div>
      <label className="field"><span>Username</span><input autoComplete="username" onChange={(event) => onChange((value) => ({ ...value, username: event.target.value }))} required value={login.username} /></label>
      <label className="field"><span>Password</span><input autoComplete="current-password" onChange={(event) => onChange((value) => ({ ...value, password: event.target.value }))} required type="password" value={login.password} /></label>
      {error && <div className="inline-message error-message">{error}</div>}
      <button className="secondary-button" type="submit">Sign in to access private cases</button>
    </form>
  );
}

function ClinicalNote({ children }) {
  return <div className="clinical-note"><ShieldCheck size={16} /><p><strong>Clinical safety.</strong> {children}</p></div>;
}

export default App;